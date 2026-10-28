"""CPU preparation and root-only native4 scripted three-note prefix."""
import argparse
import copy
from contextlib import contextmanager
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TARGET7 = HERE.parent/'index_target7_reference_v1'
spec = importlib.util.spec_from_file_location('prefix_target7_evidence', TARGET7/'probe.py')
prior = importlib.util.module_from_spec(spec); sys.modules[spec.name] = prior; spec.loader.exec_module(prior)
base, grid, cap = prior.prior, prior.grid, prior.cap


def support():
    name = 'diagnostic_index_prefix_runtime'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, HERE/'prefix_runtime.py')
        value = importlib.util.module_from_spec(spec); sys.modules[name] = value; spec.loader.exec_module(value)
    return sys.modules[name]


def evidence():
    paths = prior.actual_gate()
    root = TARGET7/'analysis/results_v1'; review = grid.read(root/'review.json')
    assert review['verdict'] == 'PASS' and not review['findings']
    assert str(root/'verification.json') in review['reviewed_sha256']
    for mapping in (review['reviewed_sha256'], *[grid.read(root/'verification.json')[key] for key in ('input_sha256', 'verified_input_sha256')]):
        assert mapping and all(Path(p).is_file() and grid.sha(p) == h for p, h in mapping.items())
        paths.update(map(Path, mapping))
    assert grid.read(root/'comparison.json')['acceptance']['passed']
    return paths | {root/'review.json', TARGET7/'probe.py', TARGET7/'cpu_inputs/teacher_index_target7.json'}


def settings():
    return grid.read(HERE/'cpu_inputs/index_settings.json')


def gate(require_review=True):
    paths = evidence(); seal = grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p) == h for p, h in seal['input_pins'].items())
    if require_review:
        review = grid.read(HERE/'review.json')
        assert seal['independent_review'] == 'passed_no_findings' and review['verdict'] == 'PASS' and not review['findings']
        assert seal['input_pins'][str(HERE/'review.json')] == grid.sha(HERE/'review.json')
    return seal, paths | {HERE/'preparation_seal.json'}


@contextmanager
def execution_scope(state):
    from guitar_learning.tool.experiments.short_finger_learning import runtime, runner
    extra = support()
    old = (base.HERE, base.INPUTS, base.settings, runtime.ShortPool, runner._evaluate)
    class CheckedPool(extra.PrefixPool):
        def __init__(self, config, out):
            super().__init__(config, out)
            try:
                import torch
                env = self.environment
                assert env.contract == grid.read(HERE/'cpu_inputs/expected_environment.json')
                assert [asdict(t) for t in env.task.targets] == grid.read(HERE/'cpu_inputs/source_task.json')['targets']
                assert env.selected_indices == (4, 7, 8) and env.M == 67
                expected = torch.zeros_like(env.focus_mask); expected[:, [4, 7, 8]] = True
                assert torch.equal(env.focus_mask, expected) and bool((env.duration_ticks == 354).all())
                grid.write(Path(out)/'prefix_native_task.json', dict(expected_environment_exact=True, original67_targets_exact=True,
                    focus_indices=[4, 7, 8], environment_count=4, duration_ticks=354, source_view=self.spec['view']))
                state['task_verified'] = True
            except BaseException:
                try: self.close()
                except BaseException as error: state['cleanup_errors'].append(dict(type=type(error).__name__, message=str(error)))
                raise
    base.HERE = HERE; base.INPUTS = dict(old[1]); base.settings = lambda finger: settings() if finger == 'index' else None
    runtime.ShortPool = CheckedPool; runner._evaluate = extra.evaluate
    try: yield
    finally:
        base.HERE, base.INPUTS, base.settings, runtime.ShortPool, runner._evaluate = old
        state['aliases_restored'] = all(a is b for a, b in zip((base.HERE, base.INPUTS, base.settings, runtime.ShortPool, runner._evaluate), old))


