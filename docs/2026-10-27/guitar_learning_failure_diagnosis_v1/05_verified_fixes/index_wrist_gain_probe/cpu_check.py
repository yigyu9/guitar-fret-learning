"""Single-cap settings, exact initialization and unchanged strict-loader checks."""
import argparse
import ast
import copy
import json
from pathlib import Path
import tempfile

import child
import run_probe


def main():
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runner import make_settings
    from guitar_learning.tool.experiments.short_finger_learning import runtime, wrist
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig

    assert not torch.cuda.is_available()
    torch.set_num_threads(1)
    baseline = run_probe.reused().original()
    old_seal = baseline.read(run_probe.OLD/'preparation_seal.json')
    assert all(baseline.sha(p) == h for p, h in old_seal['input_sha256'].items())
    plan, original_jobs = run_probe.jobs(), run_probe.reused().jobs()[:4]
    assert len(plan) == 4 and [j['name'] for j in plan] == ['index_initial', 'index_reference', 'index_zero', 'index_random']
    # Reverse only the two declared CLI substitutions to prove job reuse.
    for job, original_job in zip(plan, original_jobs):
        restored = copy.deepcopy(job)
        restored['out'] = restored['out'].replace(str(child.HERE/'runs'), str(run_probe.OLD/'runs'))
        command = restored['args']
        where = command.index(str(child.HERE/'child.py'))
        command[where:where+1] = ['-m', run_probe.reused().MODULE]
        restored['args'] = [v.replace(str(child.HERE/'runs'), str(run_probe.OLD/'runs')) for v in command]
        assert restored == original_job
    args = argparse.Namespace(teacher=str(run_probe.OLD/'teacher_index_row1.json'), mode='incremental',
        initial_std=.1711710544767014, song='05_BN2-131-B_solo', size='large', num_envs=4,
        horizon=32, updates=1, save_every=50, seed=7)
    original_control = copy.deepcopy(wrist.WRIST_CONTROL)
    original_settings = make_settings(args)
    metadata, _ = fixture(1)
    old_env = runtime.ShortEnvironment(metadata, bundle=original_settings['song_training']['bundle'],
        song=original_settings['song'], skill=original_settings['finger_skill'], device='cpu')
    torch.manual_seed(7)
    old_policy = runtime.ShortPolicy(contract=old_env.contract, size='large')
    same_rng = torch.get_rng_state().clone()
    with child.patched_control() as expected:
        assert runtime.WRIST_CONTROL is wrist.WRIST_CONTROL and wrist.WRIST_CONTROL == expected
        changed = [k for k in original_control if original_control[k] != expected[k]]
        assert sorted(changed) == ['correction_rate_bound_rad_s', 'correction_step_rad', 'schema']
        assert np.isclose(expected['correction_step_rad']/original_control['correction_step_rad'], .2)
        settings = make_settings(args)
        normalized = copy.deepcopy(settings)
        normalized['song']['short_learning']['wrist_control'] = original_control
        assert normalized == original_settings
        env = runtime.ShortEnvironment(metadata, bundle=settings['song_training']['bundle'],
            song=settings['song'], skill=settings['finger_skill'], device='cpu')
        normalized_contract = copy.deepcopy(env.contract)
        normalized_contract['task']['short_learning']['wrist_control'] = original_control
        normalized_contract['task']['song']['short_learning']['wrist_control'] = original_control
        assert normalized_contract == old_env.contract
        torch.manual_seed(7)
        policy = runtime.ShortPolicy(contract=env.contract, size='large')
        assert torch.equal(torch.get_rng_state(), same_rng)
        assert len(policy.state_dict()) == 73
        assert all(torch.equal(v, policy.state_dict()[k]) for k, v in old_policy.state_dict().items())
        actual_path = run_probe.OLD/'runs/index_initial/initial.pt'
        actual = torch.load(actual_path, map_location='cpu', weights_only=False)
        assert actual['updates'] == 0 and all(torch.equal(v, policy.state_dict()[k]) for k, v in actual['model'].items())
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        with tempfile.TemporaryDirectory(prefix='index_wrist_cap_') as folder:
            p = Path(folder)/'probe.pt'
            trainer.save(p, metadata=dict(cpu_only=True))
            restored = runtime.ShortPolicy(contract=env.contract, size='large')
            DecisionPPOTrainer(restored, PPOConfig(**settings['ppo'])).load(p)
            rejected = False
            try:
                DecisionPPOTrainer(old_policy, PPOConfig(**original_settings['ppo'])).load(p)
            except ValueError:
                rejected = True
            assert rejected
        j = torch.zeros(1, 6, 12); j[0, :, :6] = torch.eye(6)
        z = torch.zeros(1, 12)
        _, _, delta = wrist.bounded_wrist_target(z, z, z, j, torch.full((1, 6), 100.),
            torch.ones(1, dtype=torch.bool), torch.full((12,), -2.), torch.full((12,), 2.), torch.full((12,), 3.))
        assert torch.allclose(delta[0, :6], torch.full((6,), expected['correction_step_rad']))
        assert torch.count_nonzero(delta[0, 6:]) == 0
    assert wrist.WRIST_CONTROL == original_control and runtime.WRIST_CONTROL == original_control
    assert not torch.cuda.is_initialized() and not (child.HERE/'runs').exists()
    for path in (child.HERE/'child.py', child.HERE/'run_probe.py', Path(__file__)):
        ast.parse(path.read_text(), feature_version=(3, 8))
    verification = dict(CPU_only=True, GPU_executed=False, CUDA_initialized=False,
        changed_control_fields=changed, only_settings_contract_change='wrist_control schema/step/rate',
        correction_cap_deg=.1, jobs4_exact_except_child_and_output_paths=True,
        same_seed7_original_native_initial_tensors=73, same_seed7_CPU_initial_tensors=73,
        initialization_RNG_same=True, original_initial_checkpoint=str(actual_path),
        original_initial_sha256=baseline.sha(actual_path), original_preparation_pins_verified=len(old_seal['input_sha256']),
        strict_same_new_contract_load=True, strict_original_contract_rejected=True,
        bounded_helper_actual_cap_checked=True, global_control_restored=True, python38_syntax=True,
        scope='CPU preparation only; new native initial73identity check remains mandatory in run_probe; no gain result or arrival guarantee')
    for name, value in (('cpu_verification.json', verification), ('dry_run.json', dict(jobs=plan, GPU_executed=False))):
        with (child.HERE/name).open('x') as f:
            json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')
    print(json.dumps(verification, ensure_ascii=False))


if __name__ == '__main__':
    main()
