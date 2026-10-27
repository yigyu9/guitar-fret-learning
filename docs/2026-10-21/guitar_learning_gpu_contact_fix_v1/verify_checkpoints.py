"""Check actual GPU resume payloads and rejection of the same-size old backend."""
import copy
import json
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.training.ppo import PPOConfig, PPOTrainer

HERE = Path(__file__).resolve().parent


def load(path):
    return torch.load(str(path), map_location='cpu', weights_only=False)


def same(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and a.dtype == b.dtype and np.array_equal(a, b)
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return type(a) is type(b) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


source = load(HERE/'train128_final/final.pt')
resumed = load(HERE/'resume128_final_v2/initial.pt')
final = load(HERE/'resume128_final_v2/final.pt')
fields = ('identity', 'model', 'actor_optimizer', 'value_optimizer', 'cost_weight', 'updates',
          'torch_rng', 'numpy_rng', 'python_rng', 'cuda_rng')
equality = {key: same(source[key], resumed[key]) for key in fields}
assert all(equality.values()), equality
assert source['updates'] == 2 and final['updates'] == 3
assert all(bool(torch.isfinite(value).all()) for value in final['model'].values())
assert any(not torch.equal(final['model'][key], source['model'][key]) for key in source['model'])
old_path = ROOT/'docs/2026-10-20/guitar_learning_gpu_batch_v1/n128_default_v1/final.pt'
old = load(old_path)
new_arch, old_arch = copy.deepcopy(source['identity']['architecture']), copy.deepcopy(old['identity']['architecture'])
new_contract, old_contract = new_arch.pop('contract'), old_arch.pop('contract')
assert new_arch == old_arch
assert new_contract['native_backend']['schema'] == 'guitar_learning.gpu_batch.v2'
assert old_contract['native_backend']['schema'] == 'guitar_learning.gpu_batch.v1'
policy = SpecialistPolicy(512, size='medium', contract=new_contract, role='left', frozen_partner=False)
trainer = PPOTrainer(policy, PPOConfig(**source['identity']['config']))
assert trainer._identity() == source['identity']
try:
    trainer.load(old_path)
except ValueError as error:
    rejection = str(error)
    assert rejection == 'own schema/architecture/input/control/config mismatch'
else:
    raise AssertionError('Old physical contract was accepted')
result = dict(completed=True, restored_fields_equal=equality, source_updates=2, final_updates=3,
              old_same_architecture_backend_rejected=rejection, model_finite=True,
              physical_resume_scope='New prepared episodes; simulator state is not restored')
(HERE/'checkpoint_verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
