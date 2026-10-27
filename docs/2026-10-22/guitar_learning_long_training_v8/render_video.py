"""Render best/latest evaluated-policy GPU world poses; never integrate physics."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


PHASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PHASE))
sys.path.insert(0, str(ROOT))
from evaluate_checkpoints import (require, select_video_env, sha, validate_capture, write, json_io,
    CHAIN_SCHEMA, CHECKPOINT_UPDATES, checkpoint_selection, validate_input_contract, posture_metadata)


def pose_state(body_names, frame, initial):
    """Keep every saved env-world pose; only reorder quaternion dictionary keys."""
    expected = (['human/'+n for n in initial['human_body_names']] +
                ['guitar/'+n for n in initial['guitar_body_names']] + ['chair/box'])
    require(body_names == expected and len(frame) == len(expected), 'Visual/source body order differs')
    state = {actor+'_body_states': [] for actor in ('human', 'guitar', 'chair')}
    for name, row in zip(body_names, frame):
        actor = name.split('/', 1)[0]
        state[actor+'_body_states'].append(dict(pose=dict(p=dict(zip('xyz', map(float, row[:3]))),
            r=dict(zip('xyzw', map(float, row[3:7]))))))
    return state


def string_endpoints(body_names, frame):
    return [[frame[body_names.index('guitar/G:string%d%s' % (i, suffix)), :3]
             for suffix in ('', '_end')] for i in range(1, 7)]


def fit_camera(model, data, low, high):
    """Fixed full-body camera fitted to conservative source-geometry bounds."""
    import numpy as np
    vertical = np.tan(np.deg2rad(float(model.cam_fovy[0]))/2)
    horizontal = vertical*1280/720
    center, half = (low+high)/2, (high-low)/2
    distance = max(half[2]/(.75*vertical), half[0]/(.9*horizontal), .5)
    model.cam_pos[0] = [center[0], high[1]+distance, center[2]]
    model.cam_quat[0] = [0., 0., 2**-.5, 2**-.5]
    return dict(position=model.cam_pos[0].tolist(), quaternion_wxyz=model.cam_quat[0].tolist(),
        fovy_degrees=float(model.cam_fovy[0]), fit='All captured source geom bounding spheres and string endpoints; ndc x<=.9,y<=.75 reserves subtitle space')


def projection_bounds(model, data, ids):
    import numpy as np
    radius = model.geom_rbound[ids]
    points = data.geom_xpos[ids]
    depth = model.cam_pos[0, 1] - points[:, 1] - radius
    require(bool(np.all(depth > 0)), 'Source geometry behind/through camera')
    vertical = np.tan(np.deg2rad(float(model.cam_fovy[0]))/2)
    horizontal = vertical*1280/720
    x = np.max((np.abs(points[:, 0]-model.cam_pos[0, 0])+radius)/(depth*horizontal))
    y = np.max((np.abs(points[:, 2]-model.cam_pos[0, 2])+radius)/(depth*vertical))
    require(x <= .900001 and y <= .750001, 'Full-body source geometry exceeds reserved viewport')
    return dict(max_abs_ndc_x=float(x), max_abs_ndc_y=float(y))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation', type=Path, default=None)
    parser.add_argument('--evaluations', type=Path, default=PHASE/'checkpoint_evaluation.json')
    parser.add_argument('--selection', choices=('best','latest'), default='latest')
    parser.add_argument('--out', type=Path, default=None)
    parser.add_argument('--view', choices=('fullbody','hand'), default='fullbody')
    args = parser.parse_args()
    selection_pins, selected_checkpoint = {}, None
    if args.evaluation:
        evaluation = args.evaluation.resolve()
    else:
        combined_path = args.evaluations.resolve()
        combined = json.loads(combined_path.read_text())
        require(combined['completed'] and combined['requested_evaluations_completed'] and
            set(combined['evaluated_updates'])==set(CHECKPOINT_UPDATES) and
            combined['selection']==checkpoint_selection(combined['results']), 'Complete verified five-checkpoint selection required')
        selected_checkpoint = combined['selection'][args.selection]
        evaluation = Path(selected_checkpoint['evaluation'])
        selection_pins[str(combined_path)] = sha(combined_path)
    out = args.out.resolve() if args.out else PHASE/(args.selection+'_video')
    report = json.loads((evaluation/'report.json').read_text())
    metadata = json.loads((evaluation/'capture_metadata.json').read_text())
    initial = json.loads((evaluation/'visual_initial.json').read_text())
    require(selected_checkpoint is None or (selected_checkpoint['checkpoint']==report['checkpoint'] and
        selected_checkpoint['updates']==report['source_optimizer_updates']), 'Selected checkpoint identity differs')
    require(report['completed'] is True and report['num_envs'] == 1024 and
            report['source_optimizer_updates'] == metadata['source_optimizer_updates'] and
            report['gpu_scene']['closed'] and report['gpu_scene']['physx_use_gpu'] and
            report['gpu_scene']['use_gpu_pipeline'] and report['gpu_scene']['environment_count']==1024 and
            report['gpu_scene']['physics_steps']==report['ticks']*4, 'Completed1024 nativeGPU evaluation required')
    require(report['training_chain'] == metadata['training_chain'], 'Pose/evaluation training chain differs')
    chain = report['training_chain']
    require(chain['schema'] == CHAIN_SCHEMA and chain['fresh_policy'] and chain['run_completed'],
        'Verified fresh v8 completed training chain required')
    selected = select_video_env(report['episodes'])
    require(metadata['selected_env_id'] == selected and metadata['capture_envs'] == list(range(8)), 'Predeclared selection differs')
    require([row['env_id'] for row in metadata['captures']] == list(range(8)), 'Captured cohort must contain all predeclared IDs once')
    capture = next(row for row in metadata['captures'] if row['env_id'] == selected)
    pose_path = evaluation/capture['path']
    require(sha(pose_path) == capture['sha256'], 'Captured pose SHA mismatch')
    episode = next(e for e in report['episodes'] if e['env_id'] == selected)
    pinned = json.loads((evaluation/'inputs_before.json').read_text())
    pinned.update(selection_pins)
    contract = json.loads(Path(report['training_chain']['run']).joinpath('training_contract.json').read_text())
    validate_input_contract(contract)
    require(metadata['posture_reconstruction']==posture_metadata(contract, metadata['body_names']), 'Actual posture reconstruction metadata differs')
    require(not [f for f, h in pinned.items() if sha(f) != h], 'Evaluation inputs changed before render')
    require(metadata['checkpoint'] == report['checkpoint'] and
            metadata['checkpoint_sha256'] == pinned[report['checkpoint']], 'Captured checkpoint identity differs')
    # Set before importing MuJoCo. The default is software headless rendering.
    os.environ.setdefault('MUJOCO_GL', 'osmesa')
    os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE', '1')
    import mujoco
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import (
        asset_paths, build_model, set_body_poses, add_strings)
    from guitar_learning.tool._rendering import encoder, probe, FONT
    assets = set().union(*(asset_paths(a['path']) for a in initial['loaded_assets']))
    require(all(pinned.get(str(f)) == sha(f) for f in assets), 'Visual assets differ from actual evaluation inputs')
    sources = assets | {Path(__file__).resolve(), PHASE/'evaluate_checkpoints.py', FONT, pose_path,
        evaluation/'report.json', evaluation/'capture_metadata.json', evaluation/'visual_initial.json',
        ROOT/'guitar_learning/tool/_rendering.py',
        ROOT/'guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py',
        ROOT/'guitar_learning/native/initial_pose_video60_v1/replay_v6.py'}
    pinned.update({str(f): sha(f) for f in sources})
    out.mkdir(parents=True, exist_ok=False)
    write(out/'inputs_before.json', pinned)
    with np.load(str(pose_path), allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    validate_capture(arrays, len(metadata['body_names']), episode)
    body_names, bodies = metadata['body_names'], arrays['body_state']
    require(len(metadata['joint_names']) == 105 and len(bodies) >= 2, 'Nonempty actual pose/joint trace required')
    model, data, mapping, xml = build_model(initial)
    (out/'source_visual.xml').write_text(xml)
    low, high = np.full(3, np.inf), np.full(3, -np.inf)
    geom_ids = np.asarray([i for i in range(model.ngeom) if model.geom_bodyid[i] > 0 and
        (args.view == 'fullbody' or model.body(int(model.geom_bodyid[i])).name.startswith('human/LH:'))])
    require(len(geom_ids)>0, 'Nonempty camera geometry required')
    radius = model.geom_rbound[geom_ids, None]
    require(bool(np.isfinite(radius).all()), 'Invalid visual geometry bounds')
    worst_position = worst_rotation = 0.
    for frame in bodies:
        audit = set_body_poses(model, data, mapping, pose_state(body_names, frame, initial))
        worst_position = max(worst_position, audit['max_position_error_m'])
        worst_rotation = max(worst_rotation, audit['max_rotation_error_rad'])
        low = np.minimum(low, (data.geom_xpos[geom_ids]-radius).min(axis=0))
        high = np.maximum(high, (data.geom_xpos[geom_ids]+radius).max(axis=0))
        if args.view == 'fullbody':
            endpoints = np.asarray(string_endpoints(body_names, frame)).reshape(-1, 3)
            low, high = np.minimum(low, endpoints.min(axis=0)), np.maximum(high, endpoints.max(axis=0))
    camera = fit_camera(model, data, low, high)
    write(out/'presentation.json', dict(selected_env_id=selected, selection=metadata['selection'],
        checkpoint_role=args.selection if not args.evaluation else 'explicit_evaluation',
        source_optimizer_updates=report['source_optimizer_updates'],
        training_chain=report['training_chain'],
        checkpoint=report['checkpoint'], checkpoint_sha256=metadata['checkpoint_sha256'],
        source_frame=metadata['body_frame'], source_capture_hz=60, source_physics_hz=240,
        width=1280, height=720, fps=60, view=args.view, camera=camera, camera_override_for_source_visual_xml=True,
        new_physics_steps=0, physics_clock_s=0.,
        video_frames='Capture frames1..end at60fps; initial prepared frame0 retained in NPZ. Video duration equals first episode duration.',
        scope='Original visible human/guitar source meshes installed at actual GPU logical body world poses; original six string endpoints added. No integration, policy execution, interpolation, sound synthesis or pressure visualization.',
        limitation='One predeclared first episode selected by safe completion/ID from env0..7, not independent-seed generalization or best musical score. Geometric candidate diagnostics do not certify acoustic success.'))
    renderer = mujoco.Renderer(model, height=720, width=1280)
    video = out/(args.selection+'_'+('fullbody' if args.view == 'fullbody' else 'left_hand')+'_60fps.mp4')
    process = encoder(video)
    font, small = ImageFont.truetype(str(FONT), 24), ImageFont.truetype(str(FONT), 18)
    audits, started = [], time.perf_counter()
    try:
        for index in range(1, len(bodies)):
            state = pose_state(body_names, bodies[index], initial)
            audit = set_body_poses(model, data, mapping, state)
            projection = projection_bounds(model, data, geom_ids)
            before = (data.xpos.copy(), data.xquat.copy(), float(data.time))
            renderer.update_scene(data, camera='front')
            add_strings(renderer.scene, np.asarray(string_endpoints(body_names, bodies[index])))
            image = Image.fromarray(renderer.render())
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 1280, 78), fill=(22, 27, 34))
            timestamp = float(arrays['clock'][index]/240.)
            draw.text((18, 4), '정책 %d회 | 환경%d | 정책 시각 %.3f초 | 달성 %d/67' %
                (report['source_optimizer_updates'], selected, timestamp, arrays['left_count'][index]), font=font, fill='white')
            draw.text((18, 41), '실제 GPU 자세 기록 재생 · '+('전신' if args.view == 'fullbody' else '왼손 근접')+' · 60fps · 새 물리 적분 없음', font=small, fill=(215, 225, 235))
            draw.rectangle((0, 672, 1280, 720), fill=(22, 27, 34))
            draw.text((18, 681), '표면 접근 완료 %d/67 · 접촉 후보 누적 완료 %d/67 · 현재 후보 %d/67 · 압력/음향 측정 아님' %
                (arrays['near_count'][index], arrays['contact_count'][index], arrays['candidate_count'][index]), font=small, fill='white')
            if index in {1, len(bodies)//2, len(bodies)-1}:
                image.save(out/('preview_%04d.png' % index))
            process.stdin.write(image.tobytes())
            require(np.array_equal(before[0], data.xpos) and np.array_equal(before[1], data.xquat) and
                    before[2] == data.time == 0., 'Rendering changed body poses or advanced physics')
            audits.append(dict(video_frame=index-1, source_capture_frame=index, policy_time_s=timestamp,
                physics_step=int(arrays['clock'][index]), pose_readback=audit, projection=projection))
            if index % 60 == 0:
                (out/'status.json.tmp').write_text(json_io.dumps(dict(frames=index, total_frames=len(bodies)-1,
                    wall_s=time.perf_counter()-started, new_physics_steps=0))+'\n')
                (out/'status.json.tmp').replace(out/'status.json')
        process.stdin.close()
        require(process.wait() == 0, 'Video encoding failed')
        media = probe(video, len(bodies)-1)
        require(abs(float(media['stream']['duration'])-episode['task_time_s']) < .002, 'Video/actual episode duration differs')
        require(not [f for f, h in pinned.items() if sha(f) != h], 'Rendering inputs changed')
        write(out/'pose_audit.json', dict(completed=True, source_frames=len(bodies), video_frames=len(audits),
            body_count=len(body_names), joint_count=105, max_position_error_m=worst_position,
            max_rotation_error_rad=worst_rotation, new_physics_steps=0, frames=audits))
        write(out/'report.json', dict(completed=True, selected_env_id=selected, checkpoint=report['checkpoint'],
            checkpoint_role=args.selection if not args.evaluation else 'explicit_evaluation',
            source_optimizer_updates=report['source_optimizer_updates'],
            training_chain=report['training_chain'],
            full_safe=episode['left_curriculum']['full_safe'], reason=episode['reason'],
            left_success_count=episode['song']['left_success_count'], media=media, pose_audit='pose_audit.json',
            inputs_unchanged=True, new_physics_steps=0, wall_s=time.perf_counter()-started))
        print(json_io.dumps(dict(completed=True, selected_env_id=selected, frames=len(audits), video=str(video))))
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        renderer.close()


if __name__ == '__main__':
    main()
