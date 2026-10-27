"""Render supplied pose judgments and a coordinate schematic, without physics."""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
COLORS = {'yellow': '#d6a400', 'orange': '#df751e', 'red': '#cb4141'}
AXES = ('dx', 'dy', 'dz', 'elev', 'azim', 'roll')
LABELS = ('좌우 · +연주자 오른쪽', '앞뒤 · +앞', '높이 · +위',
          '넥 고도 · +들기', '넥 방위 · +몸 쪽', '넥 축 회전 · +앞판 아래로')
TARGETS = ((3, 3), (5, 5), (1, 1), (-2.5, 2.5), (0, 2), (10, 10))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run(csv_path, out):
    out.mkdir(exist_ok=False)
    inputs = [csv_path, Path(__file__), FONT,
              ROOT/'stability_adapter_2/TEAM_POSE_ENVELOPE_VISUALIZATION_PLAN.md']
    before = {str(p): sha(p) for p in inputs}
    save(out/'inputs_before.json', before)
    with csv_path.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    assert len({(r['axis'], r['value']) for r in rows}) == len(rows)
    assert set(r['axis'] for r in rows) == set(AXES)
    font_manager.fontManager.addfont(str(FONT))
    plt.rcParams.update({'font.family': font_manager.FontProperties(fname=str(FONT)).get_name(),
                         'font.size': 12, 'axes.unicode_minus': False})

    fig = plt.figure(figsize=(15, 9.5), constrained_layout=True)
    ax = fig.add_subplot(2, 2, 1, projection='3d')
    lo, hi = np.array([17, 24.5, 8]), np.array([23, 34.5, 10])
    vertices = np.array(list(itertools.product(*zip(lo, hi))))
    faces = [vertices[[0, 1, 3, 2]], vertices[[4, 5, 7, 6]],
             vertices[[0, 1, 5, 4]], vertices[[2, 3, 7, 6]],
             vertices[[0, 2, 6, 4]], vertices[[1, 3, 7, 5]]]
    ax.add_collection3d(Poly3DCollection(faces, facecolors=COLORS['yellow'], alpha=.12, edgecolors='#9b821f', linewidths=.7))
    center = (lo+hi)/2
    ax.scatter(*lo, color='#2979ae', s=65, label='기준 바디 중심 (17, 24.5, 8)')
    ax.scatter(*center, color='#7b529e', marker='D', s=70, label='조합 목표 후보 (20, 29.5, 9)')
    ax.set(xlim=(15, 25), ylim=(22, 37), zlim=(6, 12), xlabel='오른쪽 (cm)', ylabel='앞 (cm)', zlabel='위 (cm)')
    ax.set_box_aspect((10, 15, 6)); ax.view_init(elev=22, azim=-57)
    ax.set_title('바디 중심 위치 후보 · 골반 기준\n좌우 17~23 / 앞 24.5~34.5 / 위 8~10 cm')
    ax.legend(loc='upper left', bbox_to_anchor=(-.08, -.04), fontsize=11, frameon=False)

    ax = fig.add_subplot(2, 2, 2)
    for angle, color, text, style in [(0, '#727b85', '우리 수평 넥 후보 0° · 별도 기준', '--'),
                                      (22, '#2979ae', '팀원 기준 22°', '-'),
                                      (19.5, '#7b529e', '목표 후보 19.5°', '-')]:
        rad = np.radians(angle)
        ax.plot([0, np.cos(rad)], [0, np.sin(rad)], color=color, linestyle=style, linewidth=2, label=text)
    theta = np.radians(np.linspace(17, 22, 30))
    ax.fill(np.r_[0, np.cos(theta), 0], np.r_[0, np.sin(theta), 0], color=COLORS['yellow'], alpha=.25)
    ax.set(xlim=(-.08, 1.1), ylim=(-.1, .53)); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('넥 고도 · 보고서의 후보 구간 17~22°\n방향 개념도: 실제 회전 중심·기타 형상 미확인')
    ax.legend(loc='upper left', bbox_to_anchor=(0, -.05), fontsize=11, frameon=False)

    ax = fig.add_subplot(2, 2, 3)
    ax.axvspan(-2, 2, facecolor='#aaaaaa', alpha=.22, hatch='///', label='제안 허용 오차 ±2° · 미검증')
    subset = [r for r in rows if r['axis'] == 'azim']
    for r in subset:
        ax.scatter(float(r['value']), 0, s=80, color=COLORS[r['final']],
                   marker='o' if r['visual'] else '^', edgecolors='#444444', linewidths=.7)
    ax.scatter(0, .24, marker='D', color='#7b529e', s=65)
    ax.annotate('목표 후보 0°', (0, .24), xytext=(0, .36), ha='center')
    ax.annotate('+15°: 숫자 판정 노랑\n눈 판정 미기록', (15, 0), xytext=(16, .22), ha='center', fontsize=11,
                arrowprops={'arrowstyle': '-', 'color': '#777777'})
    ax.set(xlim=(-39, 39), ylim=(-.15, .53), yticks=[], xlabel='기준 대비 넥 방위 변화 (°)')
    ax.set_title('방위 ±2°는 실측 허용구간이 아님')
    ax.legend(loc='upper left', bbox_to_anchor=(0, -.24), frameon=False, fontsize=11)

    ax = fig.add_subplot(2, 2, 4)
    ax.broken_barh([(-20, 5), (0, 25)], (.09, .13), facecolors=COLORS['yellow'], alpha=.45)
    ax.scatter([-10, -5], [-.035, -.035], color=COLORS['red'], s=65)
    ax.errorbar(10, .34, xerr=10, fmt='D', color='#7b529e', capsize=5)
    ax.text(-17.5, .26, '−20~−15°', ha='center', fontsize=11)
    ax.text(12.5, .26, '0~+25°', ha='center', fontsize=11)
    ax.text(-7.5, -.14, '−10°, −5°: CSV 빨강 표본', ha='center', fontsize=11)
    ax.text(10, .43, '제안 목표 +10° ±10°', ha='center', fontsize=11)
    ax.set(xlim=(-38, 38), ylim=(-.25, .56), yticks=[], xlabel='기준 대비 넥 축 회전 (°)')
    ax.set_title('roll의 두 자연 후보 구간은 분리해서 사용\n막대는 보고서 요약: 구간 내부 전체 검증을 뜻하지 않음')
    fig.suptitle('팀원 자료의 자세 후보 · 조합 적용은 추가 검증 필요', fontsize=18)
    fig.savefig(out/'pose_candidates.png', dpi=160); plt.close(fig)

    fig, axes = plt.subplots(6, 1, figsize=(13.5, 12.5), constrained_layout=True)
    plotted_count = 0
    for i, (axis, ax, label, target) in enumerate(zip(AXES, axes, LABELS, TARGETS)):
        subset = [r for r in rows if r['axis'] == axis]
        unit = 'cm' if i < 3 else '°'
        midpoint, tolerance = target
        ax.errorbar(midpoint, .35, xerr=tolerance, fmt='D', color='#7b529e', capsize=5, markersize=6)
        ax.text(.02, .88, f'제안 후보: {midpoint:+g} ±{tolerance:g}{unit}', transform=ax.transAxes, fontsize=11)
        for r in subset:
            x = float(r['value'])
            ax.scatter(x, 0, color=COLORS[r['final']], s=70, marker='o' if r['visual'] else '^',
                       edgecolors='#444444', linewidths=.7, zorder=3)
            if r['anomaly'] == 'True':
                ax.scatter(x, 0, marker='s', s=145, facecolors='none', edgecolors='#7b529e', linewidths=2, zorder=4)
            plotted_count += 1
        values = [float(r['value']) for r in subset] + [midpoint-tolerance, midpoint+tolerance, 0]
        ax.set(xlim=(min(values)-3, max(values)+3), ylim=(-.26, .68), yticks=[], ylabel=label,
               xlabel=f'기준 자세에서 바꾼 양 ({unit})')
        ax.axvline(0, color='#888888', linewidth=.8, linestyle=':'); ax.grid(axis='x', alpha=.2)
        if axis == 'dy':
            ax.annotate('+2cm: 이상치 · 재확인', (2, 0), xytext=(4, -.21), fontsize=11,
                        arrowprops={'arrowstyle': '-', 'color': '#7b529e'})
        if axis == 'azim':
            ax.text(.57, .88, '±2° 안의 표본 없음', transform=ax.transAxes, fontsize=11)
    legend = [Patch(facecolor=COLORS[k], label=t) for k, t in [('yellow', '원자료 자연'), ('orange', '원자료 경계'), ('red', '원자료 무너짐')]]
    legend += [Line2D([], [], color='#444444', marker='o', linestyle='none', label='눈 판정 기록 있음'),
               Line2D([], [], color='#444444', marker='^', linestyle='none', label='눈 판정 미기록'),
               Line2D([], [], color='#7b529e', marker='s', markerfacecolor='none', linestyle='none', label='이상치'),
               Line2D([], [], color='#7b529e', marker='D', label='제안 목표±오차')]
    fig.legend(handles=legend, loc='outside lower center', ncol=4, frameon=False, fontsize=11)
    fig.suptitle('CSV의 96개 실제 판정 표본 · 점 사이의 안전성은 미확인', fontsize=17)
    fig.savefig(out/'judgment_samples.png', dpi=160); plt.close(fig)
    assert plotted_count == len(rows) == 96
    facts = {'new_physics_runs': 0, 'learning_updates': 0, 'schematic_not_native_render': True,
             'rows': len(rows), 'plotted_rows': plotted_count,
             'visual_recorded': sum(bool(r['visual']) for r in rows),
             'visual_not_recorded': sum(not r['visual'] for r in rows),
             'csv_has_baseline_zero_rows': any(float(r['value']) == 0 for r in rows),
             'anomalies': [r for r in rows if r['anomaly'] == 'True'],
             'position_body_center_pelvis_cm': {'baseline': lo.tolist(), 'candidate_lower': lo.tolist(),
                                               'candidate_upper': hi.tolist(), 'combined_target_candidate': center.tolist()},
             'elevation_absolute_deg': {'candidate': [17, 22], 'target_candidate': 19.5, 'current_separate_horizontal_candidate': 0},
             'azimuth_proposed_tolerance_sampled': False,
             'roll_reported_natural_delta_deg': [[-20, -15], [0, 25]],
             'six_axis_combination_verified': False, 'force_units_and_depth_certified': False}
    save(out/'facts.json', facts)
    after = {p: sha(p) for p in before}
    assert before == after
    save(out/'inputs_after.json', after)
    print(json.dumps({'rows_plotted': plotted_count, 'visual_recorded': facts['visual_recorded'], 'inputs_unchanged': before == after}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args.csv.resolve(), args.out.resolve())
