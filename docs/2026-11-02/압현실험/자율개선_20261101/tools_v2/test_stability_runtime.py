"""GPU 실행 없이 이전 검증·학습률 경계·실패 기록·원래 factory 복원을 확인한다."""
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('stability_under_test', Path(__file__).with_name('stability_runtime.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class StabilityTests(unittest.TestCase):
    def config(self, variant='conservative'):
        return dict(variant=variant, actor_lr_cap=m.VARIANTS[variant])

    def trainer(self, config, path, lr):
        trainer = object.__new__(m.trainer_class(config, path))
        trainer.actor_optimizer = SimpleNamespace(param_groups=[{'lr': lr}])
        trainer.updates = 9
        return trainer

    def test_cap_blocks_natural_lr_recovery_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            trainer = self.trainer(self.config(), Path(directory)/'KL.jsonl', 1e-5)
            def update(self, *args):
                self.actor_optimizer.param_groups[0]['lr'] = 1.25e-5
                return {'natural_press_lr': {'used_lr': 1e-5, 'next_lr': 1.25e-5}}
            with patch.object(m.OriginalTrainer, '_update', update):
                result = trainer._update({}, [])
            self.assertEqual(trainer.actor_optimizer.param_groups[0]['lr'], 1e-5)
            self.assertEqual(result['natural_press_lr']['next_lr'], 1e-5)

    def test_control_keeps_original_lr_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            trainer = self.trainer(self.config('control'), Path(directory)/'KL.jsonl', 1e-5)
            def update(self, *args):
                self.actor_optimizer.param_groups[0]['lr'] = 1.25e-5
                return {'natural_press_lr': {'next_lr': 1.25e-5}}
            with patch.object(m.OriginalTrainer, '_update', update):
                result = trainer._update({}, [])
            self.assertEqual(result['natural_press_lr']['next_lr'], 1.25e-5)

    def test_above_cap_is_rejected_before_update(self):
        trainer = self.trainer(self.config(), Path('/unused'), 3e-5)
        with patch.object(m.OriginalTrainer, '_update') as update:
            with self.assertRaises(ValueError):
                trainer._update({}, [])
            update.assert_not_called()

    def test_finite_and_nonfinite_KL_diagnostics_reraise(self):
        from guitar_learning.training.ppo import KLGuardError
        for number in (.025, float('nan')):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'KL.jsonl'
                trainer = self.trainer(self.config(), path, 1e-5)
                error = KLGuardError(dict(attempted_kl=number, target_kl=.02, retries=4, epoch=0))
                with patch.object(m.OriginalTrainer, '_update', side_effect=error):
                    with self.assertRaises(KLGuardError) as caught:
                        trainer._update({}, [])
                self.assertIs(caught.exception, error)
                row = json.loads(path.read_text())
                self.assertEqual(row['attempted_kl_finite'], number == number)
                self.assertEqual(row['diagnostic']['target_kl'], .02)
                self.assertEqual(row['committed_updates'], 9)

    def test_retry_floor_and_factor_are_unchanged(self):
        trainer = self.trainer(self.config(), Path('/unused'), 1e-5)
        trainer._retry_actor_lr(0)
        self.assertEqual(trainer.actor_optimizer.param_groups[0]['lr'], 7.5e-6)

    def test_main_restores_patches_on_failure(self):
        original = m.runtime.build_settings, m.runtime.transition_runtime, m.runtime.TransitionPolicy
        with patch.object(m.runtime, 'main', side_effect=RuntimeError('sentinel')):
            with self.assertRaisesRegex(RuntimeError, 'sentinel'):
                m.main(['train', '--out', '/unused', '--variant', 'control', '--initialize-from', '/unused'])
        self.assertEqual(original, (m.runtime.build_settings, m.runtime.transition_runtime, m.runtime.TransitionPolicy))

    def test_resume_and_evaluate_cannot_reinitialize(self):
        for args in (['train', '--resume', 'existing.pt'], ['evaluate', '--checkpoint', 'existing.pt']):
            with self.assertRaises(SystemExit):
                m.main(args+['--out', '/unused', '--initialize-from', 'source.pt'])

    def test_source_digest_change_rejected_before_load(self):
        with patch.object(m.runtime.natural, 'digest', return_value='changed'):
            with self.assertRaisesRegex(ValueError, 'SHA'):
                m.initialize_policy(None, dict(source_checkpoint='/unused', source_sha256='expected'))

    def test_saved_variant_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '조건 불일치'):
            m.validate_experiment({'stability_experiment': {'variant': 'control'}}, 'conservative')

    def test_resume_factory_never_transfers_and_restores_on_exception(self):
        from guitar_learning.training import finger_skill_runner as runner, ppo
        policy = SimpleNamespace(architecture={})
        original = runner._policy, runner._pins, ppo.DecisionPPOTrainer
        @contextmanager
        def context(settings):
            with patch.object(runner, '_policy', return_value=policy):
                yield
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(m, 'validate_experiment', return_value=self.config()), patch.object(m, 'ORIGINAL_CONTEXT', context), patch.object(m, 'initialize_policy') as transfer:
                with self.assertRaisesRegex(RuntimeError, 'sentinel'):
                    with m.stability_runtime({}, initialize=False, out=directory):
                        self.assertIs(runner._policy({}, None), policy)
                        raise RuntimeError('sentinel')
                transfer.assert_not_called()
        self.assertEqual(original, (runner._policy, runner._pins, ppo.DecisionPPOTrainer))

    def test_real_source_identity_and_model_transfer(self):
        source = m.ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/runs/study_v1/jobs/L_H32_s7_u800_train/J/final.pt'
        if not source.is_file():
            self.skipTest('검증용 성공 모델이 이 checkout에 없음')
        from guitar_learning.portability import localize
        m.torch.set_num_threads(1)
        payload = m.torch.load(source, map_location='cpu', weights_only=False)
        saved = localize(payload['metadata']['settings'])
        arch = payload['identity']['architecture']
        policy = m.StabilityPolicy(arch['state_dim'], size=saved['size'],
            contract=localize(arch['contract']), natural_press=saved['natural_press'], transition=saved['transition'])
        config = m.experiment('conservative', source)
        policy.architecture['stability_experiment'] = config
        rng = m.torch.get_rng_state().clone()
        m.initialize_policy(policy, config)
        self.assertTrue(m.torch.equal(rng, m.torch.get_rng_state()))
        self.assertTrue(all(m.torch.equal(value, payload['model'][key]) for key, value in policy.state_dict().items()))
        bad = copy.deepcopy(payload)
        bad['identity']['config']['actor_lr'] *= 2
        with patch.object(m.torch, 'load', return_value=bad):
            with self.assertRaisesRegex(ValueError, 'identity'):
                m.initialize_policy(policy, config)

    def test_actual_fresh_budget_difference_only_transfer_compatible(self):
        from guitar_learning.portability import localize, portable
        base = m.ROOT/'docs/2026-11-02/압현실험/자율개선_20261101'
        source = m.ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/runs/study_v1/jobs/L_H32_s7_u800_train/J/final.pt'
        contract_path = base/'validation/control_fresh/J/training_contract.json'
        if not source.is_file() or not contract_path.is_file():
            self.skipTest('이전 실패의 native 계약 자료 없음')
        m.torch.set_num_threads(1)
        payload = m.torch.load(source, map_location='cpu', weights_only=False)
        saved = localize(payload['metadata']['settings'])
        original_arch = payload['identity']['architecture']
        contract = localize(json.loads(contract_path.read_text()))
        policy = m.StabilityPolicy(original_arch['state_dim'], size=saved['size'],
            contract=contract, natural_press=saved['natural_press'], transition=saved['transition'])
        config = m.experiment('control', source)
        policy.architecture['stability_experiment'] = config
        before = copy.deepcopy(policy.architecture)
        self.assertNotEqual(portable(contract), portable(original_arch['contract']))
        m.initialize_policy(policy, config)
        self.assertEqual(policy.architecture, before)
        self.assertEqual(original_arch['contract']['task']['finger_skill']['planned_transitions'], 204800)
        for path in ('contract', 'core_architecture'):
            bad = copy.deepcopy(before)
            bad_contract = bad['contract'] if path == 'contract' else bad['core_architecture']['contract']
            bad_contract['task']['finger_skill']['scope'] = 'changed'
            policy.architecture = bad
            with self.assertRaisesRegex(ValueError, '관측·제어·구조'):
                m.initialize_policy(policy, config)
        policy.architecture = copy.deepcopy(before)
        policy.architecture['contract']['action']['unapproved_control_change'] = True
        with self.assertRaisesRegex(ValueError, '관측·제어·구조'):
            m.initialize_policy(policy, config)

    def test_original_transition_reset_forces_whole_AB(self):
        env = object.__new__(m.runtime.TransitionEnvironment)
        env.evaluation = env.evaluation_full_song = False
        env.phase_target = m.torch.zeros(1, dtype=m.torch.long)
        env.target_switch_count = m.torch.zeros(1, dtype=m.torch.long)
        env.target_phase_seconds = m.torch.zeros(1, 2, 3)
        env.first_contact_s = m.torch.zeros(1, 2)
        env.first_achievement_s = m.torch.zeros(1, 2)
        observed = []
        def base_reset(current, indices):
            observed.append((current.evaluation, current.evaluation_full_song))
        with patch.object(m.runtime.natural.NaturalEnvironment, '_reset_scope', base_reset):
            env._reset_scope(m.torch.tensor([0]))
        self.assertEqual(observed, [(True, True)])
        self.assertEqual((env.evaluation, env.evaluation_full_song), (False, False))


if __name__ == '__main__':
    unittest.main()
