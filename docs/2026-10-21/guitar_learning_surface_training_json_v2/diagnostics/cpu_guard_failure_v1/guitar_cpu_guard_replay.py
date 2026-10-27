import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import sys,json,gzip,hashlib,math
from collections import Counter
import numpy as np
phase=Path('/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_logging_fix_v1')
sys.path.insert(0,str(phase))
import verify_training as v
from guitar_learning.training import json_io
v.encoded=lambda value: json_io.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
from guitar_learning.song.gpu_left_curriculum import CurriculumState
v.torch.set_num_threads(1)
run=phase/'resume1550'
out=Path('/tmp/guitar_cpu_guard_audit_result_%d.json'%os.getpid())
v.require(not out.exists(),'Refusing to overwrite crash audit')
updates=sorted(run.glob('update_*.json'));n=len(updates)
v.require([p.name for p in updates]==['update_%06d.json'%i for i in range(n)],'Update holes')
settings,contract=v.read(run/'settings.json'),v.read(run/'training_contract.json')
schedule=contract['task']['provenance']['song']['schedule'];duration=settings['song_training']['episode_duration_s']
cp_path=run/'checkpoint_000349.pt';cp=v.torch.load(cp_path,map_location='cpu',weights_only=False)
v.require(cp['updates']==800,'checkpoint optimizer count')
v.require(cp['identity']['architecture']['contract']==contract and cp['identity']['config']==settings['ppo'],'checkpoint identity')
finite={k:v.finite(cp[k]) for k in ('model','actor_optimizer','value_optimizer')}
v.require(all(finite.values()) and cp['actor_optimizer']['state'] and cp['value_optimizer']['state'],'checkpoint branch states')
v.require(math.isfinite(cp['cost_weight']) and cp['cost_weight']>=0,'checkpoint cost weight')
state=cp['model']['left_curriculum_state'].numpy();v.require(state.shape==(3331,),'checkpoint curriculum shape')
counts=[sum(t['finger']==f for t in schedule) for f in range(1,5)]
curriculum=CurriculumState(counts)
initial=v.torch.load(run/'initial.pt',map_location='cpu',weights_only=False)
original=v.torch.load(phase.parent/'guitar_learning_surface_training_recovery_v1'/'resume1700'/'checkpoint_000149.pt',map_location='cpu',weights_only=False)
v.require(initial['updates']==450 and initial.keys()==original.keys() and all(v.same(value,initial[key]) for key,value in original.items() if key!='metadata'),'initial450 exact restore')
curriculum.load_state(initial['model']['left_curriculum_state'].numpy());expected_saved=None
metrics,logged=iter(v.lines(run/'learning_metrics.jsonl')),iter(v.lines(run/'episodes.jsonl'))
rows=0;episodes_count=Counter(all=0,timeline_complete=0,physical_failure=0,stage_success=0)
max_ep_error=max_update_error=0.
metrics_count=0;missing_metrics=[]
with gzip.open(run/'transitions.jsonl.gz','rt') as stream:
 for index in range(n):
  update=v.read(updates[index]);v.finite(update)
  v.require(update['update_index']==index and update['optimizer_updates']==450+index+1,'update sequence')
  v.require(update['physics_steps']==(index+1)*32*4,'physics sequence')
  v.journal(update['journal'],index+1,False)
  metric=next(metrics,None)
  if metric is None:
   v.require(index==n-1,'Metrics unexpectedly missing before final update');missing_metrics.append(index)
  else:
   v.require(v.encoded(metric)==v.encoded(update),'metrics/update mismatch');metrics_count+=1
  max_update_error=max(max_update_error,v.component_sum(update['reward_component_means'],update['mean_reward'],'update reward'))
  eh,lh,rh=hashlib.sha256(),hashlib.sha256(),hashlib.sha256()
  ended=update['completed_episodes']
  for e in ended:
   max_ep_error=max(max_ep_error,v.verify_episode(e,schedule,duration))
   eh.update(v.encoded(e)+b'\n');l=next(logged,None)
   v.require(l is not None and l['update_index']==index,'episode log sequence')
   lh.update(v.encoded(l['episode'])+b'\n')
   episodes_count['all']+=1;episodes_count['physical_failure' if e['reason']=='terminal_failure' else 'timeline_complete']+=1
   episodes_count['stage_success']+=bool(e['song']['stage_success'])
  before=curriculum.progress
  summary=curriculum.observe([dict(full_safe=e['reason']=='timeline_complete',finger_metrics=e['left_curriculum']['finger_metrics']) for e in ended])
  summary.update(completed_episodes_in_update=len(ended),progress_before=before,boundary='after committed PPO collection; no scene reset')
  v.require(v.summary_close(summary,update['left_curriculum']),'curriculum replay summary')
  if index+1==cp['updates']-450:expected_saved=curriculum.state_vector().copy()
  reward=cost=raw_ended=0
  for tick in range(32):
   line=stream.readline();v.require(line.endswith('\n'),'raw missing/incomplete row')
   raw=json.loads(line);v.finite(raw)
   v.require(raw['schema']=='guitar_learning.gpu_transition.v1' and raw['update_index']==index and raw['tick_in_update']==tick,'raw sequence')
   v.require(all(len(raw[k])==1024 for k in ('reward','cost','terminated','truncated')),'raw batch size')
   v.require(all(isinstance(x,bool) for k in ('terminated','truncated') for x in raw[k]) and not any(raw['truncated']),'raw done masks')
   v.require(all(c>=0 for c in raw['cost']),'raw costs')
   ids=[e['env_id'] for e in raw['episodes']]
   v.require(len(ids)==len(set(ids)) and set(ids)=={i for i,done in enumerate(raw['terminated']) if done},'raw done correspondence')
   for e in raw['episodes']:rh.update(v.encoded(e)+b'\n')
   raw_ended+=len(ids);reward+=math.fsum(raw['reward']);cost+=math.fsum(raw['cost']);rows+=1
  v.require(raw_ended==len(ended) and eh.digest()==lh.digest()==rh.digest(),'episode correspondence')
  v.require(math.isclose(reward/32768,update['mean_reward'],rel_tol=1e-5,abs_tol=1e-6) and math.isclose(cost/32768,update['mean_cost'],rel_tol=1e-5,abs_tol=1e-6),'raw/update means')
  if (index+1)%50==0:print('Audited committed prefix',index+1,flush=True)
 v.require(stream.read()=='','extra gzip records')
