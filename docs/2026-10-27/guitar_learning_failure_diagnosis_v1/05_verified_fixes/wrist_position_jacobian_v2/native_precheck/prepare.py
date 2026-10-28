"""Final CPU preparation only after root declares active v2 implementation complete."""
import argparse
import copy
import json
import io
import unittest
from pathlib import Path
import sys

from common import HERE, ROOT, OLD, OLD_INITIAL, reused, sha, write
from safety_check import check
import run_probe
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--active-complete', action='store_true')
    args = parser.parse_args()
    if not args.active_complete:
        raise ValueError('Wait for root active implementation completion; no final seal yet')
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner, runtime, wrist
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_teacher, read_reference
    assert not torch.cuda.is_available()
    torch.set_num_threads(1)
    assert wrist.WRIST_CONTROL['schema'].endswith('.v2'), 'Current v2 implementation required'
    original_wrist = copy.deepcopy(wrist.WRIST_CONTROL)
    old_settings = json.loads((OLD/'runs/index_initial/settings.json').read_text())
    settings = runner.make_settings(argparse.Namespace(teacher=str(OLD/'teacher_index_row1.json'), mode='incremental',
        initial_std=.1711710544767014, song='05_BN2-131-B_solo', size='large', seed=7, num_envs=4,
        horizon=32, updates=1, save_every=50))
    normalized = copy.deepcopy(settings)
    normalized['song']['short_learning']['wrist_control'] = old_settings['song']['short_learning']['wrist_control']
    assert normalized == old_settings, 'Only current wrist contract may differ'
    spec = settings['song']['short_learning']
    assert read_teacher(OLD/'teacher_index_row1.json') == spec['teacher']
    reference = read_reference(OLD/'reference_index_row1.json', spec)
    old_model = torch.load(OLD_INITIAL, map_location='cpu', weights_only=False)
    rejected = False
    try:
        runner._validate_pins(old_model['metadata'])
    except ValueError:
        rejected = True
    assert rejected, 'Old checkpoint source validation must remain strict'
    metadata, _ = fixture(4)
    environment = runtime.ShortEnvironment(metadata, bundle=settings['song_training']['bundle'],
        song=settings['song'], skill=settings['finger_skill'], device='cpu')
    torch.manual_seed(7)
    policy = runtime.ShortPolicy(contract=environment.contract, size='large')
    same = {k: bool(torch.equal(v, policy.state_dict()[k])) for k,v in old_model['model'].items()}
    assert set(old_model['model']) == set(policy.state_dict()) and len(same) == 73 and all(same.values())
    safety = check()
    safety_runtime_imported = safety.pop('active_runtime_imported')
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        'guitar_learning.tests.test_wrist_position_jacobian', 'guitar_learning.tests.test_short_finger_learning'])
    test_log = io.StringIO()
    test_result = unittest.TextTestRunner(stream=test_log, verbosity=2).run(suite)
    if not test_result.wasSuccessful():
        write(HERE/'math_test_failure.json', dict(tests_run=test_result.testsRun, log=test_log.getvalue()))
        raise AssertionError('Current wrist math/short-learning CPU tests failed; log preserved')
    with (HERE/'math_validation.txt').open('x') as stream:
        stream.write(test_log.getvalue())
    verification = dict(**safety, active_runtime_imported=True,
        safety_check_active_runtime_imported=safety_runtime_imported, current_wrist_contract=original_wrist,
        only_settings_change='short_learning.wrist_control', current_teacher_reference_valid=True,
        old_checkpoint_source_strict_rejected=True, initial_model_comparison=same,
        all73_CPU_seed7_model_tensors_equal=True, current_math_and_short_tests_passed=test_result.testsRun,
        scope='CPU model values only; no old full trainer load or native outcome claimed; current native complete strict load mandatory',
        CUDA_initialized=torch.cuda.is_initialized())
    assert not verification['CUDA_initialized'] and wrist.WRIST_CONTROL == original_wrist
    write(HERE/'cpu_verification.json', verification)
    inputs = HERE/'cpu_inputs'; inputs.mkdir()
    write(inputs/'settings.json', settings)
    extras = [ROOT/'guitar_learning/tests/fixtures/wrist_position_jacobian_native_v1.npz', OLD_INITIAL, OLD/'teacher_index_row1.json', OLD/'reference_index_row1.json',
        *map(Path, spec['teacher']['source_evidence']), *map(Path, reference['source_evidence'])]
    names = ('common.py','child.py','run_probe.py','prepare.py','safety_check.py','PLAN.md','README.md',
        'safety_verification.json','dry_run.json','cpu_verification.json','math_validation.txt')
    extras.extend(HERE/name for name in names)
    pins = runner._pins(settings, inputs, extras)
    assert all(Path(p).is_file() and sha(p) == h for p,h in pins.items())
    write(HERE/'preparation_seal.json', dict(independent_review='pending', wrist_control=original_wrist, input_pins=pins,
        controls=['reference','zero','random'], episodes_per_condition=4,
        own_initial=str(HERE/'runs/index_initial/initial.pt'), scope='fresh current source only; no old checkpoint bypass'))
    print(json.dumps(dict(CPU_only=True, source_pins=len(pins), old_checkpoint_strict_rejected=True,
        seed7_initial_equal_tensors=73, GPU_executed=False)))


if __name__ == '__main__':
    main()
