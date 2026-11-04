"""완료된 원문 평가·학습 로그를 읽어 요약 수치와 그림을 만든다."""
import json
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
STUDY = OUT.parent


def read(path):
    return json.loads((STUDY / path).read_text())


def lines(path):
    with (STUDY / path).open() as stream:
        return [json.loads(line) for line in stream]


def window_summary(rows):
    counts = [row['episode_summary']['count'] for row in rows]
    count = sum(counts)
    return dict(
        first_update=rows[0]['optimizer_updates'], last_update=rows[-1]['optimizer_updates'],
        episodes=count,
        achieved_notes=sum(row['episode_summary']['mean_left_success_count'] * n
                           for row, n in zip(rows, counts)) / count,
        **{key: sum(row['episode_summary'][key] for row in rows)
           for key in ('timeline_complete', 'physical_failure', 'wrist_failure', 'stage_success')})


training = read('학습/J/report.json')
evaluation = read('최종평가/report.json')
assert training['completed'] and evaluation['completed']
assert not training['changed_inputs'] and not evaluation['changed_inputs']
episodes = [row['episode'] for row in lines('최종평가/episodes.jsonl')]
metrics = lines('학습/J/learning_metrics.jsonl')
assert len(metrics) == training['optimizer_updates']
assert mean(e['song']['left_success_count'] for e in episodes) == evaluation['summary']['mean_left_success_count']

fingers = []
for index, name in enumerate(('검지', '중지', '약지', '소지')):
    rows = [e['left_curriculum']['finger_metrics'][index] for e in episodes]
    targets = sum(row['target_count'] for row in rows)
    achieved = sum(round(row['success_fraction'] * row['target_count']) for row in rows)
    fingers.append(dict(name=name, targets_per_episode=rows[0]['target_count'],
        total_targets=targets, achieved=achieved, mean_achieved=achieved / len(episodes),
        achieved_fraction=achieved / targets,
        near_fraction=mean(row['near_fraction'] for row in rows),
        contact_fraction=mean(row['contact_fraction'] for row in rows)))
assert sum(f['achieved'] for f in fingers) == sum(e['song']['left_success_count'] for e in episodes)

summary = dict(
    training_updates=training['optimizer_updates'], training_wall_s=training['wall_s'],
    transitions=training['transitions'], checkpoint_sha256=evaluation['checkpoint_sha256'],
    evaluation=evaluation['summary'],
    achieved_counts=[e['song']['left_success_count'] for e in episodes],
    mean_clean_audible_fraction=mean(e['song']['mean_clean_audible_fraction'] for e in episodes),
    fingers=fingers,
    wrist_inside_fraction=mean(e['left_episode_diagnostics']['wrist']['inside_fraction'] for e in episodes),
    thumb_mean_guide_distance_m=mean(e['left_episode_diagnostics']['thumb']['mean_distance_m'] for e in episodes),
    thumb_contact_candidate_fraction=mean(e['left_episode_diagnostics']['thumb_support']['contact_candidate_fraction'] for e in episodes),
    training_windows=[window_summary(metrics[a:b]) for a, b in ((450, 550), (900, 1000), (1327, 1427))],
    actor_lr_first=metrics[0]['actor_lr'], actor_lr_last=metrics[-1]['actor_lr'],
    scope='One seed, 16 deterministic full-song environments; not 16 independent training runs.')
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')

plt.rcParams.update({'font.family': 'NanumGothic', 'axes.unicode_minus': False, 'font.size': 11})
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
windows = [window_summary(metrics[i-99:i+1]) for i in range(549, len(metrics))]
axes[0].plot([w['last_update'] for w in windows], [w['achieved_notes'] for w in windows], color='#1976A3')
axes[0].set(title='학습 중 평균 달성 음 수 (전체 67음)', xlabel='학습 반복', ylabel='최근 100회 내 에피소드 평균 달성 수')
axes[0].set_ylim(bottom=0)
axes[0].grid(alpha=.2)
axes[0].text(.02, .97, '전곡 구간만 표시 · 탐색 포함\n최종 고정 모델 평가: 4.25 / 67음',
             transform=axes[0].transAxes, va='top')
for offset, field, label, color in ((-.23, 'near_fraction', '접근 기준 충족', '#9EC9DC'),
                                   (0, 'contact_fraction', '최초 접촉 기준 충족', '#56A89C'),
                                   (.23, 'achieved_fraction', '압현 달성', '#D37C43')):
    axes[1].bar([i + offset for i in range(4)], [100*f[field] for f in fingers], .23, label=label, color=color)
axes[1].set_xticks(range(4))
axes[1].set_xticklabels([f['name'] for f in fingers])
axes[1].set(title='최종 평가: 손가락별 목표 수행', ylabel='해당 손가락의 목표 중 비율 (%)', ylim=(0, 100))
axes[1].legend(loc='upper right', fontsize=9)
axes[1].grid(axis='y', alpha=.2)
fig.suptitle('상태 443 · 목표 16 · 결합 512→256: 1,427회 학습 결과', fontsize=15)
fig.savefig(OUT / '학습결과.png', dpi=180)
plt.close(fig)
