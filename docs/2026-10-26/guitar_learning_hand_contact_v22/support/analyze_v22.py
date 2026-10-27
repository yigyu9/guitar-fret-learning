"""Summarize fixed first episodes and verify v22 integration accounting."""
import json,hashlib,collections
from pathlib import Path
import numpy as np
from guitar_learning.song.task import make_task
P=Path(__file__).resolve().parents[1];R=Path('/home/ajou/yigyu/3')
report=json.loads((P/'eval_full/report.json').read_text());rows=[json.loads(l) for l in (P/'eval_full/episodes.jsonl').read_text().splitlines()]
assert report['completed'] and len(rows)==128 and sorted(e['env_id'] for e in rows)==list(range(128))
task=make_task(R/'data/song_bundles/05_BN2-131-B_solo',pre_roll_s=3.,tail_s=.5);D=sum(t.end_s-t.onset_s for t in task.targets)
def aggregate(es):
 n=len(es)
 if not n:return dict(episodes=0)
 b=[];ext=[]
 for f in range(4):
  w=[e['left_episode_diagnostics']['recovery']['by_finger'][f] for e in es];den=sum(i['planned_s'] for i in w);seen=sum(i['observed_s'] for i in w);band=sum(i['in_band_s'] for i in w)
  b.append(dict(planned_s=den,observed_s=seen,in_band_s=band,credited_occupancy=band/den if den else None))
  modes={}
  for mode in ('all','idle','press'):
   v=sum(e['left_episode_diagnostics']['extreme_combinations'][mode]['valid_s'][f] for e in es)
   modes[mode]={k:sum(e['left_episode_diagnostics']['extreme_combinations'][mode][k][f] for e in es)/v if v else None for k in ('index_like_s','pinky_like_s','distal_excess_s','any_s')}
  ext.append(modes)
 t=[e['left_episode_diagnostics']['thumb_support'] for e in es];seconds=sum(i['sampled_s'] for i in t);fixed=n*task.duration_s
 return dict(episodes=n,mean_achieved=sum(e['song']['left_success_count'] for e in es)/n,safe=sum(e['reason']=='timeline_complete' and e['left_curriculum']['full_safe'] for e in es),
  failure_reasons=dict(collections.Counter(r for e in es for r in e['failure_reasons'])),
  clean_score_fraction=sum(sum(e['left_note_ledger']['values']['clean']) for e in es)/n/D,
  wrong_score_fraction=sum(sum(e['left_note_ledger']['values']['wrong']) for e in es)/n/D,
  missing_score_fraction=sum(sum(e['left_note_ledger']['values']['missing']) for e in es)/n/D,
  B_by_finger=b,extreme_by_finger=ext,
  thumb=dict(observed_s=seconds,near_fraction_fixed_song=sum(i['near_geometry_s'] for i in t)/fixed,
   candidate_fraction_fixed_song=sum(i['contact_candidate_s'] for i in t)/fixed,
   nearbutunloaded_s=sum(i['nearbutunloaded_s'] for i in t),
   mean_normal_load_N=sum(i['normal_load_mean_N']*i['normal_load_valid_s'] for i in t)/max(sum(i['normal_load_valid_s'] for i in t),1e-30),
   max_normal_load_N=max(i['normal_load_max_N'] for i in t),
   mean_net_force_N=sum(i['native_thumb3_net_force_mean_N'] for i in t)/n,
   max_net_force_N=max(i['native_thumb3_net_force_max_N'] for i in t)))
result=dict(all_first=aggregate(rows),safe_first=aggregate([e for e in rows if e['reason']=='timeline_complete' and e['left_curriculum']['full_safe']]),
 limitations=['One seed100updates128env; no long-training performance claim.','State552 differs from v21 state551; same seed does not give identical initialized policies.','Resultants and source patch are proxies, not native contact pairs or sound.','Whole-score denominators include failed/unobserved tails.'])
from guitar_learning.training.gpu_log_records import iter_episode_rows
training=[r['episode'] for r in iter_episode_rows(P/'train_full_100')]
result['training_episodes_varying_policy']=aggregate(training)
metrics=[json.loads(l) for l in (P/'train_full_100/learning_metrics.jsonl').read_text().splitlines()]
result['training_update_component_means']={k:sum(x['reward_component_means'][k] for x in metrics)/len(metrics) for k in metrics[0]['reward_component_means']}
result['training_stage_end']=metrics[-1]['left_curriculum']
(P/'learning_analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False));print(json.dumps(result['all_first']))
