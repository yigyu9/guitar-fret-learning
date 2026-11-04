"""압현 v5 정책·초기 탐색·실행·엄격 재개를 CPU에서 함께 검사한다."""
import copy
from dataclasses import asdict
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from guitar_learning.tool.experiments import compact_press_v5 as entry
from guitar_learning.training.compact_press_v5 import CompactPressV5Policy
from guitar_learning.tests.test_compact_press_v5_policy import contract as policy_contract
from guitar_learning.tests.test_finger_decisions import FakeDecisionPool
from guitar_learning.training.ppo import DecisionPPOTrainer, PPOConfig
from guitar_learning.training.rollout import DecisionCollector


def contract(profile='corrected', pelvis=False):
    value = policy_contract(pelvis=pelvis)
    dimension = 473 if pelvis else 464
    value['observation'].update(dimension=dimension,
        fields=['state.' + str(i) for i in range(dimension)], scales=[1.] * dimension)
    value['compact_press']['schema'] = 'guitar_learning.compact_press_observation.v5'
    value['reward'] = dict(schema='guitar_learning.compact_press_reward.v5',
        compact_press_v4=entry.reward_configuration(),
        compact_press_v5=entry.improvement_configuration(profile))
    return value


class CompactV5Pool(FakeDecisionPool):
    def _obs(self):
        state = torch.zeros(2, 464)
        state[:, 0] = self.clock
        return dict(state=state, events=torch.zeros(2, 0, 26), mask=torch.zeros(2, 0, dtype=torch.bool),
            priority_events=torch.zeros(2, 8, 26), priority_mask=torch.ones(2, 8, dtype=torch.bool))


