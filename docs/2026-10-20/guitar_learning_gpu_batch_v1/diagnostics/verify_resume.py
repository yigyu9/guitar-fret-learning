"""Compare the saved strict-resume boundary without initializing CUDA."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import torch


def differences(a, b, path=''):
    if isinstance(a, torch.Tensor):
        return [] if isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b) else [path]
    if isinstance(a, np.ndarray):
        return [] if isinstance(b, np.ndarray) and np.array_equal(a, b) else [path]
    if isinstance(a, dict):
        if not isinstance(b, dict) or a.keys() != b.keys():
            return [path+'.keys']
        return [error for key in a for error in differences(a[key], b[key], path+'.'+str(key))]
    if isinstance(a, (tuple, list)):
        if type(a) is not type(b) or len(a) != len(b):
            return [path+'.length/type']
        return [error for i, (x, y) in enumerate(zip(a, b)) for error in differences(x, y, path+'.'+str(i))]
    return [] if a == b else [path]


def finite(value):
    if isinstance(value, torch.Tensor):
        return bool(torch.isfinite(value).all())
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    if isinstance(value, (tuple, list)):
        return all(finite(v) for v in value)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('before', type=Path)
    parser.add_argument('resumed', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    paths = [args.before, args.resumed, args.after]
    before, resumed, after = [torch.load(p, map_location='cpu', weights_only=False) for p in paths]
    fields = [key for key in before if key != 'metadata']
    diff = [error for key in fields for error in differences(before[key], resumed[key], key)]
    result = dict(schema='guitar_learning.gpu_resume_verification.v1',
        checkpoints={str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        boundary_exact_fields=fields, boundary_differences=diff,
        updates=[int(x['updates']) for x in (before, resumed, after)],
        final_finite=all(finite(after[k]) for k in ('model', 'actor_optimizer', 'value_optimizer')),
        curriculum_buffer_restored='left_curriculum_state' in before['model'] and
            not differences(before['model']['left_curriculum_state'], resumed['model']['left_curriculum_state']),
        actor_changed=bool(differences(before['model'], after['model'])),
        scope='model/optimizer/RNG/curriculum exact at resume boundary; physical episode intentionally restarted')
    result['passed'] = (not diff and result['final_finite'] and result['curriculum_buffer_restored'] and
                        result['actor_changed'] and after['updates'] > before['updates'])
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])


if __name__ == '__main__':
    main()
