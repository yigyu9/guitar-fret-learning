"""Inspect saved native RH poses with source meshes; never run physics or policy."""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import gzip
import json
from guitar_learning.native.paths import original_input_path

from guitar_learning.native.initial_pose_video60_v1.replay_v6 import sha, save
from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import (
    asset_paths, build_model, set_body_poses)

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT/'docs/2026-10-12/stability_adapter_2/results'
RUN = PHASE/'guitar_learning_actionable_preparation_v1/right_ppo_eval_v1'
from guitar_learning.tool._rendering import INITIAL, FONT
VIEWS = ((0, 15), (60, 15), (120, 15), (180, 15), (240, 15), (300, 15))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    import mujoco
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    initial = json.loads(INITIAL.read_text())
    assets = set().union(*(asset_paths(Path(a['path'])) for a in initial['loaded_assets']))
    pins = json.loads((RUN/'inputs_before.json').read_text())
    if any(pins.get(str(original_input_path(f))) != sha(f) for f in assets | {INITIAL}):
        raise ValueError('latest evaluation asset provenance mismatch')
    sources = assets | {INITIAL, FONT, Path(__file__).resolve(),
        Path(__file__).with_name('_rendering.py'),
        ROOT/'guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py',
        ROOT/'guitar_learning/native/initial_pose_video60_v1/replay_v6.py'}
    sources.update(RUN/name for name in ('result.json', 'settings.json', 'inputs_before.json', 'transitions.json.gz'))
    inputs = {str(f): sha(f) for f in sorted(sources)}
    save(out/'inputs_before.json', inputs)
    result = json.loads((RUN/'result.json').read_text())
    with gzip.open(RUN/'transitions.json.gz', 'rt') as stream:
        rows = [r for r in json.load(stream) if r['episode'] == 0]
    if not result['completed'] or not result['source_unchanged'] or [r['tick'] for r in rows] != list(range(420)):
        raise ValueError('complete latest seven-second evaluation required')
    for i, row in enumerate(rows):
        if [s['native']['physics_step'] for s in row['native_physics_samples240']] != list(range(4*i+1, 4*i+5)):
            raise ValueError('source sample gap')
    model, data, mapping, xml = build_model(initial)
    (out/'source_visual.xml').write_text(xml)
    names = initial['human_body_names']
    def position(state, name):
        return np.array([state['human_body_states'][names.index(name)]['pose']['p'][a] for a in 'xyz'])
    # Isolate the actual right-hand source surfaces; no shape/pose modification.
    # The pick is an empty source body, so its yellow sphere is an explicit overlay.
    for geom_id in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[geom_id])) or ''
        model.geom_rgba[geom_id] = ((1., .48, .08, 1.) if name.startswith('human/RH:thumb') else
            (.08, .63, .95, 1.) if name.startswith('human/RH:index') else
            (.65, .69, .74, 1.) if name.startswith('human/RH:') or name == 'human/R_Wrist' else (0., 0., 0., 0.))
    model.vis.headlight.ambient[:] = .45
    model.vis.headlight.diffuse[:] = .65
    model.vis.map.znear = .001
    renderer = mujoco.Renderer(model, height=480, width=640)
    font = ImageFont.truetype(str(FONT), 24)
    small = ImageFont.truetype(str(FONT), 19)
    camera = mujoco.MjvCamera(); camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.distance = .30
    records = []
    def frame(index, view):
        state = rows[index]['native_physics_samples240'][-1]['native']
        readback = set_body_poses(model, data, mapping, state)
        pick = position(state, 'RH:pick')
        camera.lookat[:] = (position(state, 'RH:palm')+position(state, 'RH:index3')+position(state, 'RH:thumb3'))/3.
        camera.azimuth, camera.elevation = VIEWS[view]
        renderer.update_scene(data, camera=camera)
        geom = renderer.scene.geoms[renderer.scene.ngeom]
        mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_SPHERE,
            np.array([.0025, .0025, .0025]), pick, np.eye(3).reshape(-1), np.array([1., .88, .04, 1.], dtype=np.float32))
        renderer.scene.ngeom += 1
        image = Image.fromarray(renderer.render())
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 640, 40), fill=(24, 30, 38))
        draw.text((14, 6), '시점 %d | 정책 %.3f초' % (view+1, (index+1)/60.), font=font, fill='white')
        records.append(dict(tick=index, physics_step=state['physics_step'], view=view+1, pose_readback=readback))
        return image
    try:
        sheet = Image.new('RGB', (1920, 1080), (24, 30, 38))
        for view in range(6):
            image = frame(251, view)
            image.save(out/('view_%d.png' % (view+1)))
            sheet.paste(image, ((view % 3)*640, 100+(view//3)*480))
        draw = ImageDraw.Draw(sheet)
        draw.text((24, 8), '최신 오른손 평가 · 4.200초 · 저장된 실제 자세의 원본 손 mesh', font=font, fill='white')
        draw.text((24, 43), '주황=엄지 / 파랑=검지 / 노랑=피크 기준점 표시(반지름 2.5mm, 실제 피크 형상 아님)', font=font, fill='white')
        draw.text((24, 76), '가림 제거를 위해 기타·몸통 숨김 · 시각화만 수행 · 접촉력/압력 검증 아님', font=small, fill=(215, 222, 230))
        sheet.save(out/'right_hand_views.png')
    finally:
        renderer.close()
    if any(sha(p) != h for p, h in inputs.items()):
        raise ValueError('render input changed')
    save(out/'report.json', dict(completed=True, source=str(RUN), episode=0,
        renderer='source meshes at exact saved native world poses; right hand isolated',
        new_physics_steps=0, inputs_unchanged=True, frames=records,
        views_azimuth_elevation_degrees=VIEWS, camera_distance_m=.30,
        pick_overlay_radius_m=.0025,
        pick_scope='empty child body of RH:index2, no pick geom or pinch dynamics',
        images={p.name: sha(p) for p in sorted(out.glob('*.png'))}))
    print('Rendered six saved-pose hand views; physics steps: 0', flush=True)


if __name__ == '__main__':
    main()
