"""봉인 V4 학습 루프를 V6 runtime에 한정하여 연결한다."""
import importlib.util
from pathlib import Path
import sys
import runtime as rt

spec = importlib.util.spec_from_file_location('cost_prior_v6_parent_learn', rt.v5.SOURCE/'learn.py')
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
old = sys.modules.get('runtime')
try:
    sys.modules['runtime'] = rt
    spec.loader.exec_module(parent)
finally:
    if old is None: sys.modules.pop('runtime', None)
    else: sys.modules['runtime'] = old

train, evaluate = parent.train, parent.evaluate
original_metadata, original_load, seed = parent.metadata, parent.load, parent.seed
DecisionPPOTrainer, PPOConfig = parent.DecisionPPOTrainer, parent.PPOConfig


def metadata(settings, pins, *, fit_steps=1000):
    import copy
    result = original_metadata(settings,pins,fit_steps=fit_steps)
    result['cost_prior'] = copy.deepcopy(rt.COST_PRIOR)
    return result


def load(trainer, path, settings):
    import torch
    saved = torch.load(path,map_location='cpu',weights_only=False)['metadata']
    if saved.get('cost_prior') != rt.COST_PRIOR:
        raise ValueError('Own V6 cost prior metadata required')
    return original_load(trainer,path,settings)


parent.metadata, parent.load = metadata, load


def compare_initial(out):
    import torch
    result = {}
    for name in ('fresh.pt','fit.pt'):
        own = torch.load(Path(out)/name,map_location='cpu',weights_only=False)
        previous = torch.load(rt.SOURCE/'runs/fit'/name,map_location='cpu',weights_only=False)
        assert own['model'].keys() == previous['model'].keys()
        unequal = [key for key in own['model'] if not torch.equal(own['model'][key],previous['model'][key])]
        controlled = sorted(rt.COST_PRIOR['tensors'])
        assert sorted(unequal) == controlled and len(own['model']) == 71
        assert all(torch.count_nonzero(own['model'][key]).item() == 0 for key in controlled)
        result[name] = dict(full_model_exact=False, unchanged_tensor_count=69,tensor_count=71,
            controlled_differences=controlled,zero_cost_head=True,old_checkpoint_loaded_into_model=False,
            own_sha=rt.base.sha(Path(out)/name),reference_sha=rt.base.sha(rt.SOURCE/'runs/fit'/name))
    rt.base.write(Path(out)/'initial_tensor_equality.json',result)
    return result


def fit(capture, settings, pins, out):
    parent.fit(capture,settings,pins,out)
    compare_initial(out)
