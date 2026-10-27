"""Render five predeclared finger-probe traces at saved poses; no new physics.

Each70-frame segment is a separate reset trial with a hard cut between trials.
This is neither a learned policy nor one continuous song trajectory.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
sys.path.insert(0, str(PHASE))
sys.path.insert(0, str(ROOT))
from render_video import pose_state, string_endpoints, fit_camera, projection_bounds
from probe_fingers import mapping, audit_trace, PUSH, HOLD, REVERSE
from evaluate_checkpoints import require, sha, write, json_io

JOINTS = tuple('LH:'+name+'2' for name in ('thumb', 'index', 'middle', 'ring', 'pinky'))
TICKS = PUSH+HOLD+REVERSE


def select_trials(report, contract):
    """Select by prepared native room only, without inspecting actual motion."""
    native, actions = mapping(contract)
    joints = contract['action_codec']['incremental_joint_names']
    require(report['completed'] is True and report['passed'] is True and report['failure'] is None and
            not report['cleanup_errors'] and not report['changed_inputs'] and not report['missing_import_pins'] and
            report['physical_terminal_rows'] == 0, 'Completed passing probe required')
    trials = report['trials']
    require(len(trials) == 84 and {(r['joint'], r['amplitude']) for r in trials} ==
            {(name, value) for name in joints for value in (.1, -.1, .2, -.2)}, 'All84 joint/command trials required')
    selected = []
    for name in JOINTS:
        j = joints.index(name)
        reference = contract['reference105_rad'][native[j]]
        positive = contract['action_upper_rad'][actions[j]]-reference
        negative = reference-contract['action_lower_rad'][actions[j]]
        amplitude = .2 if positive >= negative else -.2
        matches = [row for row in trials if row['joint'] == name and row['amplitude'] == amplitude]
        require(len(matches) == 1, 'Unique predeclared trial required: '+name)
        row = matches[0]
        require(not row['terminal'] and row['batch_error'] is None and not row['episodes'] and
                row['audit']['complete_schedule'] and row['audit']['control_contract_passed'], 'Selected probe did not complete')
        selected.append(dict(trial=row, native_joint_index=native[j], action_index=actions[j],
            positive_room_rad=positive, negative_room_rad=negative,
            selection='prepared reference has more native room; exact tie selects+0.2; actual q/range never selects'))
    return selected


def segment(frame):
    require(type(frame) is int and 1 <= frame <= TICKS, 'Source endpoint frame1..70 required')
    return 'push30' if frame <= PUSH else 'zero10' if frame <= PUSH+HOLD else 'reverse30'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', type=Path, default=PHASE/'probe_n4_retry02')
    parser.add_argument('--out', type=Path, default=PHASE/'probe_hand_video')
    args = parser.parse_args()
    source, out = args.probe.resolve(), args.out.resolve()
    report = json.loads((source/'report.json').read_text())
    initial = json.loads((source/'visual_initial.json').read_text())
    metadata = json.loads((source/'capture_metadata.json').read_text())
    control = json.loads((source/'control_contract.json').read_text())
    selected = select_trials(report, control)
    scene = json.loads((source/'gpu_scene_final.json').read_text())
    require(report['gpu_scene'] == scene and scene['closed'] is True and scene['physx_use_gpu'] is True and
            scene['use_gpu_pipeline'] is True and scene['num_envs'] == 4 and scene['simulator_count'] == 1,
            'Closed actual GPU probe required')
    require((metadata['physics_hz'], metadata['capture_hz'], metadata['push_ticks'], metadata['hold_ticks'],
             metadata['reverse_ticks']) == (240, 60, PUSH, HOLD, REVERSE) and
            metadata['joint_names'] == control['joint_names'] and len(metadata['body_names']) == 106,
            'Capture/control identities or sampling differ')
    require(json.loads((source/'lifecycle.json').read_text())['stage'] == 'report_written', 'Probe lifecycle unfinished')
    pinned = json.loads((source/'inputs_before.json').read_text())
    require(not [name for name, value in pinned.items() if sha(name) != value], 'Original probe inputs changed')
    for trial in report['trials']:
        path = (source/trial['path']).resolve()
        require(path.parent == source and sha(path) == trial['sha256'], 'Probe NPZ identity differs')
        pinned[str(path)] = trial['sha256']
    # Only the rendering process imports MuJoCo/GL; no simulator or policy runs.
    os.environ.setdefault('MUJOCO_GL', 'osmesa')
    os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE', '1')
    import mujoco
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import (
        asset_paths, build_model, set_body_poses, add_strings)
    from guitar_learning.tool._rendering import encoder, probe, FONT
    assets = set().union(*(asset_paths(row['path']) for row in initial['loaded_assets']))
    require(all(pinned.get(str(path)) == sha(path) for path in assets), 'Original visual assets differ from probe inputs')
    sources = assets | {Path(__file__).resolve(), PHASE/'render_video.py', PHASE/'probe_fingers.py',
        PHASE/'evaluate_checkpoints.py', FONT, source/'report.json', source/'capture_metadata.json',
        source/'visual_initial.json', source/'control_contract.json', source/'inputs_before.json',
        source/'gpu_scene_final.json', source/'lifecycle.json',
        ROOT/'guitar_learning/tool/_rendering.py',
        ROOT/'guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py',
        ROOT/'guitar_learning/native/initial_pose_video60_v1/replay_v6.py'}
    pinned.update({str(path): sha(path) for path in sources})
    captures = []
    for choice in selected:
        row = choice['trial']
        with np.load(str(source/row['path']), allow_pickle=False) as archive:
            arrays = {key: archive[key] for key in archive.files}
        audit = audit_trace(arrays, control, row['joint'], row['amplitude'])
        require(len(arrays['clock']) == 71 and audit == row['audit'] and audit['actual_motion_observed'],
                'Selected trace audit differs or actual motion missing')
        captures.append(arrays)
    out.mkdir(parents=True, exist_ok=False)
    write(out/'inputs_before.json', pinned)
    model, data, body_mapping, xml = build_model(initial)
    (out/'source_visual.xml').write_text(xml)
    geom_ids = np.asarray([i for i in range(model.ngeom) if model.geom_bodyid[i] > 0 and
        model.body(int(model.geom_bodyid[i])).name.startswith('human/LH:')])
    require(len(geom_ids) > 0, 'Visible source left-hand geometry required')
    radius = model.geom_rbound[geom_ids, None]
    require(bool(np.isfinite(radius).all()), 'Nonfinite source geometry bounds')
    low, high = np.full(3, np.inf), np.full(3, -np.inf)
    worst_position = worst_rotation = 0.
    for arrays in captures:
        for frame in arrays['body_state']:
            audit = set_body_poses(model, data, body_mapping, pose_state(metadata['body_names'], frame, initial))
            worst_position = max(worst_position, audit['max_position_error_m'])
            worst_rotation = max(worst_rotation, audit['max_rotation_error_rad'])
            low = np.minimum(low, (data.geom_xpos[geom_ids]-radius).min(axis=0))
            high = np.maximum(high, (data.geom_xpos[geom_ids]+radius).max(axis=0))
    camera = fit_camera(model, data, low, high)
    camera['fit'] = 'All visible LH source geometry across five selected71-frame trials; fixed camera; minimum distance0.5m'
    frames = len(selected)*TICKS
    presentation = dict(schema='guitar_learning.finger_probe_hand_video.v1', selected_trials=selected,
        source_probe=str(source), body_frame=metadata['body_frame'], body_count=106, joint_count=105,
        source_capture_hz=60, source_physics_hz=240, width=1280, height=720, fps=60,
        video_frames=frames, duration_s=frames/60., view='left_hand', camera=camera,
        camera_override_for_source_visual_xml=True, new_physics_steps=0, interpolated_frames=0, physics_clock_s=0.,
        selection='thumb2,index2,middle2,ring2,pinky2; more prepared native room selects+/-0.2; tie+0.2; not best actual q',
        montage='Saved endpoint frames1..70 from each separate reset trial; hard cuts; no interpolation',
        scope='Actual GPU world body poses installed in original visible source geometry with original six string endpoints; five commanded tests, not a learned policy or continuous song. No new physics, acoustic synthesis or pressure visualization.')
    write(out/'presentation.json', presentation)
    renderer = mujoco.Renderer(model, height=720, width=1280)
    video = out/'finger_probe_left_hand_60fps.mp4'
    process = encoder(video)
    font, small = ImageFont.truetype(str(FONT), 24), ImageFont.truetype(str(FONT), 18)
    audits, started = [], time.perf_counter()
    try:
        for trial_index, (choice, arrays) in enumerate(zip(selected, captures)):
            row = choice['trial']
            for frame in range(1, TICKS+1):
                number = trial_index*TICKS+frame
                audit = set_body_poses(model, data, body_mapping,
                    pose_state(metadata['body_names'], arrays['body_state'][frame], initial))
                projection = projection_bounds(model, data, geom_ids)
                before = data.xpos.copy(), data.xquat.copy(), float(data.time)
                renderer.update_scene(data, camera='front')
                add_strings(renderer.scene, np.asarray(string_endpoints(metadata['body_names'], arrays['body_state'][frame])))
                image = Image.fromarray(renderer.render())
                draw = ImageDraw.Draw(image)
                timestamp = float(arrays['clock'][frame]/240.)
                command = float(arrays['action'][frame, choice['action_index']])
                actual = float(arrays['q'][frame, choice['native_joint_index']])
                target = float(arrays['target'][frame, choice['native_joint_index']])
                draw.rectangle((0, 0, 1280, 78), fill=(22, 27, 34))
                draw.text((18, 4), '손가락 시험%d/5 | %s | native action %+.2f | %s' %
                    (trial_index+1, row['joint'], command, segment(frame)), font=font, fill='white')
                draw.text((18, 41), '시험 local %.3f초 | 실제 q %.3f rad | 목표 %.3f rad | native 부호이며 해부학적 굽힘/폄 명칭 아님' %
                    (timestamp, actual, target), font=small, fill=(215, 225, 235))
                draw.rectangle((0, 672, 1280, 720), fill=(22, 27, 34))
                draw.text((18, 681), '실제 GPU 자세 재생 · 시험 사이 reset/hard cut · 학습 정책/연속곡 아님 · 새 물리/보간 없음', font=small, fill='white')
                if number in {1, 175, 350}:
                    image.save(out/('preview_%04d.png' % number))
                process.stdin.write(image.tobytes())
                require(np.array_equal(before[0], data.xpos) and np.array_equal(before[1], data.xquat) and
                        before[2] == data.time == 0., 'Rendering changed poses or advanced physics')
                audits.append(dict(video_frame=number-1, source_trial=row['path'], joint=row['joint'],
                    source_capture_frame=frame, local_time_s=timestamp,
                    global_physics_step=int(arrays['global_physics_step'][frame]), segment=segment(frame),
                    native_action=command, actual_q_rad=actual, target_rad=target,
                    pose_readback=audit, hand_projection=projection))
                if number % 60 == 0:
                    (out/'status.json.tmp').write_text(json_io.dumps(dict(frames=number, total_frames=frames,
                        wall_s=time.perf_counter()-started, new_physics_steps=0))+'\n')
                    (out/'status.json.tmp').replace(out/'status.json')
        process.stdin.close()
        require(process.wait() == 0, 'Video encoding failed')
        media = probe(video, frames)
        require(abs(float(media['stream']['duration'])-350/60.) < .002, 'Video/selected endpoint duration differs')
        require(not [name for name, value in pinned.items() if sha(name) != value], 'Rendering inputs changed')
        write(out/'pose_audit.json', dict(completed=True, source_frames_per_trial=71, video_frames=len(audits),
            body_count=106, joint_count=105, max_position_error_m=worst_position,
            max_rotation_error_rad=worst_rotation, new_physics_steps=0, frames=audits))
        write(out/'report.json', dict(completed=True, source_probe=str(source), selected_trials=selected,
            media=media, pose_audit='pose_audit.json', presentation='presentation.json',
            inputs_unchanged=True, new_physics_steps=0, interpolated_frames=0, physics_clock_s=0.,
            hard_cuts_between_independent_trials=True, learned_policy=False, wall_s=time.perf_counter()-started))
        print(json_io.dumps(dict(completed=True, frames=len(audits), video=str(video))))
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        renderer.close()


if __name__ == '__main__':
    main()
