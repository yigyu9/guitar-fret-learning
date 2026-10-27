import copy
from pathlib import Path
import tempfile
import unittest

import torch
from torch.distributions import Normal

from guitar_learning.training.ppo import PPOConfig, PPOTrainer, gaussian_kl
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.tests.test_policy import policy as shared_policy
from guitar_learning.tests.test_ppo import buffer


def specialist(role='left', frozen_partner=False):
    contract = copy.deepcopy(shared_policy().architecture['contract'])
    contract['task']['specialist'] = {'role': role}
    contract['reward'] = {'specialist_role': role}
    return SpecialistPolicy(5, size='small', contract=contract,
                            role=role, frozen_partner=frozen_partner)


def inputs():
    return (torch.randn(8, 5), torch.randn(8, 2, 24), torch.ones(8, 2, dtype=torch.bool),
            torch.randn(8, 2, 24), torch.ones(8, 2, dtype=torch.bool))


def checkpoint(model):
    trainer = PPOTrainer(model, PPOConfig(actor_lr=1e-5, epochs=1, target_kl=.1))
    trainer.update(buffer(model))
    return dict(identity=copy.deepcopy(trainer._identity()), model=copy.deepcopy(model.state_dict()),
                updates=trainer.updates, metadata={'purpose': 'CPU synthetic specialist'})


