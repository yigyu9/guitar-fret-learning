import json
from pathlib import Path
import numpy as np
import torch
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.training.ppo import PPOTrainer,PPOConfig
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
p=Path(__file__).resolve().parent
source=p/'aggregate_smoke_2/final.pt'
payload=torch.load(source,map_location='cpu',weights_only=False)
a=payload['identity']['architecture']
policy=SpecialistPolicy(a['state_dim'],size=a['size'],contract=a['contract'],role=a['role'])
CurriculumCoordinator(policy,None)
trainer=PPOTrainer(policy,PPOConfig(**payload['identity']['config']))
trainer.load(source)
trainer.save(p/'smoke_reloaded.pt',metadata={'test':'full v3 restoration'})
restored=torch.load(p/'smoke_reloaded.pt',map_location='cpu',weights_only=False)
def same(a,b):
    if isinstance(a,torch.Tensor):return torch.equal(a,b)
    if isinstance(a,np.ndarray):return np.array_equal(a,b)
    if isinstance(a,dict):return a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b
assert all(same(v,restored[k]) for k,v in payload.items() if k!='metadata')
old=p.parent/'guitar_learning_gpu_long_run_check_v1/train512_large_128_v5/failure_last_valid.pt'
try:trainer.load(old)
except ValueError as error:reason=str(error)
else:raise AssertionError('v2 checkpoint must be rejected')
result=dict(completed=True,v3_full_nonmetadata_restore_exact=True,v2_strict_rejected=True,rejection=reason,device='CPU model with actual CUDA RNG topology',source=str(source))
(p/'checkpoint_contract_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
