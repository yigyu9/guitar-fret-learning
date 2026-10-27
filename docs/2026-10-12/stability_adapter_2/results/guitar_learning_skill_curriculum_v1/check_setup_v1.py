"""Verify cost pairs actually begin from equal policy/RNG and matching tasks."""
import json
from pathlib import Path
import numpy as np
import torch
from guitar_learning.recording import digest,write
P=Path(__file__).resolve().parent

def equal(a,b):
 if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
 if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and np.array_equal(a,b)
 if type(a)!=type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,(tuple,list)):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return a==b

def main():
 result={};pinned={str(Path(__file__)):digest(__file__)}
 for role in ('left','right'):
  paths=[P/(role+'_cost'+s+'_run_v2') for s in ('1p0','0p1')]
  for p in paths:
   for n in ('initial.pt','settings.json','training_contract.json','reset_initial.json'):
    pinned[str(p/n)]=digest(p/n)
  models=[torch.load(p/'initial.pt',map_location='cpu',weights_only=False) for p in paths]
  settings=[json.loads((p/'settings.json').read_text()) for p in paths]
  costs=[x['ppo'].pop('cost_weight') for x in settings]
  checks=dict(settings_except_cost_equal=equal(*settings),cost_weights=costs,model_equal=equal(models[0]['model'],models[1]['model']),
   cpu_rng_equal=equal(models[0]['torch_rng'],models[1]['torch_rng']),numpy_rng_equal=equal(models[0]['numpy_rng'],models[1]['numpy_rng']),
   python_rng_equal=equal(models[0]['python_rng'],models[1]['python_rng']),cuda_rng_equal=equal(models[0]['cuda_rng'],models[1]['cuda_rng']),
   contract_equal=equal(*[json.loads((p/'training_contract.json').read_text()) for p in paths]),
   parameter_count=sum(v.numel() for k,v in models[0]['model'].items() if k!='partner_initialized'))
  if not all(v for k,v in checks.items() if k.endswith('_equal')):raise RuntimeError('unmatched pair '+role)
  result[role]=checks
 write(P/'setup_comparison_v1.json',dict(pairs=result,inputs=pinned,inputs_unchanged=all(digest(p)==sha for p,sha in pinned.items())))
 print(json.dumps(result))

if __name__=='__main__':main()
