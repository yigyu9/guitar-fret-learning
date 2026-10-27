"""Three static views of the proposed wrist-volume translation; no runtime edits."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
SOURCE = OUT.parent/'wrist_targets_multiview_v25/생성자료'
spec = importlib.util.spec_from_file_location('wrist_views', SOURCE/'render_views.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def main():
    np = v.np
    prepared = v.load_prepared_reset_contract()
    initial, state = prepared['initial'], prepared['state']
    geometry = v.geometry_snapshot(state, initial['human_body_names'], initial['guitar_body_names'])
    gp, gr = v.frame(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    track = np.load(SOURCE/'region_track.npz')
    index, shift = 110, np.array([0., -.04, -.01])
    now = float(track['time_s'][index])
    low, high = track['lower_G_m'][index]+shift, track['upper_G_m'][index]+shift
    outer_low, outer_high = track['outer_lower_G_m'][index]+shift, track['outer_upper_G_m'][index]+shift
    wrist_g = track['wrist_G_m']
    assert np.all(wrist_g >= low) and np.all(wrist_g <= high)
    assert np.allclose(high-low, track['upper_G_m'][index]-track['lower_G_m'][index])
    strings = np.stack((geometry['starts_G_m'], geometry['ends_G_m']), 1)
    frets = geometry['fret_markers_G_m']
    task = v.make_task(v.ROOT/'data/song_bundles/05_BN2-131-B_solo', pre_roll_s=3., tail_s=.5)
    active = [t for t in task.targets if t.press_s <= now < t.end_s]
    surface = v.load_press_surface([t.string for t in task.targets], [t.fret for t in task.targets])
    plane = np.array(surface['plane_G'])
    segments = []
    for target in active:
        lo, hi = sorted([frets[target.fret-1, 1], frets[target.fret, 1]])
        a, b = strings[target.string]
        points = []
        for y in (lo+.002, hi-.002):
            point = a+(y-a[1])/(b[1]-a[1])*(b-a)
            point[2] = -(plane[0]*point[0]+plane[1]*point[1]+plane[3])/plane[2]
            points.append(point)
        segments.append(np.array(points))
    target_w = gp+gr.apply([.04, -.015, -.035])
    right = gr.apply([0., 1., 0.])
    right[2] = 0.
    right /= np.linalg.norm(right)
    backward = np.array([0., 0., 1.])
    top_rotation = v.Rotation.from_matrix(np.column_stack((right, np.cross(backward, right), backward)))
    front_rotation = gr*v.Rotation.from_matrix(v.BASE_AXES)
    side_rotation = gr*v.Rotation.from_matrix(np.array([[0., -1., 0.], [0., 0., 1.], [-1., 0., 0.]]))
    views = [('top', '위에서 · 세계 수직 상단', top_rotation, 1.),
             ('front', '앞에서 · 지판 정면', front_rotation, .86),
             ('side', '옆에서 · 넥 끝에서 몸통 방향', side_rotation, .86)]
    model, data, mapping, _ = v.build_model(initial)
    audit = v.set_body_poses(model, data, mapping, state)
    frozen = [x.copy() for x in (data.xpos, data.xquat, model.body_pos, model.body_quat)]
    title = v.ImageFont.truetype(v.FONT, 24)
    font = v.ImageFont.truetype(v.FONT, 19)
    small = v.ImageFont.truetype(v.FONT, 16)
    renderer = v.mujoco.Renderer(model, height=v.H, width=v.W)
    records = []
    try:
        for key, label, rotation, distance in views:
            eye = target_w+rotation.apply([0., 0., distance])
            assert eye[2] > .05
            q = rotation.as_quat()
            model.cam_pos[0], model.cam_quat[0] = eye, q[[3, 0, 1, 2]]
            v.mujoco.mj_camlight(model, data)
            renderer.update_scene(data, camera='front')
            v.add_strings(renderer.scene, (gp+gr.apply(strings.reshape(-1, 3))).reshape(6, 2, 3))
            image = v.Image.fromarray(renderer.render()).convert('RGBA')
            focal = v.H/2/np.tan(np.deg2rad(model.cam_fovy[0])/2)

            def project(points):
                p = rotation.inv().apply(gp+gr.apply(np.asarray(points))-eye)
                assert np.all(p[..., 2] < 0)
                return np.stack((v.W/2+focal*p[..., 0]/-p[..., 2], v.H/2-focal*p[..., 1]/-p[..., 2]), -1)

            overlay = v.Image.new('RGBA', image.size)
            draw = v.ImageDraw.Draw(overlay)
            v.box(draw, project, outer_low, outer_high, (255, 103, 95, 225))
            v.box(draw, project, low, high, (30, 225, 140, 245), True)
            if key == 'front':
                for fret in range(1, 23):
                    y = frets[fret, 1]
                    line = np.array([s[0]+(y-s[0, 1])/(s[1, 1]-s[0, 1])*(s[1]-s[0]) for s in (strings[0], strings[-1])])
                    draw.line([tuple(p) for p in project(line)], fill=(128, 190, 245, 175), width=1)
                    point = project([[0., .5*(frets[fret-1, 1]+y), surface['plane_G'][3]*-1]])[0]
                    draw.text(tuple(point), str(fret), font=small, anchor='mm', fill=(170, 215, 255))
            for points in segments:
                draw.line([tuple(p) for p in project(points)], fill=(255, 129, 35, 255), width=10)
            wrist = project(wrist_g[None])[0]
            draw.ellipse((wrist[0]-7, wrist[1]-7, wrist[0]+7, wrist[1]+7), fill='white', outline=(15, 25, 40), width=2)
            image = v.Image.alpha_composite(image, overlay).convert('RGB')
            draw = v.ImageDraw.Draw(image)
            draw.rectangle((0, 0, v.W, 91), fill=(20, 28, 39))
            draw.rectangle((0, 615, v.W, v.H), fill=(20, 28, 39))
            draw.text((18, 10), label+' | 손목 영역 중심 이동 후보', font=title, fill='white')
            draw.text((18, 49), '초록: 이동한 안내 영역  ·  빨강: 이동한 종료 경계  ·  흰 점: 초기 손목  ·  주황: 현재 압현 목표', font=font, fill=(215, 230, 245))
            description = ' / '.join(f'{v.FINGERS[t.finger]} {t.string+1}번줄 F{t.fret}' for t in active)
            draw.text((18, 624), '넥을 따라 몸통 쪽 4cm + 지판 뒤 사람 몸쪽 1cm · 크기와 높이 유지', font=title, fill='white')
            draw.text((18, 662), f't={now:.2f}s · {description} · 초기 손목은 초록 영역 안', font=font, fill=(255, 199, 122))
            draw.text((18, 692), '자세 고정 · 상자는 가림 없이 표시 · 시각화 후보만 변경 · 학습 설정 미변경 · 압현 도달성 미검증', font=small, fill=(185, 205, 225))
            path = OUT/(key+'.png')
            image.save(path)
            vertices = np.array(list(v.itertools.product(*zip(outer_low, outer_high))))
            pixels = project(vertices)
            assert np.all(pixels >= [0, 91]) and np.all(pixels <= [v.W, 615])
            records.append(dict(view=key, image=str(path), eye_W_m=eye.tolist(),
                camera_forward_W=rotation.apply([0., 0., -1.]).tolist(),
                outer_box_pixel_min=pixels.min(0).tolist(), outer_box_pixel_max=pixels.max(0).tolist()))
            print(path, flush=True)
    finally:
        renderer.close()
    assert data.time == 0 and model.nq == model.nv == 0
    assert all(np.array_equal(old, new) for old, new in zip(frozen, (data.xpos, data.xquat, model.body_pos, model.body_quat)))
    assert np.allclose(top_rotation.apply([0., 0., -1.]), [0., 0., -1.], atol=1e-12)
    v.write(HERE/'verification.json', dict(proposal_only=True, learning_settings_changed=False,
        time_s=now, shift_G_m=shift.tolist(), lower_G_m=low.tolist(), upper_G_m=high.tolist(),
        outer_lower_G_m=outer_low.tolist(), outer_upper_G_m=outer_high.tolist(),
        wrist_G_m=wrist_g.tolist(), wrist_inside=True,
        wrist_nearest_face_distance_m=float(np.minimum(wrist_g-low, high-wrist_g).min()),
        unchanged_body_transforms=True, physics_steps=0, pose_audit=audit, views=records))


if __name__ == '__main__':
    main()
