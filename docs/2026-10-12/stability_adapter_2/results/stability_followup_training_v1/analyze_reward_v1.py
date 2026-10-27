"""Explain saved deterministic reward components and configured GAE decay."""
from collections import defaultdict
import hashlib,json
from pathlib import Path
import torch
P=Path(__file__).resolve().parent;Q=P.parent/'stability_support_nominal_v1';inputs={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):inputs[str(p)]=sha(p);return json.loads(Path(p).read_text())
inputs[str(Path(__file__).resolve())]=sha(__file__)
analysis=read(P/'analysis_v1.json');label=analysis['label'];out={}
cp_path=Q/'long_on_v1/checkpoints'/(label+'.pt');inputs[str(cp_path)]=sha(cp_path)
cp=torch.load(cp_path,map_location='cpu',weights_only=True);config=cp['ppo_config']
for name,base in [('CP1',Q/'smoke_on_v2/evaluations/update_000001/native/episode_0001'),('new_checkpoint',Q/'long_on_v1/evaluations'/label/'native/episode_0001')]:
 rows=read(base/'controls.json');nr=read(base/'report.json');components=defaultdict(float)
 for row in rows:
  for term,value in row['raw_component_ledger'].items():components[term]+=value*nr['reward_scale']
  components['floor_or_safety_settlement_adjustment']+=(row['raw_reward']-row['unfloored_raw_reward'])*nr['reward_scale']
 out[name]={'scaled_component_returns':dict(components),'summed_return':sum(components.values()),'reported_return':nr['return'],
  'absolute_return_reconstruction_error':abs(sum(components.values())-nr['return'])}
result={'evaluations':out,'gamma':config['gamma'],'lambda':config['lam'],
 'GAE_TD_residual_weight_at_seconds':{str(seconds):float((config['gamma']*config['lam'])**(60*seconds)) for seconds in [.5,1,2,5]},
 'scope':'sum of saved deterministic ledger terms; GAE residual decay is a mathematical coefficient, not empirical proof of causal credit failure or full return discount',
 'input_sha256':inputs,'inputs_unchanged':all(sha(p)==h for p,h in inputs.items())}
with (P/'reward_analysis_v1.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(out))
if not result['inputs_unchanged'] or any(r['absolute_return_reconstruction_error']>1e-10 for r in out.values()):raise SystemExit('reward reconstruction failed')