def postcheck(out):
    import numpy as np
    import torch
    doc = grid.read(out/'evaluation.json'); rows = doc['episodes']; config = settings(); short = config['song']['short_learning']
    assert grid.complete(rows, 4) and doc['assigned_quotas'] == [1]*4 and doc['policy_performance'] is False
    assert all(r['selected_target_count'] == 3 and len(r['notes']) == 3 and len(r['reward_components']) == 9 and r['steps'] <= 354 for r in rows)
    by_note = {}
    for column, target in enumerate(short['view']['source_targets']):
        one = []
        for row in rows:
            note = row['notes'][column]; assert note['target_id'] == target['target_id'] and note['source_index'] == [4, 7, 8][column]
            one.append(dict(note, env_id=row['env_id'], termination=row['termination']))
        by_note[target['target_id']] = cap.repro.acceptance(one)
    with np.load(out/'trace_env0_episode0.npz') as saved: trace = dict(saved)
    meta = grid.read(out/'trace_metadata.json'); ids = [meta['joint_names'].index(n) for n in short['learned_action_names']]
    assert trace['candidate'].shape == trace['wrong'].shape == trace['released'].shape == (len(trace['time_s']), 3)
    np.testing.assert_allclose(trace['source_time_s'], trace['time_s']+short['view']['score_offset_s'], rtol=0, atol=1e-8)
    assert np.all(np.diff(np.rint(trace['time_s']*240)) == 4)
    target = trace['target'][:, ids]; native = grid.read(out/'native_effort_readback.json')['actual_native_PD105']
    assert np.isfinite(target).all() and ((target >= np.array(native['lower'])[ids]-2e-6) & (target <= np.array(native['upper'])[ids]+2e-6)).all()
    rate = float(abs(np.diff(target, axis=0)).max()) if len(target)>1 else 0.
    assert rate <= 4/60+2e-6
    hold = trace['time_s'] >= 2.; reference = grid.read(base.INPUTS['index'][1])
    np.testing.assert_allclose(target[hold], np.broadcast_to([reference['selected_targets_rad'][n] for n in short['learned_action_names']], target[hold].shape), rtol=0, atol=2e-6)
    weight = support().transition_fraction(torch.tensor(trace['time_s']), short['view']).numpy()
    goal = np.array(short['teacher']['wrist_position_G_m'])+weight[:, None]*np.array(short['prefix']['delta_G_m'])
    np.testing.assert_allclose(trace['wrist_position_goal_G_m'][hold], goal[hold], rtol=0, atol=2e-6)
    np.testing.assert_allclose(abs(trace['wrist_quaternion_goal_G_xyzw'][hold]@np.array(short['teacher']['wrist_quaternion_G_xyzw'])), 1., rtol=0, atol=2e-6)
    return dict(per_note_original_acceptance=by_note, prefix_passed=all(a['passed'] for a in by_note.values()),
        all3_achieved_attempts=sum(r['achieved'] for r in rows), attempts=4, env0_endpoints=len(target),
        selected_max_endpoint_delta_rad=rate, rate_scope='stored endpoint differences only; t0 not saved',
        postramp_endpoints=int(hold.sum()), postramp_goals_match=True if hold.any() else None,
        scope='each original music acceptance separately; no new release requirement, acoustic/free-guitar/NN claim')


def launch():
    out = HERE/'runs/index'; cap.reject_existing(out); seal, paths = gate()
    out.mkdir(parents=True, exist_ok=False); identity = (out.stat().st_dev, out.stat().st_ino)
    state = dict(task_verified=False, aliases_restored=False, cleanup_errors=[]); failure = None; completed = False
    try:
        import isaacgym
        with execution_scope(state): base.execute('index', 'reference', out, identity, seal, paths)
        grid.write(out/'prefix_acceptance.json', postcheck(out)); completed = True
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        if not (out/'report.json').exists(): grid.write(out/'report.json', dict(completed=False, closed=False, failure=failure))
        raise
    finally:
        cap.owned(out, identity); ok = state['task_verified'] and state['aliases_restored'] and not state['cleanup_errors']
        grid.write(out/'prefix_scope_report.json', dict(completed=completed and ok, failure=failure, **state))
        if failure is None and not ok: raise RuntimeError('Prefix scope failed; outputs preserved')


