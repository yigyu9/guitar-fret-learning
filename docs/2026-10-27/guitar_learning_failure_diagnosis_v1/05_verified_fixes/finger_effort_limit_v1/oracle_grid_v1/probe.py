"""Repeat the original finite scripted grid with the reviewed private finger16 effort cap."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CAP_ROOT = HERE.parent
spec = importlib.util.spec_from_file_location('grid_effort_diagnostic', CAP_ROOT/'probe.py')
cap = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cap
spec.loader.exec_module(cap)
grid = cap.parent
SCHEMA = 'diagnostic.same_grid_finger16_effort.v1'
ACTUAL_REVIEW = CAP_ROOT/'analysis/results_v1/review.json'
COUNTS = dict(index=135, middle=180)


def actual_gate():
    review = grid.read(ACTUAL_REVIEW)
    assert review['verdict'] == 'PASS' and not review['findings']
    paths = {ACTUAL_REVIEW}
    for mapping in (review['reviewed_sha256'],):
        assert mapping
        assert all(Path(p).is_file() and grid.sha(p) == h for p, h in mapping.items())
        paths.update(map(Path, mapping))
    verification_path = ACTUAL_REVIEW.parent/'verification.json'
    assert str(verification_path) in review['reviewed_sha256']
    verification = grid.read(verification_path)
    assert verification['completed']
    for name in ('input_sha256', 'verified_input_sha256'):
        mapping = verification[name]
        assert mapping and all(Path(p).is_file() and grid.sha(p) == h for p, h in mapping.items())
        paths.update(map(Path, mapping))
    launcher = CAP_ROOT/'01_launcher.json'
    assert grid.read(launcher)['returncode'] == 0 and grid.read(launcher)['completed']
    paths.add(launcher)
    # Review certifies the data, not successful index performance.
    for finger in COUNTS:
        folder = CAP_ROOT/'runs'/finger
        report = grid.read(folder/'report.json')
        assert report['completed'] and report['closed'] and report['scene_valid'] and report['loader_restored']
        assert report['failure'] is None and not report['changed_inputs'] and not report['unpinned_project_sources']
        evaluation = grid.read(folder/'evaluation.json')
        assert evaluation['assigned_quotas'] == [1]*4 and grid.complete(evaluation['episodes'], 4)
        assert evaluation['acceptance'] == cap.repro.acceptance(evaluation['episodes'])
        paths.update(folder/name for name in ('report.json', 'evaluation.json'))
    return paths


def verify_native(scene, source, declaration, count):
    import numpy as np
    actual = scene.pd_properties
    baseline = cap.expected_properties(source, actual.dtype)
    expected = baseline.copy()
    expected['effort'][declaration['native_indices']] = cap.CAP
    assert np.array_equal(actual, expected)
    changes = {key: np.flatnonzero(actual[key] != baseline[key]).tolist() for key in actual.dtype.names}
    assert changes['effort'] == declaration['native_indices']
    assert all(not ids for key, ids in changes.items() if key != 'effort')
    reverted = copy.deepcopy(scene.contract)
    reverted['initial']['native_PD_properties']['effort'] = source['initial']['native_PD_properties']['effort']
    np.testing.assert_equal(reverted, source)
    assert count in COUNTS.values() and scene.num_envs == count
    assert scene._hand_collision_readback_count == count and scene.physics_steps == 0
    assert scene.hand_collision['enabled_distinct_finger_pairs'] == 90
    return dict(**declaration, environment_count=count, expected_readback_exact=True,
        actual_native_PD105={key: actual[key].tolist() for key in actual.dtype.names},
        original_profile_native_PD105={key: baseline[key].tolist() for key in actual.dtype.names},
        changed_native_field_indices=changes,
        property_scope='Full105 last-env readback; original constructor asserts every field in every env; '
              'original K/D profile,90collision pairs; private loader only during scene creation')


@contextmanager
def effort_pool(finger):
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning import runtime
    original_pool = runtime.ShortPool
    original_loader = prepared_reset_v1.load_prepared_reset_contract
    cleanup_errors = []

    class GridEffortPool(original_pool):
        def _create_scene(self, settings, out):
            calls = []; scene = None
            try:
                with cap.effort_loader(calls):
                    scene = super()._create_scene(settings, out)
                assert prepared_reset_v1.load_prepared_reset_contract is original_loader and len(calls) == 1
                self.effort_readback = verify_native(scene, *calls[0], COUNTS[finger])
                return scene
            except BaseException:
                if scene is not None:
                    try:
                        scene.close()
                    except BaseException as error:
                        cleanup_errors.append(dict(type=type(error).__name__, message=str(error)))
                raise

        def __init__(self, settings, out):
            super().__init__(settings, out)
            try:
                assert self.contract == grid.read(grid.HERE/'runs'/finger/'training_contract.json')
                assert np.array_equal(self.scene.effort_caps.cpu().numpy(), self.scene.pd_properties['effort'])
                assert torch.equal(self.controller.caps, self.scene.effort_caps)
                self.contract['native_backend']['diagnostic_native_effort'] = self.effort_readback
                grid.write(out/'native_effort_readback.json', self.effort_readback)
            except BaseException:
                try:
                    self.close()
                except BaseException as error:
                    cleanup_errors.append(dict(type=type(error).__name__, message=str(error)))
                raise

    runtime.ShortPool = GridEffortPool
    try:
        yield cleanup_errors
    finally:
        runtime.ShortPool = original_pool
        assert prepared_reset_v1.load_prepared_reset_contract is original_loader


def cpu_checks():
    import numpy as np
    import torch
    from types import SimpleNamespace
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    source = load_prepared_reset_contract()
    private, declaration = cap.private_contract(source)
    dtype = np.dtype([(n, np.bool_ if n == 'hasLimits' else np.int32 if n == 'driveMode' else np.float32)
        for n in source['initial']['native_PD_properties']])
    native = cap.expected_properties(source, dtype)
    native['effort'][declaration['native_indices']] = cap.CAP
    for finger, count in COUNTS.items():
        scene = SimpleNamespace(pd_properties=native.copy(), contract=private, num_envs=count,
            _hand_collision_readback_count=count, physics_steps=0,
            hand_collision=dict(enabled_distinct_finger_pairs=90))
        assert verify_native(scene, source, declaration, count)['environment_count'] == count
        for field, index, value in (('effort', declaration['native_indices'][0], 20.),
                                   ('effort', 51, cap.CAP), ('stiffness', 56, 13.)):
            scene.pd_properties = native.copy(); scene.pd_properties[field][index] = value
            try:
                verify_native(scene, source, declaration, count)
            except AssertionError:
                pass
            else:
                raise AssertionError('Bad native readback accepted')
        document = grid.read(grid.HERE/'cpu_inputs'/(finger+'_grid.json'))
        assert document['valid_count'] == count and len(document['rows']) == 225
        assert grid.settings(finger, count) == grid.read(grid.HERE/'cpu_inputs'/(finger+'_settings.json'))
    from guitar_learning.tool.experiments.short_finger_learning import runtime
    from guitar_learning.runtime import prepared_reset_v1
    original_pool = runtime.ShortPool; original_loader = prepared_reset_v1.load_prepared_reset_contract
    try:
        with effort_pool('index'):
            assert runtime.ShortPool is not original_pool
            assert prepared_reset_v1.load_prepared_reset_contract is original_loader
            raise RuntimeError('CPU injected observer error')
    except RuntimeError as error:
        assert str(error) == 'CPU injected observer error'
    assert runtime.ShortPool is original_pool and prepared_reset_v1.load_prepared_reset_contract is original_loader
    return dict(CPU_only=True, GPU_executed=False, no_NN_checkpoint=True,
        original_grid_450_rows_reused=True, valid_counts=COUNTS, native_property_good_bad_checks=True,
        pool_and_loader_restored_after_injected_error=True,
        native_effort_cap_Nm=cap.CAP, original_rewards_clock_rank_ranges_collision_preserved=True)


def prepare():
    from guitar_learning.tool.experiments.short_finger_learning import runner
    cap.reject_existing(HERE/'cpu_verification.json'); cap.reject_existing(HERE/'preparation_seal.json')
    checks = cpu_checks(); evidence = actual_gate()
    for path in (grid.HERE/'preparation_seal.json', CAP_ROOT/'preparation_seal.json'):
        seal = grid.read(path)
        assert seal['independent_review'] == 'passed_no_findings'
        assert all(Path(p).is_file() and grid.sha(p) == h for p, h in seal['input_pins'].items())
        evidence.update(map(Path, seal['input_pins'])); evidence.add(path)
    grid.write(HERE/'cpu_verification.json', checks)
    evidence.update((Path(__file__), HERE/'README.md', HERE/'PLAN.md', HERE/'cpu_verification.json'))
    pins = runner._pins(grid.settings('index', COUNTS['index']), grid.HERE/'cpu_inputs', evidence)
    grid.write(HERE/'preparation_seal.json', dict(schema=SCHEMA, independent_review='pending', input_pins=pins,
        valid_counts=COUNTS, native_effort_cap_Nm=cap.CAP, original_grid=str(grid.HERE),
        scope='Same315 finite first attempts; not learned policy or production adoption; root GPU only'))
    print(dict(CPU_only=True, pins=len(pins), counts=COUNTS))


def launch(finger):
    out = HERE/'runs'/finger
    cap.reject_existing(out)
    seal_path = HERE/'preparation_seal.json'; seal = grid.read(seal_path)
    assert seal['independent_review'] == 'passed_no_findings'
    assert all(Path(p).is_file() and grid.sha(p) == h for p, h in seal['input_pins'].items())
    evidence = actual_gate()
    runtime_seal = copy.deepcopy(seal)
    for path in evidence | {seal_path}:
        runtime_seal['input_pins'][str(path)] = grid.sha(path)
    import isaacgym  # Native import precedes NumPy/Torch.
    cleanup_errors = []
    try:
        with effort_pool(finger) as cleanup_errors:
            grid.execute(finger, out, runtime_seal)
    finally:
        if out.is_dir():
            scene = grid.read(out/'gpu_scene_final.json') if (out/'gpu_scene_final.json').is_file() else {}
            valid = (scene.get('closed') is True and scene.get('environment_count') == COUNTS[finger]
                and scene.get('hand_collision_native_readback_environments') == COUNTS[finger]
                and scene.get('hand_collision', {}).get('enabled_distinct_finger_pairs') == 90
                and scene.get('diagnostic_guitar_mode') == 'fixed' and scene.get('physx_use_gpu') is True
                and scene.get('use_gpu_pipeline') is True)
            grid.write(out/'effort_grid_lifecycle.json', dict(schema=SCHEMA, scene_valid=valid,
                cleanup_errors=cleanup_errors, pool_restored=True, native_effort_cap_Nm=cap.CAP))
            if sys.exc_info()[0] is None and (not valid or cleanup_errors):
                raise RuntimeError('Effort grid lifecycle verification failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    for name in ('self-test', 'prepare', 'execute'):
        actions.add_argument('--'+name, action='store_true')
    parser.add_argument('--finger', choices=tuple(COUNTS)); args = parser.parse_args()
    sys.path.insert(0, str(grid.ROOT))
    if args.self_test: print(cpu_checks())
    elif args.prepare: prepare()
    elif args.finger is None: raise ValueError('Predeclared finger required')
    else: launch(args.finger)
