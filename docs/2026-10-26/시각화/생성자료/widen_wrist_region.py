"""Widen the agreed visual candidate, preserving all previous artifacts."""
from pathlib import Path
import ast
import itertools
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib.patches import Rectangle, Polygon
import recenter_wrist_region as recentered

previous = recentered.previous
HERE, OUT = previous.HERE, previous.OUT


def widen(narrow):
    result = dict(narrow)
    center, edge, board = (narrow['work_center_y_G_m'], narrow['reference_edge_x_G_m'], narrow['board_z_G_m'])
    result['lower_G_m'] = [edge+.01, center-.06, board-.11]
    result['upper_G_m'] = [edge+.08, center+.06, board-.02]
    return result


def native(scene, prepared, camera, narrow, wide, frame_index, path):
    # Reuse the frozen scene projection/boxes; replace its narrower-range captions.
    recentered.native_image(scene, prepared, camera, narrow, wide, frame_index, path)
    image = Image.open(path).convert('RGBA')
    outlines = Image.new('RGBA', image.size)
    recentered.box(ImageDraw.Draw(outlines), prepared, camera, narrow, recentered.BLUE, False)
    image = Image.alpha_composite(image, outlines).convert('RGB')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(previous.FONT), 23)
    small = ImageFont.truetype(str(previous.FONT), 18)
    for rect in [(0, 0, 1280, 100), (0, 624, 1280, 720)]:
        draw.rectangle(rect, fill=(22, 27, 34))
    first, last = wide['work_fret_range']
    draw.text((20, 10), f'확대안: 작업 F{first}~F{last} 중심 ±6cm | 넥 아래 1~8cm | 지판 뒤 2~11cm', font=font, fill='white')
    draw.text((20, 49), '초록: 넓힌 영역 · 파랑 테두리: 이전 보정안 · 노랑: 작업 범위와 중심 · 흰 원: 초기 손목', font=small, fill=(220, 235, 245))
    ref = wide['reference_y_G_m']
    nut, body = (wide['upper_G_m'][1]-ref)*100, (ref-wide['lower_G_m'][1])*100
    draw.text((20, 636), f'기준 F{wide["anchor_fret"]:.0f}에서 너트 쪽 {nut:.1f}cm ~ 바디 쪽 {body:.1f}cm | 허용 부피 12 × 7 × 9cm', font=font, fill='white')
    draw.text((20, 678), '초기 자세 고정 · 영역 안 위치 패널티 0을 제안 · 학습 미적용 · 압현 자세·도달성 검증 전', font=small, fill=(220, 235, 245))
    image.save(path)


def sections(wrist, narrow, wide, polygons, path):
    plt, fp = previous.plt, previous.FP
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), layout='constrained')
    ref, edge, board = narrow['reference_y_G_m'], narrow['reference_edge_x_G_m'], narrow['board_z_G_m']
    center = (wide['work_center_y_G_m']-ref)*100
    for ax in axes:
        ax.set_facecolor('#f7f9fa'); ax.grid(alpha=.2)
        ax.set_ylim(10, -5.5); ax.set_aspect('equal', adjustable='box')
        ax.set_ylabel('넥 아래 테두리부터 아래 방향 (cm)', fontproperties=fp, fontsize=12)
    ax = axes[0]
    ax.set_title('길이·높이: 중심 유지, 폭 8→12cm / 높이 4→7cm', fontproperties=fp, fontsize=14)
    ax.add_patch(Rectangle((-17, -4.5), 25, 4.5, facecolor='#c5cbd1', alpha=.8))
    work = [(v-ref)*100 for v in wide['work_edges_y_G_m']]
    ax.add_patch(Rectangle((work[0], -4.5), work[1]-work[0], 4.5, facecolor='#f5cb58', alpha=.35))
    ax.text(sum(work)/2, -3, '작업 F4~F9\n넥은 개략 표시', ha='center', fontproperties=fp, fontsize=11)
    ax.axvline(0, color='#777', linestyle=':', linewidth=1.5)
    ax.text(.3, -4.8, '기준 F5 셀 중심', fontproperties=fp, fontsize=10)
    ax.axvline(center, color='#c58a00', linestyle='--', linewidth=2)
    ax.add_patch(Rectangle((center-6, 1), 12, 7, facecolor='#31bc79', edgecolor='#168250', alpha=.35, linewidth=2))
    ax.add_patch(Rectangle((center-4, 2), 8, 4, fill=False, edgecolor='#4799eb', linewidth=2, linestyle='--'))
    ax.text(center, 4.3, '이전: ±4cm / 아래 2~6cm', ha='center', fontproperties=fp, fontsize=10, color='#245a90')
    ax.text(center, 7.2, '확대: 작업 중심 ±6cm / 아래 1~8cm', ha='center', fontproperties=fp, fontsize=11)
    point = ((wrist[1]-ref)*100, (wrist[0]-edge)*100)
    ax.plot(*point, 'o', color='#274860', markersize=8)
    ax.annotate('초기 손목', xy=point, xytext=(-16, 9), arrowprops={'arrowstyle':'->'}, fontproperties=fp, fontsize=11)
    ax.set_xlim(-17, 8)
    ax.set_xlabel('기준 F5에서 길이 방향 (cm)  ← 기타 바디 / 너트 →', fontproperties=fp, fontsize=12)
    ax = axes[1]
    ax.set_title('앞뒤 깊이: 폭 6→9cm', fontproperties=fp, fontsize=14)
    for p in polygons:
        coords = np.c_[(board-p[:, 1])*100, (p[:, 0]-edge)*100]
        ax.add_patch(Polygon(coords, facecolor='#c5cbd1', edgecolor='#687783', alpha=.8))
    ax.axvline(0, color='#c58a00', linewidth=2, linestyle='--')
    ax.text(-.25, -4.8, '지판면', ha='right', fontproperties=fp, fontsize=12)
    ax.add_patch(Rectangle((2, 1), 9, 7, facecolor='#31bc79', edgecolor='#168250', alpha=.35, linewidth=2))
    ax.add_patch(Rectangle((3, 2), 6, 4, fill=False, edgecolor='#4799eb', linewidth=2, linestyle='--'))
    ax.text(6.5, 3, '이전: 지판 뒤 3~9cm', ha='center', fontproperties=fp, fontsize=11, color='#245a90')
    ax.text(6.5, 7.2, '확대: 지판 뒤 2~11cm', ha='center', fontproperties=fp, fontsize=12)
    ax.plot((board-wrist[2])*100, point[1], 'o', color='#274860', markersize=8)
    ax.set_xlim(-2, 13)
    ax.set_xlabel('지판면에서 연주자 쪽 깊이 (cm) →', fontproperties=fp, fontsize=12)
    fig.suptitle('넓은 시작 영역: 초록은 확대안, 파란 점선은 이전 보정안', fontproperties=fp, fontsize=17)
    fig.savefig(path, dpi=160); plt.close(fig)


