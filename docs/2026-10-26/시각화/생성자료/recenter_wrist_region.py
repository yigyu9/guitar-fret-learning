"""Recenter the visual candidate on the score's fret work span; no pose solve."""
from pathlib import Path
import itertools
import json
import ast

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib.patches import Rectangle, Polygon
import propose_wrist_region as previous

ROOT, HERE, OUT = previous.ROOT, previous.HERE, previous.OUT
GREEN = (55, 235, 154, 255)
BLUE = (80, 162, 245, 255)
GOLD = (255, 212, 90, 255)
SONG = ROOT/'data/song_bundles/05_BN2-131-B_solo'


def corrected_bounds(old, frets, fret_range):
    """Use full physical cell boundaries, not an arithmetic mean fret number."""
    first, last = fret_range
    edges = sorted([float(frets[first-1, 1]), float(frets[last, 1])])
    center = sum(edges)/2
    result = dict(old)
    result['lower_G_m'] = list(old['lower_G_m'])
    result['upper_G_m'] = list(old['upper_G_m'])
    result['lower_G_m'][1], result['upper_G_m'][1] = center-.04, center+.04
    result.update(work_fret_range=fret_range, work_edges_y_G_m=edges, work_center_y_G_m=center)
    return result


def box(draw, prepared, camera, bounds, color, fill):
    vertices = np.array(list(itertools.product(*zip(bounds['lower_G_m'], bounds['upper_G_m']))))
    pixels = previous.project(vertices, prepared, camera)
    if fill:
        for axis in range(3):
            for end in (0, 1):
                face = pixels[[i for i in range(8) if ((i >> (2-axis)) & 1) == end]]
                center = face.mean(0)
                order = np.argsort(np.arctan2(face[:, 1]-center[1], face[:, 0]-center[0]))
                draw.polygon([tuple(p) for p in face[order]], fill=color[:3]+(28,))
    for i, j in itertools.combinations(range(8), 2):
        if bin(i ^ j).count('1') == 1:
            draw.line((tuple(pixels[i]), tuple(pixels[j])), fill=color, width=3 if fill else 2)


def native_image(scene, prepared, camera, old, new, frame_index, path):
    image = Image.open(HERE/'fixed_neck.jpg').convert('RGBA')
    layer = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(layer)
    font = ImageFont.truetype(str(previous.FONT), 23)
    small = ImageFont.truetype(str(previous.FONT), 18)
    first, last = new['work_fret_range']
    for cell in scene['cells']:
        quad = [tuple(p) for p in cell['quad_px']]
        if first <= cell['fret'] <= last:
            draw.polygon(quad, fill=GOLD[:3]+(24,))
            draw.line(quad+[quad[0]], fill=GOLD[:3]+(125,), width=1)
        x, y = cell['label_px']
        y += 20 if cell['fret'] >= 15 and cell['fret'] % 2 else 0
        draw.text((x, y), str(cell['fret']), font=small, anchor='mm', fill='white',
                  stroke_width=2, stroke_fill=(24, 30, 36))
    box(draw, prepared, camera, old, BLUE, False)
    box(draw, prepared, camera, new, GREEN, True)
    # The fixed scene does not show a hand moved to the new region.
    wrist = np.array(scene['wrist_G_m'])
    nearest = np.clip(wrist, new['lower_G_m'], new['upper_G_m'])
    start, end = previous.project(np.array([wrist, nearest]), prepared, camera)
    draw.line((tuple(start), tuple(end)), fill='white', width=2)
    x, y = start
    draw.ellipse((x-5, y-5, x+5, y+5), outline='white', width=2)
    draw.text((x, y+24), '초기 손목', anchor='mm', font=small, fill='white',
              stroke_width=2, stroke_fill=(24, 30, 36))
    ref = new['reference_y_G_m']
    edge = new['reference_edge_x_G_m']
    z = new['board_z_G_m']
    center_line = previous.project(np.array([[edge-.047, new['work_center_y_G_m'], z],
                                              [edge+.065, new['work_center_y_G_m'], z]]), prepared, camera)
    draw.line(tuple(map(tuple, center_line)), fill=GOLD, width=2)
    draw.text(tuple(center_line[0]-[0, 15]), '작업 범위 중심', anchor='mm', font=small,
              fill=GOLD, stroke_width=2, stroke_fill=(24, 30, 36))
    for target in scene['targets']:
        if target['onset_s'] <= frame_index/60 < target['end_s']:
            a, b = target['segment_px']
            draw.line((tuple(a), tuple(b)), fill=(255, 145, 35), width=7)
    image = Image.alpha_composite(image, layer).convert('RGB')
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1280, 100), fill=(22, 27, 34))
    draw.rectangle((0, 624, 1280, 720), fill=(22, 27, 34))
    draw.text((20, 10), f"보정안: 작업 프렛 F{first}~F{last} 중심 ±4cm | 기준 포지션 F{new['anchor_fret']:.0f}", font=font, fill='white')
    draw.text((20, 49), '초록: 보정 영역 · 파랑 테두리: 이전 영역 · 노랑: 작업 범위와 중심 · 흰 원: 초기 손목', font=small, fill=(220, 235, 245))
    near_nut = (new['upper_G_m'][1]-ref)*100
    body = (ref-new['lower_G_m'][1])*100
    draw.text((20, 636), f'기준 프렛에서 너트 쪽 {near_nut:.1f}cm ~ 바디 쪽 {body:.1f}cm | 높이 2~6cm · 지판 뒤 3~9cm', font=font, fill='white')
    draw.text((20, 678), '휴머노이드·기타 고정 · 영역 위치만 보정 · 학습 미적용 · 자연스러운 압현 자세 검증 전', font=small, fill=(220, 235, 245))
    image.save(path)


