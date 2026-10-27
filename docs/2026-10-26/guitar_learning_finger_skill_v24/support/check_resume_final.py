"""Read-only CPU verification of actual GPU save/resume boundary state."""
import json
from pathlib import Path
import numpy as np
import torch

root=Path(__file__).resolve().parents[1]
a=torch.load(root/'smoke1024_final/F/final.pt',map_location='cpu',weights_only=False)
b=torch.load(root/'resume1024_final/F/initial.pt',map_location='cpu',weights_only=False)
c=torch.load(root/'resume1024_final/F/final.pt',map_location='cpu',weights_only=False)

def equal(left,right):
    if isinstance(left,torch.Tensor): return isinstance(right,torch.Tensor) and torch.equal(left,right)
    if isinstance(left,np.ndarray): return isinstance(right,np.ndarray) and np.array_equal(left,right)
    if isinstance(left,dict): return isinstance(right,dict) and left.keys()==right.keys() and all(equal(left[k],right[k]) for k in left)
    if isinstance(left,(tuple,list)): return type(left)==type(right) and len(left)==len(right) and all(equal(x,y) for x,y in zip(left,right))
    return left==right

keys=('identity','model','actor_optimizer','value_optimizer','cost_weight','updates','torch_rng','numpy_rng','python_rng','cuda_rng')
checks={key:bool(equal(a[key],b[key])) for key in keys}
assert all(checks.values()),checks
assert c['updates']==a['updates']+1
assert equal(a['metadata']['curriculum'],b['metadata']['curriculum'])
assert b['metadata']['sampler']['reset_count']==a['metadata']['sampler']['reset_count']+1024
report=dict(completed=True, restored_exact=checks,curriculum_exact=True,
    sampler_restored_then_new_prepared_episodes=1024,old_updates=a['updates'],new_updates=c['updates'],
    physical_state_resumed=False,scope='same-phase strict optimizer/RNG/model restore, fresh prepared native episodes')
(root/'support/final_resume_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
