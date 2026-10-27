"""Animate the saved song targets and shifted wrist boxes over frozen poses."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('shifted_stills', HERE/'render_shifted.py')
stills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stills)
v, OUT = stills.v, HERE.parent


def main(thumb_overlay=False, thumb_head_cm=0, bottom_only=False):
    thumb_overlay = thumb_overlay or bool(thumb_head_cm)
    np = v.np
    track = np.load(stills.SOURCE/'region_track.npz')
    camera_records = v.json.loads((HERE/'verification.json').read_text())['views']
    top_camera = next(c for c in camera_records if c['view'] == 'top')
    source_records = v.json.loads((stills.SOURCE/'verification.json').read_text())['cameras']
    top_q = v.json.loads((stills.SOURCE/'top_down_verification.json').read_text())
    prepared = v.load_prepared_reset_contract()
    initial, state = prepared['initial'], prepared['state']
    geometry = v.geometry_snapshot(state, initial['human_body_names'], initial['guitar_body_names'])
    gp, gr = v.frame(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    right_horizontal = gr.apply([0., 1., 0.])
    right_horizontal[2] = 0.
    right_horizontal /= np.linalg.norm(right_horizontal)
    bottom_backward = np.array([0., 0., -1.])
    bottom_rotation = v.Rotation.from_matrix(np.column_stack((right_horizontal,
        np.cross(bottom_backward, right_horizontal), bottom_backward)))
    rear_rotation = gr*v.Rotation.from_matrix(np.array([[0., -1., 0.], [-1., 0., 0.], [0., 0., -1.]]))
    if thumb_head_cm:
        eye = gp+gr.apply([.04, -.015, -.035])+rear_rotation.apply([0., 0., .86])
        assert eye[2] > .05
        camera_records.insert(0, dict(view='rear', eye_W_m=eye.tolist(),
            camera_forward_W=rear_rotation.apply([0., 0., -1.]).tolist()))
    if bottom_only:
        eye = gp+gr.apply([.04, -.015, -.035])+bottom_rotation.apply([0., 0., 1.])
        camera_records = [dict(view='bottom', eye_W_m=eye.tolist(),
            camera_forward_W=bottom_rotation.apply([0., 0., -1.]).tolist())]
    shift = np.array([0., -.04, -.01])
    lows, highs = track['lower_G_m']+shift, track['upper_G_m']+shift
    times, wrist_g = track['time_s'], track['wrist_G_m']
    video_out = v.ROOT/'docs/2026-11-02/손목' if thumb_overlay else OUT
    prefix = f'thumb_head{thumb_head_cm}_' if thumb_head_cm else 'thumb_' if thumb_overlay else ''
    report_prefix = prefix+'bottom_' if bottom_only else prefix
    video_out.mkdir(parents=True, exist_ok=True)
    for camera in camera_records:
        if (video_out/(prefix+camera['view']+'.mp4')).exists():
            raise FileExistsError(video_out/(prefix+camera['view']+'.mp4'))
    thumb_corners, thumb_audit = None, None
    if thumb_overlay:
        from guitar_learning.gpu.thumb_support import load_thumb_support, thumb_support_geometry
        thumb = load_thumb_support()
        rear, plane_rear = thumb['rear_vertices'], thumb['plane']
        head_offset_m = thumb_head_cm/100.
        center_y = .5*(lows[:, 1]+highs[:, 1])+head_offset_m
        ys = np.stack((np.maximum(center_y-.04, rear[0, 1]),
                       np.minimum(center_y+.04, rear[2, 1])), -1)
        assert np.all(ys[:, 1] > ys[:, 0])
        fraction = ((ys-rear[0, 1])/(rear[2, 1]-rear[0, 1])).clip(0, 1)
        left = rear[0, 0]+fraction*(rear[3, 0]-rear[0, 0])
        right_edge = rear[1, 0]+fraction*(rear[2, 0]-rear[1, 0])
        middle, half = (left+right_edge)/2, (right_edge-left)/4
        thumb_corners = np.empty((len(times), 4, 3))
        thumb_corners[..., 0] = np.stack((middle[:, 0]-half[:, 0], middle[:, 0]+half[:, 0],
                                        middle[:, 1]+half[:, 1], middle[:, 1]-half[:, 1]), -1)
        thumb_corners[..., 1] = ys[:, [0, 0, 1, 1]]
        thumb_corners[..., 2] = -(thumb_corners[..., :2]@plane_rear[:2]+plane_rear[3])/plane_rear[2]
        # Check every drawn corner against the actual production region evaluator.
        tensor = lambda a: v.torch.tensor(a, dtype=v.torch.float64)
        unit = plane_rear[:3]/np.linalg.norm(plane_rear[:3])
        points = thumb_corners.reshape(-1, 1, 3)
        check = thumb_support_geometry(tensor(points), tensor(np.broadcast_to(-unit, points.shape).copy()),
            v.torch.ones(1, dtype=v.torch.bool), tensor(np.repeat(center_y, 4)), tensor(rear), tensor(plane_rear))
        max_delta = float(check['delta'].abs().max())
        assert bool(check['valid'].all()) and max_delta < 1e-9
        assert np.allclose(thumb_corners@plane_rear[:3]+plane_rear[3], 0., atol=1e-12)
        thumb_audit = dict(center='shifted wrist-box Gy midpoint plus headward offset',
            headward_offset_m=head_offset_m, half_length_m=.04,
            neck_width_fraction=.5, rear_plane=plane_rear.tolist(), source_sha256=thumb['contract']['source_sha256'],
            all_corners_match_production_region=True, maximum_delta_m=max_delta,
            region_center_range_G_m=np.ptp(thumb_corners.mean(1), axis=0).tolist(),
            plane_is_real_neck_rear=True, wrist_depth_shift_not_applied_to_rear_surface=True)
    bundle = v.ROOT/'data/song_bundles/05_BN2-131-B_solo'
    task = v.make_task(bundle, pre_roll_s=3., tail_s=.5)
    score_frames = v.json.loads((bundle/'training/hand_position_targets.json').read_text())['frames']
    surface = v.load_press_surface([t.string for t in task.targets], [t.fret for t in task.targets])
    plane = np.array(surface['plane_G'])
    frets = geometry['fret_markers_G_m']
    strings = np.stack((geometry['starts_G_m'], geometry['ends_G_m']), 1)
    segments = []
    for target in task.targets:
        lo, hi = sorted([frets[target.fret-1, 1], frets[target.fret, 1]])
        a, b = strings[target.string]
        points = []
        for y in (lo+.002, hi-.002):
            p = a+(y-a[1])/(b[1]-a[1])*(b-a)
            p[2] = -(plane[0]*p[0]+plane[1]*p[1]+plane[3])/plane[2]
            points.append(p)
        segments.append(np.array(points))
    right = right_horizontal
    backward = np.array([0., 0., 1.])
    rotations = dict(top=v.Rotation.from_matrix(np.column_stack((right, np.cross(backward, right), backward))),
        front=v.Rotation.from_quat(next(c['quaternion_xyzw'] for c in source_records if c['view'] == 'front')),
        side=gr*v.Rotation.from_matrix(np.array([[0., -1., 0.], [0., 0., 1.], [-1., 0., 0.]])),
        rear=rear_rotation, bottom=bottom_rotation)
    assert np.allclose(top_camera['eye_W_m'], top_q['eye_W_m'])
    model, data, mapping, _ = v.build_model(initial)
    audit = v.set_body_poses(model, data, mapping, state)
    frozen = [x.copy() for x in (data.xpos, data.xquat, model.body_pos, model.body_quat)]
    original_colors = model.geom_rgba.copy()
    rear_hidden = []
    if thumb_head_cm:
        for geom, body in enumerate(model.geom_bodyid):
            name = v.mujoco.mj_id2name(model, v.mujoco.mjtObj.mjOBJ_BODY, int(body)) or ''
            if ((name.startswith('human/') and name not in ('human/L_Wrist', 'human/L_Elbow')
                 and not name.startswith('human/LH:')) or name == 'chair'):
                rear_hidden.append(geom)
    title, font, small = [v.ImageFont.truetype(v.FONT, size) for size in (24, 19, 16)]
    labels = dict(top='위에서 · 수직 상단', front='앞에서 · 지판 정면', side='옆에서 · 넥 끝에서 몸통 방향',
        rear='뒤에서 · 넥 뒷면 · 몸통 가림 제거', bottom='아래에서 · 수직 하단 · 바닥과 몸통 가림 제거')
    active = [[i for i, target in enumerate(task.targets) if target.press_s <= now < target.end_s] for now in times]
    counts = np.bincount([i for ids in active for i in ids], minlength=len(task.targets))
    assert len(task.targets) == 67 and np.all(counts > 0)
    renderer = v.mujoco.Renderer(model, height=v.H, width=v.W)
    videos = []
    try:
        for camera in camera_records:
            key = camera['view']
            model.geom_rgba[:] = original_colors
            if key in ('rear', 'bottom'):
                model.geom_rgba[rear_hidden, 3] = 0.
            if key == 'bottom':
                floor = v.mujoco.mj_name2id(model, v.mujoco.mjtObj.mjOBJ_GEOM, 'floor')
                assert floor >= 0
                model.geom_rgba[floor, 3] = 0.
            rotation, eye = rotations[key], np.array(camera['eye_W_m'])
            assert np.allclose(rotation.apply([0., 0., -1.]), camera['camera_forward_W'])
            q = rotation.as_quat()
            model.cam_pos[0], model.cam_quat[0] = eye, q[[3, 0, 1, 2]]
            v.mujoco.mj_camlight(model, data)
            renderer.update_scene(data, camera='front')
            v.add_strings(renderer.scene, (gp+gr.apply(strings.reshape(-1, 3))).reshape(6, 2, 3))
            background = v.Image.fromarray(renderer.render()).convert('RGBA')
            focal = v.H/2/np.tan(np.deg2rad(model.cam_fovy[0])/2)

            def project(points):
                p = rotation.inv().apply(gp+gr.apply(np.asarray(points))-eye)
                assert np.all(p[..., 2] < 0)
                return np.stack((v.W/2+focal*p[..., 0]/-p[..., 2], v.H/2-focal*p[..., 1]/-p[..., 2]), -1)

            static = v.Image.new('RGBA', background.size)
            draw = v.ImageDraw.Draw(static)
            if key == 'front':
                for fret in range(1, 23):
                    y = frets[fret, 1]
                    line = np.array([s[0]+(y-s[0, 1])/(s[1, 1]-s[0, 1])*(s[1]-s[0]) for s in (strings[0], strings[-1])])
                    draw.line([tuple(p) for p in project(line)], fill=(128, 190, 245, 175), width=1)
            wrist = project(wrist_g[None])[0]
            path = video_out/(prefix+key+'.mp4')
            encoder = v.subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n',
                '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', '30', '-i', '-',
                '-an', '-c:v', 'libx264', '-threads', '2', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p', str(path)], stdin=v.subprocess.PIPE)
            try:
                for index, now in enumerate(times):
                    overlay = static.copy()
                    draw = v.ImageDraw.Draw(overlay)
                    low, high = lows[index], highs[index]
                    vertices = np.array(list(v.itertools.product(*zip(low-.03, high+.03))))
                    pixels = project(vertices)
                    assert np.all(pixels >= [0, 91]) and np.all(pixels <= [v.W, 615])
                    v.box(draw, project, low-.03, high+.03, (255, 103, 95, 225))
                    v.box(draw, project, low, high, (30, 225, 140, 245), True)
                    if thumb_overlay:
                        polygon = project(thumb_corners[index])
                        assert np.all(polygon >= [0, 91]) and np.all(polygon <= [v.W, 615])
                        draw.polygon([tuple(p) for p in polygon], fill=(40, 205, 255, 90))
                        draw.line([tuple(p) for p in np.vstack((polygon, polygon[:1]))], fill=(65, 220, 255, 255), width=5)
                        center_pixel = polygon.mean(0)
                        label_pos = (center_pixel[0]+30, min(polygon[:, 1].min()-40, 230))
                        draw.line([tuple(center_pixel), (label_pos[0]-5, label_pos[1]+13)], fill=(65, 220, 255, 255), width=2)
                        draw.text(label_pos, '엄지 접촉 범위', font=font, fill=(65, 220, 255, 255), stroke_width=2, stroke_fill=(15, 25, 40, 255))
                    upcoming = [i for i, target in enumerate(task.targets) if now < target.press_s <= now+.5]
                    for ids, color, width in ((upcoming, (255, 224, 94, 255), 6), (active[index], (255, 129, 35, 255), 10)):
                        for i in ids:
                            draw.line([tuple(p) for p in project(segments[i])], fill=color, width=width)
                    draw.ellipse((wrist[0]-7, wrist[1]-7, wrist[0]+7, wrist[1]+7), fill='white', outline=(15, 25, 40), width=2)
                    image = v.Image.alpha_composite(background, overlay).convert('RGB')
                    draw = v.ImageDraw.Draw(image)
                    draw.rectangle((0, 0, v.W, 91), fill=(20, 28, 39))
                    draw.rectangle((0, 615, v.W, v.H), fill=(20, 28, 39))
                    subject = '엄지 접촉 범위와 곡 목표' if thumb_overlay else '곡 목표와 이동한 손목 영역'
                    draw.text((18, 10), f'{labels[key]} | {subject} | t={now:.2f}s', font=title, fill='white')
                    legend = ('하늘색: 엄지 접촉 범위 · 초록: 손목 허용 · 빨강: 종료 경계 · 흰 점: 손목 · 주황/노랑: 현재/다음 압현'
                              if thumb_overlay else '초록: 안내 영역  ·  빨강: 종료 경계  ·  흰 점: 고정 초기 손목  ·  주황: 현재 압현  ·  노랑: 다음 목표')
                    draw.text((18, 49), legend, font=font, fill=(215, 230, 245))
                    description = ' / '.join(f'{v.FINGERS[task.targets[i].finger]} {task.targets[i].string+1}번줄 F{task.targets[i].fret}' for i in active[index]) or ('초기 준비' if now < 3 else '압현 목표 없음')
                    draw.text((18, 624), '현재 목표: '+description, font=title, fill=(255, 199, 122))
                    row = score_frames[min(max(int((now-3)*60), 0), len(score_frames)-1)]
                    span = row['allowed_fret_range']
                    inside = bool(np.all(wrist_g >= low) and np.all(wrist_g <= high))
                    thumb_center_description = f'손목 중심보다 헤드 쪽 {thumb_head_cm}cm' if thumb_head_cm else '옮긴 손목 중심을 따라 이동'
                    detail = (f'작업 F{span[0]}~F{span[1]} · 엄지: 넥 뒷면 가운데 50% / 길이 ±4cm · {thumb_center_description}'
                              if thumb_overlay else f'작업 F{span[0]}~F{span[1]} · 몸통 쪽 4cm + 지판 뒤 1cm · 초기 손목: '+('영역 안' if inside else '영역 밖'))
                    draw.text((18, 662), detail, font=font, fill='white')
                    note = ('사람·기타 고정 · 가림 없이 겹쳐 표시 · 접촉 면은 실제 넥 뒷면 유지 · 시각화 후보 · 학습 설정 미변경'
                            if thumb_overlay else '사람·기타 고정 · 영역과 곡 목표만 변화 · 시각화 후보 · 학습 설정 미변경 · 압현 도달성 미검증')
                    draw.text((18, 692), note, font=small, fill=(185, 205, 225))
                    if index in (110, 500, 800):
                        image.save(HERE/(prefix+key+f'_motion_{index:04d}.png'))
                    encoder.stdin.write(np.asarray(image).tobytes())
            finally:
                encoder.stdin.close()
                code = encoder.wait()
            assert code == 0
            probe = v.json.loads(v.subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,nb_frames,avg_frame_rate,duration', '-of', 'json', str(path)]))['streams'][0]
            assert int(probe['nb_frames']) == len(times) and probe['avg_frame_rate'] == '30/1'
            videos.append(dict(path=str(path), stream=probe))
            print('DONE', key, flush=True)
    finally:
        renderer.close()
        model.geom_rgba[:] = original_colors
    assert data.time == 0 and model.nq == model.nv == 0
    assert all(np.array_equal(old, new) for old, new in zip(frozen, (data.xpos, data.xquat, model.body_pos, model.body_quat)))
    if thumb_overlay and not bottom_only:
        np.savez_compressed(HERE/(prefix+'region_track.npz'), time_s=times, corners_G_m=thumb_corners,
                            wrist_lower_G_m=lows, wrist_upper_G_m=highs)
    v.write(HERE/(report_prefix+'video_verification.json'), dict(completed=True, proposal_only=True,
        learning_settings_changed=False, shift_G_m=shift.tolist(), target_count=len(task.targets),
        minimum_active_frames_per_target=int(counts.min()), frames=len(times), fps=30,
        original_duration_s=task.duration_s, video_duration_s=len(times)/30.,
        guide_center_range_G_m=np.ptp((lows+highs)/2, axis=0).tolist(),
        unchanged_body_transforms=True, physics_steps=0, pose_audit=audit, videos=videos,
        thumb_region=thumb_audit, cameras=camera_records, bottom_view_floor_hidden=bottom_only,
        rear_view_hidden_geometry_count=len(rear_hidden),
        rear_view_scope='guitar and left elbow/wrist/hand visible; other human bodies and chair hidden' if thumb_head_cm else None))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--thumb', action='store_true')
    head = parser.add_mutually_exclusive_group()
    head.add_argument('--thumb-head2', action='store_true')
    head.add_argument('--thumb-head5', action='store_true')
    parser.add_argument('--bottom', action='store_true')
    args = parser.parse_args()
    main(thumb_overlay=args.thumb, thumb_head_cm=5 if args.thumb_head5 else 2 if args.thumb_head2 else 0,
         bottom_only=args.bottom)
