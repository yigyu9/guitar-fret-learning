"""Read sealed summaries/metrics; generate standalone reward analysis artifacts."""
from pathlib import Path
import csv
import hashlib
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker

OUT = Path(__file__).resolve().parents[1]
ANALYSIS = OUT.parent
RUN = ANALYSIS.parent / 'run_01/J'
EVAL = ANALYSIS / 'fixed_evaluation_summary.json'
METRICS = RUN / 'learning_metrics.jsonl'
TERMS = [
    ('song_left_approach', '목표 패드 접근'),
    ('song_left_contact', '최초 접촉'),
    ('song_clean_hold', '압현 유지'),
    ('song_left_success', '압현 달성'),
    ('song_wrong_press', '오압현'),
    ('song_performance_deficit', '음 수행 부족'),
    ('song_finger_standby', '대기 자세'),
    ('song_thumb_support', '엄지 안내'),
    ('action_change', '행동 변화'),
]
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'mathtext.fontset': 'dejavusans', 'font.size': 11, 'axes.unicode_minus': False,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titleweight': 'bold', 'savefig.facecolor': '#ffffff'})
INITIAL, FINAL = '#9aa5b5', '#3068bf'
POS, NEG = '#18836e', '#c24e36'
data = json.loads(EVAL.read_text())
rows = [json.loads(line) for line in METRICS.open() if line.strip()]
assert len(rows) == 1478
assert [r['optimizer_updates'] for r in rows] == list(range(1, len(rows)+1))
for stage in ('initial', 'final'):
    assert data[stage]['episodes'] == 128
    assert data[stage]['scope'] == 'full_song'
    assert set(data[stage]['reward_component_mean']) == {k for k, _ in TERMS}
    assert math.isclose(sum(data[stage]['reward_component_mean'].values()),
                        data[stage]['summary']['mean_reward'], abs_tol=5e-5)
for row in rows:
    assert math.isclose(sum(row['reward_component_means'].values()), row['mean_reward'], abs_tol=1e-7)
a = np.array([data['initial']['reward_component_mean'][k] for k, _ in TERMS])
b = np.array([data['final']['reward_component_mean'][k] for k, _ in TERMS])
delta = b-a
assert math.isclose(delta.sum(), data['final']['summary']['mean_reward'] - data['initial']['summary']['mean_reward'], abs_tol=5e-5)

def fmt(v):
    return f'{v:+.3e}' if 0 < abs(v) < 0.0001 else f'{v:+.4f}' if v else '0'

def save(fig, name):
    fig.savefig(OUT / f'{name}.png', dpi=180, bbox_inches='tight')
    fig.savefig(OUT / f'{name}.svg', bbox_inches='tight')
    plt.close(fig)

# Common axis allows direct comparison of every term; numeric columns keep tiny terms visible.
fig = plt.figure(figsize=(13, 8.8))
gs = fig.add_gridspec(1, 2, width_ratios=[4, 1.2], wspace=.04)
ax = fig.add_subplot(gs[0, 0]); table = fig.add_subplot(gs[0, 1], sharey=ax)
y = np.arange(len(TERMS))
ax.barh(y-.17, a, height=.29, color=INITIAL, label='초기 모델')
ax.barh(y+.17, b, height=.29, color=FINAL, label='최종 모델 · 1,478회')
ax.set(yticks=y, yticklabels=[n for _, n in TERMS], xlim=(-14, 2.25), ylim=(8.65, -.85))
ax.axvline(0, color='#4b5563', lw=.8)
ax.grid(axis='x', alpha=.18); ax.set_axisbelow(True)
ax.set_xlabel('점 / 에피소드  ·  9개 항목 모두 같은 가로축')
ax.legend(loc='lower left', frameon=False)
table.set(xlim=(0, 1), ylim=ax.get_ylim()); table.axis('off')
table.text(.18, -.57, '초기', ha='center', weight='bold', color='#677486')
table.text(.75, -.57, '최종', ha='center', weight='bold', color=FINAL)
for i, (v0, v1) in enumerate(zip(a, b)):
    table.text(.18, i, fmt(v0), ha='center', va='center', fontsize=10)
    table.text(.75, i, fmt(v1), ha='center', va='center', fontsize=10, color=FINAL)
