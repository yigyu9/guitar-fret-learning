"""No-CUDA source-body, reference replay, guard and resource-lifecycle fixtures."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent/'index_release_clearance_v1/runs/reference'
INPUT_PATHS = {REFERENCE/name for name in ('settings.json', 'training_contract.json', 'observations4.npz', 'trace_env0_episode0.npz')}


def load_support():
    spec = importlib.util.spec_from_file_location('release_hinge_support_cpu', HERE/'support.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check(probe=None):
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning import runtime
    from guitar_learning.song.task import make_task
    torch.set_num_threads(1)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    rng = torch.get_rng_state().clone()
    with patch.object(torch.nn.Module, '__init__', side_effect=AssertionError('NN forbidden')), patch.object(torch, 'load', side_effect=AssertionError('Checkpoint forbidden')):
        s = load_support()
        settings = json.loads((REFERENCE/'settings.json').read_text())
        short = settings['song']['short_learning']
        contract = json.loads((REFERENCE/'training_contract.json').read_text())['action']['target_contract']
        data = dict(np.load(REFERENCE/'observations4.npz', allow_pickle=False))
        trace = dict(np.load(REFERENCE/'trace_env0_episode0.npz', allow_pickle=False))
        assert len(data['clock']) == 1416 and len(trace['time_s']) == 354
        # Executed historical functions are the exact named AST nodes, with no module imports.
        for key, names in s.REUSED.items():
            for name in names:
                node = s.source_node(s.SOURCES[key], name)
                assert isinstance(node, ast.FunctionDef) and not node.decorator_list
        own = s.source_node(HERE/'support.py', 'Environment._episode')
        original = s.source_node(s.SOURCES['prefix'], 'PrefixEnvironment._episode')
        assert ast.dump(own, include_attributes=False) == ast.dump(original, include_attributes=False)
        assert s.Pool._wrist_feedback is s._wrist_feedback and s.transition_fraction is s.wrist_weight
        task = make_task(settings['song_training']['bundle'], pre_roll_s=3., tail_s=.5)
        view, catalog = s.view_and_catalog(task)
        for key in ('source_indices', 'source_targets', 'score_offset_s', 'duration_ticks', 'local_end_s', 'next_press_s'):
            assert view[key] == short['view'][key]
        assert len(catalog.phrases) == 1 and catalog.phrases[0].target_indices == (4, 7, 8)
        reference = torch.tensor(contract['reference105_rad'], dtype=torch.float32)
        active = torch.tensor([contract['joint_names'].index(n) for n in contract['action_order']])
        low = torch.tensor(contract['action_lower_rad'], dtype=torch.float32)
        high = torch.tensor(contract['action_upper_rad'], dtype=torch.float32)
        ids = short['learned_action_indices']
        old_trace_targets = torch.cat((reference[None], torch.from_numpy(trace['target'][:-1])), 0)
        targets = old_trace_targets.repeat_interleave(4, 0)
        targets[:, active[ids]] = torch.from_numpy(data['old_target_rad'])
        incremental = torch.zeros(39, dtype=torch.bool)
        incremental[17:33] = True
        pool = SimpleNamespace(spec=copy.deepcopy(short), teacher_reference=reference[active], incremental_mask=incremental,
            controller=SimpleNamespace(reference=reference, active=active, action_low=low, action_high=high, target=targets),
            environment=SimpleNamespace(_local_time=lambda: torch.from_numpy(data['start_clock']).double()/240))
        desired = s.desired_reference(pool)
        raw = s.reference_raw(pool)
        physical, goals = s.convert(pool, raw)
        assert torch.equal(physical[:, ids], torch.from_numpy(data['requested_reference_action']))
        assert torch.equal(goals, torch.from_numpy(data['decoded_goal_rad']))
        assert torch.equal(raw[:, ids], torch.from_numpy(data['raw_goal_normalized']))
        other = [i for i in range(39) if i not in ids]
        assert torch.equal(raw[:, other], physical[:, other])
        env0 = data['env_id'] == 0
        np.testing.assert_array_equal(physical[env0].numpy(), trace['policy_action'])
        roundtrip = float((goals-desired[:, ids]).abs().max())
        assert roundtrip <= 4*torch.finfo(torch.float32).eps
        # Candidate changes only original N PIP/DIP, and vanishes outside the original N weight.
        before = desired.clone()
        pool.spec['reference_release_schedule']['negative_selected_rad'][2:] = [math_radians(40), math_radians(10)]
        candidate = s.desired_reference(pool)
        weight = s.negative_weight(pool.environment._local_time()+1/60, short['view'])
        changed_columns = (candidate != before).any(0).nonzero().flatten().tolist()
        assert changed_columns == [19, 20]
        assert torch.equal(candidate[weight == 0], before[weight == 0])
        assert torch.equal(candidate[:, [17, 18]], before[:, [17, 18]])
        assert bool(((candidate >= low) & (candidate <= high)).all())
        request, _ = s.convert(pool, s.reference_raw(pool))
        assert bool((request.abs() <= 1).all())
        next_selected = (targets[:, active[ids]]+request[:, ids]*(4/60)).clamp(low[ids], high[ids])
        assert bool(((next_selected-targets[:, active[ids]]).abs() <= 4/60+1e-7).all())
        assert torch.equal(pool.controller.target, targets)
        bounds = s.boundaries(short['view'])
        time = torch.tensor([bounds[0]-.01, bounds[0], bounds[1], bounds[2], bounds[3], bounds[3]+.01], dtype=torch.float64)
        assert torch.allclose(s.negative_weight(time, short['view']), torch.tensor([0., 0., 1., 1., 0., 0.], dtype=torch.float64), atol=1e-14, rtol=0)
        assert torch.allclose(s.wrist_weight(time, short['view']), torch.tensor([0., 0., 0., 1., 1., 1.], dtype=torch.float64), atol=1e-14, rtol=0)
        assert abs(bounds[2]-bounds[1]-.4417) < 1e-12
        # Reset changes only that environment's inverse-codec input and teacher memory.
        pool.spec = copy.deepcopy(short)
        pool.controller.target = targets.clone()
        pool.controller.target[1, active[ids]] = high[ids]
        after_reset, _ = s.convert(pool, raw)
        assert torch.equal(after_reset[2:], physical[2:]) and bool((after_reset[1, ids] <= 0).all())
        partial_reset(s, torch)
        guard_checks(s, torch)
        effort = effort_checks(s, prepared_reset_v1, np)
        constructor_checks(s, runtime, prepared_reset_v1)
        invalid = torch.full((1, 4), float('nan'))
        for value in (invalid, torch.full((1, 4), 1.01)):
            try:
                s.decode(value, *s.bounds(pool))
            except ValueError:
                pass
            else:
                raise AssertionError('Invalid raw goal accepted')
    assert torch.equal(torch.get_rng_state(), rng)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    assert not any(name.startswith('guitar_learning.archive') or name.startswith('guitar_learning.skills') for name in sys.modules)
    return dict(CPU_only=True, GPU_executed=False, CUDA_initialized=False, NN_created=0, checkpoints_loaded=0,
        historical_reference_rows=1416, selected4_raw_goal_exact=True, selected4_decoded_goal_exact=True,
        selected4_physical_request_exact=True, full39_env0_trace_exact=True, goal_roundtrip_max_rad=roundtrip,
        candidate_changed_action_columns=changed_columns, candidate_N_only=True, candidate_initial_press_and_other35_unchanged=True,
        native_inverse_codec_rate4_and_limits=True, staged_clock_exact=True, wrist_move_duration_s=bounds[2]-bounds[1],
        named_original_AST_only=True, episode_method_AST_exact=True, current_catalog_selected_4_7_8=True,
        original_guard=guard_checks.__name__, guard_cases=8, native105_PD_fixture=effort,
        partial_reset_and_empty_reset=True, loader_finally_and_scene_cleanup=True,
        constructor_finally_restores_target_callback=True, RNG_unchanged=True)


def math_radians(degrees):
    import math
    return degrees*math.pi/180


def partial_reset(s, torch):
    # Exercise the current ShortPool.reset method with actual own reset bookkeeping.
    from guitar_learning.training.rollout import GpuPool
    fake = SimpleNamespace(num_envs=4, scene=SimpleNamespace(device=torch.device('cpu')),
        initial_wrist_position=torch.ones(4, 3), initial_wrist_quaternion=torch.ones(4, 4),
        wrist_correction=torch.ones(4, 12), previous_arm_request=torch.ones(4, 12),
        controller=SimpleNamespace(reference=torch.arange(105, dtype=torch.float32), active=torch.arange(39)),
        environment=SimpleNamespace(local_bodies=torch.zeros(4, 1, 3), wrist_index=0,
            guitar_q=torch.tensor([[0., 0., 0., 1.]]).repeat(4, 1),
            body=torch.tensor([[[0., 0., 0., 0., 0., 0., 1.]]]).repeat(4, 1, 1)))
    with patch.object(GpuPool, 'reset', return_value=('observation', [])):
        # Bind as a subclass so the original zero-argument super resolves correctly.
        pool = object.__new__(s.Pool)
        pool.__dict__.update(fake.__dict__)
        result = s.runtime.ShortPool.reset(pool, torch.tensor([1]))
        assert result == ('observation', [])
        assert not bool(pool.wrist_correction[1].any()) and bool((pool.wrist_correction[[0, 2, 3]] == 1).all())
        assert torch.equal(pool.previous_arm_request[1], torch.arange(12, dtype=torch.float32))
        frozen = {k: getattr(pool, k).clone() for k in ('initial_wrist_position', 'initial_wrist_quaternion', 'wrist_correction', 'previous_arm_request')}
        s.runtime.ShortPool.reset(pool, torch.empty(0, dtype=torch.long))
        assert all(torch.equal(getattr(pool, k), value) for k, value in frozen.items())


def guard_checks(s, torch):
    score = torch.tensor([0., 1., 2., 3.], dtype=torch.float64)
    col, present = s.current_goal(score, torch.tensor([1., 2., 3.], dtype=torch.float64))
    assert col.tolist() == [0, 1, 2, 0] and present.tolist() == [True, True, True, False]
    n = 8
    target = torch.zeros(n, 105)
    controller = SimpleNamespace(target=target, lower=torch.full((105,), -1.), upper=torch.ones(105),
        action_low=torch.full((39,), -1.), action_high=torch.ones(39), rate=torch.full((105,), 4.))
    snapshot = dict(q=target.clone(), qd=target.clone(), body_state=torch.zeros(n, 2, 13),
        contact_force=torch.zeros(n, 2, 3), reset_body_snapshot=torch.zeros(n, dtype=torch.bool))
    snapshot['reset_body_snapshot'][4] = True
    candidate = torch.ones(n, dtype=torch.bool)
    candidate[5] = False
    wrong = torch.zeros(n, dtype=torch.bool)
    wrong[6] = True
    failed = torch.zeros(n, dtype=torch.bool)
    failed[7] = True
    def original(action, sample):
        target[:, 59] += action[:, 20]*(4/60)
        target[:, 1] += .01
        return target
    action = torch.ones(n, 39)
    action[1, 20] = -1
    action[2, 20] = 0
    action[3, 20] = -.5
    _, evidence = s.target_filter(controller, original, action, snapshot, torch.ones(n, dtype=torch.bool),
        candidate, wrong, failed, 59, 20, True)
    assert evidence['blocked'].tolist() == [True, False, False, False, False, False, False, False]
    assert target[0, 59] == 0 and target[1, 59] < 0 and target[2, 59] == 0 and target[3, 59] < 0
    assert bool((target[4:, 59] > 0).all()) and bool((target[:, 1] == .01).all())
    assert not bool(evidence['other104_error_rad'].any())
    # Run the real Pool.targets current-goal routing on a later episode: first=False must still guard.
    pool = object.__new__(s.Pool)
    pool.num_envs = n
    pool.scene = SimpleNamespace(device=torch.device('cpu'))
    pool.first = torch.zeros(n, dtype=torch.bool)
    pool.dip, pool.ai, pool.controller, pool.native_targets = 59, 20, controller, original
    pool.environment = SimpleNamespace(_score_time=lambda: torch.full((n,), 2.), end=torch.tensor([9., 9., 9., 9., 1., 9., 9., 2.5, 3.]),
        candidate=torch.ones(n, 9, dtype=torch.bool), wrong=torch.zeros(n, 9, dtype=torch.bool),
        failure=torch.zeros(n, 1, dtype=torch.bool), wrist_failure=torch.zeros(n, dtype=torch.bool),
        wrist_severe_failure=torch.zeros(n, dtype=torch.bool), clock=torch.zeros(n, dtype=torch.long))
    snapshot['reset_body_snapshot'].zero_()
    old = target[:, 59].clone()
    s.Pool.targets(pool, torch.ones(n, 39), snapshot)
    assert pool.pending['current_goal'].tolist() == [7]*n and bool(pool.pending['blocked'].all())
    assert torch.equal(old, target[:, 59]) and not bool(pool.pending['first_attempt'].any())


def effort_checks(s, prepared_reset_v1, np):
    original = prepared_reset_v1.load_prepared_reset_contract
    source = original()
    frozen = copy.deepcopy(source)
    private, document = s.private_contract(source)
    np.testing.assert_equal(source, frozen)
    dtype = np.dtype([(name, np.bool_ if name == 'hasLimits' else np.int32 if name == 'driveMode' else np.float32)
        for name in source['initial']['native_PD_properties']])
    baseline = s.expected_properties(source, dtype)
    expected = baseline.copy()
    expected['effort'][document['native_indices']] = s.CAP
    scene = SimpleNamespace(pd_properties=expected, contract=private, physics_steps=0,
        hand_collision=dict(enabled_distinct_finger_pairs=90), _hand_collision_readback_count=128, num_envs=128)
    s.verify_native(scene, source, document)
    for field, index, value in (('effort', document['native_indices'][0], 20.), ('effort', 51, .25),
            ('stiffness', 56, 13.), ('damping', 51, 2.), ('driveMode', 56, 0)):
        scene.pd_properties = expected.copy()
        scene.pd_properties[field][index] = value
        try:
            s.verify_native(scene, source, document)
        except AssertionError:
            pass
        else:
            raise AssertionError('Incorrect native PD property accepted')
    calls = []
    try:
        with s.effort_loader(calls):
            value = prepared_reset_v1.load_prepared_reset_contract()
            assert value is not source
            raise RuntimeError('loader fixture')
    except RuntimeError as error:
        assert str(error) == 'loader fixture'
    assert prepared_reset_v1.load_prepared_reset_contract is original and len(calls) == 1
    np.testing.assert_equal(original(), frozen)
    return dict(native_axes=105, changed_effort_axes=16, unchanged_other_axes=89,
        environments=128, native_bad_fields_rejected=5, original_contract_unchanged=True)


def constructor_checks(s, runtime, prepared_reset_v1):
    original = prepared_reset_v1.load_prepared_reset_contract
    closed = []
    scene = SimpleNamespace(close=lambda: closed.append('scene'))
    pool = object.__new__(s.Pool)
    pool.cleanup_errors = []
    def failed_scene(*args):
        prepared_reset_v1.load_prepared_reset_contract()
        raise ValueError('primary construction')
    with patch.object(runtime.ShortPool, '_create_scene', failed_scene):
        try:
            s.Pool._create_scene(pool, {}, None)
        except ValueError as error:
            assert str(error) == 'primary construction'
        else:
            raise AssertionError('Scene construction error lost')
    assert prepared_reset_v1.load_prepared_reset_contract is original
    def fake_scene(*args):
        prepared_reset_v1.load_prepared_reset_contract()
        return scene
    with patch.object(runtime.ShortPool, '_create_scene', fake_scene), patch.object(s, 'verify_native', side_effect=ValueError('readback failure')):
        try:
            s.Pool._create_scene(pool, {}, None)
        except ValueError as error:
            assert str(error) == 'readback failure'
        else:
            raise AssertionError('Readback failure lost')
    assert closed == ['scene'] and prepared_reset_v1.load_prepared_reset_contract is original
    def fake_init(self, *args):
        self.closed = False
        self.scene = scene
        self.controller = SimpleNamespace(targets=lambda: None)
        self.native_targets = self.controller.targets
        self.controller.targets = lambda: 'temporary'
        raise ValueError('post scene constructor')
    with patch.object(runtime.ShortPool, '__init__', fake_init):
        try:
            s.Pool({}, None)
        except ValueError as error:
            assert str(error) == 'post scene constructor'
        else:
            raise AssertionError('Constructor exception lost')
    assert closed == ['scene', 'scene']


if __name__ == '__main__':
    sys.path.insert(0, str(HERE.parents[4]))
    print(json.dumps(check(), ensure_ascii=False, indent=2))
