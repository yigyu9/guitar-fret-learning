"""One finite original-note pinky grid with the reviewed private0.25Nm cap."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PRELEARNING = HERE.parent/'low_effort_finger_prelearning_v1'
spec = importlib.util.spec_from_file_location('pinky_prelearning_source', PRELEARNING/'probe.py')
prior = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prior
spec.loader.exec_module(prior)
grid = prior.grid
cap = prior.cap
REVIEW = PRELEARNING/'analysis/results_v1/review.json'


def actual_gate():
    paths = prior.actual_gate()
    review = grid.read(REVIEW)
    assert review['verdict'] == 'PASS' and not review['findings']
    mapping = review['reviewed_sha256']
    assert mapping and all(Path(p).is_file() and grid.sha(p) == h for p, h in mapping.items())
    paths.update(map(Path, mapping)); paths.add(REVIEW)
    verification_path = REVIEW.parent/'verification.json'
    assert str(verification_path) in mapping
    verification = grid.read(verification_path)
    assert verification['completed']
    for name in ('input_sha256', 'verified_input_sha256'):
        values = verification[name]
        assert values and all(Path(p).is_file() and grid.sha(p) == h for p, h in values.items())
        paths.update(map(Path, values))
    launcher = PRELEARNING/'01_launcher.json'
    assert grid.read(launcher)['completed'] and grid.read(launcher)['returncode'] == 0
    assert len(grid.read(launcher)['children']) == 10
    paths.add(launcher)
    return paths


@contextmanager
def pinky_inputs():
    original_here = grid.HERE; original_inputs = grid.INPUTS
    grid.HERE = HERE; grid.INPUTS = dict(pinky=prior.INPUTS['pinky'])
    try:
        yield
    finally:
        grid.HERE = original_here; grid.INPUTS = original_inputs


def verify_scene(scene, source, declaration, count):
    import numpy as np
    actual = scene.pd_properties
    baseline = cap.expected_properties(source, actual.dtype)
    expected = baseline.copy(); expected['effort'][declaration['native_indices']] = cap.CAP
    assert np.array_equal(actual, expected)
    changes = {key: np.flatnonzero(actual[key] != baseline[key]).tolist() for key in actual.dtype.names}
    assert changes['effort'] == declaration['native_indices']
    assert all(not ids for key, ids in changes.items() if key != 'effort')
    reverted = copy.deepcopy(scene.contract)
    reverted['initial']['native_PD_properties']['effort'] = source['initial']['native_PD_properties']['effort']
    np.testing.assert_equal(reverted, source)
    assert 0 < count <= 225 and scene.num_envs == scene._hand_collision_readback_count == count
    assert scene.physics_steps == 0 and scene.hand_collision['enabled_distinct_finger_pairs'] == 90
    return dict(**declaration, environment_count=count, actual_native_PD105={k: actual[k].tolist() for k in actual.dtype.names},
        changed_native_field_indices=changes, expected_readback_exact=True,
        property_scope='Actual declared valid-grid count; full105 last-env readback, original constructor exact-checks every env; no hard4 verifier bypass')


@contextmanager
def controlled_pool(count):
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning import runtime
    original_pool = runtime.ShortPool
    original_loader = prepared_reset_v1.load_prepared_reset_contract
    cleanup_errors = []

    class PinkyPool(original_pool):
        def _create_scene(self, settings, out):
            calls = []; scene = None
            try:
                with cap.effort_loader(calls): scene = super()._create_scene(settings, out)
                assert prepared_reset_v1.load_prepared_reset_contract is original_loader and len(calls) == 1
                self.effort_readback = verify_scene(scene, *calls[0], count)
                return scene
            except BaseException:
                if scene is not None:
                    try: scene.close()
                    except BaseException as error: cleanup_errors.append(dict(type=type(error).__name__, message=str(error)))
                raise

        def __init__(self, settings, out):
            super().__init__(settings, out)
            try:
                expected = grid.read(PRELEARNING/'runs/pinky_reference/training_contract.json')
                expected['native_backend'].pop('diagnostic_native_effort')
                assert self.contract == expected  # Derived task/control invariant, not a new20Nm execution.
                assert np.array_equal(self.scene.effort_caps.cpu().numpy(), self.scene.pd_properties['effort'])
                assert torch.equal(self.controller.caps, self.scene.effort_caps)
                self.contract['native_backend']['diagnostic_native_effort'] = self.effort_readback
                grid.write(out/'native_effort_readback.json', self.effort_readback)
            except BaseException:
                try: self.close()
                except BaseException as error: cleanup_errors.append(dict(type=type(error).__name__, message=str(error)))
                raise

    runtime.ShortPool = PinkyPool
    try:
        yield cleanup_errors
    finally:
        runtime.ShortPool = original_pool
        assert prepared_reset_v1.load_prepared_reset_contract is original_loader


def prepare():
    assert not any(name in sys.modules for name in ('torch', 'numpy', 'isaacgym'))
    paths = actual_gate()
    assert not any(name in sys.modules for name in ('torch', 'numpy', 'isaacgym'))
    import numpy as np
    import torch
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.tests.test_gpu_control import fake_scene
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    from types import SimpleNamespace
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    cap.reject_existing(HERE/'cpu_inputs'); cap.reject_existing(HERE/'preparation_seal.json')
    source = load_prepared_reset_contract(); initial = source['initial']
    with pinky_inputs():
        provisional = grid.settings('pinky', 225); short = provisional['song']['short_learning']
        reference = read_reference(prior.INPUTS['pinky'][1], short); names = short['learned_action_names']
        ids = [initial['joint_names'].index(n) for n in names]
        lower = [initial['native_PD_properties']['lower'][i] for i in ids]
        upper = [initial['native_PD_properties']['upper'][i] for i in ids]
        document = grid.grid(reference['selected_targets_rad'], names, lower, upper)
        config = grid.settings('pinky', document['valid_count'])
    scene, _ = fake_scene(1, dtype=torch.float32); controller = BatchedController(scene, finger_action_mode='incremental')
    actions = [ACTIVE_NAMES.index(n) for n in names]
    torch.testing.assert_close(controller.action_low[actions], torch.tensor(lower), rtol=0, atol=2e-7)
    torch.testing.assert_close(controller.action_high[actions], torch.tensor(upper), rtol=0, atol=2e-7)
    assert config['song']['short_learning'] == short
    document.update(finger='pinky', joint_names=names, native_lower_rad=lower, native_upper_rad=upper,
        reference_path=str(prior.INPUTS['pinky'][1]), reference_sha256=grid.sha(prior.INPUTS['pinky'][1]),
        source_target_id=short['teacher']['source_target_id'], criterion=grid.CRITERION)
    private, declaration = cap.private_contract(source)
    dtype = np.dtype([(n, np.bool_ if n == 'hasLimits' else np.int32 if n == 'driveMode' else np.float32)
        for n in initial['native_PD_properties']])
    native = cap.expected_properties(source, dtype); native['effort'][declaration['native_indices']] = cap.CAP
    fixture = SimpleNamespace(pd_properties=native.copy(), contract=private, num_envs=document['valid_count'],
        _hand_collision_readback_count=document['valid_count'], physics_steps=0, hand_collision=dict(enabled_distinct_finger_pairs=90))
    assert verify_scene(fixture, source, declaration, document['valid_count'])['expected_readback_exact']
    fixture.pd_properties['effort'][declaration['native_indices'][0]] = 20.
    try: verify_scene(fixture, source, declaration, document['valid_count'])
    except AssertionError: pass
    else: raise AssertionError('Bad native readback accepted')
    original_here = grid.HERE; original_inputs = grid.INPUTS
    try:
        with pinky_inputs(): raise RuntimeError('CPU injected input-scope failure')
    except RuntimeError as error: assert str(error) == 'CPU injected input-scope failure'
    assert grid.HERE is original_here and grid.INPUTS is original_inputs
    inputs = HERE/'cpu_inputs'; inputs.mkdir()
    grid.write(inputs/'pinky_grid.json', document); grid.write(inputs/'pinky_settings.json', config)
    grid.write(inputs/'settings.json', config)
    grid.write(HERE/'cpu_verification.json', dict(CPU_only=True, GPU_executed=False, declared_rows=225,
        valid_count=document['valid_count'], detailed_grid_indices=document['executed_detail_grid_indices'],
        controller_native_bounds_exact=True, source_alias_restore_after_error=True,
        native_property_good_bad_checked=True, pre_native_gate_stdlib_only=True, no_NN_checkpoint=True))
    paths.update((Path(__file__), HERE/'PLAN.md', HERE/'cpu_verification.json'))
    paths.update(inputs.glob('*.json'))
    pins = runner._pins(config, inputs, paths)
    grid.write(HERE/'preparation_seal.json', dict(independent_review='pending', input_pins=pins,
        valid_count=document['valid_count'], scope='One finite pinky grid; scripted only; root GPU after independent preparation review'))
    print(dict(CPU_only=True, pins=len(pins), valid_count=document['valid_count']))


def launch():
    out = HERE/'runs/pinky'; cap.reject_existing(out)
    seal = grid.read(HERE/'preparation_seal.json')
    assert seal['independent_review'] == 'passed_no_findings'
    assert all(Path(p).is_file() and grid.sha(p) == h for p, h in seal['input_pins'].items())
    paths = actual_gate(); runtime_seal = copy.deepcopy(seal)
    for path in paths | {HERE/'preparation_seal.json'}: runtime_seal['input_pins'][str(path)] = grid.sha(path)
    count = grid.read(HERE/'cpu_inputs/pinky_grid.json')['valid_count']
    assert count == seal['valid_count']
    import isaacgym
    cleanup_errors = []
    try:
        with pinky_inputs(), controlled_pool(count) as cleanup_errors:
            grid.execute('pinky', out, runtime_seal)
    finally:
        if out.is_dir():
            scene = grid.read(out/'gpu_scene_final.json') if (out/'gpu_scene_final.json').is_file() else {}
            valid = (scene.get('closed') is True and scene.get('environment_count') == count
                and scene.get('hand_collision_native_readback_environments') == count
                and scene.get('hand_collision', {}).get('enabled_distinct_finger_pairs') == 90
                and scene.get('diagnostic_guitar_mode') == 'fixed' and scene.get('physx_use_gpu') is True
                and scene.get('use_gpu_pipeline') is True)
            grid.write(out/'pinky_grid_lifecycle.json', dict(scene_valid=valid, cleanup_errors=cleanup_errors,
                input_and_pool_scopes_restored=True, declared_valid_count=count))
            if sys.exc_info()[0] is None and (not valid or cleanup_errors): raise RuntimeError('Pinky grid lifecycle failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true'); group.add_argument('--execute', action='store_true')
    args = parser.parse_args(); sys.path.insert(0, str(grid.ROOT))
    if args.prepare: prepare()
    else: launch()
