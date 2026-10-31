"""공유 noNN 런타임을 유지하고 PIP/DIP 복귀 준비만120ms 앞당긴다."""
import argparse
from contextlib import contextmanager
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent/'index_release_hinge_native_v1'
ROOT = HERE.parents[4]
SCHEMA = 'diagnostic.release_close_lead.v2'
LEAD_S = .12
spec = importlib.util.spec_from_file_location('shared_release_native_v1', PARENT/'probe.py')
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)


def reference_raw(pool, lead_s=LEAD_S, shared=None):
    """두 hinge만 같은120ms closing을 일찍 수행한다. 실제각/속도는 수정하지 않는다."""
    import torch
    shared = base.support() if shared is None else shared
    desired = shared.desired_reference(pool)
    schedule = pool.spec['reference_release_schedule']
    ids = pool.spec['learned_action_indices']
    time = pool.environment._local_time()+1/60
    start, _, _, finish = shared.boundaries(pool.spec['view'])
    weight = ((time-start)/.10).clamp(0, 1)-((time-(finish-.12-lead_s))/.12).clamp(0, 1)
    fraction = (time/pool.spec['teacher']['ramp_s']).clamp(0, 1).to(pool.teacher_reference)
    goal = pool.teacher_reference.clone()
    goal[ids] = goal.new_tensor(schedule['reference_selected_rad'])
    plain = pool.teacher_reference+fraction[:, None]*(goal-pool.teacher_reference)
    hinges = ids[2:]
    desired[:, hinges] = plain[:, hinges]+weight.to(desired)[:, None]*(
        desired.new_tensor(schedule['negative_selected_rad'][2:])-goal[hinges])
    c = pool.controller
    raw = shared.runtime.trajectory_actions(desired, c.target[:, c.active], pool.teacher_reference,
        c.action_low, c.action_high, pool.incremental_mask, max_speed=4.)
    raw[:, ids] = shared.encode(desired[:, ids], *shared.bounds(pool))
    return raw


def cpu_check():
    import numpy as np
    import torch
    torch.set_num_threads(1)
    assert not torch.cuda.is_initialized() and not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    rng = torch.get_rng_state().clone()
    shared = base.support()
    cfg = base.read(PARENT/'cpu_inputs/candidate.json')
    contract = base.read(PARENT/'runs/candidate/training_contract.json')['action']['target_contract']
    z = np.load(PARENT/'runs/candidate/trace_env0_episode0.npz', allow_pickle=False)
    ref = torch.tensor(contract['reference105_rad'], dtype=torch.float32)
    active = torch.tensor([contract['joint_names'].index(n) for n in contract['action_order']])
    lo, hi = (torch.tensor(contract[k], dtype=torch.float32) for k in ('action_lower_rad', 'action_upper_rad'))
    clock = torch.arange(354, dtype=torch.float64)/60
    target = torch.cat((ref[None], torch.from_numpy(z['target'][:-1])), 0)
    mask = torch.zeros(39, dtype=torch.bool); mask[17:33] = True
    pool = SimpleNamespace(spec=copy.deepcopy(cfg['song']['short_learning']),
        teacher_reference=ref[active], incremental_mask=mask,
        controller=SimpleNamespace(reference=ref, active=active, action_low=lo, action_high=hi, target=target),
        environment=SimpleNamespace(_local_time=lambda: clock))
    original = shared.reference_raw(pool)
    assert torch.equal(reference_raw(pool, 0.), original)
    changed = reference_raw(pool)
    original_action, original_goal = shared.convert(pool, original)
    action, goal = shared.convert(pool, changed)
    np.testing.assert_array_equal(original_action.numpy(), z['policy_action'])
    endpoints = clock+1/60
    difference = (goal != original_goal).any(-1)
    assert bool(difference.any())
    assert bool((endpoints[difference] >= 3.592-1e-12).all())
    assert bool((endpoints[difference] <= 3.832+1e-12).all())
    assert torch.equal(goal[:, :2], original_goal[:, :2])
    assert torch.equal(changed[:, :19], original[:, :19]) and torch.equal(changed[:, 21:], original[:, 21:])
    assert torch.equal(changed[~difference], original[~difference])
    assert bool(((goal >= lo[17:21]) & (goal <= hi[17:21])).all()) and bool((action.abs() <= 1).all())
    next_q = (target[:, active[17:21]]+action[:, 17:21]*(4/60)).clamp(lo[17:21], hi[17:21])
    assert bool(((next_q-target[:, active[17:21]]).abs() <= 4/60+2e-7).all())
    assert torch.equal(rng, torch.get_rng_state())
    return dict(CPU_only=True, native_runs=0, zero_lead_bitexact=True, original354_request_bitexact=True,
        only_selected_goal_columns=[19,20], before_new_close_and_after_old_close_bitexact=True,
        MCP_other_actions_unchanged=True, native_range_and_rate4_preserved=True, RNG_unchanged=True,
        closing_lead_s=LEAD_S, closing_duration_s=.12, new_closing_bounds_s=[3.592,3.712],
        unchanged_wrist_bounds_s=[3.2703,3.712], original_music_times_unchanged=True)


