"""CPU audit of actual small GPU runs; no native imports or GPU execution."""
from pathlib import Path
import copy
import gzip
import hashlib
import json
import random
from types import SimpleNamespace

import numpy as np
import torch

from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.training.ppo import PPOTrainer, PPOConfig


PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]


def same(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and np.array_equal(a, b)
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def finite(value):
    if isinstance(value, torch.Tensor):
        assert torch.isfinite(value).all()
        return 1
    if isinstance(value, dict):
        return sum(finite(v) for v in value.values())
    if isinstance(value, (tuple, list)):
        return sum(finite(v) for v in value)
    return 0


def load(path):
    return torch.load(path, map_location='cpu', weights_only=False)


def main():
    torch.set_num_threads(1)
    result = dict(scope='Short GPU integration and strict restore; not song performance or learned naturalness', runs={})
    for name, transitions, updates in [('gpu_smoke2', 1024, 2), ('gpu_resume1', 512, 3)]:
        run = PHASE/name
        report = json.loads((run/'report.json').read_text())
        assert report['completed'] and report['lifecycle_verified']
        assert report['failure'] is None and not report['cleanup_errors']
        assert not report['changed_inputs'] and not report['missing_import_pins']
        assert report['transitions'] == transitions and report['optimizer_updates'] == updates
        journal = report['journal']
        assert all(journal[k] == transitions for k in ('sampled', 'logged', 'durable', 'committed'))
        assert journal['closed'] and not journal['failed'] and not journal['discarded']
        with gzip.open(run/'transitions.jsonl.gz', 'rt') as stream:
            rows = [json.loads(line) for line in stream]
        assert len(rows)*16 == transitions
        assert not any(any(r['terminated']) or any(r['truncated']) for r in rows)
        means = []
        for path in sorted(run.glob('update_*.json')):
            row = json.loads(path.read_text())
            components = row['reward_component_means']
            for key in ('song_finger_coordination', 'song_finger_standby'):
                assert 0 < components[key] <= .05/60+1e-8
            assert abs(sum(components.values())-row['mean_reward']) < 1e-7
            means.append({k:components[k] for k in ('song_finger_coordination', 'song_finger_standby')})
        checkpoint = load(run/'final.pt')
        counts = {key:finite(checkpoint[key]) for key in ('model','actor_optimizer','value_optimizer')}
        assert checkpoint['updates'] == updates
        assert checkpoint['model']['left_curriculum_state'].shape == (3331,)
        assert checkpoint['identity']['architecture']['contract']['reward']['schema'].endswith('.v5')
        result['runs'][name] = dict(transitions=transitions, optimizer_updates=updates, rows=len(rows),
            finite_tensor_counts=counts, new_reward_component_means=means, physical_failures=0,
            checkpoint_sha256=hashlib.sha256((run/'final.pt').read_bytes()).hexdigest())
    saved = load(PHASE/'gpu_smoke2/final.pt')
    restored = load(PHASE/'gpu_resume1/initial.pt')
    keys = ('identity','model','actor_optimizer','value_optimizer','cost_weight','updates',
            'torch_rng','numpy_rng','python_rng','cuda_rng')
    assert all(same(saved[k],restored[k]) for k in keys)
    final = load(PHASE/'gpu_resume1/final.pt')
    assert not same(final['model'], restored['model'])
    for k in ('actor_optimizer','value_optimizer'):
        assert not same(final[k],restored[k])
    result['exact_restore'] = list(keys)
    old_path = ROOT/'docs/2026-10-22/guitar_learning_long_training_v4/training/final.pt'
    if not old_path.is_file():
        candidates = list((ROOT/'docs/2026-10-22/guitar_learning_long_training_v4').glob('*/final.pt'))
        assert len(candidates)==1, candidates
        old_path = candidates[0]
    old = load(old_path)
    contract = saved['identity']['architecture']['contract']
    settings = json.loads((PHASE/'gpu_smoke2/settings.json').read_text())
    policy = SpecialistPolicy(512,size='large',contract=contract,role='left',frozen_partner=False)
    CurriculumCoordinator(policy, SimpleNamespace(environment=SimpleNamespace(finger_counts=[25,18,12,12])))
    trainer = PPOTrainer(policy,PPOConfig(**settings['ppo']))
    # Match old PPO configuration so the reward/architecture contract is the rejection cause.
    trainer.config = PPOConfig(**old['identity']['config'])
    assert old['identity']['architecture']['contract']['reward']['schema'].endswith('.v4')
    snapshots = copy.deepcopy((policy.state_dict(),trainer.actor_optimizer.state_dict(),
        trainer.value_optimizer.state_dict(),torch.get_rng_state(),np.random.get_state(),random.getstate()))
    try:
        trainer.load(old_path)
    except ValueError as error:
        rejection = str(error)
        assert rejection == 'own schema/architecture/input/control/config mismatch'
    else:
        raise AssertionError('old rewardv4 checkpoint accepted')
    after = (policy.state_dict(),trainer.actor_optimizer.state_dict(),trainer.value_optimizer.state_dict(),
        torch.get_rng_state(),np.random.get_state(),random.getstate())
    assert same(snapshots,after)
    result['old_v4_rejected_without_mutation'] = dict(path=str(old_path),reason=rejection,
        sha256=hashlib.sha256(old_path.read_bytes()).hexdigest())
    source = json.loads((PHASE/'tested_source_manifest.json').read_text())['source']
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in source.items())
    result['active_source_unchanged_since_freeze'] = len(source)
    (PHASE/'training_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: GPU2 updates + exact restore + GPU1 update, strict v4 rejection, source unchanged')


if __name__ == '__main__':
    main()
