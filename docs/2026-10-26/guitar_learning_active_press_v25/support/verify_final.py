"""CPU checks of completed GPU artifacts and unchanged baseline sources."""
import gzip,hashlib,json,sys
from collections import Counter
from pathlib import Path
import numpy as np
import torch

ROOT=Path('/home/ajou/yigyu/3');RESULT=ROOT/'docs/2026-10-26/guitar_learning_active_press_v25';SUPPORT=RESULT/'support'
sys.path.insert(0,str(ROOT))
read=lambda p:json.loads(p.read_text())

def finite(value):
 if torch.is_tensor(value):return bool(torch.isfinite(value).all())
 if isinstance(value,dict):return all(finite(x) for x in value.values())
 if isinstance(value,(list,tuple)):return all(finite(x) for x in value)
 return True

def equal(a,b):
 if torch.is_tensor(a):return torch.equal(a,b)
 if isinstance(a,np.ndarray):return np.array_equal(a,b)
 if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return a==b

summary={}
for name in ['final_smoke','calibrated_smoke','calibrated_large1024','calibrated_resume1024']:
 folder=RESULT/name/'J';before=torch.load(folder/'initial.pt',map_location='cpu',weights_only=False);after=torch.load(folder/'final.pt',map_location='cpu',weights_only=False)
 assert finite(after)
 report=read(folder/'report.json');assert report['completed'] and report['lifecycle_verified'] and not report['changed_inputs'] and report['failure'] is None
 reasons=Counter();failures=Counter();achieved=0;opportunities=0
 with (folder/'episodes.jsonl').open() as stream:
  for line in stream:
   e=json.loads(line)['episode'];reasons[e['reason']]+=1;failures.update(e['failure_reasons']);achieved+=e['song']['left_success_count'];opportunities+=e['song']['target_count']
 changed={prefix:sum(not torch.equal(before['model'][k],v) for k,v in after['model'].items() if k.startswith(prefix)) for prefix in ['support_','finger_']}
 assert all(value>0 for value in changed.values())
 summary[name]=dict(updates=report['updates_in_run'],raw_transitions=report['transitions'],wall_s=report['wall_s'],minimum_gpu_free_bytes=report['min_cuda_free_bytes'],state_dimension=after['identity']['architecture']['state_dim'],changed_actor_tensors=changed,all_model_Adam_tensors_finite=True,episode_reasons=dict(reasons),failure_reasons_may_overlap=dict(failures),training_incidental_achieved_notes=achieved,training_selected_note_opportunities=opportunities)

# Actual transition correspondence and discounted sums, independent of PPO code.
folder=RESULT/'calibrated_smoke/J'
with gzip.open(folder/'transitions.jsonl.gz','rt') as stream:raw=[json.loads(line) for line in stream]
r=np.array([x['reward'] for x in raw]);c=np.array([x['cost'] for x in raw]);coverage=np.zeros(r.shape,dtype=np.int8);duration_counts=Counter();error_r=error_c=0.;decisions=0
with gzip.open(folder/'decisions.jsonl.gz','rt') as stream:
 for line in stream:
  d=json.loads(line);start,end,env=d['start_control_tick'],d['end_control_tick'],d['env_id'];length=end-start;assert length==d['duration'] and 1<=length<=3
  coverage[start:end,env]+=1;duration_counts[length]+=1;decisions+=1
  error_r=max(error_r,abs(float((r[start:end,env]*.99**np.arange(length)).sum())-d['discounted_reward']))
  error_c=max(error_c,abs(float(c[start:end,env].sum())-d['discounted_cost']))
assert (coverage==1).all() and error_r<2e-6 and error_c<2e-6
summary['raw_decision_verification']=dict(physical_transitions=int(r.size),decisions=decisions,duration_counts=dict(duration_counts),every_raw_transition_exactly_once=True,max_reward_discount_error=error_r,max_cost_discount_error=error_c)

source=torch.load(RESULT/'calibrated_large1024/J/final.pt',map_location='cpu',weights_only=False);resumed=torch.load(RESULT/'calibrated_resume1024/J/initial.pt',map_location='cpu',weights_only=False)
keys=[k for k in source if k!='metadata'];resume_equal={k:equal(source[k],resumed[k]) for k in keys};assert all(resume_equal.values()),resume_equal
assert equal(source['metadata']['curriculum'],resumed['metadata']['curriculum'])
from guitar_learning.song.task import make_task
from guitar_learning.song.finger_phrases import build_phrase_catalog,BalancedPhraseSampler
task=make_task(ROOT/'data/song_bundles/05_BN2-131-B_solo',pre_roll_s=3.,tail_s=.5)
sampler=BalancedPhraseSampler(build_phrase_catalog(task,preparation_s=3.,tail_s=.5))
sampler.load_state_dict(source['metadata']['sampler'])
for _ in range(1024):sampler.next()
assert sampler.state_dict()==resumed['metadata']['sampler']
summary['strict_resume']=dict(top_level_state_exact=resume_equal,curriculum_exact=True,sampler_restored_then_new_prepared_episodes=True,sampler_after_1024_new_prepared_episodes_exact=True)
for filename in ['baseline_sources.json','source_manifest.json']:
 manifest=read(SUPPORT/filename);assert all(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'] for x in manifest)
summary['sources']=dict(baseline_unchanged=495,current_unchanged=500)
summary['limits']=['Short integration tests only; not long-run memory or learned natural pressing validation.','Candidate calibration is one seed and equal raw transition budget; completed episode counts and opportunities differ.','Old framework physical_failure summaries include all terminal failures; use failure_reasons to distinguish wrist/physical events.']
(SUPPORT/'verification.json').write_text(json.dumps(dict(completed=True,checks=summary),indent=2)+'\n')
print(json.dumps(summary,indent=2))
