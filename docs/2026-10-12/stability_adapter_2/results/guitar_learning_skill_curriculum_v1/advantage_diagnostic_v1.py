"""First-rollout signal scales, not a proof of later gradient causality."""
from pathlib import Path
import json
import torch
from guitar_learning.ppo import compute_gae
from guitar_learning.recording import digest,write
P=Path(__file__).resolve().parent
pinned={str(Path(__file__)):digest(__file__),str(Path('/home/ajou/yigyu/3/guitar_learning/ppo.py')):digest('/home/ajou/yigyu/3/guitar_learning/ppo.py')};results={}
for role in ('left','right'):
 paths=[P/(role+'_cost'+s+'_run_v2/rollout_first.pt') for s in ('1p0','0p1')]
 for p in paths:pinned[str(p)]=digest(p)
 batches=[torch.load(p,map_location='cpu',weights_only=False) for p in paths];b=batches[0]
 ar,_=compute_gae(b['reward'],b['reward_value'],b['next_reward_value'],b['terminated'],b['truncated'],.99,.95)
 ac,_=compute_gae(b['cost'],b['cost_value'],b['next_cost_value'],b['terminated'],b['truncated'],1.,.95)
 results[role]=dict(first_rollout_field_equal={k:torch.equal(b[k],batches[1][k]) for k in b},reward_adv_std=float(ar.std(unbiased=False)),cost_adv_std=float(ac.std(unbiased=False)),
  cost_to_reward_std_ratio=float(ac.std(unbiased=False)/ar.std(unbiased=False)),
  weighted_std_ratios={str(w):float(w*ac.std(unbiased=False)/ar.std(unbiased=False)) for w in (1.,.1)},
  scope='pre-standardization GAE spread on initial rollout only; not actor gradient share and not later learning effect')
write(P/'advantage_diagnostic_v1.json',dict(results=results,inputs=pinned,inputs_unchanged=all(digest(p)==s for p,s in pinned.items())))
print(json.dumps(results))
