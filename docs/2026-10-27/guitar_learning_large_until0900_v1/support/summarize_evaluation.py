import json
from pathlib import Path
from statistics import mean, median
from collections import Counter
from guitar_learning.training.gpu_log_records import iter_episode_rows
ROOT=Path('/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_large_until0900_v1')
comparison={}
for label in ('initial','final','1250'):
    folder=ROOT/'analysis'/('evaluation_'+label)
    if not (folder/'report.json').exists():
        continue
    report=json.loads((folder/'report.json').read_text())
    rows=[r['episode'] for r in iter_episode_rows(folder)]
    summary=dict(report.get('summary',{}))
    if rows:
        summary.update(mean_duration_s=mean(e['steps']/60 for e in rows),
            median_duration_s=median(e['steps']/60 for e in rows),
            max_achieved_notes=max(e['song']['left_success_count'] for e in rows),
            target_count_unique=sorted(set(e['song']['target_count'] for e in rows)),
            achieved_note_histogram=dict(sorted(Counter(e['song']['left_success_count'] for e in rows).items())),
            achieved_note_totals_by_finger={name:sum(round(e['left_curriculum']['finger_metrics'][i]['target_count']*e['left_curriculum']['finger_metrics'][i]['success_fraction']) for e in rows) for i,name in enumerate(('index','middle','ring','pinky'))},
            failure_reasons=dict(Counter(reason for e in rows for reason in e['failure_reasons'])),
            env0_first_episode=[dict(achieved_notes=e['song']['left_success_count'],reason=e['reason'],duration_s=e['steps']/60) for e in rows if e['env_id']==0],
            mean_reward_components={k:mean(e['reward_components'][k] for e in rows) for k in rows[0]['reward_components']})
    comparison[label]=dict(path=str(folder),checkpoint=report.get('checkpoint'),
        completed=report['completed'],summary=summary,actual_simulated_transitions=report['actual_simulated_transitions'],
        selected_episode_transitions=report['selected_episode_transitions'],lifecycle_verified=report.get('lifecycle_verified'),
        changed_inputs=report.get('changed_inputs'),missing_import_pins=report.get('missing_import_pins'),
        wall_s=report.get('wall_s'))
(ROOT/'support/evaluation_comparison.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(comparison,ensure_ascii=False,indent=2))