fig.suptitle('각 보상항에서 실제로 받은 점수', x=.11, ha='left', fontsize=20, weight='bold', y=.985)
fig.text(.11, .926, '동일한 67음 전곡 · 모델별 128환경의 첫 에피소드 평균 · 실패 포함', fontsize=12, color='#4b5563')
fig.subplots_adjust(top=.86, bottom=.17, left=.16, right=.97)
fig.text(.11, .095, '9항목 합계: 초기 −17.8209 → 최종 −16.8970     |     평균 달성 음: 1.5859 → 1.1953 / 67', fontsize=12, weight='bold')
fig.text(.11, .052, '종료 비용은 별도: 0 → +0.4464 (학습에서는 비용으로 차감). 위 막대는 할인 전 실제 지급값의 합입니다.', fontsize=10, color='#4b5563')
fig.text(.11, .025, '접근 항은 잠재함수 차이(PBRS)입니다. 음수 크기를 거리로 읽거나, 덜 음수인 것을 접근 실력 향상으로 단정할 수 없습니다.', fontsize=10, color='#4b5563')
save(fig, '01_reward_comparison')

fig, ax = plt.subplots(figsize=(12, 8))
ax.barh(y, delta, color=[POS if v>=0 else NEG for v in delta], height=.56)
ax.set(yticks=y, yticklabels=[n for _, n in TERMS], ylim=(8.7, -.7), xlim=(-5.4, 6.1))
ax.axvline(0, color='#4b5563', lw=.8); ax.grid(axis='x', alpha=.18); ax.set_axisbelow(True)
for i, v in enumerate(delta):
    ax.text(v + (.10 if v>=0 else -.10), i, fmt(v), va='center', ha='left' if v>=0 else 'right', fontsize=11)
ax.set_xlabel('최종 − 초기  ·  점 / 에피소드  ·  오른쪽은 총보상 증가, 왼쪽은 감소')
fig.suptitle('총보상 증가 +0.9238점은 어디에서 나왔나?', x=.13, ha='left', fontsize=20, weight='bold', y=.98)
fig.text(.13, .916, '항목별 변화의 산술 분해입니다. 정책 학습에 대한 인과 기여도는 아닙니다.', fontsize=11, color='#4b5563')
fig.subplots_adjust(top=.85, bottom=.19, left=.17, right=.97)
fig.text(.13, .091, '접근 항 +4.7612점이 오압현 −4.3336점을 상쇄했습니다.', fontsize=13, weight='bold')
fig.text(.13, .049, '압현 달성 보상에는 손가락별 균형계수가 적용됩니다. 검지 중심 → 약지 중심으로 바뀌면 달성 개수와 보상은 다르게 변할 수 있습니다.', fontsize=10, color='#4b5563')
fig.text(.13, .022, '엄지 안내는 +0.1824 → +0.0061, 대기 자세는 +0.2264 → +0.1350으로 감소했습니다.', fontsize=10, color='#4b5563')
save(fig, '02_reward_changes')

# Weight means by actual transition counts, then convert 60-Hz means to points per simulated env-second.
bins = []
for start in range(0, len(rows), 50):
    part = rows[start:start+50]
    weights = [r['transitions'] for r in part]
    bins.append({'update_start': part[0]['optimizer_updates'], 'update_end': part[-1]['optimizer_updates'],
                 'transitions': sum(weights),
                 'points_per_env_second': {k: float(np.average([r['reward_component_means'][k] for r in part], weights=weights)*60) for k, _ in TERMS}})
fig, axes = plt.subplots(3, 3, figsize=(14, 10.2))
x = [(w['update_start']+w['update_end'])/2 for w in bins]
for ax, (k, name) in zip(axes.flat, TERMS):
    yy = [w['points_per_env_second'][k] for w in bins]
    ax.axvspan(750, 1478, color='#eaf1fb', zorder=0)
    ax.axvline(750, color='#8c9bb0', lw=.8, ls='--')
    ax.plot(x, yy, color=FINAL, lw=2, marker='o', ms=2.5)
    ax.axhline(0, color='#a0a7b1', lw=.6)
    ax.set_title(name, loc='left', pad=11, fontsize=13)
    ax.set_xlim(1, 1478); ax.set_xticks([1, 500, 1000, 1478]); ax.grid(axis='y', alpha=.18)
    ax.set_xlabel('학습 반복'); ax.set_ylabel('점 / 환경·초')
    ax.ticklabel_format(axis='y', style='sci', scilimits=(-3, 3), useMathText=False)