class CompactPressV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_explicit_settings_stds_profiles_and_h32_h128_budgets(self):
        self.assertEqual(set(entry.IMPROVEMENT_PROFILES),
            {'corrected', 'preparation', 'full_hold', 'combined'})
        args = entry.parser().parse_args(['train', '--out', 'unused'])
        self.assertIsNone(args.improvement_profile)
        self.assertIsNone(args.initial_support_std)
        self.assertIsNone(args.initial_finger_std)
        for horizon in (32, 128):
            for profile in entry.IMPROVEMENT_PROFILES:
                settings = entry.build_settings(improvement_profile=profile, updates=4, num_envs=2, horizon=horizon)
                entry.validate_settings(settings)
                self.assertEqual(settings['finger_skill']['planned_transitions'], 4 * 2 * horizon)
                self.assertEqual(settings['finger_skill']['full_song_after'], 2 * horizon)
                self.assertEqual(settings['compact_press']['initial_support_std'], .15)
                self.assertEqual(settings['compact_press']['initial_finger_std'], .35)
                self.assertEqual(settings['compact_press']['state_dim'], 464)
                self.assertEqual(settings['compact_press']['fusion_hidden'], [512, 256])
                self.assertEqual(settings['song']['left_fraction'],
                    1. if profile in ('full_hold', 'combined') else .4)
        self.assertEqual(entry.build_settings(include_pelvis=True)['compact_press']['state_dim'], 473)

    def test_default_evaluate_and_render_dispatch_through_v5_without_recursion(self):
        from guitar_learning.tool.evaluation import evaluate_finger_skill
        from guitar_learning.tool.demonstration import render_finger_skill
        with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                patch('sys.argv', ['evaluate', 'saved.pt', '--out', 'unused']), \
                patch.object(entry, 'evaluate', return_value=(dict(episodes=2, scope='full_song', completed=True), [])) as call:
            evaluate_finger_skill.main()
        call.assert_called_once_with(Path('saved.pt'), Path('unused'), num_envs=None, scope='full_song')
        with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                patch.object(entry, 'render', return_value='v5 render') as call:
            self.assertEqual(render_finger_skill.render('saved.pt', 'unused'), 'v5 render')
        call.assert_called_once_with('saved.pt', 'unused', scope='full_song', num_envs=None)
        settings = entry.build_settings()
        with patch.object(entry, 'read_checkpoint', return_value=settings) as reader, \
                patch.object(render_finger_skill, '_render', return_value='native render') as native:
            self.assertEqual(entry.render('saved.pt', 'unused'), 'native render')
        reader.assert_called_once_with('saved.pt')
        native.assert_called_once_with('saved.pt', 'unused', num_envs=None, scope='full_song')

    def test_c1_settings_install_original_clock_and_restore_task_factory(self):
        from guitar_learning.song import task
        from guitar_learning.tool.prepare_press_targets import BASE_TASK_FACTORY, source_clock_runtime
        self.assertIs(task.make_task, BASE_TASK_FACTORY)
        settings = entry.build_settings(song='press_sequence_c1_v1', num_envs=2, updates=1)
        self.assertEqual(settings['song_training']['episode_duration_s'], 47.25)
        self.assertEqual(settings['song_training']['control_ticks'], 2835)
        self.assertIs(task.make_task, BASE_TASK_FACTORY)
        with source_clock_runtime():
            self.assertEqual(entry.build_settings(song='press_sequence_c1_v1', num_envs=2, updates=1), settings)
        self.assertIs(task.make_task, BASE_TASK_FACTORY)
        with self.assertRaisesRegex(ValueError, '등록되지 않은'):
            entry.build_settings(song='press_sequence_c7_v1')

    def test_initial_groups_no_runner_shift_and_all33_distribution(self):
        for pelvis in (False, True):
            settings = entry.build_settings(include_pelvis=pelvis)
            model = CompactPressV5Policy(settings['compact_press']['state_dim'], contract=contract(pelvis=pelvis))
            shift = math.log(settings['initial_std']) + 3.
            self.assertEqual(shift, 0.)
            with torch.no_grad():
                model.support_log_std.add_(shift)
                model.finger_log_std.add_(shift)
            torch.testing.assert_close(model.log_std[:17].exp(), torch.full((17,), .15))
            torch.testing.assert_close(model.log_std[17:].exp(), torch.full((16,), .35))
            self.assertEqual(model.architecture['initial_stds'], dict(support17=.15, finger16=.35))
            self.assertEqual(model.actor_encoder.state[0].in_features, 473 if pelvis else 464)
            self.assertEqual(model.actor_encoder.goal[0].weight.shape, (64, 26))
            self.assertEqual(model.actor_encoder.fusion[0].weight.shape, (512, 768))
            self.assertEqual(model.actor_head.out_features, 33)

    def test_invalid_settings_old_contract_and_bad_std_rejected(self):
        settings = entry.build_settings()
        for bad_value in (0., -.1, True, float('nan'), float('inf'), math.exp(2) + 1):
            with self.subTest(value=bad_value), self.assertRaises(ValueError):
                entry.build_settings(initial_finger_std=bad_value)
        for key, value in (('initial_std', .35), ('compact_press_v5', {})):
            bad = copy.deepcopy(settings)
            bad[key] = value
            with self.assertRaises(ValueError):
                entry.validate_settings(bad)
        for profile in entry.IMPROVEMENT_PROFILES:
            bad = entry.build_settings(improvement_profile=profile)
            bad['song']['left_fraction'] = .8
            with self.assertRaises(ValueError):
                entry.validate_settings(bad)
        with self.assertRaises(ValueError):
            CompactPressV5Policy(452, contract=policy_contract())
        bad = contract()
        bad['reward']['compact_press_v4'] = dict(schema='retired.baseline')
        with self.assertRaises(ValueError):
            entry.validate_contract(settings, bad)
        for version in (2, 3, 4):
            with self.assertRaises(ValueError):
                entry.validate_metadata(dict(schema='guitar_learning.compact_press_resume.v' + str(version), settings=settings))

    def test_new_state_and_goal_gradient_mask_and_critic_separation(self):
        model = CompactPressV5Policy(464, contract=contract())
        state = torch.randn(2, 464, requires_grad=True)
        goals = torch.randn(2, 8, 26, requires_grad=True)
        valid = torch.ones(2, 8, dtype=torch.bool)
        valid[:, 1::2] = False
        arguments = [state, torch.zeros(2, 0, 26), torch.zeros(2, 0, dtype=torch.bool), goals, valid]
        with torch.no_grad():
            model.actor_head.weight.normal_(0., .02)
        before = model(*arguments)
        state_gradient, goal_gradient = torch.autograd.grad(before['mean'][:, :33].sum(), (state, goals))
        self.assertTrue(bool((state_gradient[:, -12:] != 0).all()))
        self.assertTrue(bool(goal_gradient[valid].abs().sum() > 0))
        self.assertFalse(bool(goal_gradient[~valid].any()))
        arguments[3] = goals.detach().clone()
        arguments[3][~valid] = float('nan')
        for key, value in model(*arguments).items():
            torch.testing.assert_close(before[key], value, rtol=0, atol=0)
        self.assertFalse({id(p) for p in model.actor_parameters()} & {id(p) for p in model.value_parameters()})

    def test_runtime_restore_and_resume_custom_stds_preserved(self):
        from guitar_learning.training import rollout, finger_skill_runner as runner
        def current():
            return (rollout.GpuPool, runner._policy, runner.resume_schema,
                runner._validate_metadata_schema, runner._pins, runner.SCHEMA)
        before = current()
        with self.assertRaisesRegex(RuntimeError, '의도된 실패'):
            with entry.runtime():
                self.assertIsNot(rollout.GpuPool, before[0])
                raise RuntimeError('의도된 실패')
        self.assertEqual(current(), before)
        settings = entry.build_settings(initial_support_std=.2, initial_finger_std=.4,
            improvement_profile='preparation', include_pelvis=True)
        args = entry.parser().parse_args(['train', '--out', 'unused', '--resume', 'saved.pt'])
        with patch.object(entry, 'read_checkpoint', return_value=copy.deepcopy(settings)), \
                patch.object(runner, 'run', return_value='대체 실행') as run:
            self.assertEqual(entry.train(args), '대체 실행')
        self.assertEqual(run.call_args[0][0]['compact_press'], settings['compact_press'])
        for option in ('--initial-support-std .15', '--initial-finger-std .35',
                '--improvement-profile combined', '--no-include-pelvis', '--horizon 128'):
            args = entry.parser().parse_args(['train', '--out', 'unused', '--resume', 'saved.pt'] + option.split())
            with patch.object(entry, 'read_checkpoint', return_value=copy.deepcopy(settings)), self.assertRaises(ValueError):
                entry.train(args)

    def test_h32_h128_collector_continues_without_reset(self):
        for horizon in (32, 128):
            pool = CompactV5Pool(failure=False)
            model = CompactPressV5Policy(464, contract=contract())
            collector = DecisionCollector(model, pool)
            first, _ = collector.collect(horizon)
            second, _ = collector.collect(horizon)
            self.assertEqual(first['state'].shape, (horizon, 2, 464))
            self.assertEqual(second['state'][0, :, 0].tolist(), [float(horizon)] * 2)
            self.assertEqual(pool.clock.tolist(), [float(2 * horizon)] * 2)
            self.assertFalse(pool.resets)

    def test_all_profiles_real_environment_policy_and_substeps(self):
        from guitar_learning.gpu.compact_press_v5 import CompactPressV5Environment
        from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG
        from guitar_learning.tests.test_compact_press_v5_environment import SKILL
        from guitar_learning.training import finger_skill_runner as runner
        for profile in entry.IMPROVEMENT_PROFILES:
            for pelvis in (False, True):
                class Environment(CompactPressV5Environment):
                    include_pelvis = pelvis
                    improvement_profile = profile
                settings = entry.build_settings(improvement_profile=profile, include_pelvis=pelvis, num_envs=2)
                settings['device'] = 'cpu'
                song = copy.deepcopy(SONG)
                song['left_fraction'] = settings['song']['left_fraction']
                metadata, snapshot = fixture(2)
                env = Environment(metadata, bundle=BUNDLE, song=song, skill=SKILL, device='cpu')
                observation = env.reset([0, 1], snapshot)
                with entry.runtime():
                    model = runner._policy(settings, SimpleNamespace(observation=observation, contract=env.contract))
                action = model.act(**observation)['action']
                self.assertEqual(action.shape, (2, 39))
                self.assertFalse(bool(action[:, 33:].any()))
                env.begin_control(action)
                for _ in range(4):
                    env.substep(dict(snapshot, physics_step=env.clock + 1))
                after, reward, cost, *_ = env.end_control()
                self.assertEqual(after['state'].shape, (2, 473 if pelvis else 464))
                self.assertEqual(after['priority_events'].shape, (2, 8, 26))
                self.assertTrue(bool(torch.isfinite(reward).all() & torch.isfinite(cost).all()))

    def test_ppo_update_checkpoint_pins_architecture_and_learned_std_roundtrip(self):
        from guitar_learning.portability import checkpoint_inputs, portable, settings_digest, ROOT
        from guitar_learning.training.training_log_io import digest, write
        settings = entry.build_settings(initial_support_std=.2, initial_finger_std=.4, num_envs=2, updates=1)
        config = PPOConfig(epochs=1, minibatch_size=8, lambda_lr=0.)
        settings['ppo'] = asdict(config)
        model = CompactPressV5Policy(464, contract=contract(), initial_support_std=.2, initial_finger_std=.4)
        trainer = DecisionPPOTrainer(model, config)
        buffer, completed = DecisionCollector(model, CompactV5Pool(failure=False)).collect(4)
        before = model.actor_head.weight.detach().clone()
        trainer.update(buffer, completed)
        self.assertFalse(torch.equal(before, model.actor_head.weight))
        with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as folder:
            folder = Path(folder)
            source = folder / 'source.txt'
            source.write_text('원본')
            settings_path = folder / 'settings.json'
            write(settings_path, portable(settings))
            metadata = dict(schema=entry.RESUME_SCHEMA, settings=portable(settings),
                settings_sha256=settings_digest(settings), input_contract=checkpoint_inputs(
                    {str(source): digest(source), str(settings_path): digest(settings_path)},
                    settings, settings_path=settings_path))
            path = folder / 'v5.pt'
            trainer.save(path, metadata=metadata)
            self.assertEqual(entry.read_checkpoint(path), settings)
            restored = CompactPressV5Policy(464, contract=contract(), initial_support_std=.2, initial_finger_std=.4)
            restored_trainer = DecisionPPOTrainer(restored, config)
            restored_trainer.load(path)
            self.assertEqual(restored_trainer.updates, 1)
            for key, value in model.state_dict().items():
                torch.testing.assert_close(value, restored.state_dict()[key], rtol=0, atol=0)
            with self.assertRaisesRegex(ValueError, 'architecture'):
                DecisionPPOTrainer(CompactPressV5Policy(464, contract=contract()), config).load(path)
            payload = torch.load(path, map_location='cpu', weights_only=False)
            for field, value in (('initial_stds', dict(support17=.15, finger16=.35)), ('fusion', [256, 256])):
                bad = copy.deepcopy(payload)
                bad['identity']['architecture'][field] = value
                wrong = folder / (field + '.pt')
                torch.save(bad, wrong)
                with self.assertRaisesRegex(ValueError, 'architecture'):
                    entry.read_checkpoint(wrong)
            source.write_text('변경')
            with self.assertRaisesRegex(ValueError, 'input sources changed'):
                entry.read_checkpoint(path)


if __name__ == '__main__':
    unittest.main()