def sections(wrist, old, new, polygons, path):
    plt, fp = previous.plt, previous.FP
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), layout='constrained')
    ref, edge, board = old['reference_y_G_m'], old['reference_edge_x_G_m'], old['board_z_G_m']
    along, below, depth = (wrist[1]-ref)*100, (wrist[0]-edge)*100, (board-wrist[2])*100
    center = (new['work_center_y_G_m']-ref)*100
    for ax in axes:
        ax.set_facecolor('#f7f9fa'); ax.grid(alpha=.2)
        ax.set_ylim(8, -5.5); ax.set_aspect('equal', adjustable='box')
        ax.set_ylabel('넥 아래 테두리부터 아래 방향 (cm)', fontproperties=fp, fontsize=12)
    ax = axes[0]
    ax.set_title('길이 방향: 초기 손목 대신 작업 범위를 기준으로', fontproperties=fp, fontsize=15)
    ax.add_patch(Rectangle((-18, -4.5), 24, 4.5, facecolor='#c5cbd1', alpha=.8))
    work = [(v-ref)*100 for v in new['work_edges_y_G_m']]
    ax.add_patch(Rectangle((work[0], -4.5), work[1]-work[0], 4.5, facecolor='#f5cb58', alpha=.35))
    ax.text((work[0]+work[1])/2, -3, '작업 F4~F9\n넥은 개략 표시', ha='center', fontproperties=fp, fontsize=11)
    ax.axvline(0, color='#777', linestyle=':', linewidth=1.5)
    ax.text(.3, -4.8, '기준 F5 셀 중심', fontproperties=fp, fontsize=10)
    ax.axvline(center, color='#c58a00', linestyle='--', linewidth=2)
    ax.add_patch(Rectangle((-13, 2), 8, 4, fill=False, edgecolor='#4799eb', linewidth=2, linestyle='--'))
    ax.text(-10, 2.7, '이전', color='#3076bd', ha='center', fontproperties=fp, fontsize=12)
    ax.add_patch(Rectangle((center-4, 2), 8, 4, facecolor='#31bc79', edgecolor='#168250', alpha=.35, linewidth=2))
    ax.text(center, 3.3, '보정 영역\n작업 중심 ±4cm', ha='center', fontproperties=fp, fontsize=12)
    ax.plot(along, below, 'o', color='#274860', markersize=8)
    ax.annotate('초기 손목은 새 영역 밖', xy=(along, below), xytext=(-17, 7),
                arrowprops={'arrowstyle':'->'}, fontproperties=fp, fontsize=11)
    ax.set_xlim(-18, 6)
    ax.set_xlabel('기준 F5에서 길이 방향 (cm)  ← 기타 바디 / 너트 →', fontproperties=fp, fontsize=12)
    ax = axes[1]
    ax.set_title('높이·깊이: 이전 범위 유지', fontproperties=fp, fontsize=15)
    for p in polygons:
        coords = np.c_[(board-p[:, 1])*100, (p[:, 0]-edge)*100]
        ax.add_patch(Polygon(coords, facecolor='#c5cbd1', edgecolor='#687783', alpha=.8))
    ax.axvline(0, color='#c58a00', linewidth=2, linestyle='--')
    ax.text(-.25, -4.8, '지판면', ha='right', fontproperties=fp, fontsize=12)
    ax.add_patch(Rectangle((3, 2), 6, 4, facecolor='#31bc79', edgecolor='#168250', alpha=.35, linewidth=2))
    ax.text(6, 3.2, '지판 뒤 3~9cm\n넥 아래 2~6cm', ha='center', fontproperties=fp, fontsize=12)
    ax.plot(depth, below, 'o', color='#274860', markersize=8)
    ax.set_xlim(-2, 11)
    ax.set_xlabel('지판면에서 연주자 쪽 깊이 (cm) →', fontproperties=fp, fontsize=12)
    fig.suptitle('손목 영역의 바디 쪽 편향 보정 — 압현 자세를 풀어 얻은 영역은 아님', fontproperties=fp, fontsize=17)
    fig.savefig(path, dpi=160); plt.close(fig)


