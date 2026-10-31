"""봉인된 V4 루프를 별도 모듈에 로드하여 새 보상 계약으로만 실행한다."""
import importlib.util
import sys
import runtime as rt

# V4 파일의 import runtime을 이번 모듈에만 결합하고 전역 alias를 즉시 복원한다.
spec = importlib.util.spec_from_file_location('settlement_v5_parent_learn', rt.SOURCE/'learn.py')
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
metadata, load, seed = parent.metadata, parent.load, parent.seed
DecisionPPOTrainer, PPOConfig = parent.DecisionPPOTrainer, parent.PPOConfig


def fit(capture, settings, pins, out):
    # 상이한 보상 계약 때문에 V4를 load하지 않는다. 저장된 tensor만 읽어 초기 동일성을 검증한다.
    parent.fit(capture, settings, pins, out)
    import torch
    from pathlib import Path
    result = {}
    for name in ('fresh.pt', 'fit.pt'):
        own = torch.load(Path(out)/name, map_location='cpu', weights_only=False)
        previous = torch.load(rt.SOURCE/'runs/fit'/name, map_location='cpu', weights_only=False)
        assert own['model'].keys() == previous['model'].keys()
        unequal = [key for key in own['model'] if not torch.equal(own['model'][key], previous['model'][key])]
        result[name] = dict(exact=not unequal, tensor_count=len(own['model']), unequal=unequal,
            own_sha=rt.base.sha(Path(out)/name), reference_sha=rt.base.sha(rt.SOURCE/'runs/fit'/name),
            old_checkpoint_loaded_into_model=False)
    rt.base.write(Path(out)/'initial_tensor_equality.json', result)
    assert all(row['exact'] for row in result.values()), 'Fresh/fit tensors differ from frozen V4'
