"""Read-only episode/control summaries from preserved validation raw files."""
from pathlib import Path
import json,gzip,math
import numpy as np
BASE=Path(__file__).resolve().parent

def read(path):
 with (gzip.open(path,'rt') if str(path).endswith('.gz') else Path(path).open()) as stream:return json.load(stream)

def summarize(folder):
 contract=read(folder/'training_contract.json')
 targets=contract['task']['targets']
 role_names=contract['action']['names']
 if (folder/'initial_values.json').exists():
  names=read(folder/'initial_values.json')['joint_names']
  prepared=read(folder/'reset_0001.json')['sample']
  groups=[sorted(folder.glob('transition_*.json.gz'))]
 else:
  first=folder/'episode_0000'
  names=read(first/'initial_values.json')['joint_names']
  prepared=read(first/'prepared.json')['sample']
  groups=[sorted(p.glob('transition_*.json.gz')) for p in sorted(folder.glob('episode_*'))]
 q0=np.array([r['pos'] for r in prepared['native']['human_dof_states']])
 target0=np.array(contract['action']['target_contract']['q_ref_rad'])
 upper_order=contract['action']['target_contract']['native_order']
 reference=dict(zip(upper_order,target0))
 action_indices=[names.index(n) for n in role_names]
 peak_q=np.zeros(39);peak_target=np.zeros(39);peak_action=np.zeros(39)
 stats={t['target_id']:dict(min_distance_m=math.inf,min_audible_distance_m=None,onset_distance_m=None,
    onset_time_error_s=math.inf,candidate_samples=0,audible_samples=0,audible_candidate_samples=0) for t in targets}
 count=0;steps=0;all_support=0;any_support=0;feet=0;max_g=0.;max_r=0.;max_foot=0.;errors=[];episodes=[]
 trace=[]
 for files in groups:
  for path in files:
   row=read(path);info=row['info'];steps+=1
   action=np.array(row['action']);peak_action=np.maximum(peak_action,np.abs(action))
   target=np.array(info['native_control']['native_final_target105_rad'])
   peak_target=np.maximum(peak_target,np.abs(target[action_indices]-np.array([reference[n] for n in role_names])))
   if info.get('episode'):episodes.append(info['episode'])
   for sample,measurement in zip(info['native_control']['physics_samples240'],info['physics_measurements']):
    music,safety=measurement['music'],measurement['stability'];time=music['task_time_s'];count+=1
    q=np.array([r['pos'] for r in sample['native']['human_dof_states']])
    peak_q=np.maximum(peak_q,np.abs(q[action_indices]-q0[action_indices]))
    flags=np.array(safety['flags']);all_support+=bool(flags[:3].all());any_support+=bool(flags[:3].any());feet+=bool(flags[-2:].all())
    max_g=max(max_g,float(np.linalg.norm(safety['guitar_delta_m'])))
    max_r=max(max_r,float(np.linalg.norm(safety['guitar_rotation_vector_rad'])))
    max_foot=max(max_foot,float(np.linalg.norm(safety['foot_delta_m'],axis=1).max()))
    errors.extend(x for x in safety['failure_reasons'] if x not in errors)
    for t in targets:
     key=t['target_id'];s=stats[key];distance=float(np.linalg.norm(music['geometry'][key]['delta']));candidate=music['targets'][key]['candidate']
     s['min_distance_m']=min(s['min_distance_m'],distance);s['candidate_samples']+=int(candidate)
     if abs(time-t['onset_s'])<s['onset_time_error_s']:
      s['onset_time_error_s']=abs(time-t['onset_s']);s['onset_distance_m']=distance
     if t['onset_s']<=time<t['end_s']:
      s['audible_samples']+=1;s['audible_candidate_samples']+=int(candidate)
      s['min_audible_distance_m']=distance if s['min_audible_distance_m'] is None else min(s['min_audible_distance_m'],distance)
   trace.append(dict(step=steps,task_time_s=info['task_time_s'],reward=row['reward'],cost=info['cost'],
    first_target_distance_m=float(np.linalg.norm(info['physics_measurements'][-1]['music']['geometry'][targets[0]['target_id']]['delta'])),
    strict=info['music']['matched50'],missed=info['music']['missed_strict'],terminated=row['terminated'],truncated=row['truncated']))
 roles={}
 for role,ix in [('left_arm',slice(0,12)),('fingers',slice(12,33)),('right',slice(33,39))]:
  roles[role]=dict(peak_normalized_action=float(peak_action[ix].max()),peak_submitted_target_offset_rad=float(peak_target[ix].max()),
                 peak_actual_q_difference_from_first_prepared_rad=float(peak_q[ix].max()))
 for key,s in stats.items():s['audible_candidate_fraction']=s['audible_candidate_samples']/s['audible_samples'] if s['audible_samples'] else None
 return dict(run=str(folder),control_steps=steps,physics_samples=count,all_three_support_fraction=all_support/count,
             any_support_fraction=any_support/count,both_feet_fraction=feet/count,max_guitar_translation_m=max_g,
             max_guitar_rotation_rad=max_r,max_foot_translation_m=max_foot,failure_reasons=errors,roles=roles,
             target_geometry_stats=stats,episodes=episodes,updates=[read(p) for p in sorted(folder.glob('update_*.json'))],trace=trace)

if __name__=='__main__':
 rows=[]
 for folder in sorted(BASE.iterdir()):
  if folder.is_dir() and (folder/'report.json').exists() and (folder/'training_contract.json').exists():
   result=summarize(folder);trace=result.pop('trace')
   with (BASE/(folder.name+'_trace.json')).open('x') as stream:json.dump(trace,stream,allow_nan=False)
   rows.append(result)
 with (BASE/'analysis.json').open('x') as stream:json.dump(rows,stream,indent=2,allow_nan=False);stream.write('\n')
 print(json.dumps([{k:r[k] for k in ('run','control_steps','physics_samples','all_three_support_fraction','both_feet_fraction','failure_reasons')} for r in rows],indent=2))
