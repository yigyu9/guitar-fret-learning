"""CPU preparation; root-only two-scene index reference collision-pair diagnostic."""
import argparse
import copy
from contextlib import contextmanager
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys
import time

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1]
ROOT = DIAG.parents[2]
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
TEACHER = DIAG / '03_short_learning/other_finger_precheck_v3/teacher_index_row1.json'
REFERENCE = DIAG / '03_short_learning/other_finger_precheck_v3/reference_index_row1.json'
PAIR = ('LH:index1', 'LH:middle1')
BIT = 1 << 25
CONDITIONS = ('baseline', 'refilter')
SCHEMA = 'diagnostic.index_proximal_pair_isolation.v1'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def reject_existing(out):
    if out.exists() or out.is_symlink():
        raise FileExistsError(str(out))
    if any(p.is_symlink() for p in out.parents):
        raise ValueError('Output parent symlink refused')


def owned(out, identity):
    if out.is_symlink() or (out.stat().st_dev, out.stat().st_ino) != identity:
        raise RuntimeError('Output directory ownership changed')


def shape_rows(shapes):
    return [(name, i, row['filter']) for name, values in shapes.items()
            for i, row in enumerate(values)]


def matrix(shapes):
    rows = shape_rows(shapes)
    return [[a[0], a[1], b[0], b[1], (a[2] & b[2]) == 0]
            for a, b in itertools.combinations(rows, 2)]


def matrix_sha(rows):
    return hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()


def condition_properties(baseline, original_contract, condition, external):
    if condition not in CONDITIONS:
        raise ValueError('Predeclared condition required')
    result = copy.deepcopy(baseline)
    assert len(shape_rows(result)) == 55 and all(len(result[n]) == 1 for n in PAIR)
    assert all(not (mask & BIT) for _, _, mask in shape_rows(baseline))
    assert all(type(mask) is int and 0 <= mask < (1 << 20) for mask in external)
    if condition == 'refilter':
        for name in PAIR:
            result[name][0]['filter'] |= BIT
    before, after = matrix(baseline), matrix(result)
    assert len(before) == len(after) == 1485
    changes = [[a, b] for a, b in zip(before, after) if a[-1] != b[-1]]
    assert len(changes) == int(condition == 'refilter')
    if changes:
        assert set((changes[0][0][0], changes[0][0][2])) == set(PAIR)
        assert changes[0][0][-1] is True and changes[0][1][-1] is False
    assert matrix_sha(before) == original_contract['human_pair_matrix_sha256']
    for name, values in baseline.items():
        for i, old in enumerate(values):
            assert {k: v for k, v in old.items() if k != 'filter'} == {
                k: v for k, v in result[name][i].items() if k != 'filter'}
    for old, new in zip(shape_rows(baseline), shape_rows(result)):
        for mask in external:
            assert ((old[2] & mask) == 0) == ((new[2] & mask) == 0)
    native = copy.deepcopy(original_contract)
    if condition == 'refilter':
        native.update(schema=SCHEMA, diagnostic_only=True, condition=condition,
            baseline_contract=copy.deepcopy(original_contract), pair_bit=BIT,
            disabled_pair=list(PAIR), enabled_distinct_finger_pairs=89,
            preserved_other_human_shape_pairs=1396,
            preserved_baseline_human_shape_pairs=1484,
            human_pair_matrix_sha256=matrix_sha(after),
            scope='Only index1/middle1 shape pair excluded before native prepare; '
                  '1396 source-mask pair truths preserved, 1484 baseline truths preserved; '
                  'diagnostic finite reference, not production filter or policy performance')
        for row in native['changed_filters']:
            row['after'] = result[row['body']][row['shape']]['filter']
    document = dict(schema=SCHEMA, condition=condition, original_90_contract=original_contract,
        submitted_contract=native, pair_bit=BIT, pair_bodies=list(PAIR),
        pair_masks_before={n: baseline[n][0]['filter'] for n in PAIR},
        pair_masks_after={n: result[n][0]['filter'] for n in PAIR},
        baseline_matrix=before, submitted_matrix=after,
        baseline_matrix_sha256=matrix_sha(before), submitted_matrix_sha256=matrix_sha(after),
        changed_baseline_pairs=changes, preserved_baseline_pairs=1485-len(changes),
        actual_external_filters=sorted(set(external)), external_pair_changes=0,
        nonfilter_properties_exact=True,
        wrapper_scope='hand_collision module function replaced only during ShortPool constructor; '
                      'original helper first, copied return, condition bit OR, original native '
                      'shape setter/readback/prepare_sim and external assertions unchanged; finally restored')
    return result, native, document


