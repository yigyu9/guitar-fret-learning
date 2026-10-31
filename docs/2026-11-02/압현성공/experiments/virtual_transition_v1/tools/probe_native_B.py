"""새 B 후보를 실제 GPU 물리에서 유지한다. 압현 학습 성공 검사가 아니다.

후보 상태는 reset 때만 적용한다. 이후에는 기존 제어기의 목표각/하체 제어로
2초를 진행하며 실제 패드와 B 셀의 거리 및 물리 실패를 기록한다.
"""
if __name__ == '__main__':
    import isaacgym

import argparse
import copy
import hashlib
import json
from pathlib import Path

import torch
from guitar_learning.training.launch import settings_document
from guitar_learning.training.rollout import GpuPool
from guitar_learning.tool.experiments import natural_press as natural
from guitar_learning.gpu.contact import measure_wrist_region

HERE = Path(__file__).resolve().parent.parent
SONG = 'virtual_middle_s3_f6_f7_ABAB_v1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    candidate_path = HERE/'geometry/candidate_B.json'
    candidate = json.loads(candidate_path.read_text())
    if not candidate['candidate_valid'] or candidate['native_verified']:
        raise ValueError('CPU 후보 원본과 검증 결과를 구분해야 함')
    config = natural.load_configuration('virtual_finger_v9_middle_s3_f6', 'E0', 'aligned', 'arm16')
    catalog, original = natural.catalog_goal(config)
    goal = copy.deepcopy(original)
    goal.update(state=candidate['state'], hold_target105=candidate['hold_target105'])

    class ProbePool(GpuPool):
        def _create_scene(self, settings, scene_out):
            factory = natural.catalog_goal
            natural.catalog_goal = lambda unused: (catalog, goal)
            try:
                return natural.NaturalScene(self.num_envs, 'left', device=settings['device'],
                    out=scene_out, natural_press=config)
            finally:
                natural.catalog_goal = factory

        def reset(self, indices=None):
            _, rows = super().reset(indices)
            ids = (torch.arange(self.num_envs, device=self.scene.device) if indices is None else
                torch.as_tensor(indices, device=self.scene.device, dtype=torch.long))
            self.controller.target[ids] = self.scene.initial_hold[ids]
            c = self.controller
            action = natural.normalized_action(c.target[:, c.active], c.reference[c.active],
                c.action_low, c.action_high)
            self.environment.previous_action[ids] = action[ids]
            self.observation = self.environment.observation()
            return self.observation, rows

    settings = settings_document(song=SONG, size='large', num_envs=4, horizon=32,
        updates=2, seed=7, checkpoint_every=100)
    (out/'settings.json').write_text(json.dumps(settings, ensure_ascii=False, indent=2))
    pool = None
    samples = []
    failed = []
    report = dict(schema='virtual_transition.native_B_probe.v1', passed=False,
        scope='B hover reachability/hold only; not learned pressing or dynamic A to B reachability',
        candidate_sha256=hashlib.sha256(candidate_path.read_bytes()).hexdigest())
    try:
        pool = ProbePool(settings, out)
        initial = pool.scene.q.clone()
        c = pool.controller
        action = natural.normalized_action(pool.scene.initial_hold[:, c.active],
            c.reference[c.active], c.action_low, c.action_high)
        for tick in range(120):
            _, _, _, terminated, truncated, episodes = pool.step(action)
            env = pool.environment
            wrist = measure_wrist_region(env.local_bodies[:, env.wrist_index],
                torch.full((pool.num_envs,), 5.5, device=env.device, dtype=torch.float64),
                env.wrist_region_times, env.wrist_region_lower, env.wrist_region_upper)
            normal = env.press_plane[:3]/torch.linalg.vector_norm(env.press_plane[:3])
            tangent = env.surface_delta[:, 1]+env.surface_height[:, 1, None]*normal
            samples.append(dict(time_s=(tick+1)/60., height_m=env.surface_height[:, 1].tolist(),
                distance_m=env.surface_distance[:, 1].tolist(), normal_cos=env.surface_alignment[:, 1].tolist(),
                tangent_distance_m=torch.linalg.vector_norm(tangent, dim=-1).tolist(),
                candidate=env.candidate[:, 1].tolist(), wrong=env.wrong[:, 1].tolist(),
                wrist_excess_m=wrist['delta'].tolist(),
                q_max_reset_delta_rad=(pool.scene.q-initial).abs().amax(-1).tolist()))
            if not torch.isfinite(pool.scene.q).all() or not torch.isfinite(pool.scene.body_state).all():
                raise FloatingPointError('비유한 native 상태')
            if episodes or bool((terminated | truncated).any()):
                failed.extend(episodes)
                break
        tail = samples[-30:]
        distances = [v for row in tail for v in row['distance_m']]
        heights = [v for row in tail for v in row['height_m']]
        normals = [v for row in tail for v in row['normal_cos']]
        tangents = [v for row in tail for v in row['tangent_distance_m']]
        excess = [abs(v) for row in tail for xyz in row['wrist_excess_m'] for v in xyz]
        report.update(physics_steps=pool.scene.physics_steps, control_ticks=len(samples),
            finite=True, reset_calls=pool.scene.reset_calls,
            final_half_second=dict(max_pad_distance_m=max(distances), height_range_m=[min(heights),max(heights)],
                min_normal_cos=min(normals), max_tangent_distance_m=max(tangents), max_B_wrist_axis_excess_m=max(excess)),
            failed_episodes=failed, samples=samples)
        report['passed'] = (len(samples) == 120 and not failed and max(distances) <= .03
            and min(heights) >= -.002 and max(heights) <= .03 and min(normals) >= .1
            and max(tangents) <= .006 and max(excess) <= .01)
    finally:
        if pool is not None:
            pool.close()
            report['scene_destroyed'] = pool.scene.closed
        (out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    if not report['passed']:
        raise RuntimeError('B native 도달/유지 조건 미충족; report.json 확인')


if __name__ == '__main__':
    main()