class SpecialistPolicyTests(unittest.TestCase):
    def test_independent_branches_and_common_value_contract(self):
        model = specialist('joint')
        left = {id(p) for p in model.actor_encoders['left'].parameters()}
        right = {id(p) for p in model.actor_encoders['right'].parameters()}
        value = {id(p) for p in model.value_parameters()}
        self.assertFalse(left & right)
        self.assertFalse((left | right) & value)
        self.assertEqual(model.architecture['schema'], 'guitar_specialists39_v1')
        self.assertEqual(model.architecture['likelihood'], 'trainable_channels_only_v1')
        result = model.act(*inputs())
        self.assertEqual(result['action'].shape, (8, 39))
        self.assertEqual(result['reward_value'].shape, (8,))
        self.assertEqual(result['cost_value'].shape, (8,))
        with self.assertRaises(ValueError): specialist('joint', True)

    def test_inactive_actions_noise_likelihood_and_entropy(self):
        for role, active, inactive in (('left', slice(0, 33), slice(33, 39)),
                                       ('right', slice(33, 39), slice(0, 33))):
            with self.subTest(role=role):
                model = specialist(role)
                data = inputs()
                result = model.act(*data)
                self.assertTrue(torch.equal(result['action'][:, inactive], torch.zeros_like(result['action'][:, inactive])))
                self.assertTrue(torch.equal(result['latent'][:, inactive], torch.zeros_like(result['latent'][:, inactive])))
                latent = result['latent'][:, active]
                correction = 2 * (torch.log(torch.tensor(2.)) - latent - torch.nn.functional.softplus(-2 * latent))
                expected = (Normal(result['mean'][:, active], result['log_std'][:, active].exp()).log_prob(latent) - correction).sum(-1)
                self.assertTrue(torch.allclose(result['logp'], expected))
                changed_inactive = result['latent'].clone()
                changed_inactive[:, inactive] = 10.
                actual = model.evaluate(*data, changed_inactive)
                self.assertTrue(torch.equal(actual['logp'], result['logp']))
                expected_entropy = Normal(result['mean'][:, active], result['log_std'][:, active].exp()).entropy().sum(-1)
                self.assertTrue(torch.equal(actual['entropy'], expected_entropy))

    def test_real_ppo_update_preserves_inactive_parameters_and_kl(self):
        for role, inactive_role, inactive in (('left', 'right', slice(33, 39)),
                                               ('right', 'left', slice(0, 33))):
            with self.subTest(role=role):
                model = specialist(role)
                trainer = PPOTrainer(model, PPOConfig(actor_lr=1e-5, epochs=1, target_kl=.1))
                data = inputs()
                with torch.no_grad(): before_distribution = model(*data)
                before = copy.deepcopy(model.state_dict())
                trainer.update(buffer(model))
                after_distribution = model(*data)
                for key, value in model.state_dict().items():
                    if key.startswith(('actor_encoders.' + inactive_role, 'actor_heads.' + inactive_role)):
                        self.assertTrue(torch.equal(before[key], value), key)
                self.assertTrue(torch.equal(before['log_std'][inactive], model.log_std[inactive]))
                self.assertTrue(torch.equal(model.log_std.grad[inactive], torch.zeros_like(model.log_std.grad[inactive])))
                self.assertEqual(float(gaussian_kl(before_distribution['mean'][:, inactive],
                                                 before_distribution['log_std'][:, inactive],
                                                 after_distribution['mean'][:, inactive],
                                                 after_distribution['log_std'][:, inactive])), 0.)
                self.assertFalse(torch.equal(before['actor_heads.' + role + '.bias'], model.actor_heads[role].bias))

    def test_full_actor_transfer_and_frozen_partner_survive_update_and_resume(self):
        source = specialist('left')
        source_checkpoint = checkpoint(source)
        target = specialist('right', True)
        with self.assertRaisesRegex(ValueError, 'frozen partner'):
            target.act(*inputs())
        metadata = target.transfer_actor(source_checkpoint, 'left')
        self.assertEqual(metadata['source_updates'], 1)
        self.assertEqual(metadata['source_metadata']['purpose'], 'CPU synthetic specialist')
        data = inputs()
        expected = source.act(*data, deterministic=True)['action'][:, :33].detach().clone()
        actual = target.act(*data)['action'][:, :33]
        self.assertTrue(torch.equal(expected, actual))
        trainer = PPOTrainer(target, PPOConfig(actor_lr=1e-5, epochs=1, target_kl=.1))
        trainer.update(buffer(target))
        self.assertTrue(torch.equal(expected, target.act(*data)['action'][:, :33]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'frozen.pt'
            trainer.save(path, {'partner': metadata})
            restored = PPOTrainer(specialist('right', True), trainer.config)
            restored.load(path)
            self.assertTrue(bool(restored.policy.partner_initialized[0]))
            self.assertTrue(torch.equal(expected, restored.policy.act(*data)['action'][:, :33]))

    def test_joint_transfer_preserves_both_deterministic_branches(self):
        left, right = specialist('left'), specialist('right')
        left_checkpoint, right_checkpoint = checkpoint(left), checkpoint(right)
        target = specialist('joint')
        target.transfer_actor(left_checkpoint, 'left')
        target.transfer_actor(right_checkpoint, 'right')
        data = inputs()
        expected = torch.cat((left.act(*data, deterministic=True)['action'][:, :33],
                              right.act(*data, deterministic=True)['action'][:, 33:]), -1)
        self.assertTrue(torch.equal(expected, target.act(*data, deterministic=True)['action']))

    def test_incompatible_or_untrained_transfers_are_rejected_before_mutation(self):
        good = checkpoint(specialist('left'))
        variants = []
        for field, value in (('observation', {'different': True}), ('action', {'dimension': 40}),
                             ('termination', {'different': True}), ('task', {'source': 'other'})):
            bad = copy.deepcopy(good)
            bad['identity']['architecture']['contract'][field] = value
            variants.append(bad)
        for updates in (0, True):
            bad = copy.deepcopy(good)
            bad['updates'] = updates
            variants.append(bad)
        bad = copy.deepcopy(good)
        bad['identity']['architecture']['schema'] = 'guitar_attention39_v1'
        variants.append(bad)
        bad = copy.deepcopy(good)
        bad['identity']['architecture']['role'] = 'right'
        variants.append(bad)
        bad = copy.deepcopy(good)
        bad['model']['actor_heads.left.bias'][0] = float('nan')
        variants.append(bad)
        bad = copy.deepcopy(good)
        bad['model']['actor_heads.left.bias'] = torch.zeros(32)
        variants.append(bad)
        target = specialist('joint')
        before = copy.deepcopy(target.state_dict())
        for payload in variants:
            with self.assertRaises(ValueError): target.transfer_actor(payload, 'left')
            self.assertTrue(all(torch.equal(value, target.state_dict()[key]) for key, value in before.items()))

    def test_strict_resume_rejects_different_role_reward_or_partner_mode(self):
        trainer = PPOTrainer(specialist('left'))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'left.pt'
            trainer.save(path)
            for target in (specialist('right'), specialist('joint'), specialist('left', True)):
                with self.assertRaisesRegex(ValueError, 'mismatch'):
                    PPOTrainer(target).load(path)
            target = specialist('left')
            target.architecture['contract']['reward']['new_weight'] = 2.
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                PPOTrainer(target).load(path)


if __name__ == '__main__':
    unittest.main()
