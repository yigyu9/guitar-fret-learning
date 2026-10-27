import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import torch

from guitar_learning.training import finger_skill_runner as runner
from guitar_learning.training.finger_skill_curriculum import FingerSkillCurriculum, ExposureSchedule
from guitar_learning.training.decision_ppo import DecisionPPOTrainer
from guitar_learning.training.ppo import PPOConfig
from guitar_learning.tests.test_finger_decisions import TinyDecisionPolicy, FakeDecisionPool


def settings(phase='auto'):
    return dict(device='cuda:0', seed=7, num_envs=2, horizon=3, updates=4,
        finger_skill=dict(schema='guitar_learning.finger_skill.v1', phase=phase,
            scope='full_song' if phase == 'J' else 'phrases', exploration='independent',
            hold_ticks=3, preparation_updates=2, finger_updates=3))


def evaluation_row(phase, ready=True):
    return dict(evaluation=True, valid=True, reason='timeline_complete', steps=10,
        finger_skill_eval=dict(phase=phase, scope='phrase', wrist_inside_fraction=1. if ready else 0.),
        song=dict(completed=True), left_curriculum=dict(full_safe=True,
            finger_metrics=[dict(target_count=64, success_fraction=.5 if ready else 0.) for _ in range(4)]))


class FingerSkillRunnerTests(unittest.TestCase):
    def test_phase_scope_budget_and_dispatch(self):
        source = settings()
        self.assertEqual(runner.phase_budgets(source), dict(R=12, F=18, J=24))
        self.assertEqual(runner.phase_settings(source, 'J')['finger_skill']['scope'], 'full_song')
        self.assertEqual(source['finger_skill']['phase'], 'auto')
        self.assertEqual(runner.phase_budgets(settings('F'))['F'], 24)
        from guitar_learning.tool.training.legacy_gpu_runner import run
        with patch.object(runner, 'run', return_value={'new': True}) as dispatch:
            self.assertEqual(run(source, object()), {'new': True})
            dispatch.assert_called_once()

    def _orchestrate(self, temp, *, r_ready=True, f_ready=True, phase='auto'):
        stages = []
        evaluations = []
        def train(active, out, curriculum, **kwargs):
            stages.append((active['finger_skill']['phase'], kwargs.copy(), curriculum.state_dict()))
            if kwargs.get('updates') != 0:
                curriculum.commit(kwargs['updates']*active['horizon']*active['num_envs'] if kwargs.get('updates') is not None
                                  else curriculum.status()['remaining_transitions'])
            return dict(report=dict(stopped='updates_complete', completed=True), checkpoint=str(out/'final.pt'))
        def evaluate(checkpoint, out, **kwargs):
            curriculum = kwargs['curriculum']
            current = curriculum.phase
            row = evaluation_row(current, r_ready if current == 'R' else f_ready)
            readiness = curriculum.evaluate([row])
            evaluations.append((current, kwargs))
            return dict(readiness=readiness, readiness_checkpoint=str(out/'evaluated.pt'),
                        actual_simulated_transitions=20), [row]
        args = SimpleNamespace(out=Path(temp)/'run', resume=None)
        with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                patch('torch.cuda.is_available', return_value=True), \
                patch.object(runner, '_train_phase', side_effect=train), \
                patch.object(runner, 'evaluate_checkpoint', side_effect=evaluate):
            report = runner.run(settings(phase), args)
        return report, stages, evaluations

    def test_auto_skips_ready_r_transfers_and_full_song_j(self):
        with tempfile.TemporaryDirectory() as temp:
            report, stages, evaluations = self._orchestrate(temp)
        self.assertEqual([row[0] for row in stages], ['R', 'F', 'J'])
        self.assertEqual(stages[0][1]['updates'], 0)
        self.assertTrue(stages[1][1]['transfer'].endswith('R_initial_evaluation/evaluated.pt'))
        self.assertTrue(stages[2][1]['transfer'].endswith('F_evaluation/evaluated.pt'))
        self.assertEqual(report['training_transitions'], 42)
        self.assertEqual(report['evaluation_actual_simulated_transitions'], 40)
        self.assertEqual(report['evaluation_selected_episode_transitions'], 20)
        self.assertTrue(report['completed'])
        self.assertEqual(report['final_phase'], 'J')

    def test_auto_r_training_uses_evaluated_resume_and_f_stalls(self):
        with tempfile.TemporaryDirectory() as temp:
            report, stages, evaluations = self._orchestrate(temp, r_ready=False)
        self.assertEqual([row[0] for row in stages], ['R', 'R'])
        self.assertTrue(stages[1][1]['resume'].endswith('R_initial_evaluation/evaluated.pt'))
        self.assertEqual(report['stopped'], 'R_stalled')
        self.assertFalse(report['completed'])
        with tempfile.TemporaryDirectory() as temp:
            report, stages, _ = self._orchestrate(temp, f_ready=False)
        self.assertEqual([row[0] for row in stages], ['R', 'F'])
        self.assertEqual(report['stopped'], 'F_stalled')
        self.assertFalse(report['completed'])

    def test_direct_phase_has_no_readiness_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            report, stages, evaluations = self._orchestrate(temp, phase='F')
        self.assertEqual([row[0] for row in stages], ['F'])
        self.assertEqual(evaluations, [])
        self.assertEqual(report['training_transitions'], 24)
        self.assertTrue(report['completed'])

    def test_pipeline_wall_budget_stops_before_starting_a_scene(self):
        with tempfile.TemporaryDirectory() as temp:
            active = settings('F')
            active['max_wall_seconds'] = 0.
            with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                    patch('torch.cuda.is_available', return_value=True), \
                    patch.object(runner, '_train_phase') as train:
                report = runner.run(active, SimpleNamespace(out=Path(temp)/'run', resume=None))
            train.assert_not_called()
            self.assertEqual(report['stopped'], 'wall_budget')
            self.assertFalse(report['completed'])
            self.assertEqual(report['training_transitions'], 0)

    def test_direct_resume_requests_additional_updates_and_preserves_original_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            active = settings('F')
            active['updates'] = 1
            curriculum = FingerSkillCurriculum('F', budgets=dict(R=12, F=12, J=12))
            curriculum.commit(12)
            checkpoint = root/'prior.pt'
            torch.save(dict(metadata=dict(schema=runner.RESUME_SCHEMA,
                curriculum=curriculum.state_dict())), checkpoint)
            observed = []
            def train(settings, out, current, **kwargs):
                observed.append((current.config['budgets'].copy(), kwargs['updates']))
                current.commit(kwargs['updates']*settings['horizon']*settings['num_envs'])
                return dict(report=dict(stopped='updates_complete'), checkpoint=str(out/'final.pt'))
            with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                    patch('torch.cuda.is_available', return_value=True), \
                    patch.object(runner, '_train_phase', side_effect=train):
                report = runner.run(active, SimpleNamespace(out=root/'resume', resume=checkpoint))
            self.assertEqual(observed, [(dict(R=12, F=12, J=12), 1)])
            self.assertEqual(report['training_transitions'], 18)
            self.assertTrue(report['manual_budget_extension'])
            self.assertEqual(report['curriculum']['config']['budgets']['F'], 12)

    def test_joint_v25_has_no_readiness_or_transfer_and_preserves_original_exposure_on_resume(self):
        active = settings('J')
        active['finger_skill'] = dict(schema='guitar_learning.finger_skill.v2', phase='J',
            exploration='independent', hold_ticks=1, scope='scheduled',
            planned_transitions=24, full_song_after=6)
        active['ppo'] = dict(advantage_normalization='joint', cost_weight=1., episode_cost_budget=None, lambda_lr=0.)
        calls = []
        def train(value, out, schedule, **kwargs):
            calls.append((copy.deepcopy(value), schedule.state_dict(), kwargs))
            schedule.commit(kwargs['updates']*value['horizon']*value['num_envs'])
            return dict(report=dict(stopped='updates_complete'), checkpoint=str(out/'final.pt'))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                    patch('torch.cuda.is_available', return_value=True), \
                    patch.object(runner, '_train_phase', side_effect=train), \
                    patch.object(runner, 'evaluate_checkpoint') as evaluate:
                fresh = runner.run(active, SimpleNamespace(out=root/'fresh', resume=None))
            evaluate.assert_not_called()
            self.assertEqual(fresh['training_transitions'], 24)
            self.assertEqual(len(calls), 1)
            self.assertIsNone(calls[0][2]['transfer'])
            saved = ExposureSchedule(24)
            saved.commit(24)
            checkpoint = root/'prior.pt'
            torch.save(dict(metadata=dict(schema=runner.RESUME_SCHEMA_V2,
                curriculum=saved.state_dict())), checkpoint)
            resumed = copy.deepcopy(active)
            resumed['updates'] = 1
            resumed['finger_skill'].update(planned_transitions=6, full_song_after=1)
            with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                    patch('torch.cuda.is_available', return_value=True), \
                    patch.object(runner, '_train_phase', side_effect=train):
                report = runner.run(resumed, SimpleNamespace(out=root/'resume', resume=checkpoint))
            self.assertEqual(calls[-1][0]['finger_skill']['planned_transitions'], 24)
            self.assertEqual(calls[-1][0]['finger_skill']['full_song_after'], 6)
            self.assertEqual(calls[-1][2]['updates'], 1)
            self.assertEqual(report['training_transitions'], 30)
            self.assertTrue(report['manual_budget_extension'])
            self.assertEqual(report['curriculum']['config']['full_song_after'], 6)

    def test_joint_v25_restore_applies_progress_before_prepared_reset_and_rejects_v24(self):
        trainer = DecisionPPOTrainer(TinyDecisionPolicy('J'), PPOConfig(epochs=1))
        active = settings('J')
        active['finger_skill'] = dict(schema='guitar_learning.finger_skill.v2', phase='J')
        schedule = ExposureSchedule(24)
        schedule.commit(7)
        calls = []
        sampler = SimpleNamespace(state_dict=lambda: dict(index=3),
            load_state_dict=lambda state: calls.append(('sampler', state)))
        pool = SimpleNamespace(environment=SimpleNamespace(sampler=sampler), observation=None,
            set_training_progress=lambda committed: calls.append(('progress', committed)))
        def reset():
            calls.append(('reset', None))
            return dict(state='prepared_full_song'), []
        pool.reset = reset
        with tempfile.TemporaryDirectory() as temp:
            checkpoint = Path(temp)/'joint.pt'
            trainer.save(checkpoint, runner.checkpoint_metadata(active, schedule, pool))
            restored = ExposureSchedule(24)
            runner.restore_checkpoint(trainer, pool, restored, checkpoint)
            self.assertEqual(calls, [('sampler', dict(index=3)), ('progress', 7), ('reset', None)])
            self.assertEqual(restored.status()['next_reset_scope'], 'full_song')
            old = Path(temp)/'v24.pt'
            trainer.save(old, runner.checkpoint_metadata(settings('J'),
                FingerSkillCurriculum('J', budgets=dict(R=1, F=1, J=24)), pool))
            with self.assertRaisesRegex(ValueError, 'metadata'):
                runner.restore_checkpoint(trainer, pool, ExposureSchedule(24), old)

    def test_same_phase_resume_restores_sampler_before_reset(self):
        config = PPOConfig(epochs=1)
        trainer = DecisionPPOTrainer(TinyDecisionPolicy('F'), config)
        curriculum = FingerSkillCurriculum('F', budgets=dict(R=12, F=18, J=24))
        curriculum.commit(6)
        calls = []
        class Sampler:
            def state_dict(self):
                return dict(index=9)
            def load_state_dict(self, state):
                calls.append(('restore_sampler', state))
        pool = SimpleNamespace(environment=SimpleNamespace(sampler=Sampler()), observation=None)
        def reset():
            calls.append(('reset', None))
            return dict(state='prepared'), []
        pool.reset = reset
        with tempfile.TemporaryDirectory() as temp:
            checkpoint = Path(temp)/'own.pt'
            trainer.save(checkpoint, runner.checkpoint_metadata(settings('F'), curriculum, pool))
            restored = FingerSkillCurriculum('F', budgets=dict(R=12, F=18, J=24))
            runner.restore_checkpoint(trainer, pool, restored, checkpoint)
            self.assertEqual(restored.training_transitions['F'], 6)
            self.assertEqual(calls[0], ('restore_sampler', dict(index=9)))
            self.assertEqual(calls[1][0], 'reset')
            self.assertEqual(pool.observation, dict(state='prepared'))
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                runner.restore_checkpoint(trainer, pool,
                    FingerSkillCurriculum('R', budgets=dict(R=12, F=19, J=24)), checkpoint)

    def test_fixed_evaluation_counts_first_episode_failures_and_closes_scene(self):
        instances = []
        class Pool(FakeDecisionPool):
            def __init__(self, active, out):
                super().__init__(k=1)
                self.environment = SimpleNamespace(task=SimpleNamespace(duration_s=.1),
                    set_evaluation=lambda **kwargs: None)
                self.scene = SimpleNamespace(diagnostics=dict(closed=False, physx_use_gpu=True,
                    use_gpu_pipeline=True, simulator_count=1, environment_count=2))
                instances.append(self)
            def step(self, action):
                self.actions.append(action.clone())
                self.clock += 1
                done = torch.tensor([self.clock[0] == 2, self.clock[1] == 3])
                self.observation = self._obs()
                episodes = []
                for index in done.nonzero().flatten().tolist():
                    row = evaluation_row('F')
                    row.update(env_id=index, steps=int(self.clock[index]), reward=1., cost=0.)
                    row['song'].update(stage_success=False, left_success_count=0, right_success_count=0)
                    if index == 0:
                        row.update(reason='terminal_failure')
                        row['song']['completed'] = False
                        row['left_curriculum']['full_safe'] = False
                    episodes.append(row)
                return self.observation, torch.ones(2), torch.zeros(2), done, torch.zeros(2, dtype=torch.bool), episodes
            def reset(self, ids=None):
                return super().reset(torch.arange(2) if ids is None else ids)
            def close(self):
                self.scene.diagnostics['closed'] = True
        class Monitor:
            def __init__(self, *args, **kwargs): pass
            def start(self): pass
            def progress(self, context): pass
            def close(self, reason): pass
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            active = settings('F')
            active.update(size='small', initial_std=.05, min_available_memory_gib=0.,
                          ppo=dict(epochs=1), horizon=1)
            trainer = DecisionPPOTrainer(TinyDecisionPolicy('F'), PPOConfig(epochs=1))
            checkpoint = root/'own.pt'
            trainer.save(checkpoint, dict(schema=runner.RESUME_SCHEMA, settings=active, input_pins={}))
            pins = {str(checkpoint): runner.digest(checkpoint)}
            with patch.dict('sys.modules', {'isaacgym': SimpleNamespace()}), \
                    patch('guitar_learning.training.gpu_pool.GpuPool', Pool), \
                    patch('guitar_learning.training.monitoring.Monitor', Monitor), \
                    patch('torch.cuda.mem_get_info', return_value=(2*1024**3, 4*1024**3)), \
                    patch.object(runner, '_policy', return_value=TinyDecisionPolicy('F')), \
                    patch.object(runner, '_pins', return_value=pins), \
                    patch.object(runner, 'project_source_paths', return_value=set()):
                report, rows = runner.evaluate_checkpoint(checkpoint, root/'evaluation', scope='phrases')
            self.assertEqual([row['env_id'] for row in rows], [0, 1])
            self.assertEqual(report['episodes'], 2)
            self.assertEqual(report['summary']['physical_failure'], 1)
            self.assertEqual(report['actual_simulated_transitions'], 6)
            self.assertTrue(report['completed'])
            self.assertTrue(instances[0].scene.diagnostics['closed'])

    def test_checkpoint_sources_and_evaluator_parser(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'input.py'
            path.write_text('original')
            metadata = dict(input_pins={str(path): runner.digest(path)})
            runner._validate_pins(metadata)
            path.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'changed'):
                runner._validate_pins(metadata)
        from guitar_learning.tool.evaluation.evaluate_finger_skill import parser
        args = parser().parse_args(['own.pt', '--out', 'result'])
        self.assertEqual(args.scope, 'full_song')
        self.assertIsNone(args.num_envs)


if __name__ == '__main__':
    unittest.main()
