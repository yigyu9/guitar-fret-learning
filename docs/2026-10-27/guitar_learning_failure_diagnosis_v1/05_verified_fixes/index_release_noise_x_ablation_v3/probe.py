"""V2 noisy noNN reference, with only applied index1_x noise disabled."""
import argparse
import ast
from contextlib import contextmanager
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'index_release_close_lead_v2'
SCHEMA = 'diagnostic.release_noise_x_ablation.v3'
spec = importlib.util.spec_from_file_location('release_noise_v2_source', SOURCE/'probe.py')
v2 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v2
spec.loader.exec_module(v2)
base = v2.base
sys.path.insert(0, str(v2.ROOT))


def transformed_run():
    """Whitelist exactly three AST edits; preserve the original draw/hash/error path."""
    source = inspect.getsource(base.run)
    tree = ast.parse(source)
    hashes, additions, rows = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and ast.dump(node.value.func) == ast.dump(ast.parse('noise_hash.update', mode='eval').body):
            hashes.append(node)
        if isinstance(node, ast.BinOp) and ast.dump(node) == ast.dump(ast.parse('before.atanh() + noise', mode='eval').body):
            additions.append(node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'dict' and any(k.arg == 'raw_noisy_goal' for k in node.keywords):
            rows.append(node)
    assert len(hashes) == len(additions) == len(rows) == 1, 'Upstream noisy branch changed'
    additions[0].right.id = 'applied_noise'
    rows[0].keywords.append(ast.keyword(arg='applied_noise', value=ast.parse('applied_noise[i].cpu().numpy().copy()', mode='eval').body))
    inserted = ast.parse('applied_noise = noise.clone()\napplied_noise[:, 0] = 0.').body
    holders = [n for n in ast.walk(tree) if isinstance(getattr(n, 'body', None), list) and hashes[0] in n.body]
    assert len(holders) == 1
    body = holders[0].body
    index = body.index(hashes[0])+1
    body[index:index] = inserted
    ast.fix_missing_locations(tree)
    namespace = {}
    exec(compile(tree, str(Path(base.__file__).resolve()), 'exec'), base.__dict__, namespace)
    return namespace['run'], hashlib.sha256(source.encode()).hexdigest()


def preflight():
    old = base.HERE
    try:
        base.HERE = SOURCE
        pins = base.gate()
    finally:
        base.HERE = old
    for mode in ('candidate', 'noisy_candidate'):
        folder = SOURCE/'runs'/mode
        report, audit = base.read(folder/'report.json'), base.read(folder/'inputs_after.json')
        assert report['completed'] and report['closed'] and report['completed_attempts'] == 128
        assert not report['failure'] and not report['cleanup_errors']
        assert all(report[k] == 0 for k in ('NN_constructors', 'checkpoint_loads', 'PPO_updates', 'fit_steps'))
        assert audit['verified'] and audit['input_pins'] == pins and not base.changed_pins(audit['input_pins'])
    assert base.read(SOURCE/'runs/candidate/evaluation.json')['acceptance']['stage_ready']
    return pins


@contextmanager
def execution_scope():
    run, _ = transformed_run()
    old = base.run
    try:
        with v2.execution_scope():
            base.HERE, base.SCHEMA, base.run = HERE, SCHEMA, run
            yield
    finally:
        base.run = old


def prepare():
    pins = dict(preflight())
    _, digest = transformed_run()
    (HERE/'cpu_inputs').mkdir(exist_ok=False)
    for name in ('noisy_candidate.json', 'settings.json'):
        shutil.copy2(SOURCE/'cpu_inputs'/name, HERE/'cpu_inputs'/name)
    provenance = {}
    for mode in ('baseline', 'candidate'):
        (HERE/'runs'/mode).mkdir(parents=True, exist_ok=False)
        provenance[mode] = dict(new_native_run=False, original_folder=str(SOURCE/'runs'/mode), files={})
        for name in ('report.json', 'evaluation.json'):
            original = SOURCE/'runs'/mode/name
            target = HERE/'runs'/mode/name
            shutil.copy2(original, target)
            provenance[mode]['files'][name] = base.sha(target)
            pins[str(original)] = base.sha(original)
    for mode in ('candidate', 'noisy_candidate'):
        for name in ('report.json', 'evaluation.json', 'inputs_after.json', 'trace_env0_episode0.npz',
                     'trace_metadata.json', 'reference_noise4.npz', 'training_contract.json'):
            original = SOURCE/'runs'/mode/name
            if original.is_file():
                pins[str(original)] = base.sha(original)
    base.write(HERE/'reuse_provenance.json', provenance)
    base.write(HERE/'experiment.json', dict(schema=SCHEMA, noNN=True, checkpoints_loaded=0,
        seed=7, original_draw_shape=[128,4], selected_action_indices=[17,18,19,20],
        applied_zero_noise_columns=[0], applied_zero_action_names=['index1_x'],
        sigma_and_draws_unchanged=True, V2_schedule_and_goals_unchanged=True,
        original_run_source_sha256=digest, baseline_candidate_are_reused_not_rerun=True))
    from cpu_check import check
    base.write(HERE/'cpu_verification.json', check())
    for path in HERE.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            pins[str(path.resolve())] = base.sha(path)
    base.write(HERE/'preparation_seal.json', dict(schema=SCHEMA, input_pins=pins, independent_review='pending'))
    print(json.dumps(dict(CPU_prepared=True, native_runs=0, pins=len(pins))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'preflight', 'gate-check', 'execute'))
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'preflight':
        preflight()
        print(json.dumps(dict(ready=True, native_runs=0)))
    elif args.action == 'gate-check':
        assert not any(name in sys.modules for name in ('torch', 'numpy', 'isaacgym'))
        old = base.HERE
        try:
            base.HERE = HERE
            base.gate()
        finally:
            base.HERE = old
        print(json.dumps(dict(ready=True, stdlib_only=True)))
    else:
        preflight()
        old = base.HERE
        try:
            base.HERE = HERE
            base.gate()
        finally:
            base.HERE = old
        import isaacgym
        sys.path.insert(0, str(v2.ROOT))
        with execution_scope():
            base.run('noisy_candidate')
        out = HERE/'runs/noisy_candidate'
        try:
            import numpy as np
            original = base.read(SOURCE/'runs/noisy_candidate/trace_metadata.json')['noise_stream_sha256']
            current = base.read(out/'trace_metadata.json')['noise_stream_sha256']
            assert current == original, 'Original full128 noise draw stream changed'
            with np.load(out/'reference_noise4.npz', allow_pickle=False) as data:
                assert bool((data['applied_noise'][:,0] == 0).all())
                np.testing.assert_array_equal(data['applied_noise'][:,1:], data['scaled_noise'][:,1:])
            report = base.read(out/'report.json')
            assert report['completed'] and report['completed_attempts'] == 128
            base.write(out/'experiment_verification.json', dict(completed=True,
                original_full128_noise_hash_preserved=True, only_applied_noise_col0_zero=True,
                noNN=True, attempts=128))
        except BaseException as error:
            base.write(out/'experiment_verification.json', dict(completed=False, failure=repr(error)))
            raise
