"""검수된 V2 참고 동작을 바꾸지 않고 제어 전 관측/목표만 수집한다."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent/'index_release_close_lead_v2'
spec = importlib.util.spec_from_file_location('release_learning_capture_v2', SOURCE/'probe.py')
v2 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v2
spec.loader.exec_module(v2)
base = v2.base
FIELDS = ('state', 'events', 'mask', 'priority_events', 'priority_mask')


def preflight():
    old = base.HERE
    try:
        base.HERE = SOURCE
        pins = base.gate()
    finally:
        base.HERE = old
    source = SOURCE/'runs/candidate'
    report = base.read(source/'report.json')
    audit = base.read(source/'inputs_after.json')
    assert report['completed'] and report['closed'] and report['completed_attempts'] == 128
    assert not report['failure'] and not report['cleanup_errors']
    assert all(report[key] == 0 for key in ('NN_constructors','checkpoint_loads','PPO_updates','fit_steps'))
    assert audit['verified'] and audit['input_pins'] == pins
    assert not base.changed_pins(pins)
    assert base.read(source/'evaluation.json')['acceptance']['stage_ready']
    for name in ('report.json', 'inputs_after.json', 'evaluation.json',
                 'trace_env0_episode0.npz', 'training_contract.json'):
        path = source/name
        pins[str(path)] = base.sha(path)
    return pins


def prepare():
    pins = preflight()
    (HERE/'cpu_inputs').mkdir(exist_ok=False)
    for name in ('candidate.json', 'settings.json'):
        shutil.copy2(SOURCE/'cpu_inputs'/name, HERE/'cpu_inputs'/name)
    (HERE/'runs/baseline').mkdir(parents=True, exist_ok=False)
    reused = {}
    for name in ('report.json', 'evaluation.json'):
        path = SOURCE/'runs/baseline'/name
        target = HERE/'runs/baseline'/name
        shutil.copy2(path, target)
        reused[name] = dict(source=str(path), sha256=base.sha(target))
        pins[str(path)] = base.sha(path)
    base.write(HERE/'reuse_provenance.json', dict(new_native_run=False, baseline=reused))
    paths = [Path(__file__).resolve(), HERE/'cpu_check.py', HERE/'cpu_verification.json',
             HERE.parent/'PLAN.md', HERE/'reuse_provenance.json',
             *list((HERE/'cpu_inputs').glob('*.json')), *list((HERE/'runs/baseline').glob('*.json'))]
    pins.update({str(path.resolve()): base.sha(path) for path in paths})
    base.write(HERE/'preparation_seal.json', dict(input_pins=pins, independent_review='pending',
        purpose='Only pre-control557 observation and selected4 goal capture; noNN'))


def collect_rows(pool, raw, shared):
    """제어 전 관측과 목표를 복사하며 물리 상태와 난수는 바꾸지 않는다."""
    ids = pool.spec['learned_action_indices']
    goal = shared.decode(raw[:, ids], *shared.bounds(pool))
    rows = []
    for i in range(4):
        assert bool(pool.first[i])
        row = dict(env_id=i, clock=int(pool.environment.clock[i]),
                   time_s=float(pool.environment._local_time()[i]))
        values = {key: pool.observation[key][i] for key in FIELDS}
        values.update(raw_goal_normalized=raw[i, ids], decoded_goal_rad=goal[i],
                      old_target_rad105=pool.controller.target[i])
        row.update({key: value.detach().cpu().numpy().copy() for key, value in values.items()})
        rows.append(row)
    return rows


def execute():
    preflight()
    old = base.HERE
    try:
        base.HERE = HERE
        base.gate()
    finally:
        base.HERE = old
    import isaacgym
    import numpy as np
    sys.path.insert(0, str(v2.ROOT))
    shared = base.support()
    original_geometry = base.geometry_function
    records = []

    def reference(pool):
        raw = v2.reference_raw(pool, shared=shared)
        records.extend(collect_rows(pool, raw, shared))
        return raw

    def geometry():
        saved = base.HERE
        try:
            base.HERE = SOURCE
            return original_geometry()
        finally:
            base.HERE = saved

    failure = None
    try:
        with v2.execution_scope():
            base.support().reference_raw = reference
            base.HERE = HERE
            base.SCHEMA = 'diagnostic.release_learning_capture.v4'
            base.geometry_function = geometry
            base.run('candidate')
    except BaseException as error:
        failure = error
        raise
    finally:
        base.geometry_function = original_geometry
        try:
            name = 'observations4.npz' if failure is None else 'partial_observations4.npz'
            base.save_rows(HERE/'runs/candidate'/name, records)
        except BaseException as error:
            if failure is None:
                raise
            try:
                base.write(HERE/'capture_preservation_error.json', dict(error=repr(error)))
            except BaseException as log_error:
                failure.capture_preservation_errors = (repr(error), repr(log_error))
    out = HERE/'runs/candidate'
    try:
        data = np.load(out/'observations4.npz', allow_pickle=False)
        assert len(records) == 1416 and data['state'].shape == (1416,557)
        np.testing.assert_array_equal(data['env_id'], np.tile(np.arange(4),354))
        np.testing.assert_array_equal(data['clock'], np.repeat(np.arange(354)*4,4))
        for key in FIELDS+('raw_goal_normalized','decoded_goal_rad','old_target_rad105'):
            assert bool(np.isfinite(data[key]).all()), key
        trace = np.load(out/'trace_env0_episode0.npz', allow_pickle=False)
        original = np.load(SOURCE/'runs/candidate/trace_env0_episode0.npz', allow_pickle=False)
        for key in ('q','target','body_state','candidate'):
            np.testing.assert_array_equal(trace[key], original[key])
        np.testing.assert_array_equal(data['raw_goal_normalized'][::4], trace['raw_goal_normalized'])
        np.testing.assert_array_equal(data['decoded_goal_rad'][::4], trace['decoded_goal_rad'])
        np.testing.assert_array_equal(data['old_target_rad105'][4::4], trace['target'][:-1])
        assert base.read(out/'evaluation.json')['episodes'] == base.read(SOURCE/'runs/candidate/evaluation.json')['episodes']
        assert base.read(out/'training_contract.json') == base.read(SOURCE/'runs/candidate/training_contract.json')
        base.write(out/'capture_verification.json', dict(completed=True, native=True, noNN=True,
            rows=1416, environments=[0,1,2,3], controls=354, state_dim=557,
            timing='before-control; label uses next endpoint as originalV2',
            q_target_body_candidate_and128ledger_exact=True, source_contract_exact=True))
    except BaseException as error:
        base.write(out/'capture_verification.json', dict(completed=False, failure=repr(error)))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','preflight','execute'))
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'preflight':
        preflight()
        print(json.dumps(dict(ready=True, native_runs=0)))
    else:
        execute()
