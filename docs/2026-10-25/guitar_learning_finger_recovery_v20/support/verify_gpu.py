"""Check native recovery recording, strict resume, and frozen control contracts."""
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace

PHASE = Path(__file__).resolve().parents[1]
ROOT = PHASE.parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np
import torch
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.training.gpu_log_records import iter_episode_rows
from guitar_learning.training.ppo import PPOConfig, PPOTrainer
from guitar_learning.tool.inspect_gpu_training_log import inspect

torch.set_num_threads(1)


def load(path):
    return torch.load(path, map_location='cpu', weights_only=False)


def equal(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and np.array_equal(a, b)
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return type(a) == type(b) and len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def main():
    result = dict(schema='guitar_learning.finger_recovery_gpu_verification.v1', runs={})
    old_run = ROOT/'docs/2026-10-25/guitar_learning_press_acquisition_v1/gpu_v19'
    previous = json.loads((old_run/'training_contract.json').read_text())
    current = json.loads((PHASE/'gpu_A/training_contract.json').read_text())
    for name in ('action', 'termination', 'native_backend'):
        assert previous[name] == current[name], name
    expected_task = copy.deepcopy(previous['task'])
    expected_task['song']['finger_recovery'] = current['reward']['finger_recovery']
    assert expected_task == current['task'], 'Only explicit recovery config may be added to task settings'
    for name in ('surface_learning', 'finger_tracking', 'action_change', 'wrist_region'):
        assert previous['reward'][name] == current['reward'][name], name
    assert current['observation']['dimension'] == 544
    assert current['observation']['event_dim'] == 24
    assert current['observation']['priority_slots'] == 8
    for name in ('gpu/control.py', 'gpu/scene.py', 'core/finger_control.py', 'training/ppo.py'):
        path = ROOT/'guitar_learning'/name
        before = ROOT/'guitar_learning/archive/20261025_before_finger_recovery_v20/guitar_learning'/name
        assert path.read_bytes() == before.read_bytes(), name
    result['unchanged_physics_control_success_PPO'] = True
    old_initial = load(old_run/'initial.pt')
    new_initial = load(PHASE/'gpu_A/initial.pt')
    assert equal(old_initial['model'], new_initial['model'])
    result['same_seed_small_initial_model_exact'] = True
    for folder, shape_rate in (('gpu_A', 0.), ('gpu_B', .004)):
        run = PHASE/folder
        result['runs'][folder] = inspect(run)
        contract = json.loads((run/'training_contract.json').read_text())
        assert contract['reward']['schema'] == 'guitar_learning.gpu_tensor_song_reward.v20'
        assert contract['reward']['finger_recovery']['shape_rate_per_s'] == shape_rate
        episodes = [r['episode'] for r in iter_episode_rows(run)]
        assert {e['env_id'] for e in episodes} == set(range(16)), 'Each environment must have ended at least one episode'
        for e in episodes:
            d = e['left_episode_diagnostics']
            assert d['schema'] == 'guitar_learning.gpu_left_episode_diagnostics.v3'
            assert len(d['recovery']['by_finger']) == 4
            assert 'full_gate_runs' in d['standby']
            for metric, term in (('standby', 'song_finger_standby'), ('shape', 'song_finger_coordination')):
                key = 'weighted_'+('standby' if metric == 'standby' else 'shape')+'_reward'
                assert abs(sum(d[metric][key])-e['reward_components'][term]) < 1e-5
            for f in d['recovery']['by_finger']:
                assert 0 <= f['credited_in_band_fraction'] <= 1+1e-8
                assert f['complete_windows']+f['incomplete_or_unobserved_windows'] == f['planned_windows']
                assert f['return_within3s_windows'] <= f['complete_windows']
            if shape_rate == 0:
                assert e['reward_components']['song_finger_coordination'] == 0
        result['runs'][folder]['diagnostic_reward_ledger_exact_within_1e_minus5'] = True
    source = load(PHASE/'gpu_A/final.pt')
    initial = load(PHASE/'gpu_A_resume/initial.pt')
    final = load(PHASE/'gpu_A_resume/final.pt')
    restored = {k: equal(source[k], initial[k]) for k in source if k != 'metadata'}
    assert all(restored.values()), restored
    assert (initial['updates'], final['updates']) == (65, 66)
    changed = {k: not equal(initial[k], final[k]) for k in ('model', 'actor_optimizer', 'value_optimizer')}
    assert all(changed.values())
    result['resume_nonmetadata_exact'] = restored
    result['resumed_update_changed'] = changed
    settings = json.loads((PHASE/'gpu_A/settings.json').read_text())
    episodes = [r['episode'] for r in iter_episode_rows(PHASE/'gpu_A')]
    counts = [f['target_count'] for f in episodes[0]['left_curriculum']['finger_metrics']]
    policy = SpecialistPolicy(544, size='small', role='left', contract=current)
    CurriculumCoordinator(policy, SimpleNamespace(environment=SimpleNamespace(finger_counts=counts)))
    trainer = PPOTrainer(policy, PPOConfig(**settings['ppo']))
    def state():
        return copy.deepcopy((policy.state_dict(), trainer.actor_optimizer.state_dict(),
            trainer.value_optimizer.state_dict(), trainer.updates, trainer.cost_weight,
            torch.get_rng_state(), np.random.get_state(), random.getstate()))
    before = state()
    for rejected in (old_run/'final.pt', PHASE/'gpu_B/final.pt'):
        try:
            trainer.load(rejected)
        except ValueError as error:
            assert 'mismatch' in str(error)
        else:
            raise AssertionError('Different reward/option contract must be rejected: '+str(rejected))
        assert equal(before, state())
    result['actual_v19_rejected_without_state_mutation'] = True
    result['actual_v20_shape_option_mismatch_rejected_without_state_mutation'] = True
    for folder in ('gpu_A_resume', 'gpu_large1024'):
        result['runs'][folder] = inspect(PHASE/folder)
    result['verified'] = True
    result['scope'] = 'Implementation, native GPU recording and strict resume; no posture efficacy or convergence claim'
    (PHASE/'gpu_verification.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
