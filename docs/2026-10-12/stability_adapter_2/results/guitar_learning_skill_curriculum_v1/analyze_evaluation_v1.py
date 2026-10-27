"""Closed deterministic evaluations: current goal and prepared reset only."""
from pathlib import Path
import json,gzip
import numpy as np
from guitar_learning.recording import write,digest
P=Path(__file__).resolve().parent
pins={str(Path(__file__)):digest(__file__)};results={};training={}
for role in ('left','right'):
 for cost in ('1p0','0p1'):
  training_path=P/(role+'_cost'+cost+'_run_v2/skill_report.json');pins[str(training_path)]=digest(training_path)
  te=json.loads(training_path.read_text())['episodes']
  training[role+'_cost'+cost]=dict(contact_episodes=sum(bool(e['specialist']['skill']['contact_targets']) for e in te),hold_episodes=sum(bool(e['specialist']['skill']['held_targets']) for e in te),matching_cross_episodes=sum(bool(e['specialist']['skill']['crossed_targets']) for e in te))
  folder=P/(role+'_cost'+cost+'_eval_v1')
  for n in ('result.json','transitions.json.gz'):pins[str(folder/n)]=digest(folder/n)
  r=json.loads((folder/'result.json').read_text());rows=json.loads(gzip.decompress((folder/'transitions.json.gz').read_bytes()))
  if not r['completed'] or not r['source_unchanged']:raise RuntimeError('evaluation incomplete '+str(folder))
  episodes=r['episodes'];infos=[x['info'] for x in rows];flags=np.array([i['stability']['flags'] for i in infos]);g=[np.linalg.norm(i['stability']['guitar_delta_m'])*1000 for i in infos]
  results[folder.name]=dict(role=role,skill=r['skill'],cost_weight=r['cost_weight'],episodes=len(episodes),successes=sum(x['specialist']['stage_success'] for x in episodes),
   physical_failures=sum(x['reason']=='terminal_failure' for x in episodes),
   contact_episodes=sum(bool(e['specialist']['skill']['contact_targets']) for e in episodes),hold_episodes=sum(bool(e['specialist']['skill']['held_targets']) for e in episodes),
   original_music_matched50=sum(x['music']['matched50'] for x in episodes),
   mean_return=float(np.mean([x['reward'] for x in episodes])),mean_cost=float(np.mean([x['cost'] for x in episodes])),max_guitar_mm60=float(max(g)),
   all_support_presence60=float(np.mean(flags[:,:3].any(axis=1))),both_feet_presence60=float(np.mean(flags[:,-2:].all(axis=1))),
   target_contact_endpoints=sum(any(i['fret_candidates'].values()) for i in infos),
   total_actual_geometric_crossings=sum(x['specialist']['skill']['geometric_crossings'] for x in episodes),
   mean_marker_mm=float(np.mean([v*1000 for i in infos for v in i['goal_distance_m'].values()])),
   mean_guide_mm=float(np.mean([i['pick_guide']['distance_m']*1000 for i in infos])) if role=='right' else None,
   scope='two deterministic episodes, same prepared start;60Hz endpoint statistics; no unseen targets/generalization certification')
write(P/'evaluation_comparison_v1.json',dict(results=results,training_skill_details=training,inputs=pins,inputs_unchanged=all(digest(p)==s for p,s in pins.items())))
print(json.dumps(results))