@contextmanager
def collision_wrapper(condition, external, expected, calls):
    from guitar_learning.gpu import hand_collision
    original = hand_collision.left_hand_collision_properties

    def wrapped(shapes):
        baseline, contract = original(shapes)
        result, native, document = condition_properties(baseline, contract, condition, external)
        if document != expected:
            raise ValueError('Collision condition differs from CPU declaration')
        calls.append(document)
        return result, native

    hand_collision.left_hand_collision_properties = wrapped
    try:
        yield
    finally:
        hand_collision.left_hand_collision_properties = original


def settings():
    from guitar_learning.tool.experiments.short_finger_learning.runner import make_settings
    return make_settings(argparse.Namespace(teacher=str(TEACHER), mode='incremental',
        initial_std=.1711710544767014, song='05_BN2-131-B_solo', size='large', seed=7,
        num_envs=4, horizon=32, updates=1, save_every=50))


def declaration_inputs():
    from guitar_learning.gpu.hand_collision import left_hand_collision_properties
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    initial = load_prepared_reset_contract()['initial']
    manifest = read(ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json')
    external = [0] + [row['filter'] for row in manifest['shape_properties']]
    baseline, contract = left_hand_collision_properties(initial['actual_shape_properties']['human'])
    return baseline, contract, external


def cpu_checks():
    import tempfile
    import torch
    from guitar_learning.gpu import hand_collision
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.tests.test_gpu_control import fake_scene
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    from guitar_learning.tool.validation.press_acquisition import trajectory_actions
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    config = settings()
    spec = config['song']['short_learning']
    reference = read_reference(REFERENCE, spec)
    baseline, original, external = declaration_inputs()
    documents = {c: condition_properties(baseline, original, c, external)[2] for c in CONDITIONS}
    assert documents['baseline']['submitted_contract'] == original
    assert documents['refilter']['submitted_contract']['enabled_distinct_finger_pairs'] == 89
    original_function = hand_collision.left_hand_collision_properties
    calls = []
    try:
        with collision_wrapper('refilter', external, documents['refilter'], calls):
            from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
            hand_collision.left_hand_collision_properties(
                load_prepared_reset_contract()['initial']['actual_shape_properties']['human'])
            raise RuntimeError('CPU restoration fixture')
    except RuntimeError as error:
        assert str(error) == 'CPU restoration fixture'
    assert hand_collision.left_hand_collision_properties is original_function and len(calls) == 1
    scene, sample = fake_scene(4, dtype=torch.float32)
    controller = BatchedController(scene, finger_action_mode='incremental')
    active_ref = controller.reference[controller.active]
    goal = active_ref.clone()
    from guitar_learning.core.control import ACTIVE_NAMES
    for name, angle in reference['selected_targets_rad'].items():
        goal[ACTIVE_NAMES.index(name)] = angle
    assert bool(((goal >= controller.action_low) & (goal <= controller.action_high)).all())
    inc = torch.zeros(39, dtype=torch.bool)
    inc[controller.incremental_actions] = True
    for tick in range(spec['view']['duration_ticks']):
        old = controller.target.clone()
        desired = active_ref + min((tick+1)/120., 1.)*(goal-active_ref)
        action = trajectory_actions(desired.repeat(4, 1), old[:, controller.active],
            active_ref, controller.action_low, controller.action_high, inc, max_speed=4.)
        target = controller.targets(action, sample)
        assert bool(torch.isfinite(target).all())
        assert bool((abs(target-old) <= controller.rate/60 + 2e-7).all())
        assert bool(((target >= controller.lower) & (target <= controller.upper)).all())
    ids = [ACTIVE_NAMES.index(name) for name in spec['learned_action_names']]
    torch.testing.assert_close(target[:, controller.active[ids]], goal[ids].repeat(4, 1), rtol=0, atol=2e-7)
    with tempfile.TemporaryDirectory() as temp:
        existing = Path(temp)/'existing'; existing.mkdir()
        sentinel = existing/'sentinel'; sentinel.write_bytes(b'unchanged')
        link = Path(temp)/'link'; link.symlink_to(Path(temp)/'absent')
        for out in (existing, link, link/'new'):
            try:
                launch('baseline', out, Path(temp)/'absent_seal')
            except (FileExistsError, ValueError):
                pass
            else:
                raise AssertionError('Existing/symlink output accepted')
        assert sentinel.read_bytes() == b'unchanged' and not list(existing.glob('*.json'))
    assert 'isaacgym' not in sys.modules and not torch.cuda.is_initialized()
    return config, documents, external, dict(CPU_only=True, GPU_executed=False,
        pure_checks=['1485 human pairs: baseline preserved; exactly one refilter pair changed',
            'actual compound-guitar/chair filters unchanged; every nonfilter property exact',
            'constructor-function restoration on injected failure',
            'original selected4 reference codec: finite/native bounds/4rad/s and endpoint',
            'existing/dangling/symlink-parent output rejected before native import; sentinel preserved'],
        NN_or_checkpoint_created=False, assigned_quotas=[1]*4,
        max_control_ticks=spec['view']['duration_ticks'], max_physics_steps=4*spec['view']['duration_ticks'],
        limitation='CPU selected-reference action arithmetic only; native wrist/physics fit and outcome untested')


def prepare():
    from guitar_learning.tool.experiments.short_finger_learning import runner
    reject_existing(HERE/'cpu_inputs')
    config, documents, external, checks = cpu_checks()
    inputs = HERE/'cpu_inputs'; inputs.mkdir()
    write(inputs/'settings.json', config)
    for condition, document in documents.items():
        write(inputs/(condition+'_collision.json'), document)
    write(HERE/'cpu_verification.json', checks)
    extras = {Path(__file__), HERE/'README.md', HERE/'cpu_verification.json', TEACHER, REFERENCE,
              *inputs.glob('*.json')}
    spec = config['song']['short_learning']
    extras.update(map(Path, spec['teacher']['source_evidence']))
    reference = runner.read_reference(REFERENCE, spec)
    extras.update(map(Path, reference['source_evidence']))
    pins = runner._pins(config, inputs, extras)
    write(HERE/'preparation_seal.json', dict(schema=SCHEMA, independent_review='pending',
        input_pins=pins, external_filters=external,
        scope='Two fresh scenes, each four reference first attempts including failures; no NN/checkpoint; root GPU only'))
    print(json.dumps(dict(CPU_only=True, input_pins=len(pins), conditions=list(CONDITIONS), GPU_executed=False)))


def execute(condition, out, identity, seal):
    import numpy as np
    import torch
    from guitar_learning.training.recording import project_source_paths
    from guitar_learning.gpu import hand_collision
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPool
    config = settings()
    assert config == read(HERE/'cpu_inputs/settings.json')
    runner.write(out/'settings.json', config)
    pins = runner._pins(config, out, [HERE/'preparation_seal.json', *map(Path, seal['input_pins'])])
    runner.write(out/'inputs_before.json', pins)
    random.seed(7); np.random.seed(7); torch.manual_seed(7); torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    pool = None; failure = None; completed = False; calls = []; started = time.monotonic()
    original_function = hand_collision.left_hand_collision_properties
    expected = read(HERE/'cpu_inputs'/(condition+'_collision.json'))
    try:
        with collision_wrapper(condition, seal['external_filters'], expected, calls):
            pool = ShortPool(config, out)
        assert hand_collision.left_hand_collision_properties is original_function
        assert len(calls) == 1 and pool.scene.physics_steps == 0
        assert pool.scene.metadata['hand_collision'] == expected['submitted_contract']
        assert pool.scene._hand_collision_readback_count == 4
        runner.write(out/'collision_condition.json', calls[0])
        runner.write(out/'training_contract.json', pool.contract)

        class ReferencePlaceholder:
            def act(self, *args, **kwargs):
                # Original evaluator overwrites this tensor in its reference branch.
                return {'action': pool.scene.q.new_zeros((4, 39))}

        runner._evaluate(pool, ReferencePlaceholder(), pool.spec,
            argparse.Namespace(episodes=4, control='reference', reference=str(REFERENCE)), out)
        owned(out, identity)
        evaluation = read(out/'evaluation.json')
        assert evaluation['assigned_quotas'] == [1]*4
        assert len(evaluation['episodes']) == 4
        assert sorted(r['env_id'] for r in evaluation['episodes']) == list(range(4))
        assert all(0 < r['steps'] <= pool.spec['view']['duration_ticks'] for r in evaluation['episodes'])
        assert pool.scene.physics_steps == 4*max(r['steps'] for r in evaluation['episodes'])
        trace = np.load(out/'trace_env0_episode0.npz', allow_pickle=False)
        names = pool.scene.metadata['body_names']
        body_names = ['human/LH:index'+str(i) for i in (1, 2, 3)] + ['human/LH:middle1']
        ids = [names.index(n) for n in body_names]
        selected = trace['net_body_force_n'][:, ids]
        np.savez_compressed(out/'pair_forces_env0.npz', time_s=trace['time_s'],
            body_names=np.asarray(body_names), body_indices=np.asarray(ids), force_W_n=selected,
            resultant_n=np.linalg.norm(selected.astype(np.float64), axis=-1))
        assert pool.scene.physics_steps % 4 == 0
        assert pool.scene.physics_steps <= pool.spec['view']['duration_ticks']*4
        assert not list(out.glob('*.pt'))
        completed = True
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        close_failure = None
        try:
            if pool is not None:
                pool.close()
        except BaseException as error:
            close_failure = dict(type=type(error).__name__, message=str(error))
        owned(out, identity)
        changed = [p for p, value in pins.items() if not Path(p).is_file() or sha(p) != value]
        missing = sorted(project_source_paths(list(sys.modules.items())) - set(pins))
        final = read(out/'gpu_scene_final.json') if (out/'gpu_scene_final.json').is_file() else {}
        verified = not changed and not missing
        restored = hand_collision.left_hand_collision_properties is original_function
        runner.write(out/'inputs_after.json', dict(verified=verified, changed_paths=changed,
            unpinned_project_sources=missing, input_pins=pins))
        runner.write(out/'report.json', dict(schema=SCHEMA, condition=condition,
            completed=completed and verified and restored and not close_failure and final.get('closed') is True,
            closed=final.get('closed') is True, failure=failure, close_failure=close_failure,
            changed_inputs=changed, unpinned_project_sources=missing, wrapper_calls=len(calls), wrapper_restored=restored,
            wall_s=time.monotonic()-started, no_NN_or_checkpoint=True,
            force_scope='env0 first attempt 60Hz native body resultant, including failure endpoint; '
                        'not pair pressure or 240Hz extrema'))
        if failure is None and (not verified or not restored or close_failure or not final.get('closed')):
            raise RuntimeError('Source/close verification failed; outputs preserved')


def launch(condition, out, seal_path):
    reject_existing(out)  # Before seal access and, critically, before native import.
    seal = read(seal_path)
    if seal['independent_review'] != 'passed_no_findings':
        raise ValueError('Independently reviewed CPU preparation required')
    if any(not Path(p).is_file() or sha(p) != h for p, h in seal['input_pins'].items()):
        raise ValueError('Preparation input SHA changed')
    out.mkdir(parents=True, exist_ok=False)
    identity = (out.stat().st_dev, out.stat().st_ino)
    write(out/'invocation.json', dict(argv=sys.argv, condition=condition, schema=SCHEMA,
        source_scope='current v3 source only; no historical checkpoint/NN; two separate scene invocations'))
    try:
        import isaacgym  # Native import before NumPy/Torch; root executes this branch only.
        execute(condition, out, identity, seal)
    except BaseException as error:
        owned(out, identity)
        if not (out/'report.json').exists():
            write(out/'report.json', dict(schema=SCHEMA, completed=False, closed=False,
                failure=dict(type=type(error).__name__, message=str(error)),
                scope='Failure before normal native lifecycle report; original exception propagated'))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', action='store_true')
    action.add_argument('--self-test', action='store_true')
    action.add_argument('--dry-plan', action='store_true')
    action.add_argument('--execute', action='store_true')
    parser.add_argument('--condition', choices=CONDITIONS)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    if args.dry_plan:
        print(json.dumps([dict(condition=c, out=str(HERE/'runs'/c),
            argv=[PYTHON, '-B', str(Path(__file__).resolve()), '--execute', '--condition', c])
            for c in CONDITIONS], indent=2))
    elif args.prepare:
        prepare()
    elif args.self_test:
        print(json.dumps(cpu_checks()[3], indent=2))
    else:
        if args.condition is None:
            raise ValueError('Predeclared condition required')
        launch(args.condition, HERE/'runs'/args.condition, HERE/'preparation_seal.json')


if __name__ == '__main__':
    main()