def prepare():
    sys.path.insert(0, str(ROOT))
    assert 'isaacgym' not in sys.modules
    pins = base.gate()
    assert not base.changed_pins(pins)
    old = base.read(PARENT/'runs/candidate/evaluation.json')['acceptance']
    assert not old['music_passed'] and not old['stage_ready'] and old['release_passed']
    assert base.read(PARENT/'runs/candidate/report.json')['completed']
    assert base.baseline_matches_original(base.read(PARENT/'runs/baseline/evaluation.json'))
    inputs = HERE/'cpu_inputs'
    inputs.mkdir(exist_ok=False)
    cfg = base.read(PARENT/'cpu_inputs/candidate.json')
    cfg['song']['short_learning']['execution_schedule'] = dict(schema=SCHEMA,
        shared_runtime_schema='diagnostic.release_hinge_native.v1', modified_actions=[19,20],
        closing_lead_s=LEAD_S, original_close_s=[3.712,3.832], new_close_s=[3.592,3.712],
        opening_and_wrist_unchanged=True, original_music_times_unchanged=True,
        scope='Only normalized PIP/DIP reference goal schedule is advanced; no neural policy or physical state override')
    for mode in ('candidate', 'noisy_candidate'):
        value = copy.deepcopy(cfg)
        value['song']['short_learning']['execution_mode'] = mode
        base.write(inputs/(mode+'.json'), value)
    base.write(inputs/'settings.json', cfg)
    reuse = HERE/'runs/baseline'
    reuse.mkdir(parents=True, exist_ok=False)
    for name in ('evaluation.json', 'report.json'):
        shutil.copy2(PARENT/'runs/baseline'/name, reuse/name)
    base.write(HERE/'baseline_reuse.json', dict(new_native_run=False, original_folder=str(PARENT/'runs/baseline'),
        files={name: base.sha(reuse/name) for name in ('evaluation.json','report.json')},
        reason='Same current source/assets/seed; original baseline was exact to historical q/targets/body and gates. No old checkpoint/source pin rewriting.'))
    base.write(HERE/'cpu_verification.json', cpu_check())
    extra = set(map(Path, pins)) | set(inputs.glob('*.json')) | {Path(__file__).resolve(), HERE/'PLAN.md',
        HERE/'cpu_verification.json', HERE/'baseline_reuse.json', PARENT/'preparation_seal.json',
        PARENT/'runs/baseline/report.json', PARENT/'runs/baseline/evaluation.json',
        PARENT/'runs/baseline/trace_env0_episode0.npz', PARENT/'runs/baseline/inputs_after.json',
        PARENT/'runs/candidate/report.json', PARENT/'runs/candidate/evaluation.json',
        PARENT/'runs/candidate/trace_env0_episode0.npz', PARENT/'runs/candidate/training_contract.json',
        reuse/'evaluation.json', reuse/'report.json'}
    from guitar_learning.training.finger_skill_runner import _pins
    current = _pins(cfg, inputs, extra)
    base.write(HERE/'preparation_seal.json', dict(schema=SCHEMA, independent_review='pending', input_pins=current))
    print(json.dumps(dict(CPU_prepared=True, new_native_runs=0, pins=len(current))))


@contextmanager
def execution_scope():
    shared = base.support()
    proxy = SimpleNamespace(Pool=shared.Pool, convert=shared.convert, compact_episode=shared.compact_episode,
                            reference_raw=lambda pool: reference_raw(pool, shared=shared))
    old = base.HERE, base.SCHEMA, base.support
    base.HERE, base.SCHEMA, base.support = HERE, SCHEMA, lambda: proxy
    try:
        yield
    finally:
        base.HERE, base.SCHEMA, base.support = old


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--gate-check', action='store_true')
    group.add_argument('--execute', choices=('candidate','noisy_candidate'))
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.gate_check:
        assert not any(n in sys.modules for n in ('numpy','torch','isaacgym'))
        # The stdlib gate must not initialize the shared numerical support.
        original = base.HERE
        base.HERE = HERE
        try:
            base.gate()
        finally:
            base.HERE = original
        print(json.dumps(dict(stdlib_only=True, ready=True)))
    else:
        # base.run first performs its stdlib gate; do that before numerical support as well.
        original = base.HERE
        base.HERE = HERE
        try:
            base.gate()
        finally:
            base.HERE = original
        import isaacgym
        sys.path.insert(0, str(ROOT))
        with execution_scope():
            base.run(args.execute)