def main():
    source_path = HERE/'wrist_region_recentered.json'
    source = json.loads(source_path.read_text())
    assert all(previous.sha(Path(p)) == h for p, h in source['source_sha256'].items())
    scene = json.loads((HERE/'scene.json').read_text())
    camera = json.loads((HERE/'camera.json').read_text())
    prepared = previous.load_prepared_reset_contract()
    _, hulls, pins = previous._extract_plane(previous.ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/guitar_compound.xml', scene['press_plane']['source_sha256'])
    wrist = np.array(scene['wrist_G_m'])
    rows = []
    for row in source['rows']:
        narrow = row['corrected']; wide = widen(narrow)
        lo, hi = np.array(wide['lower_G_m']), np.array(wide['upper_G_m'])
        assert np.allclose(hi-lo, [.07, .12, .09])
        assert np.all(lo <= narrow['lower_G_m']) and np.all(hi >= narrow['upper_G_m'])
        for corner in itertools.product(*zip(lo, hi)):
            assert previous.penalty(corner, wide) == 0
        f, anchor = row['frame'], narrow['anchor_fret']
        native(scene, prepared, camera, narrow, wide, f, OUT/f'wrist_region_anchor{round(anchor)}_wide.png')
        rows.append(dict(frame=f, time_s=row['time_s'], previous_region=narrow, wide_region=wide,
            bodyward_bounds_cm=[(wide['reference_y_G_m']-hi[1])*100, (wide['reference_y_G_m']-lo[1])*100],
            initial_wrist_distance_to_region_cm=float(np.linalg.norm(previous.excess(wrist, wide))*100)))
    first = rows[0]
    sections(wrist, first['previous_region'], first['wide_region'], previous.neck_slice(hulls, first['wide_region']['reference_y_G_m']), OUT/'wrist_region_wide_axes.png')
    pins.update(source['source_sha256'])
    for path in [Path(__file__), HERE/'recenter_wrist_region.py', source_path]:
        pins[str(path)] = previous.sha(path)
    result = dict(schema='wrist_region_wide_visual_candidate.v1', proposal_only=True, learning_implemented=False,
        work_center='same physical midpoint of score allowed_fret_range cell boundaries as recentered candidate',
        half_width_along_m=.06, below_edge_cm=[1,8], behind_board_cm=[2,11], rows=rows,
        intended_position_rule='zero penalty inside, weak excess-distance penalty outside; no center/orientation target',
        limitations=['visual range change only; fixed humanoid/guitar; no physics or policy executed',
                      'not derived from solved natural press poses; reachability/collisions not established'], source_sha256=pins)
    (HERE/'wrist_region_wide.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    ast.parse(Path(__file__).read_text())
    print(json.dumps({'completed':True, 'initial_distance_cm':[r['initial_wrist_distance_to_region_cm'] for r in rows]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
