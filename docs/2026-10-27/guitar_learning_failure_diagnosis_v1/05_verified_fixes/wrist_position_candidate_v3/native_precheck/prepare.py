"""CPU-only readers, exact settings, initial model and fixed original-CLI plan checks."""
import json
import copy
import io
import unittest
from pathlib import Path
import sys
import tempfile

import run_precheck as run


def main():
    sys.path.insert(0, str(run.ROOT))
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.__main__ import parser
    from guitar_learning.tool.experiments.short_finger_learning import runner, runtime
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    from guitar_learning.tool.experiments.short_finger_learning.wrist import WRIST_CONTROL
    baseline = run.reused().original()
    assert not torch.cuda.is_available() and WRIST_CONTROL['schema'].endswith('.v3')
    run.reject_existing(run.HERE/'runs')
    plan = run.jobs()
    assert len(plan) == 8 and len({j['out'] for j in plan}) == 8
    assert [j['name'] for j in plan] == [f+'_'+c for f in run.FINGERS for c in ('initial', 'reference', 'zero', 'random')]
    inputs = run.HERE/'cpu_inputs'; inputs.mkdir()
    settings_by_finger, references, hashes = {}, {}, {}
    evidence = set()
    for finger in run.FINGERS:
        group = [j for j in plan if j['finger'] == finger]
        args = parser().parse_args(group[0]['args'][group[0]['args'].index(baseline.MODULE)+1:])
        settings = runner.make_settings(args)
        spec = settings['song']['short_learning']
        assert settings['num_envs'] == 4 and settings['updates'] == 1 and settings['horizon'] == 32
        assert settings['seed'] == 7 and settings['size'] == 'large' and settings['checkpoint_every'] == 50
        assert spec['schema'] == 'guitar_learning.short_finger_learning.v2'
        assert spec['wrist_control'] == WRIST_CONTROL and spec['teacher']['ramp_s'] == 2 and spec['view']['local_onset_s'] == 3
        ref_job = group[1]
        reference_path = Path(ref_job['args'][ref_job['args'].index('--reference')+1])
        reference = read_reference(reference_path, spec)
        assert len(reference['selected_targets_rad']) == 4
        references[finger] = dict(path=str(reference_path), sha256=baseline.sha(reference_path),
            target_id=spec['teacher']['source_target_id'], finger=spec['finger'])
        for job in group[1:]:
            evaluated = parser().parse_args(job['args'][job['args'].index(baseline.MODULE)+1:])
            assert evaluated.episodes == 4 and Path(evaluated.checkpoint) == inputs.parent/'runs'/(finger+'_initial')/'initial.pt'
            assert evaluated.control == job['control']
        metadata, snapshot = fixture(4)
        env = runtime.ShortEnvironment(metadata, bundle=settings['song_training']['bundle'],
            song=settings['song'], skill=settings['finger_skill'], device='cpu')
        observation = env.reset(range(4), snapshot)
        torch.manual_seed(7)
        policy = runtime.ShortPolicy(contract=env.contract, size='large')
        assert len(policy.state_dict()) == 73 and observation['state'].shape == (4, 561)
        hashes[finger] = run.model_hash(policy.state_dict())
        previous_base = (run.DIAG/'05_verified_fixes/wrist_position_jacobian_v2/native_precheck'
            if finger == 'index' else run.PREVIOUS)
        old_settings = baseline.read(previous_base/'runs'/(finger+'_initial')/'settings.json')
        normalized = copy.deepcopy(settings)
        normalized['song']['short_learning']['wrist_control'] = old_settings['song']['short_learning']['wrist_control']
        assert normalized == old_settings, 'Only wrist control contract may change'
        previous_control = old_settings['song']['short_learning']['wrist_control']
        for key in ('ramp_s','policy_onset_s','rotation_length_scale_m','damping','correction_step_rad',
                    'correction_rate_bound_rad_s','target_bounds','requested_target_rate','jacobian_coordinates',
                    'jacobian_groups','jacobian_basis'):
            assert WRIST_CONTROL[key] == previous_control[key], key
        old_checkpoint = previous_base/'runs'/(finger+'_initial')/'initial.pt'
        old_payload = torch.load(old_checkpoint, map_location='cpu', weights_only=False)
        assert set(old_payload['model']) == set(policy.state_dict()) and len(old_payload['model']) == 73
        assert run.model_hash(old_payload['model']) == hashes[finger]
        rejected = False
        try: runner._validate_pins(old_payload['metadata'])
        except ValueError: rejected = True
        assert rejected, 'Old v2 checkpoint must be rejected under current v3 source'
        evidence.add(old_checkpoint)
        baseline.write(inputs/(finger+'_settings.json'), settings)
        settings_by_finger[finger] = settings
        evidence.update(map(Path, spec['teacher']['source_evidence']))
        evidence.update(map(Path, reference['source_evidence']))
        evidence.update((Path(spec['teacher']['input_path']), reference_path))
    assert len(set(hashes.values())) == 1
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'output'
        path.mkdir()
        try: run.reject_existing(path)
        except FileExistsError: pass
        else: raise AssertionError('Existing output accepted')
        link = Path(temp)/'dangling'; link.symlink_to(Path(temp)/'missing')
        try: run.reject_existing(link)
        except FileExistsError: pass
        else: raise AssertionError('Dangling output symlink accepted')
    scope_suite = unittest.defaultTestLoader.loadTestsFromNames([
        'guitar_learning.tests.test_short_finger_learning.ShortLearningTests.test_evaluation_trace_saves_candidate_and_contract_scopes',
        'guitar_learning.tests.test_short_finger_learning.ShortLearningTests.test_checkpoint_contract_mode_and_mask_strict'])
    scope_log = io.StringIO()
    scope_result = unittest.TextTestRunner(stream=scope_log, verbosity=2).run(scope_suite)
    with (run.HERE/'field_scope_cpu_tests.txt').open('x') as stream:stream.write(scope_log.getvalue())
    assert scope_result.wasSuccessful() and scope_result.testsRun == 2
    baseline.write(run.HERE/'dry_run.json', dict(jobs=plan, GPU_executed=False, old_checkpoints_used=False))
    baseline.write(run.HERE/'cpu_verification.json', dict(CPU_only=True, GPU_executed=False, native_executed=False, active_runtime_imported=True,
        current_wrist_control=WRIST_CONTROL, parent_short_schema='guitar_learning.short_finger_learning.v2',
        previous_v2_checkpoint_source_strict_rejected=True, current_v2_contract_strict_rejected_CPU_test=True,
        candidate_trace_field='wrist_candidate_arm_rad', candidate_trace_width=12,
        candidate_trace_scope=WRIST_CONTROL['candidate_arm_scope'], requested_delta_scope=WRIST_CONTROL['requested_delta_scope'],
        CPU_trace_metadata_and_strict_contract_tests_passed=scope_result.testsRun,
        only_settings_change='wrist_control', original_PD_range_codec_reward_settings_preserved=True,
        original_cap_ramp_onset_Jacobian_math_contract_preserved=True, old73_model_value_only_equal=True, references=references, settings_exact_files=[str(inputs/(f+'_settings.json')) for f in run.FINGERS],
        CPU_initial73_model_sha256=hashes, state_dim=561, selected_action_count=4,
        output_existing_and_dangling_symlink_rejected=True, original_CLI_jobs=8,
        source_test_scope='upstream current-source tests/review are separate; this script audits precheck readers/settings/model/inputs',
        CUDA_initialized=torch.cuda.is_initialized(), scope='preparation only; no native outcome or learned performance'))
    assert not torch.cuda.is_initialized()
    evidence.update(run.HERE/p for p in ('run_precheck.py','prepare.py','skeleton_check.py','PLAN.md','README.md','dry_run.json','skeleton_verification.json','cpu_verification.json','field_scope_cpu_tests.txt'))
    evidence.update((Path(run.reused().__file__), Path(baseline.__file__), run.PREVIOUS/'run_regression.py',
        run.ROOT/'guitar_learning/tests/fixtures/wrist_position_jacobian_native_v1.npz',
        run.ROOT/'guitar_learning/README.md', run.ROOT/'guitar_learning/AGENTS.md'))
    evidence.update(inputs/(f+'_settings.json') for f in run.FINGERS)
    # _pins includes its output settings path; use the already-created middle settings under its original name.
    baseline.write(inputs/'settings.json', settings_by_finger['middle'])
    pins = runner._pins(settings_by_finger['middle'], inputs, evidence)
    active = {p:h for p,h in pins.items() if str(p).startswith(str(run.ROOT/'guitar_learning')+'/') and p.endswith('.py')}
    assert all(baseline.sha(p) == h for p,h in pins.items())
    baseline.write(run.HERE/'preparation_seal.json', dict(independent_review='pending', input_pins=pins,
        active_source_pins=active, wrist_control=WRIST_CONTROL, CPU_initial_model_sha256=hashes['middle'],
        planned_jobs=8, controls=['reference','zero','random'], episodes_per_condition=4,
        scope='CPU preparation only; wait for current v3 source freeze, independent prep review and root GPU handoff'))
    print(json.dumps(dict(CPU_only=True, jobs=8, input_pins=len(pins), CPU_initial73_equal=True, GPU_executed=False)))


if __name__ == '__main__':
    main()