def main():
    scene = json.loads((HERE/'scene.json').read_text())
    camera = json.loads((HERE/'camera.json').read_text())
    track_path = SONG/'training/hand_position_targets.json'
    track = json.loads(track_path.read_text())
    manifest = json.loads((SONG/'manifest.json').read_text())['files']['training/hand_position_targets.json']
    assert previous.sha(track_path) == manifest['sha256'] and track_path.stat().st_size == manifest['bytes']
    prepared = previous.load_prepared_reset_contract()
    initial = prepared['initial']
    geometry = previous.geometry_snapshot(prepared['state'], initial['human_body_names'], initial['guitar_body_names'])
    frets = np.asarray(geometry['fret_markers_G_m'])
    plane, hulls, pins = previous._extract_plane(ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/guitar_compound.xml', scene['press_plane']['source_sha256'])
    wrist = np.array(scene['wrist_G_m'])
    frames = [219, int(np.argmin(np.abs(np.array(scene['anchor_fret'])-9)))]
    rows = []
    for f in frames:
        track_index = max(0, f-180)  # visualization includes 3 s policy pre-roll.
        item = track['frames'][track_index]
        anchor = scene['anchor_fret'][f]
        assert abs(anchor-item['anchor_fret']) < 1e-5
        old = previous.bounds(anchor, frets, plane, hulls)
        new = corrected_bounds(old, frets, item['allowed_fret_range'])
        old_center = (old['lower_G_m'][1]+old['upper_G_m'][1])/2
        shift = new['work_center_y_G_m']-old_center
        body = [(new['reference_y_G_m']-new[key][1])*100 for key in ['upper_G_m', 'lower_G_m']]
        assert np.allclose(np.array(new['upper_G_m'])-new['lower_G_m'], [.04, .08, .06])
        for corner in itertools.product(*zip(new['lower_G_m'], new['upper_G_m'])):
            assert previous.penalty(corner, new) == 0
        native_image(scene, prepared, camera, old, new, f, OUT/f'wrist_region_anchor{round(anchor)}_recentered.png')
        rows.append(dict(frame=f, time_s=f/60, old=old, corrected=new, bodyward_bounds_cm=body,
            shift_toward_nut_cm=shift*100, initial_wrist_distance_to_region_cm=float(np.linalg.norm(previous.excess(wrist, new))*100)))
    sections(wrist, rows[0]['old'], rows[0]['corrected'], previous.neck_slice(hulls, rows[0]['old']['reference_y_G_m']), OUT/'wrist_region_recentered_axes.png')
    for path in [Path(__file__), HERE/'propose_wrist_region.py', HERE/'scene.json', HERE/'camera.json', HERE/'fixed_neck.jpg', track_path, SONG/'manifest.json', previous.FONT]:
        pins[str(path)] = previous.sha(path)
    result = dict(schema='wrist_region_recentered_visual_candidate.v1', proposal_only=True, learning_implemented=False,
        method='physical midpoint of score allowed_fret_range cell boundaries +/-4cm; height/depth unchanged',
        half_width_along_m=.04, below_edge_cm=[2,6], behind_board_cm=[3,9], rows=rows,
        limitations=['geometric work-span centering candidate, not a kinematically solved natural grasp',
                      'humanoid and guitar remain at prepared pose; no physics or policy executed',
                      'height/depth unchanged; full region fingertip reach and joint posture not established'],
        source_sha256=pins)
    (HERE/'wrist_region_recentered.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    ast.parse(Path(__file__).read_text())
    print(json.dumps(rows, ensure_ascii=False))


if __name__ == '__main__':
    main()