v.require(next(metrics,None) is None and next(logged,None) is None,'extra metric/episode records')
v.require(np.allclose(state,expected_saved,rtol=1e-10,atol=1e-12),'checkpoint full3331 replay mismatch')
check=CurriculumState(counts);check.load_state(state)
pins,manifest=v.read(run/'inputs_before.json'),v.read(phase/'training_source_manifest.json')
source=manifest['source'];v.require(len(source)==manifest['active_python_count'],'source count')
modified=[]
for name,expected in pins.items():
 if name in source:
  v.require(v.digest(phase/'source_training'/Path(name).relative_to(v.ROOT))==expected,'historical input snapshot '+name)
  if v.digest(Path(name))!=expected:modified.append(name)
 else:v.require(v.digest(Path(name))==expected,'non-source input SHA changed '+name)
for name,expected in source.items():v.require(pins.get(name)==expected and v.digest(phase/'source_training'/Path(name).relative_to(v.ROOT))==expected,'source snapshot changed '+name)
last=v.read(updates[-1]);v.require((run/'transitions.jsonl.gz').stat().st_size==last['journal']['compressed_bytes'],'raw bytes beyond recorded prefix')
caches=[e for e in v.lines(run/'events.jsonl') if e.get('event')=='cuda_cache_release' and e['reason']=='optimizer_boundary']
steps={branch:sorted(set(float(value['step']) for value in cp[branch]['state'].values() if 'step' in value)) for branch in ('actor_optimizer','value_optimizer')}
result=dict(schema='guitar_learning.surface_logging_guard_crash_journal_audit.v1',audit_checks_passed=True,training_completed=False,
 status='SIGFPE interrupted run; report/final GPU cleanup absent, not a successful1550-update JSON-guard run',
 final_report_present=(run/'report.json').exists(),final_checkpoint_present=(run/'final.pt').exists(),failure_checkpoint_present=(run/'failure_last_valid.pt').exists(),
 durable_logged_prefix=dict(update_indices=[0,n-1],local_updates_logged=n,optimizer_updates_logged=450+n,committed_transitions=n*32768,raw_rows=rows,
  gzip_all_members_CRC_EOF=True,raw_bytes=(run/'transitions.jsonl.gz').stat().st_size,metrics_rows=metrics_count,missing_metrics_update_indices=missing_metrics,
  episode_rows=episodes_count['all'],episode_counts=dict(episodes_count),update_raw_episode_exact_correspondence=True,available_metrics_exact_correspondence=True,
  last_journal=last['journal'],PPO_nonfinite_counts_zero=True,max_episode_reward_sum_abs_error=max_ep_error,max_update_reward_sum_abs_error=max_update_error),
 recoverable_checkpoint=dict(path=str(cp_path),sha256=v.digest(cp_path),optimizer_updates=cp['updates'],source_prefix_update_indices=[0,cp['updates']-451],optimizer_offset=450,
  committed_transitions=(cp['updates']-450)*32768,chain_committed_transitions=cp['updates']*32768,finite_tensor_counts=finite,curriculum_values=int(state.size),
  curriculum_replay_max_abs_error=float(np.max(np.abs(state-expected_saved))),curriculum_summary=check.summary(),optimizer_step_values=steps,
  identity_matches_run_contract=True,cost_weight=cp['cost_weight'],scope='CPU-valid model, both optimizers, RNG and curriculum; actual GPU resume not performed'),
 unsaved_logged_updates=dict(update_indices=[cp['updates']-450,n-1],optimizer_update_counts=[cp['updates']+1,450+n],count=n-(cp['updates']-450),transitions=(n-(cp['updates']-450))*32768,
  scope='Logs and rewards exist; corresponding trained weights/RNG are not saved. Re-running these updates is not exact continuation of the lost in-memory policy.'),
 integrity=dict(input_SHA_verified=len(pins),frozen_source_SHA_verified=len(source),historical_source_snapshot_matches=True,current_source_modified_since_run=modified),
 last_optimizer_boundary_cache_event=dict(count=len(caches),last_update_index=caches[-1]['update_index'],after=caches[-1]['after']),
 limits=['No final report, final checkpoint, failure recovery checkpoint or verified GPU-close lifecycle is inferred.',
  'A valid logged PPO prefix is not a saved checkpoint at that prefix.',
  'Signal136/SIGFPE native cause is outside this journal/checkpoint audit.',
  'A new process resumes from a prepared physical episode, not the interrupted mid-song GPU state.'])
with out.open('x') as f:json_io.dump(result,f,indent=2,allow_nan=False)
print(json_io.dumps(dict(audit=str(out),logged_updates=n,checkpoint_updates=cp['updates'],raw_rows=rows,episodes=dict(episodes_count),finite=finite,source=len(source),pins=len(pins)),indent=2),flush=True)
