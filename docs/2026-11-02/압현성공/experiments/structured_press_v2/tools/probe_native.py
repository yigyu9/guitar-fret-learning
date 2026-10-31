"""학습 전에 실제 GPU에서 초기 자세와 유한 PD 유지의 안전성을 검사한다."""
import isaacgym
import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path
import torch
from guitar_learning.tool.experiments.structured_geometry import nested_input_paths


def pose_sha(q, hold):
    return hashlib.sha256(struct.pack('<210f', *(list(q)+list(hold)))).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--stage', choices=('A', 'B'), default='A')
    parser.add_argument('--song')
    parser.add_argument('--include-center', action='store_true')
    parser.add_argument('--render-initial-only', action='store_true')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(args.catalog.read_text())
    geometry = args.catalog
    if args.include_center:
        if args.stage != 'B':
            raise ValueError('center plus perturbation batch requires B hold probe')
        catalog = copy.deepcopy(catalog)
        for goal in catalog['goals']:
            goal['perturbations'].append(dict(q105=goal['q105'], candidate_valid=True,
                native_verified=False, probe_center=True))
        geometry = args.out/'probe_catalog.json'
        geometry.write_text(json.dumps(catalog, ensure_ascii=False))
    report = dict(stage=args.stage, scope='native finite-PD hold; no learning or forced joint state during episode', goals=[])
    if args.render_initial_only:
        report['scope'] = 'native first 60Hz endpoint images only; not a six-second safety probe'
    with nested_input_paths():
        from guitar_learning.tool.experiments.structured_press import build_settings, structured_runtime, StructuredPool
        for goal in catalog['goals']:
            if args.song and goal['song'] != args.song:
                continue
            torch.manual_seed(7)
            settings = build_settings(goal['song'], args.stage, geometry,
                num_envs=64 if args.stage == 'B' else 4, updates=1, allow_unverified=True)
            out = args.out/goal['song']
            out.mkdir(parents=True, exist_ok=True)
            with structured_runtime(settings['structured_press']):
                if args.render_initial_only:
                    from isaacgym import gymapi
                    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym
                    from guitar_learning.tool.demonstration.render_finger_skill import _create_cameras
                    original_gym = gymapi.acquire_gym
                    gymapi.acquire_gym = lambda: GraphicsGym(original_gym())
                    try:
                        pool = StructuredPool(settings, out)
                    finally:
                        gymapi.acquire_gym = original_gym
                    cameras = _create_cameras(pool.scene, gymapi)
                else:
                    pool = StructuredPool(settings, out)
                try:
                    env, scene = pool.environment, pool.scene
                    torch.testing.assert_close(scene.reference105,
                        torch.tensor(catalog['reference105'], device=scene.device), rtol=0, atol=0)
                    initial = scene.q.clone()
                    hold = env.hold_action.clone()
                    torch.testing.assert_close(env.previous_action, hold, rtol=0, atol=0)
                    initial_rows = []
                    for index in range(pool.num_envs):
                        variant = None
                        if args.stage == 'B':
                            errors = [(initial[index]-torch.tensor(p['q105'], device=initial.device)).abs().max().item()
                                      for p in goal['perturbations']]
                            variant = min(range(len(errors)), key=errors.__getitem__)
                            assert errors[variant] < 1e-5
                        initial_rows.append(dict(env=index, variant=variant,
                            pose_sha256=pose_sha(initial[index].cpu().tolist(), scene.initial_hold[index].cpu().tolist()),
                            height_m=float(env.surface_height[index, 0]),
                            distance_m=float(env.surface_distance[index, 0]),
                            normal_cos=float(env.surface_alignment[index, 0]),
                            candidate=bool(env.candidate[index, 0]), wrong=bool(env.wrong[index, 0]),
                            wrist_excess_m=env.guide['delta'][index].cpu().tolist()))
                    alive = torch.ones(pool.num_envs, dtype=torch.bool, device=scene.device)
                    prepress = torch.zeros_like(alive)
                    first_prepress = {}
                    substep_prepress = torch.zeros_like(alive)
                    original_substep = env.substep
                    def record_substep(sample):
                        original_substep(sample)
                        before_onset = env._local_time() < 3.-1e-8
                        substep_prepress.logical_or_(alive & before_onset &
                            (env.candidate[:, 0] | env.wrong[:, 0]))
                    env.substep = record_substep
                    max_arm_drift = torch.zeros(pool.num_envs, device=scene.device)
                    first_physics = None
                    episodes = []
                    for tick in range(1 if args.render_initial_only else 360):
                        _, _, _, terminated, truncated, rows = pool.step(hold)
                        if args.render_initial_only:
                            import numpy as np
                            from PIL import Image
                            scene.gym.step_graphics(scene.sim)
                            scene.gym.render_all_camera_sensors(scene.sim)
                            for name, camera in cameras.items():
                                pixels = scene.gym.get_camera_image(scene.sim, scene.envs[0], camera, gymapi.IMAGE_COLOR)
                                rgb = np.asarray(pixels).reshape(720, 1280, 4)[..., :3].copy()
                                Image.fromarray(rgb).save(out/(name+'.png'))
                        if tick < 180:
                            fresh = alive & ~prepress & (env.candidate[:, 0] | env.wrong[:, 0])
                            for index in fresh.nonzero().flatten().cpu().tolist():
                                first_prepress[str(index)] = dict(tick=tick+1,
                                    candidate=bool(env.candidate[index, 0]), wrong=bool(env.wrong[index, 0]),
                                    height_m=float(env.surface_height[index, 0]),
                                    distance_m=float(env.surface_distance[index, 0]),
                                    source_flags=env.wrong_source_flags[index].cpu().tolist())
                            prepress |= alive & (env.candidate[:, 0] | env.wrong[:, 0])
                        drift = (scene.q[:, pool.controller.active[:12]]-
                                 initial[:, pool.controller.active[:12]]).abs().amax(-1)
                        max_arm_drift = torch.maximum(max_arm_drift, torch.where(alive, drift, 0.))
                        if first_physics is None:
                            first_physics = [dict(height_m=float(env.surface_height[i, 0]),
                                distance_m=float(env.surface_distance[i, 0]),
                                normal_cos=float(env.surface_alignment[i, 0]),
                                candidate=bool(env.candidate[i, 0]), wrong=bool(env.wrong[i, 0]),
                                wrist_excess_m=env.guide['delta'][i].cpu().tolist())
                                for i in range(pool.num_envs)]
                        episodes.extend(row for row in rows if bool(alive[row['env_id']]))
                        done = terminated | truncated
                        alive &= ~done
                        if not bool(alive.any()):
                            break
                        ids = done.nonzero().flatten()
                        if len(ids):
                            # 첫 에피소드 통계는 이미 닫혔다. 나머지 환경을 계속 검사하기
                            # 위해 종료 행만 정상 reset하며 이후 에피소드의 통계는 버린다.
                            pool.reset(ids)
                            hold[ids] = env.hold_action[ids]
                    row = dict(song=goal['song'], initial=initial_rows, first_physics=first_physics,
                        v9_reference_unchanged=True,
                        center_pose_sha256=pose_sha(goal['q105'], goal['hold_target105']),
                        center_variant=len(goal['perturbations'])-1 if args.include_center else None,
                        pretarget_press=prepress.cpu().tolist(),
                        first_prepress=first_prepress,
                        pretarget_press_240hz=substep_prepress.cpu().tolist(),
                        max_arm_drift_rad=max_arm_drift.cpu().tolist(), ticks=tick+1, episodes=episodes)
                    report['goals'].append(row)
                    (args.out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
                    print(json.dumps(dict(song=goal['song'], ticks=tick+1,
                        prepress=int(prepress.sum()), completed=len(episodes)), ensure_ascii=False), flush=True)
                finally:
                    pool.close()


if __name__ == '__main__':
    main()
