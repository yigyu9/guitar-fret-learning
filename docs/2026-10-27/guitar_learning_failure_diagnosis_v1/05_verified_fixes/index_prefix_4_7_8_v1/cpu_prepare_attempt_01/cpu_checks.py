"""Bounded fixtures for the explicitly different prefix view and collector."""
import copy
from dataclasses import asdict
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(probe, config, metadata):
    import numpy as np
    import torch
    from guitar_learning.tests.test_short_finger_learning import setup
    from guitar_learning.tool.experiments.short_finger_learning import runtime, runner
    extra = probe.support(); short = config['song']['short_learning']; view = short['view']
    _, snapshot, observation, _, original, _ = setup(count=4)
    env = extra.PrefixEnvironment(metadata, bundle=config['song_training']['bundle'], song=config['song'], skill=config['finger_skill'], device='cpu')
    assert [asdict(t) for t in env.task.targets] == probe.grid.read(probe.HERE/'cpu_inputs/source_task.json')['targets']
    assert view['duration_ticks'] == 354 and (view['minimum_ticks'], view['desired_ticks'], view['maximum_ticks']) == (343, 373, 354)
    np.testing.assert_allclose([view['score_offset_s'], view['local_end_s'], view['next_press_s']-view['score_offset_s']], [2.4497, 5.7051, 5.9102], rtol=0, atol=1e-12)
    assert view['local_end_s'] < 354/60 < view['next_press_s']-view['score_offset_s']
    np.testing.assert_allclose([[t[k]-view['score_offset_s'] for k in ('press_s', 'onset_s', 'end_s')] for t in view['source_targets']],
        [[2.88, 3, 3.1703], [3.832, 3.952, 4.7299], [3.832, 5.3568, 5.7051]], rtol=0, atol=1e-12)
    env.reset(range(4), snapshot)
    expected = torch.zeros_like(env.focus_mask); expected[:, [4, 7, 8]] = True
    assert torch.equal(env.focus_mask, expected) and env.M == 67 and bool((env.duration_ticks == 354).all())
    assert torch.equal(env.finger_weights[:, [4, 7, 8]], torch.ones(4, 3))
    assert env.catalog.phrases[0].opportunities == (3, 0, 0, 0)
    start, finish = 3.1703, 3.832
    times = torch.tensor([0., 2., start-1e-8, start, (start+finish)/2, finish, 4.7299, 5.3568, 5.9], dtype=torch.float64)
    np.testing.assert_allclose(extra.transition_fraction(times, view), [0, 0, 0, 0, .5, 1, 1, 1, 1], rtol=0, atol=1e-12)
    assert float(extra.transition_fraction(torch.tensor(start+1e-8, dtype=torch.float64), view)) < 1e-7
    assert bool(torch.isfinite(extra.transition_fraction(times, view)).all())
    # The initial ramp, quaternion and original v3 arithmetic are identical before motion.
    fake = SimpleNamespace(spec=short, environment=SimpleNamespace(_local_time=lambda: torch.tensor([0., 1., 2., 3.1])),
        initial_wrist_position=torch.zeros(4, 3), initial_wrist_quaternion=torch.tensor([[0., 0., 0., 1.]]*4),
        wrist_correction=torch.zeros(4, 12), previous_arm_request=torch.zeros(4, 12), wrist_position_groups=(),
        controller=SimpleNamespace(active=torch.arange(39), action_low=torch.full((39,), -10.), action_high=torch.full((39,), 10.), rate=torch.full((105,), 4.)))
    fake.environment.wrist_index=0; fake.environment.guitar_index=1
    fake.scene=SimpleNamespace(snapshot=lambda:dict(q=torch.zeros(4, 105), reset_body_snapshot=torch.zeros(4, dtype=torch.bool)), com=torch.zeros(2, 3))
    def error(*args): return torch.zeros(4, 6), torch.zeros(4, 6, 12)
    def bounded(desired, correction, previous, *unused): return desired.clone(), correction.clone(), desired.new_zeros(4, 12), desired.clone()
    with patch.object(runtime, 'wrist_error_and_jacobian', error), patch.object(runtime, 'bounded_wrist_target', bounded):
        desired=torch.zeros(4, 39); fraction=torch.tensor([1/120, 61/120, 1., 1.])
        runtime.ShortPool._wrist_feedback(fake, desired.clone(), fraction); before=copy.deepcopy(fake.last_wrist_feedback)
        extra.PrefixPool._wrist_feedback(fake, desired.clone(), fraction)
        assert all(torch.equal(before[k], fake.last_wrist_feedback[k]) for k in before)
    # Every note and native release latch survives compacting, without changing the9 reward terms.
    env.note['left'][0, [4, 7, 8]] = torch.tensor([True, False, True])
    env.note['released'][0, [4, 7, 8]] = torch.tensor([True, False, True])
    env.note['release_s'][0, [4, 7, 8]] = torch.tensor([5.7, 0., 8.2])
    raw = env._episode(0, False); compact = extra.compact_episode(raw, short)
    assert [n['source_index'] for n in compact['notes']] == [4, 7, 8] and not compact['achieved']
    assert [n['released'] for n in compact['notes']] == [True, False, True]
    assert compact['reward_components'] == raw['reward_components'] and len(compact['reward_components']) == 9
    # Existing collector quota semantics: failed env0 retry is excluded, other first attempts retained.
    env.reset(range(4), snapshot); calls=[]; resets=[]
    scene=SimpleNamespace(q=snapshot['q'], target=snapshot['target'], body_state=snapshot['body_state'], snapshot=lambda:snapshot, names=metadata['joint_names'], metadata=metadata)
    pool=SimpleNamespace(num_envs=4, observation=observation, environment=env, scene=scene,
        teacher_reference=torch.zeros(39), controller=SimpleNamespace(active=torch.arange(39), target=snapshot['target'], action_low=torch.full((39,), -10.), action_high=torch.full((39,), 10.)),
        incremental_mask=torch.ones(39, dtype=torch.bool), last_policy_action=torch.zeros(4,39), last_executed_action=torch.zeros(4,39), last_wrist_feedback=before)
    def step(action):
        calls.append(action.clone()); env.clock += 4; env.steps += 1
        ids=[0] if len(calls)==1 else list(range(4))
        return observation, None, None, torch.tensor([True, False, False, False]), torch.zeros(4, dtype=torch.bool), [env._episode(i, i==0) for i in ids]
    pool.step=step; pool.reset=lambda ids:(resets.append(ids.tolist()) or observation, None)
    saved=(probe.base.HERE, probe.base.INPUTS, probe.base.settings, runtime.ShortPool, runner._evaluate)
    closed=[]
    class FakePool:
        def __init__(self, settings, out):
            self.environment=SimpleNamespace(contract=copy.deepcopy(env.contract), task=env.task, selected_indices=(4,7,8), M=67, focus_mask=expected.clone(), duration_ticks=torch.full((4,),354))
            self.spec=short
            if mode=='wrong_mask': self.environment.focus_mask[:,8]=False
            if mode=='wrong_contract': self.environment.contract['task']['short_learning']['view']['duration_ticks']=373
        def close(self):
            closed.append(True)
            if mode=='wrong_contract': raise RuntimeError('CPU close error')
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        extra.evaluate(pool, probe.base.Actions(short['learned_action_indices'], 'reference'), short,
            SimpleNamespace(control='reference', reference=str(probe.base.INPUTS['index'][1]), episodes=4), root)
        evaluation=probe.grid.read(root/'evaluation.json')
        assert probe.grid.complete(evaluation['episodes'],4) and len(calls)==2 and resets==[[0]]
        assert evaluation['episodes'][0]['reason']=='terminal_failure' and all(len(r['notes'])==3 for r in evaluation['episodes'])
        with np.load(root/'trace_env0_episode0.npz') as trace: assert trace['candidate'].shape==(1,3) and trace['released'].shape==(1,3)
        with patch.object(extra,'PrefixPool',FakePool):
            for mode in ('good','wrong_mask','wrong_contract'):
                folder=root/mode;folder.mkdir();state=dict(cleanup_errors=[]);n=len(closed)
                try:
                    with probe.execution_scope(state): runtime.ShortPool(config,folder)
                except AssertionError: assert mode!='good' and len(closed)==n+1
                else: assert mode=='good' and state['task_verified']
                assert state['aliases_restored'] and probe.base.INPUTS is saved[1]
                assert bool(state['cleanup_errors']) == (mode=='wrong_contract')
        assert all(a is b for a,b in zip((probe.base.HERE,probe.base.INPUTS,probe.base.settings,runtime.ShortPool,runner._evaluate),saved))
        root=root/'guard';out=root/'runs/index';out.mkdir(parents=True);sentinel=out/'keep';sentinel.write_bytes(b'keep')
        with patch.object(probe,'HERE',root),patch.object(probe,'gate',side_effect=AssertionError('must reject before gate')):
            try: probe.launch()
            except FileExistsError: pass
            else: raise AssertionError('Existing output admitted')
            assert sentinel.read_bytes()==b'keep';sentinel.unlink();out.rmdir();out.symlink_to(root/'absent')
            try: probe.launch()
            except (FileExistsError,ValueError): pass
            else: raise AssertionError('Symlink output admitted')
    assert not torch.cuda.is_initialized()
    return dict(prefix_CPU_only=True, native_prefix_trials=0, original67_targets_exact=True, selected_mask_three_only=True,
        three_opportunities_and_original_weights=True, independent_clock354_nextsamefinger_cap=True,
        original_A_ramp_wrist_math_exact=True, piecewise_continuous_finite_hold_B_across_gap=True,
        three_note_compact_original9rewards_and_release_latches=True, four_first_attempts_failed_retry_excluded=True,
        task_mask_contract_errors_and_double_close_error_preserved=True, all_scope_objects_identity_restored=True,
        existing_output_unchanged_symlink_rejected_before_gate=True)
