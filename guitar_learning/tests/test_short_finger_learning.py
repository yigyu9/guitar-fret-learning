"""CPU contracts, scope, likelihood and partial-reset safety for short diagnostics."""
import copy
import json
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from guitar_learning.core.control import ACTIVE_NAMES, LEFT_ARM_NAMES
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.gpu.simplified_finger_environment import SimplifiedFingerEnvironment
from guitar_learning.song.task import make_task
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE
from guitar_learning.training.gpu_pool import GpuPool
from guitar_learning.training.decision_ppo import DecisionPPOTrainer
from guitar_learning.training.ppo import PPOConfig
from guitar_learning.training.recording import digest
from guitar_learning.tool.experiments.short_finger_learning.spec import (
    read_teacher, subset, diagnostic_spec, selected_actions)
from guitar_learning.tool.experiments.short_finger_learning.runtime import (
    ShortEnvironment, ShortPolicy, ShortPool, teacher_goal)
from guitar_learning.tool.experiments.short_finger_learning.runner import compact_episode, summary


def setup(count=2, mode='incremental'):
    metadata, snapshot = fixture(count)
    task = make_task(BUNDLE, pre_roll_s=3., tail_s=.5)
    target = next(t for t in task.targets if t.finger == 2)
    teacher = dict(schema='short_finger_teacher.v2', source_target_id=target.target_id, finger=2,
        ramp_s=2., condition='fixed_wrist_pose', wrist_position_G_m=[0.,0.,0.],
        wrist_quaternion_G_xyzw=[0.,0.,0.,1.], arm_targets_rad={name: float(snapshot['target'][0, metadata['joint_names'].index(name)])
                                   for name in LEFT_ARM_NAMES})
    spec = diagnostic_spec(task, teacher, mode, .05)
    song = dict(SONG, finger_action_mode=mode, short_learning=spec)
    metadata['action_contract']['action_codec'] = dict(mode=mode)
    skill = dict(schema='guitar_learning.finger_skill.v2', phase='J', exploration='independent',
                 hold_ticks=1, scope='scheduled', planned_transitions=400, full_song_after=100)
    env = ShortEnvironment(metadata, bundle=BUNDLE, song=song, skill=skill, device='cpu')
    obs = env.reset(range(count), snapshot)
    return env, snapshot, obs, metadata, song, skill


class ShortLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_default_guards_and_diagnostic_position(self):
        env, _, _, metadata, song, skill = setup(mode='position')
        self.assertEqual(env.finger_action_mode, 'position')
        self.assertEqual(FingerSkillEnvironment.allowed_finger_action_modes, ('incremental',))
        with self.assertRaises(ValueError):
            SimplifiedFingerEnvironment(metadata, bundle=BUNDLE, song=song, skill=skill, device='cpu')
        from guitar_learning.training.launch_settings import settings_document
        with self.assertRaises(ValueError):
            settings_document('left', learning_family='finger-skill', finger_action_mode='position')

    def test_onset_scope_observation_and_no_exposure_switch(self):
        env, snapshot, obs, *_ = setup()
        index = env.selected_index
        self.assertEqual(obs['state'].shape, (2, 561))
        self.assertEqual(env.focus_mask.sum(-1).tolist(), [1, 1])
        torch.testing.assert_close(env.onset[index]-env.score_offset, torch.full((2,), 3., dtype=torch.float64))
        self.assertGreater(float(env.press[index]-env.score_offset[0]), 0)
        self.assertEqual(env.catalog.phrases[0].target_indices, (index,))
        env.set_training_progress(400)
        env.reset([0], snapshot)
        self.assertEqual(env.focus_mask.sum(-1).tolist(), [1, 1])
        # Visible event and priority target identities must be from selected scope.
        observation = env.observation()
        self.assertLessEqual(int(observation['priority_mask'].sum()), 2)
        self.assertEqual(env.contract['task']['finger_skill']['scope'], 'fixed_source_subset')
        self.assertIsNone(env.contract['task']['finger_skill']['full_song_after'])

    def test_partial_reset_preserves_other_clock_and_failure_state(self):
        env, snapshot, *_ = setup()
        env.clock[:] = torch.tensor([20, 44]); env.wrist_elapsed[:] = torch.tensor([.5, .8])
        env.failure_paid[:] = True
        env.reset([0], snapshot)
        self.assertEqual(env.clock.tolist(), [0, 44])
        self.assertAlmostEqual(float(env.wrist_elapsed[1]), .8, places=6)
        self.assertEqual(env.failure_paid.tolist(), [False, True])

    def test_mask_logp_kl_entropy_and_gradient(self):
        env, _, obs, *_ = setup()
        model = ShortPolicy(contract=env.contract, size='small')
        args = tuple(obs[k] for k in ('state', 'events', 'mask', 'priority_events', 'priority_mask'))
        sample = model.act(*args)
        evaluated = model.evaluate(*args, sample['latent'])
        torch.testing.assert_close(sample['logp'], evaluated['logp'])
        torch.testing.assert_close((evaluated['logp']-sample['logp']).exp(), torch.ones(2))
        mask = model._active_mask()
        self.assertEqual(mask.nonzero().flatten().tolist(), list(selected_actions(2)))
        latent = sample['latent'].clone(); latent[:, ~mask] += .7
        torch.testing.assert_close(model.evaluate(*args, latent)['logp'], sample['logp'])
        mean, std = sample['mean'].clone(), sample['log_std'].clone()
        mean[:, ~mask] += .2; std[:, ~mask] += .3
        torch.testing.assert_close(model.analytic_kl(sample['mean'], sample['log_std'], mean, std), torch.zeros(2))
        loss = -evaluated['logp'].mean(); loss.backward()
        self.assertTrue(all(p.grad is None for p in model.support_head.parameters()))
        self.assertEqual(float(model.finger_log_std.grad.reshape(-1)[torch.tensor([0,1,2,3,8,9,10,11,12,13,14,15])].abs().sum()), 0.)
        for name, head in model.finger_heads.items():
            self.assertEqual(any(p.requires_grad for p in head.parameters()), name == 'middle')

    def test_teacher_does_not_modify_learned_joints_or_reset_physics(self):
        env, snapshot, _, metadata, song, _ = setup()
        reference = snapshot['target'][0, [metadata['joint_names'].index(n) for n in ACTIVE_NAMES]]
        goal = teacher_goal(reference, song['short_learning'])
        ids = list(selected_actions(2))
        torch.testing.assert_close(goal[ids], reference[ids])
        pool = ShortPool.__new__(ShortPool)
        pool.environment = env
        pool.spec = song['short_learning']
        pool.teacher_reference, pool.teacher_final = reference, goal
        pool.learn_mask = torch.zeros(39, dtype=torch.bool); pool.learn_mask[ids] = True
        pool.incremental_mask = torch.tensor([n.startswith('LH:') for n in ACTIVE_NAMES])
        low, high = reference-10, reference+10
        pool.controller = SimpleNamespace(target=reference.expand(2,-1).clone(), active=torch.arange(39),
            action_low=low, action_high=high)
        action = torch.randn(2,39).tanh()
        with patch.object(GpuPool, 'step', return_value='one_tick') as step, \
                patch.object(pool, '_wrist_feedback', side_effect=lambda desired, fraction: desired):
            self.assertEqual(pool.step(action), 'one_tick')
            executed = step.call_args.args[0]
            torch.testing.assert_close(executed[:,ids], action[:,ids], rtol=0, atol=0)
            self.assertTrue(torch.equal(executed[:,33:], torch.zeros(2,6)))
            self.assertEqual(step.call_count,1)

    def test_cpu_collector_ppo_update_keeps_teacher_parameters_frozen(self):
        from guitar_learning.training.finger_decisions import DecisionCollector
        env, snapshot, observation, *_ = setup()
        model = ShortPolicy(contract=env.contract, size='small')
        class Pool:
            num_envs = 2
            valid = True
            def __init__(self): self.observation = observation
            def step(self, action):
                env.begin_control(action)
                for _ in range(4): env.substep(dict(snapshot, physics_step=env.clock+1))
                return env.end_control()
            def plan_decisions(self, remaining): return env.plan_decisions(remaining)
            def decision_observation(self, plan, obs): return env.decision_observation(plan, obs)
            def reset(self, ids): return env.reset(ids, snapshot), []
        before = {name: p.detach().clone() for name, p in model.named_parameters() if not p.requires_grad}
        std_before = model.finger_log_std.detach().clone()
        collector = DecisionCollector(model, Pool())
        buffer, completed = collector.collect(4)
        self.assertTrue(bool((buffer['duration'] == 1).all()))
        trainer = DecisionPPOTrainer(model, PPOConfig(epochs=1, minibatch_size=8))
        result = trainer.update(buffer, completed)
        self.assertEqual(trainer.updates, 1)
        self.assertTrue(math.isfinite(result['analytic_kl']))
        for name, p in model.named_parameters():
            if name in before: torch.testing.assert_close(p, before[name], rtol=0, atol=0)
        inactive = torch.tensor([0,1,2,3,8,9,10,11,12,13,14,15])
        torch.testing.assert_close(model.finger_log_std.reshape(-1)[inactive], std_before.reshape(-1)[inactive], rtol=0, atol=0)

    def test_settings_initial_std_matches_actual_policy_spec(self):
        from guitar_learning.tool.experiments.short_finger_learning.__main__ import parser
        from guitar_learning.tool.experiments.short_finger_learning.runner import make_settings
        env,*_=setup()
        teacher=env.contract['task']['short_learning']['teacher']
        args=parser().parse_args(['train','--teacher','test.json','--mode','position',
            '--initial-std','.01','--size','small','--num-envs','2','--updates','1','--out','unused'])
        with patch('guitar_learning.tool.experiments.short_finger_learning.runner.read_teacher',return_value=teacher):
            settings=make_settings(args)
        self.assertEqual(settings['initial_std'],.01)
        self.assertEqual(settings['song']['short_learning']['initial_std'],.01)

    def test_std_contract_rejects_silently_clamped_scale(self):
        env, *_ = setup()
        spec = env.contract['task']['short_learning']
        with self.assertRaises(ValueError): diagnostic_spec(env.task, spec['teacher'], 'position', .001)
        value = diagnostic_spec(env.task, spec['teacher'], 'position', math.exp(-5))
        self.assertEqual(value['initial_std'], math.exp(-5))

    def test_wrist_pose_interpolation_and_origin_jacobian(self):
        from guitar_learning.tool.experiments.short_finger_learning.wrist import interpolated_pose, wrist_error_and_jacobian
        initial = torch.tensor([[0.,0.,0.,1.],[0.,0.,0.,1.]])
        position, quaternion = interpolated_pose(torch.zeros(2,3), initial, torch.ones(3),
            torch.tensor([0.,0.,0.,-1.]), torch.tensor([0.,1.]))
        torch.testing.assert_close(position, torch.tensor([[0.,0.,0.],[1.,1.,1.]]))
        torch.testing.assert_close(quaternion, initial)
        bodies = torch.zeros(1,3,13); bodies[:,:,6] = 1.
        native = torch.zeros(1,2,6,12); native[0,0,5,0] = 1.
        error, jacobian = wrist_error_and_jacobian(dict(body_state=bodies,jacobian=native),
            1,2,torch.tensor([.1,0.,0.]),torch.arange(12),torch.zeros(1,3),initial[:1])
        torch.testing.assert_close(error, torch.zeros(1,6))
        self.assertAlmostEqual(float(jacobian[0,1,0]),-.1,places=6)
        self.assertAlmostEqual(float(jacobian[0,5,0]),.1,places=6)

    def test_wrist_feedback_skips_reset_nan_and_bounds_active_arm(self):
        from guitar_learning.tool.experiments.short_finger_learning.wrist import bounded_wrist_target, WRIST_CONTROL
        base = torch.zeros(2,12); J=torch.zeros(2,6,12)
        J[0] = float('nan'); J[1,:,:6] = torch.eye(6)
        goal, correction, delta = bounded_wrist_target(base,base.clone(),base.clone(),J,
            torch.ones(2,6),torch.tensor([False,True]),torch.full((12,),-.003),
            torch.full((12,),.003),torch.ones(12)*3)
        torch.testing.assert_close(delta[0],torch.zeros(12))
        self.assertTrue(torch.isfinite(goal).all())
        self.assertLessEqual(float(delta.abs().max()),WRIST_CONTROL['correction_step_rad']+1e-8)
        self.assertLessEqual(float(goal.abs().max()),.003+1e-8)
        self.assertGreater(float(delta[1].abs().sum()),0.)
        torch.testing.assert_close(correction,goal-base)

    def test_wrist_partial_reset_reinitializes_only_reset_teacher_rows(self):
        env,snapshot,_,metadata,_,_=setup()
        pool=ShortPool.__new__(ShortPool); pool.num_envs=2
        pool.scene=SimpleNamespace(device=torch.device('cpu'))
        pool.environment=env
        pool.controller=SimpleNamespace(reference=snapshot['target'][0],active=torch.tensor(
            [metadata['joint_names'].index(n) for n in ACTIVE_NAMES]))
        pool.initial_wrist_position=torch.full((2,3),42.)
        pool.initial_wrist_quaternion=torch.full((2,4),42.)
        pool.wrist_correction=torch.ones(2,12)
        pool.previous_arm_request=torch.full((2,12),42.)
        with patch.object(GpuPool,'reset',return_value=('observation',[])) as reset:
            self.assertEqual(pool.reset([0]),('observation',[]))
            reset.assert_called_once_with([0])
        torch.testing.assert_close(pool.wrist_correction[0],torch.zeros(12))
        torch.testing.assert_close(pool.wrist_correction[1],torch.ones(12))
        torch.testing.assert_close(pool.initial_wrist_position[1],torch.full((3,),42.))
        torch.testing.assert_close(pool.previous_arm_request[1],torch.full((12,),42.))

    def test_checkpoint_contract_mode_and_mask_strict(self):
        env, *_ = setup()
        policy = ShortPolicy(contract=env.contract, size='small')
        trainer = DecisionPPOTrainer(policy, PPOConfig())
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder)/'model.pt'; trainer.save(file)
            changed = copy.deepcopy(env.contract)
            changed['task']['short_learning']['mode'] = 'position'
            other = DecisionPPOTrainer(ShortPolicy(contract=changed, size='small'), PPOConfig())
            with self.assertRaises(ValueError): other.load(file)
            trainer.load(file)

    def test_teacher_evidence_sha_and_named_arm_validation(self):
        env, *_ = setup()
        teacher = copy.deepcopy(env.contract['task']['short_learning']['teacher'])
        with tempfile.TemporaryDirectory() as folder:
            evidence=Path(folder)/'source.txt'; evidence.write_text('sealed evidence')
            teacher['source_evidence'] = {str(evidence):digest(evidence)}
            file=Path(folder)/'teacher.json'; file.write_text(json.dumps(teacher))
            value=read_teacher(file)
            self.assertEqual(value['input_sha256'], digest(file))
            evidence.write_text('changed')
            with self.assertRaises(ValueError): read_teacher(file)

    def test_compact_record_keeps_failed_attempt_denominator(self):
        env, _, _, *_ = setup()
        env.failure[0, 0] = True
        env.invalid[0] = True
        row = env._episode(0, True)
        compact = compact_episode(row, env.contract['task']['short_learning'])
        report = summary([compact])
        self.assertEqual(report['episodes'], 1)
        self.assertEqual(report['physical_failure_fraction'], 1.)
        self.assertEqual(report['achieved_fraction'], 0.)
        self.assertNotIn('left_note_ledger', compact)


if __name__ == '__main__':
    unittest.main()
