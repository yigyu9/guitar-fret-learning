"""Summarize fixed phrase evaluations and the completed R run."""
from collections import defaultdict
import json
import os
from pathlib import Path


RESULT = Path(__file__).resolve().parents[1]
TRAINING = RESULT/'training'


def read(path):
    return json.loads(path.read_text())


def evaluation(name):
    report = read(TRAINING/name/'report.json')
    groups = defaultdict(lambda: dict(count=0, wrist_sum=0.))
    totals = defaultdict(float)
    reward_totals = defaultdict(float)
    with (TRAINING/name/'episodes.jsonl').open() as stream:
        for line in stream:
            episode = json.loads(line)['episode']
            group = groups[episode['finger_skill']['phrase_id']]
            group['count'] += 1
            group['wrist_sum'] += episode['finger_skill_eval']['wrist_inside_fraction']
            diag = episode['left_episode_diagnostics']
            seconds = diag['physics_sampled_s']
            thumb = diag['thumb_support']
            totals['seconds'] += seconds
            totals['thumb_near_s'] += thumb['near_geometry_s']
            totals['thumb_candidate_s'] += thumb['contact_candidate_s']
            totals['thumb_valid_s'] += thumb['valid_s']
            totals['thumb_quality_integral'] += thumb['quality_integral']
            totals['thumb_signed_gap_integral'] += thumb['mean_signed_gap_m']*thumb['valid_s']
            for key, value in episode['reward_components'].items():
                reward_totals[key] += value
            for axis in range(3):
                totals['wrist_excess_integral_'+str(axis)] += diag['wrist']['mean_excess_G_xyz_m'][axis]*seconds
    return dict(summary=report['summary'], readiness=report['readiness'],
        wall_s=report['wall_s'], groups={key: dict(count=value['count'],
            wrist_inside_fraction=value['wrist_sum']/value['count']) for key, value in sorted(groups.items())},
        totals=dict(totals), mean_reward_components={key: value/report['episodes'] for key, value in reward_totals.items()},
        thumb_near_fraction=totals['thumb_near_s']/totals['seconds'],
        thumb_candidate_fraction=totals['thumb_candidate_s']/totals['seconds'],
        thumb_mean_quality=totals['thumb_quality_integral']/totals['thumb_valid_s'],
        thumb_mean_signed_gap_mm=1000*totals['thumb_signed_gap_integral']/totals['thumb_valid_s'],
        wrist_time_weighted_mean_excess_G_xyz_mm=[1000*totals['wrist_excess_integral_'+str(i)]/totals['seconds'] for i in range(3)])


initial, final = evaluation('R_initial_evaluation'), evaluation('R_evaluation')
pipeline = read(TRAINING/'report.json')
metrics = [json.loads(line) for line in (TRAINING/'R/learning_metrics.jsonl').read_text().splitlines()]
assert len(metrics) == 32 and pipeline['stopped'] == 'R_stalled'
assert initial['groups'].keys() == final['groups'].keys()
assert all(initial['groups'][key]['count'] == final['groups'][key]['count'] for key in initial['groups'])
summary = dict(schema='guitar_learning.finger_skill_hour01_analysis.v1',
    pipeline_stopped=pipeline['stopped'], pipeline_wall_s=pipeline['wall_s'],
    updates=len(metrics), training_transitions=pipeline['training_transitions'],
    collection_s=sum(row['collection_s'] for row in metrics),
    update_s=sum(row['update_s'] for row in metrics),
    initial_fixed_phrase_evaluation=initial, final_fixed_phrase_evaluation=final,
    note_scope='phrase evaluation; not the original67-note whole-song denominator',
    thumb_scope='geometry and loaded-body candidate; not certified contact-pair pressure',
    full_song_evaluation='full_song_evaluation/report.json', video='video/report.json')
whole_song_report = RESULT/'full_song_evaluation/report.json'
if whole_song_report.exists():
    report = read(whole_song_report)
    rows = [json.loads(line)['episode'] for line in (whole_song_report.parent/'episodes.jsonl').read_text().splitlines()]
    summary['final_full_song_evaluation'] = dict(episodes=len(rows), targets_per_episode=67,
        summary=report['summary'], completed=report['completed'],
        finger_achieved_counts=[sum(round(e['left_curriculum']['finger_metrics'][i]['success_fraction']*
            e['left_curriculum']['finger_metrics'][i]['target_count']) for e in rows) for i in range(4)],
        wrist_inside_episode_mean=sum(e['finger_skill_eval']['wrist_inside_fraction'] for e in rows)/len(rows),
        thumb_near_fraction_time_weighted=sum(e['left_episode_diagnostics']['thumb_support']['near_geometry_s']
            for e in rows)/sum(e['left_episode_diagnostics']['physics_sampled_s'] for e in rows))
video_report = RESULT/'video/report.json'
if video_report.exists():
    summary['video_verification'] = 'support/video_verification.json'
    summary['rendered_environment_achieved_notes'] = read(video_report)['episode']['song']['left_success_count']
(RESULT/'analysis.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')

os.environ.setdefault('MPLCONFIGDIR', '/tmp/guitar_learning_hour01_matplotlib')
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
labels = ['Initial', 'After R32']
axes[0].bar(labels, [100*initial['readiness']['wrist_inside_fraction'],
                     100*final['readiness']['wrist_inside_fraction']], color=['#a6b8cc', '#367db8'])
axes[0].axhline(80, color='#bd4d42', linestyle='--', label='R to F threshold: 80%')
axes[0].set(ylabel='Mean episode fraction (%)', ylim=(0, 100), title='Wrist inside guidance region')
axes[0].legend(frameon=False)
axes[1].bar(labels, [100*initial['thumb_near_fraction'], 100*final['thumb_near_fraction']],
            color=['#a6b8cc', '#c1783e'])
axes[1].set(ylabel='Fraction of physics time (%)', ylim=(0, 100), title='Thumb near rear-neck geometry')
fig.suptitle('Same 1024 fixed phrase episodes | R only; fingers not trained')
fig.savefig(RESULT/'fixed_evaluation.png', dpi=160)
plt.close(fig)

fig, axis = plt.subplots(figsize=(12, 4.8), constrained_layout=True)
names = list(initial['groups'])
x = list(range(len(names)))
axis.plot(x, [100*initial['groups'][key]['wrist_inside_fraction'] for key in names],
          'o-', label='Initial', color='#8b9cad')
axis.plot(x, [100*final['groups'][key]['wrist_inside_fraction'] for key in names],
          'o-', label='After R32', color='#367db8')
axis.axhline(80, linestyle='--', color='#bd4d42', label='Overall gate threshold (reference)')
axis.set_xticks(x)
axis.set_xticklabels([key.removeprefix('phrase-') for key in names], rotation=60, ha='right')
axis.set(xlabel='Original phrase-group range', ylabel='Mean episode wrist inside fraction (%)',
         title='Wrist result by phrase; matched initial/final counts', ylim=(-3, 103))
axis.legend(frameon=False)
fig.savefig(RESULT/'phrase_wrist.png', dpi=160)
plt.close(fig)
print('Analysis and fixed-evaluation figures saved.')
