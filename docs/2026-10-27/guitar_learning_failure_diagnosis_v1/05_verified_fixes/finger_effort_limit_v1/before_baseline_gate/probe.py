"""CPU prepare, then root-only 0.25 Nm finger16 diagnostic of fixed grid selections."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1]
ROOT = DIAG.parents[2]
REPRO = DIAG/'05_verified_fixes/finger_only_oracle_acquisition_v1/reproduction_v1'
module_spec = importlib.util.spec_from_file_location('effort_baseline_reproduction', REPRO/'probe.py')
repro = importlib.util.module_from_spec(module_spec)
sys.modules[module_spec.name] = repro
module_spec.loader.exec_module(repro)
parent = repro.parent
SCHEMA = 'diagnostic.finger16_native_effort_limit.v1'
CAP = .25
BASELINE_REVIEW = REPRO/'analysis/results_v1/review.json'


def reject_existing(out):
    parent.reject_existing(out)
    if any(p.is_symlink() for p in out.parents):
        raise ValueError('Output parent symlink refused')


def owned(out, identity):
    if out.is_symlink() or (out.stat().st_dev, out.stat().st_ino) != identity:
        raise RuntimeError('Output directory ownership changed')


def private_contract(source):
    import numpy as np
    result = copy.deepcopy(source)
    names = source['initial']['joint_names']
    ids = [i for i, name in enumerate(names) if name.startswith('LH:') and not name.startswith('LH:thumb')]
    assert len(names) == 105 and len(ids) == 16
    assert set(ids) <= set(source['initial']['position_indices'])
    before = source['initial']['native_PD_properties']['effort']
    assert all(before[i] == 20. for i in ids)
    for i in ids:
        result['initial']['native_PD_properties']['effort'][i] = CAP
    reverted = copy.deepcopy(result)
    reverted['initial']['native_PD_properties']['effort'] = copy.deepcopy(before)
    np.testing.assert_equal(reverted, source)
    assert result is not source and result['initial'] is not source['initial']
    document = dict(schema=SCHEMA, diagnostic_only=True, cap_Nm=CAP,
        engineering_value_not_human_limit=True, native_indices=ids, joint_names=[names[i] for i in ids],
        effort_before_Nm=[before[i] for i in ids], effort_after_Nm=[CAP]*16,
        unchanged_other_axes=89, unchanged_thumb_axes=5, source_sha256=source['source_sha256'],
        source_contract_except_16_effort_exact=True,
        scope='Private contract after original verified loader; only finger16 native POSITION effort fields changed. '
              'Original state/config/target105/sourceSHA and JSON untouched; no force/pressure upper bound.')
    return result, document


@contextmanager
def effort_loader(calls):
    from guitar_learning.runtime import prepared_reset_v1
    original = prepared_reset_v1.load_prepared_reset_contract

    def changed():
        source = original()  # Keep the full original source verification; no alternate loader.
        private, document = private_contract(source)
        calls.append((source, document))
        return private

    prepared_reset_v1.load_prepared_reset_contract = changed
    try:
        yield
    finally:
        prepared_reset_v1.load_prepared_reset_contract = original


def expected_properties(source, dtype):
    import numpy as np
    from guitar_learning.core.finger_control import default_profile
    native = source['initial']['native_PD_properties']
    assert set(dtype.names) == set(native)
    result = np.empty(105, dtype=dtype)
    for name in dtype.names:
        result[name] = native[name]
    profile = default_profile()
    for i, name in enumerate(source['initial']['joint_names']):
        if name.startswith('LH:'):
            prefix = 'thumb' if name.startswith('LH:thumb') else 'finger'
            result['stiffness'][i] = profile[prefix+'_stiffness']
            result['damping'][i] = profile[prefix+'_damping']
    return result


def verify_native(scene, source, document):
    import numpy as np
    actual = scene.pd_properties
    baseline = expected_properties(source, actual.dtype)
    expected = baseline.copy(); expected['effort'][document['native_indices']] = CAP
    assert np.array_equal(actual, expected)
    changed = {key: np.flatnonzero(actual[key] != baseline[key]).tolist() for key in actual.dtype.names}
    assert changed['effort'] == document['native_indices']
    assert all(not ids for key, ids in changed.items() if key != 'effort')
    reverted = copy.deepcopy(scene.contract)
    reverted['initial']['native_PD_properties']['effort'] = source['initial']['native_PD_properties']['effort']
    np.testing.assert_equal(reverted, source)
    assert scene.physics_steps == 0
    assert scene.hand_collision['enabled_distinct_finger_pairs'] == 90
    assert scene._hand_collision_readback_count == scene.num_envs == 4
    return dict(**document, actual_native_PD105={key: actual[key].tolist() for key in actual.dtype.names},
        original_profile_native_PD105={key: baseline[key].tolist() for key in actual.dtype.names},
        changed_native_field_indices=changed, expected_readback_exact=True,
        property_scope='Full105 last-env readback array; original scene constructor asserts all native fields '
                       'exact for every environment. Original LH K/D profile applied in both arrays.',
        loader_scope='Module function replaced only inside ShortPool subclass._create_scene; finally restored; '
                     'no later loader, controller, state or reward override')


def baseline_actual_gate():
    review = parent.read(BASELINE_REVIEW)
    assert review['verdict'] == 'PASS' and not review['findings']
    reviewed = review['reviewed_sha256']
    assert reviewed and all(Path(p).is_file() and parent.sha(p) == h for p, h in reviewed.items())
    paths = {BASELINE_REVIEW, *map(Path, reviewed)}
    launcher = parent.read(REPRO/'01_launcher.json')
    assert launcher['returncode'] == 0 and launcher['completed']
    paths.add(REPRO/'01_launcher.json')
    # A review PASS certifies the records, not 4/4 performance. Never require/replace the acceptance result.
    for finger in repro.SELECTED:
        folder = REPRO/'runs'/finger
        for name in ('evaluation.json', 'report.json', 'settings.json', 'training_contract.json',
                     'inputs_before.json', 'inputs_after.json', 'gpu_scene_final.json', 'trace_metadata.json', 'statistics.json'):
            paths.add(folder/name)
        report = parent.read(folder/'report.json'); evaluation = parent.read(folder/'evaluation.json')
        assert report['completed'] and report['closed'] and report['failure'] is None
        assert parent.complete(evaluation['episodes'], 4) and evaluation['assigned_quotas'] == [1]*4
        assert evaluation['acceptance'] == repro.acceptance(evaluation['episodes'])
    return paths


def cpu_checks():
    import tempfile
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    original = prepared_reset_v1.load_prepared_reset_contract
    source = original(); saved = copy.deepcopy(source)
    changed, document = private_contract(source)
    np.testing.assert_equal(source, saved)
    assert all(changed['initial']['native_PD_properties']['effort'][i] == CAP for i in document['native_indices'])
    calls = []
    try:
        with effort_loader(calls):
            private = prepared_reset_v1.load_prepared_reset_contract()
            assert private['initial']['native_PD_properties']['effort'] != source['initial']['native_PD_properties']['effort']
            raise RuntimeError('CPU injected constructor error')
    except RuntimeError as error:
        assert str(error) == 'CPU injected constructor error'
    assert prepared_reset_v1.load_prepared_reset_contract is original and len(calls) == 1
    np.testing.assert_equal(original(), saved)
    dtype = np.dtype([(name, np.bool_ if name == 'hasLimits' else np.int32 if name == 'driveMode' else np.float32)
        for name in source['initial']['native_PD_properties']])
    baseline = expected_properties(source, dtype)
    expected = baseline.copy(); expected['effort'][document['native_indices']] = CAP
    for field in dtype.names:
        indices = np.flatnonzero(baseline[field] != expected[field]).tolist()
        assert indices == (document['native_indices'] if field == 'effort' else [])
    with tempfile.TemporaryDirectory() as temp:
        existing = Path(temp)/'old'; existing.mkdir(); (existing/'sentinel').write_bytes(b'unchanged')
        link = Path(temp)/'link'; link.symlink_to(Path(temp)/'absent')
        for path in (existing, link, link/'new'):
            try:
                launch('index', path, Path(temp)/'absent')
            except (FileExistsError, ValueError):
                pass
            else:
                raise AssertionError('Existing/symlink output accepted')
        assert (existing/'sentinel').read_bytes() == b'unchanged' and not list(existing.glob('*.json'))
    checks = {}
    for finger in repro.SELECTED:
        grid = parent.read(repro.BASE/'cpu_inputs'/(finger+'_grid.json'))
        target = repro.document_for(finger, grid)
        assert target == parent.read(REPRO/'cpu_inputs'/(finger+'_targets.json'))
        assert parent.settings(finger, 4) == parent.read(REPRO/'cpu_inputs'/(finger+'_settings.json'))
        checks[finger] = dict(selected_grid_index=repro.SELECTED[finger], assigned_quotas=[1]*4,
            exact_reproduction_targets=True, exact_original_settings=True)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return document, dict(CPU_only=True, GPU_executed=False, CUDA_initialized=False,
        checks=checks, private_copy_only16_effort_exact=True, original_contract_state_target_unchanged=True,
        unchanged_other89_native_axes=True, unchanged_all_other_native_PD_properties=True,
        loader_restored_after_injected_error=True, existing_symlink_output_rejected_before_native=True,
        original_acceptance_unchanged=True, baseline_actual_review_required=str(BASELINE_REVIEW),
        no_NN_checkpoint_or_new_cap_search=True)


def prepare():
    from guitar_learning.tool.experiments.short_finger_learning import runner
    reject_existing(HERE/'cpu_inputs'); reject_existing(HERE/'preparation_seal.json')
    document, checks = cpu_checks()
    inputs = HERE/'cpu_inputs'; inputs.mkdir()
    parent.write(inputs/'effort_declaration.json', document)
    paths = repro.evidence() | {Path(__file__), HERE/'README.md', REPRO/'probe.py', REPRO/'preparation_seal.json'}
    for finger in repro.SELECTED:
        config = parent.settings(finger, 4)
        target = repro.document_for(finger, parent.read(repro.BASE/'cpu_inputs'/(finger+'_grid.json')))
        parent.write(inputs/(finger+'_settings.json'), config); parent.write(inputs/(finger+'_targets.json'), target)
    parent.write(inputs/'settings.json', parent.settings('index', 4))
    parent.write(HERE/'cpu_verification.json', checks)
    paths.update(inputs.glob('*.json')); paths.add(HERE/'cpu_verification.json')
    pins = runner._pins(parent.settings('index', 4), inputs, paths)
    parent.write(HERE/'preparation_seal.json', dict(schema=SCHEMA, independent_review='pending', input_pins=pins,
        baseline_actual_review_required=str(BASELINE_REVIEW), selected_grid_indices=repro.SELECTED,
        scope='CPU prepared only. Root launches two0.25Nm scenes after independent baseline20Nm actual review; '
              'review PASS is not performance acceptance, and the 4/4 rule is unchanged.'))
    print(json.dumps(dict(CPU_only=True, pins=len(pins), cap_Nm=CAP, GPU_executed=False)))


def execute(finger, out, identity, seal, baseline_paths):
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPool
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    from guitar_learning.training.recording import project_source_paths

    class EffortPool(ShortPool):
        def _create_scene(self, settings, target_out):
            calls = []; scene = None
            original = prepared_reset_v1.load_prepared_reset_contract
            try:
                with effort_loader(calls):
                    scene = super()._create_scene(settings, target_out)
                assert prepared_reset_v1.load_prepared_reset_contract is original and len(calls) == 1
                self.effort_readback = verify_native(scene, *calls[0])
                return scene
            except BaseException:
                if scene is not None:
                    scene.close()
                raise

        def step(self, actions):
            result = super().step(actions)
            if not self.velocity_done:
                self.velocity_trace.append(dict(time_s=float(self.environment._local_time()[0]),
                    native_qd=self.scene.qd[0, self.controller.active[self.spec['learned_action_indices']]].cpu().numpy().copy()))
                self.velocity_done = any(row['env_id'] == 0 for row in result[-1])
            return result

    config = parent.settings(finger, 4)
    document = repro.document_for(finger, parent.read(repro.BASE/'cpu_inputs'/(finger+'_grid.json')))
    assert config == parent.read(HERE/'cpu_inputs'/(finger+'_settings.json'))
    assert document == parent.read(HERE/'cpu_inputs'/(finger+'_targets.json'))
    reference = read_reference(parent.INPUTS[finger][1], config['song']['short_learning'])
    runner.write(out/'settings.json', config)
    pins = runner._pins(config, out, [HERE/'preparation_seal.json', *map(Path, seal['input_pins']), *baseline_paths])
    runner.write(out/'inputs_before.json', pins)
    random.seed(7); np.random.seed(7); torch.manual_seed(7); torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    pool = None; completed = False; failure = None; resources = {}; started = time.monotonic()
    original_loader = prepared_reset_v1.load_prepared_reset_contract
    try:
        pool = EffortPool(config, out); pool.velocity_done = False; pool.velocity_trace = []
        assert pool.effort_readback['cap_Nm'] == CAP
        assert pool.effort_readback['source_sha256'] == parent.read(HERE/'cpu_inputs/effort_declaration.json')['source_sha256']
        normalized = copy.deepcopy(pool.contract)
        assert normalized == parent.read(REPRO/'runs'/finger/'training_contract.json')
        pool.contract['native_backend']['diagnostic_native_effort'] = pool.effort_readback
        assert np.array_equal(pool.scene.effort_caps.cpu().numpy(), pool.scene.pd_properties['effort'])
        assert torch.equal(pool.controller.caps, pool.scene.effort_caps)
        runner.write(out/'native_effort_readback.json', pool.effort_readback)
        runner.write(out/'training_contract.json', pool.contract)
        episodes, statistics, details, ticks = parent.collect(pool, document, reference)
        repro.identify(episodes, statistics, document)
        assert list(details) == [0]
        assert all(sum(p['samples'] for p in s['phases'].values()) == e['steps'] for s, e in zip(statistics, episodes))
        runner.write(out/'evaluation.json', dict(assigned_quotas=[1]*4, episodes=episodes, summary=runner.summary(episodes),
            acceptance=repro.acceptance(episodes), policy_performance=False,
            scope='Same selected target, original acceptance and full failure denominator; only native finger16 effort cap changed'))
        metadata = parent.read(REPRO/'runs'/finger/'statistics.json')
        runner.write(out/'statistics.json', dict(phase_order=metadata['phase_order'], phase_scope=metadata['phase_scope'],
            gate_order=metadata['gate_order'], metric_order=metadata['metric_order'], rows=statistics, scope=metadata['scope']))
        trace = details[0]; velocities = pool.velocity_trace
        assert len(trace) == len(velocities)
        assert all(a['time_s'] == b['time_s'] for a, b in zip(trace, velocities))
        filename = 'trace_grid%06d_env0_first.npz'%repro.SELECTED[finger]
        np.savez_compressed(out/filename, **{key: np.asarray([row[key] for row in trace]) for key in trace[0]},
            selected_native_qd=np.asarray([row['native_qd'] for row in velocities]))
        runner.write(out/'trace_metadata.json', dict(joint_names=pool.scene.names, body_names=pool.scene.metadata['body_names'],
            env_id=0, attempt_id=document['rows'][0]['attempt_id'], grid_index=repro.SELECTED[finger], file=filename,
            selected_native_qd_names=pool.spec['learned_action_names'],
            velocity_scope='Native velocity-coordinate qd, not a claim of d(qpos)/dt for MCP2axis; observed post-step only',
            wrist_control=pool.spec['wrist_control'], scope='env0 first attempt60Hz, failure endpoint included; no pair pressure/240Hz maximum'))
        resources.update(physics_steps=pool.scene.physics_steps, control_ticks=ticks)
        assert pool.scene.physics_steps == ticks*4 and ticks <= pool.spec['view']['duration_ticks']
        assert not list(out.glob('*.pt')); completed = True
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error)); raise
    finally:
        close_failure = None
        try:
            if pool is not None: pool.close()
        except BaseException as error:
            close_failure = dict(type=type(error).__name__, message=str(error))
        owned(out, identity)
        changed = [p for p, h in pins.items() if not Path(p).is_file() or parent.sha(p) != h]
        missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        scene = parent.read(out/'gpu_scene_final.json') if (out/'gpu_scene_final.json').is_file() else {}
        verified = not changed and not missing
        restored = prepared_reset_v1.load_prepared_reset_contract is original_loader
        scene_valid = (scene.get('closed') is True and scene.get('environment_count') == 4 and
            scene.get('hand_collision', {}).get('enabled_distinct_finger_pairs') == 90 and
            scene.get('hand_collision_native_readback_environments') == 4 and scene.get('diagnostic_guitar_mode') == 'fixed' and
            scene.get('physx_use_gpu') is True and scene.get('use_gpu_pipeline') is True and
            scene.get('physics_steps') == resources.get('physics_steps'))
        runner.write(out/'inputs_after.json', dict(verified=verified, changed_paths=changed,
            unpinned_project_sources=missing, input_pins=pins))
        runner.write(out/'report.json', dict(schema=SCHEMA, completed=completed and verified and restored and not close_failure and scene_valid,
            closed=scene.get('closed') is True, scene_valid=scene_valid, failure=failure, close_failure=close_failure,
            loader_restored=restored, changed_inputs=changed, unpinned_project_sources=missing,
            resources=resources, selected_grid_index=repro.SELECTED[finger], assigned_first_attempts=4,
            cap_Nm=CAP, no_NN_checkpoint=True, wall_s=time.monotonic()-started))
        if failure is None and (not verified or not restored or close_failure or not scene_valid):
            raise RuntimeError('Effort diagnostic source/close verification failed; outputs preserved')


def launch(finger, out, seal_path):
    reject_existing(out)
    seal = parent.read(seal_path)
    assert seal['independent_review'] == 'passed_no_findings'
    assert all(Path(p).is_file() and parent.sha(p) == h for p, h in seal['input_pins'].items())
    baseline_paths = baseline_actual_gate()  # Before native import; acceptance need not pass.
    out.mkdir(parents=True, exist_ok=False); identity = (out.stat().st_dev, out.stat().st_ino)
    parent.write(out/'invocation.json', dict(argv=sys.argv, finger=finger, schema=SCHEMA, cap_Nm=CAP))
    try:
        import isaacgym
        execute(finger, out, identity, seal, baseline_paths)
    except BaseException as error:
        owned(out, identity)
        if not (out/'report.json').exists():
            parent.write(out/'report.json', dict(completed=False, closed=False,
                failure=dict(type=type(error).__name__, message=str(error)), scope='Failure before normal lifecycle report'))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare', 'self-test', 'dry-plan', 'execute'):
        group.add_argument('--'+name, action='store_true')
    parser.add_argument('--finger', choices=tuple(repro.SELECTED)); args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    if args.prepare: prepare()
    elif args.self_test: print(json.dumps(cpu_checks()[1], indent=2))
    elif args.dry_plan:
        print(json.dumps([dict(finger=f, baseline_review=str(BASELINE_REVIEW), out=str(HERE/'runs'/f),
            argv=[parent.PYTHON, '-B', str(Path(__file__).resolve()), '--execute', '--finger', f]) for f in repro.SELECTED], indent=2))
    else:
        if args.finger is None: raise ValueError('Predeclared finger required')
        launch(args.finger, HERE/'runs'/args.finger, HERE/'preparation_seal.json')


if __name__ == '__main__': main()
