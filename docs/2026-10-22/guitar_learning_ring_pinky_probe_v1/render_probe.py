"""Render four preselected3s probe clips from saved60Hz world poses; no physics."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from guitar_learning.training import json_io

PHASE_NAMES = {2:'pulse · 작은 이동', 3:'hold · 목표 유지',
               4:'return · 원래 목표 복귀', 5:'hold · 복귀 목표 유지',
               6:'coordinated return · 준비 목표 방향 복귀'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json_io.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def select_cases(metadata):
    """Native headroom at probe start only; never select by motion or force."""
    names = metadata['tested_joint_names']
    lower, upper = np.asarray(metadata['native_lower_rad']), np.asarray(metadata['native_upper_rad'])
    starts = np.asarray(metadata['probe_start_target_rad'])
    require(len(names) == 8 and lower.shape == upper.shape == (8,) and starts.shape == (18, 8), 'Expected18 cases and8 native axes')
    require(np.isfinite(starts).all() and np.isfinite(lower).all() and np.isfinite(upper).all() and
            (lower <= upper).all() and (starts >= lower-1e-6).all() and (starts <= upper+1e-6).all(), 'Invalid native headroom evidence')
    cases = metadata['cases']
    require(len(cases) == 18 and {c['env_id'] for c in cases} == set(range(18)), 'Unique18 case IDs required')
    selected = []
    for name in ('LH:ring2', 'LH:pinky1_z', 'LH:pinky3'):
        axis = names.index(name)
        options = [c for c in cases if c['kind'] == 'pulse' and c['joint'] == name]
        require(len(options) == 2 and {c['direction'] for c in options} == {-1, 1}, 'Both predefined pulse directions required')
        def headroom(case):
            require(case['axis_index'] == axis, 'Case axis mapping differs')
            target = starts[case['env_id'], axis]
            return float(upper[axis]-target if case['direction'] > 0 else target-lower[axis])
        chosen = min(options, key=lambda c:(-headroom(c), c['env_id']))
        selected.append(dict(chosen, selection_headroom_rad=headroom(chosen)))
    coordinated = next(c for c in cases if c['env_id'] == 17)
    require(coordinated['kind'] == 'coordinated_return', 'Predeclared coordinated case17 required')
    return selected+[dict(coordinated, selection_headroom_rad=None)]


def clip_frames(clock, start):
    """Drop prefix/t0; retain exactly180 recorded endpoints without resampling."""
    require(type(start) is int and start in (0, 600), 'Actual prepared/learned10 probe start required')
    clock = np.asarray(clock)
    require(clock.ndim == 1 and len(clock) == start+181 and
            np.array_equal(clock, np.arange(len(clock))*4), 'Complete60Hz capture at actual240Hz clock required')
    return np.arange(start+1, start+181)


def pose_state(names, frame, initial):
    expected = ['human/'+n for n in initial['human_body_names']]+['guitar/'+n for n in initial['guitar_body_names']]+['chair/box']
    require(names == expected and frame.shape == (106, 13), 'Original106-body source order required')
    result = {actor+'_body_states':[] for actor in ('human', 'guitar', 'chair')}
    for name, row in zip(names, frame):
        result[name.split('/', 1)[0]+'_body_states'].append(dict(pose=dict(
            p=dict(zip('xyz', map(float, row[:3]))), r=dict(zip('xyzw', map(float, row[3:7]))))))
    return result


def fit_camera(model, low, high):
    vertical = np.tan(np.deg2rad(float(model.cam_fovy[0]))/2)
    horizontal = vertical*1280/720
    center, half = (low+high)/2, (high-low)/2
    distance = max(half[2]/(.6*vertical), half[0]/(.88*horizontal), .1)
    model.cam_pos[0] = [center[0], high[1]+distance, center[2]]
    model.cam_quat[0] = [0., 0., 2**-.5, 2**-.5]
    return dict(position=model.cam_pos[0].tolist(), quaternion_wxyz=model.cam_quat[0].tolist(),
        fovy_degrees=float(model.cam_fovy[0]), fit='Fixed union of original left-hand/wrist and two neck-mesh bounding spheres across all720 source frames; x<=.88,y<=.6 reserves captions')


def projection(model, data, ids):
    radius = model.geom_rbound[ids]
    points = data.geom_xpos[ids]
    depth = model.cam_pos[0, 1]-points[:, 1]-radius
    require((depth > 0).all(), 'Hand/neck geometry behind camera')
    vertical = np.tan(np.deg2rad(float(model.cam_fovy[0]))/2)
    horizontal = vertical*1280/720
    x = float(np.max((np.abs(points[:, 0]-model.cam_pos[0, 0])+radius)/(depth*horizontal)))
    y = float(np.max((np.abs(points[:, 2]-model.cam_pos[0, 2])+radius)/(depth*vertical)))
    require(x <= .880001 and y <= .600001, 'Hand/neck source bounds overlap reserved captions')
    return dict(max_abs_ndc_x=x, max_abs_ndc_y=y)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=PHASE/'probe')
    parser.add_argument('--variant', choices=('prepared', 'learned10'), default='learned10')
    parser.add_argument('--out', type=Path, default=None)
    args = parser.parse_args()
    folder = args.run.resolve()/args.variant
    out = args.out.resolve() if args.out else PHASE/('video_'+args.variant)
    pins = {}
    def read(path):
        pins[str(path)] = sha(path)
        return json.loads(path.read_text())
    report = read(folder/'report.json'); metadata = read(folder/'capture_metadata.json')
    initial = read(folder/'visual_initial.json')
    require(report['completed'] and report['schedule_completed'] and report['probe_started'] and
            report['gpu_scene']['closed'] and report['gpu_scene']['physx_use_gpu'] and report['gpu_scene']['use_gpu_pipeline'] and
            report['gpu_scene']['environment_count'] == 18,
            'Actual complete3s probe with closed native GPU required; censored runs are not stretched')
    require(metadata['probe_start_frame'] == metadata['prefix_ticks'] == (600 if args.variant == 'learned10' else 0), 'Variant/prefix clock mismatch')
    actual_pins = read(folder/'inputs_before.json')
    require(all(Path(p).is_file() and sha(p) == h for p,h in actual_pins.items()), 'Probe inputs changed')
    pins.update(actual_pins)
    selected = select_cases(metadata)
    clips = []
    for case in metadata['cases']:
        path = folder/case['path']
        require(sha(path) == case['sha256'], 'Case capture SHA differs')
        pins[str(path)] = case['sha256']
        with np.load(path, allow_pickle=False) as archive:
            start = metadata['probe_start_frame']
            require(np.allclose(archive['target'][start, metadata['tested_native_indices']],
                metadata['probe_start_target_rad'][case['env_id']], atol=1e-6, rtol=0), 'Headroom is not actual captured start target')
            if case['env_id'] not in {c['env_id'] for c in selected}:
                continue
            arrays = {key:archive[key].copy() for key in archive.files}
        indices = clip_frames(arrays['clock'], start)
        frames = len(arrays['clock'])
        expected = dict(body_state=(frames,106,13), q=(frames,105), qd=(frames,105), target=(frames,105),
                        action=(frames,39), global_physics_step=(frames,), segment=(frames,))
        require(all(arrays[k].shape == shape and np.isfinite(arrays[k]).all() for k,shape in expected.items()), 'Invalid actual60Hz pose/control capture')
        require(np.array_equal(arrays['global_physics_step'], arrays['clock']) and
                np.isin(arrays['segment'][indices], list(PHASE_NAMES)).all(), 'Unexpected actual physics/phase clock')
        clips.append((case['env_id'], arrays, indices))
    by_id = {i:(a, ix) for i,a,ix in clips}
    # MuJoCo imports/context creation occur only in the real render entry point.
    os.environ.setdefault('MUJOCO_GL', 'osmesa')
    os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE', '1')
    import mujoco
    from PIL import Image, ImageDraw, ImageFont
    from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import asset_paths, build_model, set_body_poses, add_strings
    from guitar_learning.tool._rendering import encoder, probe, FONT
    assets = set().union(*(asset_paths(a['path']) for a in initial['loaded_assets']))
    require(all(actual_pins.get(str(p)) == sha(p) for p in assets), 'Visual source assets differ from actual probe')
    for path in assets | {Path(__file__).resolve(), FONT, ROOT/'guitar_learning/tool/_rendering.py',
            ROOT/'guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py',
            ROOT/'guitar_learning/native/initial_pose_video60_v1/replay_v6.py'}:
        pins[str(path)] = sha(path)
    out.mkdir(parents=True, exist_ok=False)
    write(out/'inputs_before.json', pins)
    model, data, mapping, xml = build_model(initial)
    (out/'source_visual.xml').write_text(xml)
    geom_ids = []
    for i in range(model.ngeom):
        body = model.body(int(model.geom_bodyid[i])).name
        mesh = model.mesh(int(model.geom_dataid[i])).name if model.geom_type[i] == mujoco.mjtGeom.mjGEOM_MESH else ''
        if body.startswith('human/LH:') or body == 'human/L_Wrist' or mesh in ('guitar/guitar_neck1', 'guitar/guitar_neck2'):
            geom_ids.append(i)
    require(len(geom_ids) > 0 and any(model.mesh(int(model.geom_dataid[i])).name.startswith('guitar/guitar_neck')
        for i in geom_ids if model.geom_type[i] == mujoco.mjtGeom.mjGEOM_MESH), 'Visible hand and original neck required')
    geom_ids = np.asarray(geom_ids)
    low, high = np.full(3,np.inf), np.full(3,-np.inf)
    radius = model.geom_rbound[geom_ids,None]
    position_error = rotation_error = 0.
    for case in selected:
        arrays, indices = by_id[case['env_id']]
        for index in indices:
            audit = set_body_poses(model,data,mapping,pose_state(metadata['body_names'],arrays['body_state'][index],initial))
            position_error = max(position_error,audit['max_position_error_m'])
            rotation_error = max(rotation_error,audit['max_rotation_error_rad'])
            low = np.minimum(low,(data.geom_xpos[geom_ids]-radius).min(0))
            high = np.maximum(high,(data.geom_xpos[geom_ids]+radius).max(0))
    camera = fit_camera(model,low,high)
    write(out/'presentation.json',dict(variant=args.variant,selection=selected,camera=camera,
        source_hz=60,source_physics_hz=240,width=1280,height=720,fps=60,clips=4,frames=720,duration_s=12.,
        selection_rule='For ring2,pinky1_z,pinky3 select pulse direction with greater native headroom at actual probe start; tie lower case ID. Always include coordinated17. Outcomes/forces not used.',
        scope='Four separate3s diagnostic cases concatenated at recorded endpoint cadence. Prefix is omitted from pictures but retained in source timestamps. Original meshes/world poses; no interpolation, new physics, policy execution, force/pressure rendering or audio. Non-tested q may respond physically although their targets are held.'))
    renderer = mujoco.Renderer(model,height=720,width=1280)
    video = out/'ring_pinky_probe_60fps.mp4'
    process = encoder(video)
    font, small = ImageFont.truetype(str(FONT),24), ImageFont.truetype(str(FONT),18)
    audits = []
    try:
        for clip_id,case in enumerate(selected):
            arrays, indices = by_id[case['env_id']]
            shown = [case['axis_index']] if case['kind'] == 'pulse' else [metadata['tested_joint_names'].index(n) for n in ('LH:ring2','LH:pinky1_z','LH:pinky3')]
            for index in indices:
                source = arrays['body_state'][index]
                audit = set_body_poses(model,data,mapping,pose_state(metadata['body_names'],source,initial))
                viewport = projection(model,data,geom_ids)
                before = data.xpos.copy(),data.xquat.copy(),float(data.time)
                renderer.update_scene(data,camera='front')
                endpoints = np.asarray([[source[metadata['body_names'].index('guitar/G:string%d%s'%(s,suffix)),:3]
                    for suffix in ('','_end')] for s in range(1,7)])
                add_strings(renderer.scene,endpoints)
                image = Image.fromarray(renderer.render()); draw = ImageDraw.Draw(image)
                draw.rectangle((0,0,1280,89),fill=(22,27,34)); draw.rectangle((0,588,1280,720),fill=(22,27,34))
                label = '%s %+.0f'%(case['joint'],case['direction']) if case['kind']=='pulse' else '약지·소지8축 준비 목표 방향 복귀'
                draw.text((18,5),'약지·소지 실제 반전 검사 | %s | clip%d/4 · case%d'%(label,clip_id+1,case['env_id']),font=font,fill='white')
                draw.text((18,42),'%s | 원본 %.3fs · 검사 %.3fs | %s'%(args.variant,arrays['clock'][index]/240.,(index-metadata['probe_start_frame'])/60.,PHASE_NAMES[int(arrays['segment'][index])]),font=small,fill='white')
                for line,axis in enumerate(shown):
                    joint = metadata['tested_native_indices'][axis]; action = metadata['tested_action_indices'][axis]
                    text = '%s   실제 q %+.2f°   목표 %+.2f°   요청 %+.3f rad/s'%(metadata['tested_joint_names'][axis],np.rad2deg(arrays['q'][index,joint]),np.rad2deg(arrays['target'][index,joint]),4*arrays['action'][index,action])
                    draw.text((18,595+27*line),text,font=small,fill=(225,235,245))
                draw.text((18,690),'실제 GPU 자세 기록 · 원본60Hz 끝점만 재생 · 물리 적분/보간/학습 없음 · 접촉 합력은 압력·끼임 확증이 아님',font=small,fill=(210,220,230))
                require(np.array_equal(before[0],data.xpos) and np.array_equal(before[1],data.xquat) and before[2]==data.time==0.,'Renderer changed recorded poses or physics clock')
                frame = len(audits)
                if frame in (0,360,719): image.save(out/('preview_%04d.png'%frame))
                process.stdin.write(image.tobytes())
                audits.append(dict(video_frame=frame,clip=clip_id,case=case['env_id'],source_frame=int(index),
                    source_clock=int(arrays['clock'][index]),segment=int(arrays['segment'][index]),pose_readback=audit,projection=viewport))
        process.stdin.close(); require(process.wait()==0,'Video encoding failed')
        media = probe(video,720)
        require(all(Path(p).is_file() and sha(p)==h for p,h in pins.items()),'Render inputs changed')
        write(out/'pose_audit.json',dict(completed=True,new_physics_steps=0,frames=audits,
            max_position_error_m=position_error,max_rotation_error_rad=rotation_error))
        write(out/'report.json',dict(completed=True,variant=args.variant,selected_cases=[c['env_id'] for c in selected],
            media=media,previews=['preview_0000.png','preview_0360.png','preview_0719.png'],inputs_unchanged=True,
            new_physics_steps=0,source_probe=str(folder),scope='Diagnostic saved-pose playback; no training efficacy or pressure/impingement certification'))
        print(json_io.dumps(dict(completed=True,video=str(video))))
    finally:
        if process.poll() is None: process.kill(); process.wait()
        renderer.close()


if __name__ == '__main__':
    main()
