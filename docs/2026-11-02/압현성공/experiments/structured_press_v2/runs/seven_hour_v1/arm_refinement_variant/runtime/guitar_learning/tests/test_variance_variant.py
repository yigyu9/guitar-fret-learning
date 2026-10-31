"""새 schema의 분포 일치·엄격 이전·계수 구분을 CPU에서 검사한다."""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import torch
from torch.distributions import Normal, kl_divergence
from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
_entry = nested_input_paths(); _entry.__enter__()
from guitar_learning.tool.experiments import variance_variant as v
from guitar_learning.training.ppo import PPOConfig


class VarianceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.payload = torch.load(v.TRANSFER, map_location='cpu', weights_only=False)
        cls.arch = v.localize(cls.payload['identity']['architecture'])

    def make_policy(self, factor=.05, size='small', stage='B'):
        settings = v.train_settings(factor)
        config = settings['structured_press']
        if stage == 'free_v9':
            config = v.sp.load_configuration(config['geometry'], config['song'], 'free_v9')
        contract = copy.deepcopy(self.arch['contract']); contract['structured_press'] = config
        return v.VariancePolicy(self.arch['state_dim'], size=size, contract=contract,
                                structured=config, factor=factor), settings

    def data(self, count=4):
        dim = self.arch['state_dim']
        return (torch.zeros(count, dim), torch.zeros(count, 7, 24), torch.ones(count, 7, dtype=torch.bool),
                torch.zeros(count, 8, 24), torch.ones(count, 8, dtype=torch.bool))

    def test_mean_unchanged_selected_four_std_scaled_after_floor(self):
        model, _ = self.make_policy()
        base = v.BASE_POLICY(self.arch['state_dim'], size='small',
            contract=model.architecture['contract'], structured=model.structured)
        base.load_state_dict(model.state_dict())
        data = self.data(); expected = base(*data); actual = model(*data)
        self.assertTrue(torch.equal(actual['mean'], expected['mean']))
        axes = model.variance['selected_axes']; unchanged = [i for i in range(39) if i not in axes]
        self.assertTrue(torch.equal(actual['log_std'][:, unchanged], expected['log_std'][:, unchanged]))
        self.assertTrue(torch.allclose(actual['log_std'][:, axes].exp(), expected['log_std'][:, axes].exp()*.05))
        with torch.no_grad(): model.core.finger_log_std.fill_(-5)
        self.assertTrue(torch.allclose(model(*data)['log_std'][:, axes].exp(), torch.full((4, 4), .005)))
        self.assertEqual(model.architecture['schema'], v.VariancePolicy.schema)
        self.assertNotEqual(model.architecture['schema'], base.architecture['schema'])

    def test_sampling_logp_kl_entropy_all_use_actual_forward_distribution(self):
        model, _ = self.make_policy(); data = self.data()
        torch.manual_seed(7); result = model.act(*data)
        active = model.active_mask
        gaussian = Normal(result['mean'][:, active], result['log_std'][:, active].exp())
        latent = result['latent'][:, active]
        correction = 2*(torch.log(torch.tensor(2.))-latent-torch.nn.functional.softplus(-2*latent))
        expected_logp = (gaussian.log_prob(latent)-correction).sum(-1)
        self.assertTrue(torch.allclose(result['logp'], expected_logp, atol=2e-5))
        evaluated = model.evaluate(*data, result['latent'])
        self.assertTrue(torch.equal(evaluated['logp'], result['logp']))
        self.assertTrue(torch.allclose(evaluated['entropy'], gaussian.entropy().sum(-1)))
        updated_mean, updated_std = result['mean']+.003, result['log_std']+.01
        expected_kl = kl_divergence(gaussian, Normal(updated_mean[:, active], updated_std[:, active].exp())).sum(-1)
        self.assertTrue(torch.allclose(model.analytic_kl(result['mean'], result['log_std'], updated_mean, updated_std), expected_kl))
        self.assertTrue(torch.isfinite(result['action']).all())

    def test_real_ppo_update_uses_variant_distribution_and_remains_finite(self):
        model, _ = self.make_policy(); data = self.data(8)
        with torch.no_grad(): result = model.act(*data)
        buffer = {name:value.reshape((2, 4)+value.shape[1:]) for name,value in zip(
            ('state','events','mask','priority_events','priority_mask'), data)}
        for name in ('latent','logp','reward_value','cost_value'):
            value = result[name]; buffer[name] = value.reshape((2, 4)+value.shape[1:])
        buffer.update(old_mean=result['mean'].reshape(2,4,39), old_log_std=result['log_std'].reshape(2,4,39),
            next_reward_value=torch.zeros(2,4), next_cost_value=torch.zeros(2,4),
            reward=torch.arange(8.).reshape(2,4)/10, cost=torch.zeros(2,4),
            terminated=torch.zeros(2,4,dtype=torch.bool), truncated=torch.zeros(2,4,dtype=torch.bool),
            valid=torch.ones(2,4,dtype=torch.bool), duration=torch.ones(2,4,dtype=torch.long))
        trainer = v.sp.StructuredTrainer(model, PPOConfig(epochs=1,minibatch_size=8,retry_lr_factor=.5))
        output = trainer.update(buffer)
        self.assertEqual(trainer.updates, 1)
        self.assertTrue(__import__('math').isfinite(output['actor_loss']))
        self.assertTrue(all(torch.isfinite(value).all() for value in model.parameters()))

    def test_full_strict_base_transfer_model_equal_except_target_mask(self):
        before = v.digest(v.TRANSFER)
        model, _ = self.make_policy(size='large')
        model.initialize_from(v.TRANSFER, expected_sha256=before)
        for name, expected in self.payload['model'].items():
            if name != 'active_mask': self.assertTrue(torch.equal(model.state_dict()[name], expected), name)
        self.assertEqual(model.active_mask.nonzero().flatten().tolist(), model.structured['active_axes'])
        self.assertEqual(before, v.digest(v.TRANSFER))
        self.assertEqual(len(v.verify_audit()), 64)

    def test_temporary_bridge_preserves_control_initialization_cpu_rng(self):
        settings = v.train_settings(.05)
        contract = copy.deepcopy(self.arch['contract']); contract['structured_press'] = settings['structured_press']
        torch.manual_seed(7)
        control = v.BASE_POLICY(self.arch['state_dim'], size='large', contract=contract,
                                structured=settings['structured_press'])
        control.initialize_from(v.TRANSFER, expected_sha256=v.digest(v.TRANSFER))
        control_rng = torch.get_rng_state().clone()
        torch.manual_seed(7)
        variant, _ = self.make_policy(size='large')
        variant.initialize_from(v.TRANSFER, expected_sha256=v.digest(v.TRANSFER))
        self.assertTrue(torch.equal(control_rng, torch.get_rng_state()))
        for name, value in control.state_dict().items():
            self.assertTrue(torch.equal(value, variant.state_dict()[name]), name)

    def test_checkpoint_rejects_wrong_factor_and_old_schema(self):
        model, _ = self.make_policy()
        trainer = v.sp.StructuredTrainer(model)
        with tempfile.TemporaryDirectory(prefix='variance_identity_') as temporary:
            path = Path(temporary)/'checkpoint.pt'; trainer.save(path)
            other, _ = self.make_policy(.1)
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                v.sp.StructuredTrainer(other).load(path)
            old = v.BASE_POLICY(self.arch['state_dim'], size='small',
                contract=model.architecture['contract'], structured=model.structured)
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                v.sp.StructuredTrainer(old).load(path)

    def test_variant_B_to_free_v9_validates_own_identity_before_transfer(self):
        from guitar_learning.portability import portable
        model, settings = self.make_policy(size='large')
        model.initialize_from(v.TRANSFER, expected_sha256=v.digest(v.TRANSFER))
        trainer = v.sp.StructuredTrainer(model, PPOConfig(**settings['ppo']))
        schedule = v.official.ExposureSchedule(settings['finger_skill']['planned_transitions'])
        pool = SimpleNamespace(environment=SimpleNamespace(sampler=SimpleNamespace(state_dict=lambda: {})))
        with tempfile.TemporaryDirectory(prefix='variance_free_transfer_') as temporary:
            out = Path(temporary)
            (out/'settings.json').write_text(__import__('json').dumps(portable(settings)))
            pins = v.official._pins(settings, out)
            metadata = v.official.checkpoint_metadata(settings, schedule, pool, input_pins=pins, settings_path=out/'settings.json')
            path = out/'model.pt'; trainer.save(path, metadata=metadata)
            free, _ = self.make_policy(size='large', stage='free_v9')
            free.initialize_from(path, expected_sha256=v.digest(path))
            self.assertEqual(int(free.active_mask.sum()), 33)
            for name, expected in model.state_dict().items():
                if name != 'active_mask': self.assertTrue(torch.equal(free.state_dict()[name], expected), name)


if __name__ == '__main__':
    unittest.main()