fig.suptitle('학습 중 보상항별 변화', x=.075, ha='left', fontsize=21, weight='bold', y=.985)
fig.text(.075, .934, '50회 묶음의 전이 수 가중 평균 × 60Hz · 마지막 묶음은 28회 · 탐색 행동 포함', fontsize=12, color='#4b5563')
fig.text(.075, .903, '750회 이후 새 에피소드부터 전곡으로 전환(푸른 배경). 전환 전후는 곡 길이·목표 구성이 다릅니다.', fontsize=11, color='#4b5563')
fig.subplots_adjust(top=.835, bottom=.11, left=.08, right=.97, hspace=.64, wspace=.36)
fig.text(.075, .045, '각 패널의 세로축 범위가 다릅니다. 높이로 항목 간 점수를 비교하지 마세요. 초기·최종 비교 그래프의 “점/에피소드”와도 단위가 다릅니다.', fontsize=10, color='#4b5563')
save(fig, '03_training_reward_trends')

with (OUT/'reward_comparison.csv').open('w', newline='', encoding='utf-8-sig') as f:
    writer=csv.writer(f); writer.writerow(['보상항', '로그 키', '초기_점_에피소드', '최종_점_에피소드', '변화_최종빼기초기'])
    for (key, name), v0, v1 in zip(TERMS, a, b): writer.writerow([name, key, v0, v1, v1-v0])
with (OUT/'training_reward_50update_bins.csv').open('w', newline='', encoding='utf-8-sig') as f:
    writer=csv.writer(f);writer.writerow(['시작_반복', '종료_반복', '전이수']+[n+'_점_환경초' for _, n in TERMS])
    for w in bins: writer.writerow([w['update_start'],w['update_end'],w['transitions']]+[w['points_per_env_second'][k] for k, _ in TERMS])

verification = {
    'evaluation_source': str(EVAL), 'evaluation_sha256': hashlib.sha256(EVAL.read_bytes()).hexdigest(),
    'training_source': str(METRICS), 'training_sha256': hashlib.sha256(METRICS.read_bytes()).hexdigest(),
    'updates': len(rows), 'transitions': sum(r['transitions'] for r in rows), 'training_hz': 60,
    'evaluation_components_sum': {'initial': float(sum(a)), 'final': float(sum(b))},
    'evaluation_reported_mean_reward': {s:data[s]['summary']['mean_reward'] for s in ('initial','final')},
    'component_sum_minus_reported_reward': {s:float(sum(data[s]['reward_component_mean'].values()) - data[s]['summary']['mean_reward']) for s in ('initial','final')},
    'max_training_sum_residual': max(abs(sum(r['reward_component_means'].values())-r['mean_reward']) for r in rows),
    'delta_sum': float(sum(delta)), 'comparison_unit': 'undiscounted effective points per completed first episode; failures included',
    'training_unit': 'transition-weighted mean effective reward at 60Hz, multiplied by 60 (points per simulated env-second)',
    'termination_cost_separate': {s:data[s]['summary']['mean_cost'] for s in ('initial','final')},
    'training_bin_count': len(bins), 'checks_passed': True,
}
(OUT/'verification.json').write_text(json.dumps(verification, ensure_ascii=False, indent=2)+'\n')

md = '''# 최신 large 학습: 보상항별 실제 지급값

2026-10-27 오전9시까지 수행한 large / GPU1024 / H32 / 1478회 학습을 대상으로 한다. 이 자료는 원자료를 읽어 시각화했으며 학습·보상 구현은 변경하지 않았다.

## 1. 같은 전곡을 평가했을 때 받은 점수

초기·최종 모델 각각 128환경의 **첫 에피소드**, 원곡67음을 평가한 결과다. 실패도 포함한다. 초기 모델은 학습 전 정책이며 행동0 시험은 아니다. 아래 값은 **실제 계수가 적용된 보상의 할인 전 누적값을 에피소드 간 평균**한 것이다. 매 시점 점수나 PPO의 할인된 return이 아니다.

![항목별 초기·최종 비교](01_reward_comparison.png)

| 보상항 | 초기 | 최종 | 변화(최종−초기) |
|---|---:|---:|---:|
'''
for (_, name), v0, v1 in zip(TERMS, a, b):
    md += f'| {name} | {fmt(v0)} | {fmt(v1)} | {fmt(v1-v0)} |\n'
