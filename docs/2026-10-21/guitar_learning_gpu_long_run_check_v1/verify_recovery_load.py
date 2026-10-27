"""Compare the actual failure checkpoint with the resumed initial payload."""
import json
from pathlib import Path
import numpy as np
import torch
p = Path(__file__).resolve().parent
source = torch.load(p/'train1024_large_70/failure_last_valid.pt', map_location='cpu', weights_only=False)
resumed = torch.load(p/'train1024_large_64_cache_v2/initial.pt', map_location='cpu', weights_only=False)


def equal(left, right):
    if isinstance(left, torch.Tensor):
        return torch.equal(left, right)
    if isinstance(left, np.ndarray):
        return np.array_equal(left, right)
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equal(left[k], right[k]) for k in left)
    if isinstance(left, (list, tuple)):
        return type(left) is type(right) and len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right))
    return left == right


keys = ['identity', 'model', 'actor_optimizer', 'value_optimizer', 'cost_weight', 'updates',
        'torch_rng', 'numpy_rng', 'python_rng', 'cuda_rng']
fields = {key: equal(source[key], resumed[key]) for key in keys}
assert all(fields.values()), fields
assert source['updates'] == 26
result = dict(completed=True, restored_fields_equal=fields, source_updates=26,
              scope='Actual failure_last_valid to resumed initial model/optimizers/RNG/curriculum; new prepared physical episodes')
(p/'recovery_load_verification.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
