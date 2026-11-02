if not __debug__:raise RuntimeError('Scientific checks require optimization disabled')
from pathlib import Path
import json,gzip,hashlib,math,sys
D=Path(__file__).resolve().parents[2];R=next(p for p in D.parents if (p/'scripts/tab2body.py').exists());sys.path.insert(0,str(R))
from guitar_learning.training.training_log_io import iter_episode_rows
state=json.loads((D/'status.json').read_text());output={'schema':'index_middle.motion_training_analysis.v1','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'training':{},'motion':{}}
for seed in (7,17):
 metrics=[]
 for u in (100,200,300):metrics.extend(json.loads(x) for x in (D/f'모델/base_seed{seed}_u{u}/J/learning_metrics.jsonl').read_text().splitlines())
 assert all('wrist_failure' in x['episode_summary'] or x['episode_summary']['count']==0 for x in metrics),'missing wrist failures for nonempty episode summary'
 output['training'][str(seed)]={'updates':len(metrics),'transitions':sum(x['transitions'] for x in metrics),'actor_accepted_steps':sum(x['diagnostics']['minibatches']['actor_accepted']['steps'] for x in metrics),'actor_rejected_steps':sum(x['diagnostics']['minibatches']['actor_rejected']['steps'] for x in metrics),'critic_steps':sum(x['diagnostics']['minibatches']['value']['steps'] for x in metrics),'learning_rate_first':metrics[0]['actor_lr'],'learning_rate_last':metrics[-1]['actor_lr'],'learning_rate_min':min(x['actor_lr'] for x in metrics),'kl_retries':sum(x['kl_retries'] for x in metrics),'maximum_accepted_kl':max(x['analytic_kl'] for x in metrics),'mean_raw_reward_advantage_std':sum(x['diagnostics']['advantages']['reward_raw']['std'] for x in metrics)/len(metrics),'mean_raw_cost_advantage_std':sum(x['diagnostics']['advantages']['cost_raw']['std'] for x in metrics)/len(metrics),'signal_scope':'advantage std is not gradient contribution','mean_stochastic_training_cost':sum(x['mean_cost'] for x in metrics)/len(metrics),'training_completed_physical_failures':sum(x['episode_summary']['physical_failure'] for x in metrics),'training_completed_wrist_failures':sum(x['episode_summary'].get('wrist_failure',0) for x in metrics),'training_scope':'training stochastic completed episodes only, not deterministic evaluation'}
for record in state['results']:
 if record['updates']!=300:continue
 path=Path(record['evaluation']);episodes=[x['episode'] for x in iter_episode_rows(path)];e0=next(x for x in episodes if x['env_id']==0);eid=e0['finger_control_diagnostics']['episode_id'];times={'prepare':[],'A':[],'gap':[],'B':[],'tail':[]};joint_names=None
 with gzip.open(path/'finger_control_trace.jsonl.gz','rt') as stream:
  for line in stream:
   row=json.loads(line)
   if row['episode_id']!=eid:continue
   t=row['episode_time_s'];phase='prepare' if t<3 else 'A' if t<4.5 else 'gap' if t<5.25 else 'B' if t<6.75 else 'tail';times[phase].append(row);joint_names=row['joint_names']
 phases={}
 for phase,rows in times.items():
  if not rows:continue
  fingers={}
  for name in ('index','middle'):
   ids=[i for i,joint in enumerate(joint_names) if ('LH:'+name) in joint];assert len(ids)==4
   values={}
   for field in ('requested_target_rad','applied_target_rad','actual_rad','velocity_rad_s'):
    values[field+'_mean']=[sum(x[field][i] for x in rows)/len(rows) for i in ids]
    values[field+'_range']=[max(x[field][i] for x in rows)-min(x[field][i] for x in rows) for i in ids]
   values['applied_actual_tracking_rms_rad']=[math.sqrt(sum((x['applied_target_rad'][i]-x['actual_rad'][i])**2 for x in rows)/len(rows)) for i in ids]
   fingers[name]=values
  phases[phase]={'physics_samples':len(rows),'fingers':fingers}
 raw={k:[sum(x['finger_control_diagnostics']['values'][k][i] for x in episodes)/len(episodes) for i in range(21)] for k in ('requested_tracking_error_rad_rms','applied_tracking_error_rad_rms','rate_limit_gap_rad_rms','velocity_rad_s_rms')}
 output['motion'][f"seed{record['seed']}_{record['mode']}"]={'phase_motion_env0':phases,'all_environment_whole_episode_control_summary':raw,'source_trace_sha256':hashlib.sha256((path/'finger_control_trace.jsonl.gz').read_bytes()).hexdigest(),'scope':'phase motion is final checkpoint env0 entire episode at240Hz; all-env values are arithmetic means of per-episode RMS, not pooled RMS or every-env phase trajectories','wrong_sources_mean_seconds':{k:[sum(x['left_note_ledger']['values'][k][i] for x in episodes)/len(episodes) for i in (0,1)] for k in ('other_higher_time','own_wrong_fret_time','own_wrong_string_time')}}
(D/'진단/motion_training_summary.json').write_text(json.dumps(output,indent=2));print('training and late checkpoint phase-motion analysis completed')