md += f'| **9항목 합계** | **{sum(a):+.4f}** | **{sum(b):+.4f}** | **{sum(delta):+.4f}** |\n'
md += '''
종료 비용은 위 9항목과 별개다. 평균 비용은 초기0, 최종+0.446432로 학습 시 차감한다. 보상·비용은 서로 다른 할인과 critic을 사용하므로 단순한 원시 합계 차이를 PPO 목적함수와 같다고 해석하면 안 된다.

## 2. 무엇이 총보상 변화를 만들었나

![항목별 점수 변화](02_reward_changes.png)

- **총보상은 +0.9238점 증가했지만 평균 달성 음은 1.5859→1.1953/67개로 감소했다.** 총보상만으로 음악 성능 개선을 판단할 수 없다.
- **오압현 감점은 −0.8556→−5.1893으로 약6.07배 커졌다.** 가중 접촉·유지·달성 점수 증가와 함께 봐야 한다. 이는 실제 기타 음향 녹음 판정이 아니라 현재 구현의 접촉 후보 기반 오압현 판정이다.
- **접근 항의 누적값은 −12.5321→−7.7710으로 변했다.** `0.99 × Φ_next − Φ_current` 형태의 잠재함수 차이(PBRS)이고 종료 정산이 포함된다. 덜 음수인 것만으로 목표와 더 가까워졌다고 판단할 수 없다. 체류시간·궤적·종료 시점도 영향을 준다.
- **압현 달성 점수는 +0.2656→+0.4171로 올랐지만 실제 달성 개수는 줄었다.** 원곡 손가락별 균형계수는 검지0.670, 중지0.931, 약지·소지1.396이다. 초기203음은 모두 검지, 최종153음은 약지148·소지5로, 가중 점수와 원곡 달성 개수는 다르게 움직였다.
- **음 수행 부족은 −6.5838→−6.5200으로 거의 줄지 않았다.** 목표 수행이 전반적으로 부족한 상태가 남았다.
- **대기 자세는 +0.2264→+0.1350, 엄지 안내는 +0.1824→+0.0061로 감소했다.** 이 보상만으로 자세 품질이나 접촉률을 직접 환산할 수는 없다. 다만 해당 목표에 대한 지급 신호가 줄어든 것은 확인된다.
- **행동 변화 감점은 최종 −3.12×10⁻⁷점으로 매우 작다.** LH21 손가락·엄지는 이 비용에서 제외되어 있다. 이 항목이 손가락을 움직이지 못하게 만든 직접 비용이라고 보기는 어렵다.

초기는128환경 모두 정상 끝, 최종은124환경 정상 끝·4환경 물리 실패·손목 종료0이다. 따라서 위 표는 동일 전곡 시험의 실패 포함 비교이지, 모든 에피소드의 길이가 같다는 뜻은 아니다. 단일 학습·한 곡·한 번의128환경 평가 결과다.

## 3. 학습하는 동안의 변화

![학습 중 9개 보상항 추세](03_training_reward_trends.png)

`learning_metrics.jsonl`의 1478개 갱신 기록을 사용한다. 각 점은50회 묶음(마지막28회)의 전이 수 가중 평균에60을 곱한 **점/환경·초**다. 환경1024개의 점수를 합한 값이 아니다. 평활한 곡선이 아니라 구간별 실제 평균이며 끝나지 않은 에피소드의 전이도 포함한다. 첫 그래프의 점/에피소드와 단위가 다르므로 숫자를 직접 비교하지 않는다.

750회 이후 새로 시작하는 환경부터 구간 학습에서 전곡으로 바뀐다. 푸른 배경의 초기에는 아직 진행 중인 구간 에피소드가 섞여 있다. 전환 전후에는 목표 수·길이·손가락 구성이 달라지므로 곡선 변화를 정책 성능 변화 하나로 설명할 수 없다. 학습 곡선은 탐색 행동을 포함하며 고정 평가와도 조건이 다르다. 각 패널은 읽기 쉽도록 세로축 범위가 다르다.

## 원자료와 재현

- `reward_comparison.csv`: 위 표의 반올림 전9항목 값.
- `training_reward_50update_bins.csv`: 추세 그래프에 사용한 모든 구간의 수치.
- `verification.json`: 원자료 SHA256, 전이 수, 합계 검산 결과.
- `support/build_charts.py`: 그래프·표 생성 도구. 이 디렉토리의 산출물만 갱신한다.
- 평가 원본: `../fixed_evaluation_summary.json`
- 학습 원본: `../../run_01/J/learning_metrics.jsonl`

평가에서 9항목 합과 별도로 누적 기록된 총보상의 차이는 초기 +0.0000202322점, 최종 −0.0000003463점이다. 소수 넷째 자리 표시에 영향을 주지 않는 작은 잔차이며, 완전 동일한 값이라고 가정하지 않았다. 모든1478회에서9항목의 합과 기록된 전이당 평균 보상의 차이는 최대1.17e-9점이었다. 비용은 항목 합에서 제외했다. 기존 로그·checkpoint·학습 소스는 수정하지 않았다.
'''
(OUT/'README.md').write_text(md)
print(json.dumps(verification, ensure_ascii=False, indent=2))
