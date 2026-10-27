"""One compact recorded-contact figure on exact-pose source geometry, no physics."""
import argparse
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from .analyze_v1 import selected
from ..initial_pose_video60_v1.replay_v6 import sha, save, original_expected_inputs
from ..initial_pose_video60_v1.static_visual_v7 import build_model, set_body_poses, asset_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    import mujoco
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    root = Path(__file__).resolve().parents[2]
    run, out = args.run.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    initial = json.loads((run / 'initial_values.json').read_text())
    font_path = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    brief = root / 'paper/initial_pose/current_v3/contact_visualization_v1/BRIEF.md'
    files = {Path(__file__).resolve(), Path(__file__).with_name('analyze_v1.py'), Path(__file__).resolve().parents[1] / 'initial_pose_video60_v1/replay_v6.py', Path(__file__).resolve().parents[1] / 'initial_pose_video60_v1/static_visual_v7.py', args.analysis.resolve(), brief, font_path}
    files.update(run / name for name in ('initial_values.json', 'states240.json', 'contacts240.json', 'attempt.json', 'support_wrapper.json'))
    assets = set()
    for value in initial['loaded_assets']:
        assets.update(asset_paths(Path(value['path'])))
    files.update(assets)
    pins = {str(path): sha(path) for path in files}
    save(out / 'inputs_before.json', pins)
    brief_text = brief.read_text()
    assert brief_text.strip()
    expected = original_expected_inputs(run)
    assert all(expected[str(path.resolve())] == sha(path) for path in assets)
    analysis = json.loads(args.analysis.read_text())
    frame = next(frame for frame in analysis['frames'] if frame['physics_step'] == 6960)
    contacts = [contact for contact in frame['contacts'] if contact['positive_lambda']]
    state = selected(run / 'states240.json', [6960])[6960]['state']
    model, data, mapping, xml = build_model(initial)
    camera_specs = [('front_contact', [0, 1.25, .85], [0, 0, .72]), ('oblique_contact', [1., 1.05, .9], [0, 0, .72])]
    xml_root = ET.fromstring(xml)
    visual = xml_root.find('visual/global')
    visual.set('offwidth', '450'); visual.set('offheight', '270')
    world = xml_root.find('worldbody')
    for name, eye, target in camera_specs:
        forward = np.array(target) - eye; forward /= np.linalg.norm(forward)
        right = np.cross(forward, [0, 0, 1.]); right /= np.linalg.norm(right)
        up = np.cross(right, forward)
        ET.SubElement(world, 'camera', name=name, pos=' '.join(map(str, eye)), xyaxes=' '.join(map(str, np.r_[right, up])), fovy='34')
    human_names = {contact['human_body'].split('/', 1)[1] for contact in contacts}
    overlay = ET.fromstring(ET.tostring(xml_root))
    for geom in overlay.findall('./worldbody/body/geom'):
        rgba = geom.get('rgba', '.65 .65 .65 1').split(); rgba[-1] = '.12'; geom.set('rgba', ' '.join(rgba))
    geometry_fields = {'type', 'size', 'pos', 'quat', 'euler', 'axisangle', 'xyaxes', 'zaxis', 'fromto', 'mesh'}
    collision_count = 0
    for actor, asset in zip(('human', 'guitar'), initial['loaded_assets']):
        source = ET.parse(asset['path'])
        for body in source.findall('./worldbody//body'):
            name = body.get('name')
            if (actor == 'guitar' and name != 'G:body') or (actor == 'human' and name not in human_names):
                continue
            target = overlay.find("./worldbody/body[@name='%s/%s']" % (actor, name))
            for geom in body.findall('geom'):
                if geom.get('contype') == '0' or geom.get('conaffinity') == '0':
                    continue
                attributes = {key: value for key, value in geom.attrib.items() if key in geometry_fields}
                if 'mesh' in attributes:
                    attributes['mesh'] = actor + '/' + attributes['mesh']
                ET.SubElement(target, 'geom', attributes, rgba='.05 .65 .9 .28' if actor == 'guitar' else '.8 .55 .25 .25', contype='0', conaffinity='0')
                collision_count += 1
    font, small = ImageFont.truetype(str(font_path), 19), ImageFont.truetype(str(font_path), 14)
    canvas = Image.new('RGB', (900, 650), 'white')
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 2), '29초 실제 기록 접촉점 · 같은 몸체 자세에서 형상 비교', font=font, fill='black')
    draw.text((12, 28), '시각 메시만 표시', font=small, fill='black')
    draw.text((462, 28), '투명 충돌 소스 형상 + 실제 양성 접촉 표식', font=small, fill='black')
    colors = {'human/Chest': (230, 125, 20), 'human/R_Shoulder': (220, 55, 70), 'human/R_Hip': (40, 110, 230), 'human/Spine': (155, 65, 200)}
    ids = {'human/Chest': '1', 'human/R_Shoulder': '2', 'human/R_Hip': '3', 'human/Spine': '4'}
    evidence = []
    for column, tree in enumerate((xml_root, overlay)):
        current = mujoco.MjModel.from_xml_string(ET.tostring(tree, encoding='unicode'))
        current_data = mujoco.MjData(current)
        current_mapping = [(actor, index, mujoco.mj_name2id(current, mujoco.mjtObj.mjOBJ_BODY, name), name) for actor, index, _, name in mapping]
        error = set_body_poses(current, current_data, current_mapping, state)
        renderer = mujoco.Renderer(current, height=270, width=450)
        try:
            for row_index, (camera_name, eye, target) in enumerate(camera_specs):
                renderer.update_scene(current_data, camera=camera_name)
                image = Image.fromarray(renderer.render())
                image_draw = ImageDraw.Draw(image)
                image_draw.text((8, 4), '정면 확대' if row_index == 0 else '비스듬한 확대', font=small, fill='black', stroke_width=2, stroke_fill='white')
                if column == 1:
                    cid = mujoco.mj_name2id(current, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)
                    rotation = current_data.cam_xmat[cid].reshape(3, 3)
                    focal = 270 / (2 * math.tan(math.radians(34) / 2))
                    points_by_body = {}
                    for contact in contacts:
                        point = np.array(contact['guitar_point_W_m'])
                        local = rotation.T @ (point - current_data.cam_xpos[cid])
                        x, y = 225 + focal * local[0] / -local[2], 135 - focal * local[1] / -local[2]
                        color = colors[contact['human_body']]
                        image_draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color, outline='white', width=1)
                        points_by_body.setdefault(contact['human_body'], []).append((x, y))
                    fixed_labels = {'human/Chest': (8, 55), 'human/R_Shoulder': (330, 35), 'human/R_Hip': (330, 223), 'human/Spine': (8, 125)}
                    short_labels = {'human/Chest': '1 가슴', 'human/R_Shoulder': '2 오른쪽 상완', 'human/R_Hip': '3 오른쪽 허벅지', 'human/Spine': '4 척추 몸통'}
                    for body, projected in points_by_body.items():
                        point = np.mean(projected, axis=0)
                        label_x, label_y = fixed_labels[body]
                        color = colors[body]
                        text = short_labels[body]
                        box = image_draw.textbbox((label_x, label_y), text, font=small)
                        leader_x = box[2] + 3 if label_x < 225 else label_x - 3
                        image_draw.line((float(point[0]), float(point[1]), leader_x, label_y + 10), fill='white', width=4)
                        image_draw.line((float(point[0]), float(point[1]), leader_x, label_y + 10), fill=color, width=2)
                        image_draw.text((label_x, label_y), text, font=small, fill=color, stroke_width=2, stroke_fill='white')
                canvas.paste(image, (column * 450, 50 + row_index * 270))
                evidence.append({'panel': [column, row_index], 'camera': camera_name, 'transform_error': error, 'clock_s': float(current_data.time)})
                assert current_data.time == 0
        finally:
            renderer.close()
    draw = ImageDraw.Draw(canvas)
    labels = [('human/Chest', '1 가슴'), ('human/R_Shoulder', '2 오른쪽 상완'), ('human/R_Hip', '3 오른쪽 허벅지'), ('human/Spine', '4 척추 몸통')]
    for index, (key, label) in enumerate(labels):
        draw.text((12 + index * 220, 591), label, font=small, fill=colors[key])
    draw.text((12, 611), '점: 원기록 λ>0인 접촉 특징점(두께 제외), 가림을 무시한 투영 표식 · 크기는 힘이 아님', font=small, fill='black')
    draw.text((12, 630), '충돌 소스는 PhysX cooked 형상과 다를 수 있음 · 무반응 후보 λ=0은 표시하지 않음', font=small, fill='black')
    canvas.save(out / 'recorded_contacts_29s.png')
    assert all(sha(path) == digest for path, digest in pins.items())
    save(out / 'render_report.json', {'renderer': 'MuJoCo source geometry, exact recorded body poses, no physics', 'positive_raw_rows': len(contacts), 'note': 'Raw rows may contain duplicate points; marker count is not unique physical contact count. Markers are X-ray projected feature points, not pressure area or surface boundary.', 'collision_overlay_geom_count': collision_count, 'collision_overlay_scope': 'Only contacted source human bodies and G:body active source collision declarations; not a native cooked mesh reconstruction', 'panels': evidence, 'inputs_unchanged': True, 'new_physics_steps': 0, 'image': str(out / 'recorded_contacts_29s.png')})


if __name__ == '__main__':
    main()
