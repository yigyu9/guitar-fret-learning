"""World-vertical still of the existing frozen pose and saved wrist track."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('wrist_views', HERE/'render_views.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def main():
    np = v.np
    prepared = v.load_prepared_reset_contract()
    initial, state = prepared['initial'], prepared['state']
    geometry = v.geometry_snapshot(state, initial['human_body_names'], initial['guitar_body_names'])
    gp, gr = v.frame(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    track = np.load(HERE/'region_track.npz')
    index = 110
    now = float(track['time_s'][index])
    strings = np.stack((geometry['starts_G_m'], geometry['ends_G_m']), 1)
    frets = geometry['fret_markers_G_m']
    task = v.make_task(v.ROOT/'data/song_bundles/05_BN2-131-B_solo', pre_roll_s=3., tail_s=.5)
    surface = v.load_press_surface([t.string for t in task.targets], [t.fret for t in task.targets])
    target_w = gp+gr.apply([.04, -.015, -.035])
    eye = target_w+np.array([0., 0., 1.0])
    backward = np.array([0., 0., 1.])
    right = gr.apply([0., 1., 0.])
    right[2] = 0.
    right /= np.linalg.norm(right)
    rotation = v.Rotation.from_matrix(np.column_stack((right, np.cross(backward, right), backward)))
    model, data, mapping, _ = v.build_model(initial)
    audit = v.set_body_poses(model, data, mapping, state)
    frozen = [x.copy() for x in (data.xpos, data.xquat, model.body_pos, model.body_quat)]
    q = rotation.as_quat()
    model.cam_pos[0], model.cam_quat[0] = eye, q[[3, 0, 1, 2]]
    v.mujoco.mj_camlight(model, data)
    renderer = v.mujoco.Renderer(model, height=v.H, width=v.W)
    try:
        renderer.update_scene(data, camera='front')
        v.add_strings(renderer.scene, (gp+gr.apply(strings.reshape(-1, 3))).reshape(6, 2, 3))
        image = v.Image.fromarray(renderer.render()).convert('RGBA')
    finally:
        renderer.close()
    focal = v.H/2/np.tan(np.deg2rad(model.cam_fovy[0])/2)

    def project(points):
        p = rotation.inv().apply(gp+gr.apply(np.asarray(points))-eye)
        assert np.all(p[..., 2] < 0)
        return np.stack((v.W/2+focal*p[..., 0]/-p[..., 2], v.H/2-focal*p[..., 1]/-p[..., 2]), -1)

    overlay = v.Image.new('RGBA', image.size)
    draw = v.ImageDraw.Draw(overlay)
    v.box(draw, project, track['outer_lower_G_m'][index], track['outer_upper_G_m'][index], (255, 103, 95, 230))
    v.box(draw, project, track['lower_G_m'][index], track['upper_G_m'][index], (30, 225, 140, 245), True)
    for fret in range(1, 23):
        y = frets[fret, 1]
        line = np.array([s[0]+(y-s[0, 1])/(s[1, 1]-s[0, 1])*(s[1]-s[0]) for s in (strings[0], strings[-1])])
        draw.line([tuple(p) for p in project(line)], fill=(128, 190, 245, 175), width=1)
    active = [t for t in task.targets if t.press_s <= now < t.end_s]
    plane = np.array(surface['plane_G'])
    for target in active:
        lo, hi = sorted([frets[target.fret-1, 1], frets[target.fret, 1]])
        points = []
        a, b = strings[target.string]
        for y in (lo+.002, hi-.002):
            point = a+(y-a[1])/(b[1]-a[1])*(b-a)
            point[2] = -(plane[0]*point[0]+plane[1]*point[1]+plane[3])/plane[2]
            points.append(point)
        draw.line([tuple(p) for p in project(points)], fill=(255, 129, 35, 255), width=10)
    wrist = project(track['wrist_G_m'][None])[0]
    draw.ellipse((wrist[0]-7, wrist[1]-7, wrist[0]+7, wrist[1]+7), fill='white', outline=(15, 25, 40), width=2)
    image = v.Image.alpha_composite(image, overlay).convert('RGB')
    draw = v.ImageDraw.Draw(image)
    title = v.ImageFont.truetype(v.FONT, 24)
    font = v.ImageFont.truetype(v.FONT, 19)
    draw.rectangle((0, 0, v.W, 91), fill=(20, 28, 39))
    draw.rectangle((0, 635, v.W, v.H), fill=(20, 28, 39))
    draw.text((18, 10), '수직 상단 시점 | 세계 수직 방향에서 내려다봄', font=title, fill='white')
    draw.text((18, 49), '초록: 손목 안내 영역  ·  빨강: 지속 이탈 종료 경계  ·  흰 점: 초기 손목  ·  주황: 현재 압현 목표', font=font, fill=(215, 230, 245))
    description = ' / '.join(f'{v.FINGERS[t.finger]} {t.string+1}번줄 F{t.fret}' for t in active)
    draw.text((18, 645), f't={now:.2f}s · 현재 목표: {description} · 사람과 기타 고정', font=title, fill=(255, 199, 122))
    draw.text((18, 684), '카메라: 세계 −Z 방향 · 원근 투영 · 실측 초기 자세의 정적 재구성', font=font, fill=(215, 230, 245))
    path = v.OUT/'top_down.png'
    image.save(path)
    assert np.allclose(rotation.apply([0., 0., -1.]), [0., 0., -1.], atol=1e-12)
    assert np.array_equal(eye[:2], target_w[:2])
    assert data.time == 0 and model.nq == model.nv == 0
    assert all(np.array_equal(old, new) for old, new in zip(frozen, (data.xpos, data.xquat, model.body_pos, model.body_quat)))
    v.write(HERE/'top_down_verification.json', dict(image=str(path), time_s=now, eye_W_m=eye.tolist(),
        target_W_m=target_w.tolist(), camera_forward_W=rotation.apply([0., 0., -1.]).tolist(),
        unchanged_body_transforms=True, physics_steps=0, pose_audit=audit))
    print(path)


if __name__ == '__main__':
    main()