def prepare():
    assert not any(n in sys.modules for n in ('numpy', 'torch', 'isaacgym'))
    paths = evidence(); cap.reject_existing(HERE/'cpu_inputs'); cap.reject_existing(HERE/'preparation_seal.json')
    import torch
    from guitar_learning.song.task import make_task
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    config = base.settings('index'); task = make_task(config['song_training']['bundle'], pre_roll_s=3., tail_s=.5)
    extra = support(); view, _ = extra.view_and_catalog(task)
    a = config['song']['short_learning']['teacher']; b = grid.read(TARGET7/'cpu_inputs/teacher_index_target7.json')
    assert a['arm_targets_rad'] == b['arm_targets_rad'] and a['wrist_quaternion_G_xyzw'] == b['wrist_quaternion_G_xyzw']
    delta = [y-x for x, y in zip(a['wrist_position_G_m'], b['wrist_position_G_m'])]
    short = config['song']['short_learning']; short.update(schema=extra.SCHEMA, view=view,
        prefix=dict(source_indices=[4, 7, 8], delta_G_m=delta, transition='linear wrist position from original A end to shared B press; hold B across gap',
            A_teacher_source=str(base.INPUTS['index'][0]), B_teacher_source=str(TARGET7/'cpu_inputs/teacher_index_target7.json')),
        schedule='fixed original3note prefix; next same-finger press cap; not full-song switch',
        result_scope='conditional noNN index prefix4/7/8; other fingers excluded; original predicates/rewards; separate native release latches')
    inputs = HERE/'cpu_inputs'; inputs.mkdir()
    grid.write(inputs/'index_settings.json', config); grid.write(inputs/'settings.json', config)
    grid.write(inputs/'source_task.json', dict(targets=[asdict(t) for t in task.targets], provenance=task.provenance))
    metadata, _ = fixture(4); metadata['action_contract'] = grid.read(base.FRESH/'runs/index/training_contract.json')['action']['target_contract']
    env = extra.PrefixEnvironment(metadata, bundle=config['song_training']['bundle'], song=config['song'], skill=config['finger_skill'], device='cpu')
    grid.write(inputs/'expected_environment.json', env.contract)
    declaration, checks = base.cpu_checks(); grid.write(inputs/'effort_declaration.json', declaration)
    tests = importlib.util.spec_from_file_location('prefix_cpu_checks', HERE/'cpu_checks.py'); checks_module = importlib.util.module_from_spec(tests); tests.loader.exec_module(checks_module)
    checks.update(checks_module.check(sys.modules[__name__], config, metadata))
    grid.write(HERE/'cpu_verification.json', checks)
    grid.write(inputs/'commands.json', [dict(finger='index', control='reference', episodes=4, argv=[grid.PYTHON, '-B', str(Path(__file__).resolve()), '--execute'])])
    paths.update(inputs.glob('*.json')); paths.update((Path(__file__).resolve(), HERE/'prefix_runtime.py', HERE/'cpu_checks.py', HERE/'PLAN.md', HERE/'cpu_verification.json'))
    paths.update(base.INPUTS['index']); paths.update(Path(row['path']) for row in task.provenance['provenance'])
    grid.write(HERE/'preparation_seal.json', dict(independent_review='pending', input_pins=runner._pins(config, inputs, paths), scope='CPU prepared only; root-only native4 noNN prefix'))
    result = subprocess.run([grid.PYTHON, '-B', str(Path(__file__).resolve()), '--gate-check'], text=True, capture_output=True, check=True)
    grid.write(HERE/'fresh_process_gate.json', json.loads(result.stdout)); seal = grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')] = grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal, ensure_ascii=False, indent=2)+'\n')
    print(dict(CPU_only=True, GPU_executed=False, pins=len(seal['input_pins']), native_trials=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); group = parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare', 'execute', 'gate-check', 'dry-plan'): group.add_argument('--'+name, action='store_true')
    args = parser.parse_args(); sys.path.insert(0, str(grid.ROOT))
    if args.prepare: prepare()
    elif args.execute: launch()
    elif args.dry_plan: print(json.dumps([dict(finger='index', control='reference', episodes=4, selected_indices=[4, 7, 8], ticks=354, out=str(HERE/'runs/index'))]))
    else:
        assert not any(n in sys.modules for n in ('torch', 'numpy', 'isaacgym')); seal, _ = gate(require_review=False)
        if seal['independent_review'] == 'pending':
            try: launch()
            except (FileNotFoundError, AssertionError): pass
            else: raise AssertionError('Unreviewed native admitted')
        else: gate()
        assert not any(n in sys.modules for n in ('torch', 'numpy', 'isaacgym')) and not (HERE/'runs').exists()
        print(json.dumps(dict(stdlib_gate=True, Torch_imported=False, NumPy_imported=False, IsaacGym_imported=False)))
