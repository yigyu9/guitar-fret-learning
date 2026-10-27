"""Exact state restoration and real same-shape v17 rejection, on CPU."""
import copy
import json
from pathlib import Path
import random
import numpy as np
import torch
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.training.ppo import PPOTrainer, PPOConfig
root = Path(__file__).resolve().parents[4]
phase = Path(__file__).resolve().parents[1]
torch.set_num_threads(1)
def load(path): return torch.load(path,map_location='cpu',weights_only=False)
def equal(x,y):
    if isinstance(x,torch.Tensor): return isinstance(y,torch.Tensor) and torch.equal(x,y)
    if isinstance(x,np.ndarray): return isinstance(y,np.ndarray) and np.array_equal(x,y)
    if isinstance(x,dict): return isinstance(y,dict) and x.keys()==y.keys() and all(equal(x[k],y[k]) for k in x)
    if isinstance(x,(tuple,list)): return type(x)==type(y) and len(x)==len(y) and all(equal(a,b) for a,b in zip(x,y))
    return x==y
first,initial,final = (load(phase/name) for name in ('gpu_smoke/final.pt','gpu_resume/initial.pt','gpu_resume/final.pt'))
checks = {k:equal(first[k],initial[k]) for k in first if k!='metadata'}
settings = json.loads((phase/'gpu_smoke/settings.json').read_text())
contract = json.loads((phase/'gpu_smoke/training_contract.json').read_text())
policy = SpecialistPolicy(544,size='small',role='left',contract=contract)
# Match real curriculum buffers before identity/load comparison.
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from types import SimpleNamespace
targets = json.loads((root/'docs/2026-10-24/guitar_learning_long_training_v17/evaluation_update_1000_1024/targets.json').read_text())
counts = [sum(t['finger']==i for t in targets) for i in range(1,5)]
CurriculumCoordinator(policy,SimpleNamespace(environment=SimpleNamespace(finger_counts=counts)))
trainer = PPOTrainer(policy,PPOConfig(**settings['ppo']))
old_path = root/'docs/2026-10-24/guitar_learning_compact_logging_v1/gpu_smoke_retry1/final.pt'
before = copy.deepcopy((policy.state_dict(),trainer.actor_optimizer.state_dict(),trainer.value_optimizer.state_dict(),trainer.updates,torch.get_rng_state(),np.random.get_state(),random.getstate()))
try:
    trainer.load(old_path)
except ValueError as error:
    assert 'mismatch' in str(error)
else:
    raise AssertionError('v17 must not resume into v18')
after = (policy.state_dict(),trainer.actor_optimizer.state_dict(),trainer.value_optimizer.state_dict(),trainer.updates,torch.get_rng_state(),np.random.get_state(),random.getstate())
result = dict(all_nonmetadata_state_exact=all(checks.values()),checks=checks,
    initial_updates=initial['updates'],final_updates=final['updates'],
    model_updated=not equal(initial['model'],final['model']),
    actor_optimizer_updated=not equal(initial['actor_optimizer'],final['actor_optimizer']),
    value_optimizer_updated=not equal(initial['value_optimizer'],final['value_optimizer']),
    real_v17_rejected=True,rejection_preserved_all_state=equal(before,after))
assert result['all_nonmetadata_state_exact'] and result['initial_updates']==65 and result['final_updates']==66
assert all(result[k] for k in ('model_updated','actor_optimizer_updated','value_optimizer_updated','rejection_preserved_all_state'))
(phase/'checkpoint_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
