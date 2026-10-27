import copy
import hashlib
import random
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch
from torch.distributions import Normal

from guitar_learning.training.ppo import PPOConfig, PPOTrainer, gaussian_kl
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.training.policy import Policy
from guitar_learning.tests.test_policy import policy as shared_policy
from guitar_learning.tests.test_ppo import buffer, assert_tree


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


def finger_contract():
    return dict(schema='guitar_learning.training.v1',
        observation=dict(dimension=544, priority_slots=8,
            finger_targets=dict(schema='guitar_learning.left_finger_targets.v1',
                slots=[f+'_'+kind for f in ('index', 'middle', 'ring', 'pinky')
                       for kind in ('tracking', 'next')])),
        action=dict(dimension=39), task={}, reward={}, termination={},
        native_backend=dict(pipeline='gpu'))


def finger_inputs():
    return (torch.randn(3, 544), torch.randn(3, 4, 24), torch.ones(3, 4, dtype=torch.bool),
            torch.randn(3, 8, 24), torch.ones(3, 8, dtype=torch.bool))


class FingerTargetPolicyTests(unittest.TestCase):
    def test_explicit_eight_slots_finite_gradients_and_inactive_actions(self):
        model = SpecialistPolicy(544, size='small', contract=finger_contract())
        self.assertEqual(model.architecture['priority_slots'], tuple(finger_contract()['observation']['finger_targets']['slots']))
        self.assertEqual(model.actor_encoders['left'].output[0].in_features, 1408)
        self.assertEqual(model.value_encoder.output[0].in_features, 1408)
        data = finger_inputs()
        result = model.act(*data)
        self.assertTrue(torch.equal(result['action'][:, 33:], torch.zeros(3, 6)))
        self.assertTrue(all(torch.isfinite(v).all() for v in result.values()))
        with torch.no_grad():
            model.actor_heads['left'].weight.fill_(.001)
        priority = data[3].clone().requires_grad_(True)
        result = model(*data[:3], priority, data[4])
        (result['mean'][:, :33].sum()+result['reward_value'].sum()+result['cost_value'].sum()).backward()
        self.assertTrue(torch.isfinite(priority.grad).all())
        self.assertTrue((priority.grad.abs().sum((0, 2)) > 0).all())
        self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None))
        self.assertTrue(all(p.grad is None for p in model.actor_encoders['right'].parameters()))

    def test_eight_slot_masks_and_shape_validation(self):
        model = SpecialistPolicy(544, size='small', contract=finger_contract())
        data = list(finger_inputs())
        data[4][:, 1::2] = False
        expected = model(*data)
        padded = data[3].clone(); padded[~data[4]] = float('nan')
        actual = model(*data[:3], padded, data[4])
        for key in expected:
            self.assertTrue(torch.equal(expected[key], actual[key]), key)
        output = model(data[0], data[1], torch.zeros_like(data[2]),
                       torch.full_like(data[3], float('nan')), torch.zeros_like(data[4]))
        self.assertTrue(all(torch.isfinite(v).all() for v in output.values()))
        invalid = []
        for field, value in ((0, torch.zeros(3, 512)), (3, torch.zeros(3, 2, 24)),
                             (4, torch.ones(3, 2, dtype=torch.bool)), (4, torch.ones(3, 8))):
            case = list(data); case[field] = value; invalid.append(case)
        case = list(data); case[3] = data[3].clone(); case[3][0, 0, 0] = float('nan'); invalid.append(case)
        for case in invalid:
            with self.assertRaises(ValueError): model(*case)

    def test_only_explicit_gpu_left_contract_can_enable_eight_slots(self):
        for role in ('right', 'joint'):
            with self.assertRaises(ValueError):
                SpecialistPolicy(544, size='small', contract=finger_contract(), role=role)
        for field, value in (('priority_slots', 2), ('priority_slots', True), ('dimension', 512),
                             ('finger_targets', {}), ('finger_targets', None)):
            c = finger_contract(); c['observation'][field] = value
            with self.assertRaises(ValueError): SpecialistPolicy(544, size='small', contract=c)
        for field, value in (('schema', 'other'), ('slots', ['wrong']*8)):
            c = finger_contract(); c['observation']['finger_targets'][field] = value
            with self.assertRaises(ValueError): SpecialistPolicy(544, size='small', contract=c)
        for backend in ({'pipeline': 'cpu'}, None, {}):
            c = finger_contract(); c['native_backend'] = backend
            with self.assertRaises(ValueError): SpecialistPolicy(544, size='small', contract=c)
        c = finger_contract(); del c['observation']['finger_targets']
        with self.assertRaises(ValueError): SpecialistPolicy(544, size='small', contract=c)
        with self.assertRaises(ValueError): SpecialistPolicy(512, size='small', contract=finger_contract())

    def test_legacy_two_slot_seed_and_architecture_are_unchanged(self):
        # Recorded from the live pre-change classes, before edits; no archive execution.
        contract = dict(schema='guitar_learning.training.v1', observation=dict(dimension=5),
                        action=dict(dimension=39), task={}, reward={}, termination={})
        for cls, kwargs, model_hash, rng_hash, count in (
            (Policy, {}, 'b2142d2c5e4cc59415d064b370e6bc7d4c89ca334121fda5b53e496487edbde1',
             'bc802f6e42dca39b1c441bb8767f47c8ce29bb9515512c8ab981009dc0cee9b1', 841552),
            (SpecialistPolicy, dict(role='left'), '4289279d77da1babbf5652fb8eac6eb971c991a79c63701641919f63810849fa',
             '8dce885d3bec14b44f4d3bcb08b174dd39ccb09fd3eefb8e91d5aca6ce5a0194', 1257040),
            (SpecialistPolicy, dict(role='right'), '4289279d77da1babbf5652fb8eac6eb971c991a79c63701641919f63810849fa',
             '8dce885d3bec14b44f4d3bcb08b174dd39ccb09fd3eefb8e91d5aca6ce5a0194', 1257040)):
            torch.manual_seed(8721)
            model = cls(5, size='small', contract=contract, **kwargs)
            digest = hashlib.sha256()
            for key, value in model.state_dict().items():
                digest.update(key.encode()); digest.update(value.detach().numpy().tobytes())
            self.assertEqual(digest.hexdigest(), model_hash)
            self.assertEqual(hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(), rng_hash)
            self.assertEqual(sum(p.numel() for p in model.parameters()), count)
            self.assertEqual(model.architecture['priority_slots'], ('current', 'nearest_strict_deadline'))
            self.assertEqual(model.value_encoder.output[0].in_features, 640)
        c = copy.deepcopy(contract); c['observation'].update(dimension=500, priority_slots=2)
        right = SpecialistPolicy(500, size='small', contract=c, role='right')
        self.assertEqual(right.architecture['priority_slots'], ('current', 'nearest_strict_deadline'))

    def test_eight_slot_strict_resume_and_wrong_slot_identity_rejection(self):
        trainer = PPOTrainer(SpecialistPolicy(544, size='small', contract=finger_contract()),
                             PPOConfig(actor_lr=1e-5, epochs=1, target_kl=.1))
        data = finger_inputs()
        with torch.no_grad():
            action = trainer.policy.act(*data)
        batch = {key:value[:, None] for key,value in zip(
            ('state', 'events', 'mask', 'priority_events', 'priority_mask'), data)}
        for key in ('latent', 'logp', 'reward_value', 'cost_value'):
            batch[key] = action[key][:, None]
        batch.update(old_mean=action['mean'][:, None], old_log_std=action['log_std'][:, None].clone(),
                     next_reward_value=torch.zeros(3, 1), next_cost_value=torch.zeros(3, 1),
                     reward=torch.arange(3.).reshape(3, 1)/10, cost=torch.zeros(3, 1),
                     terminated=torch.zeros(3, 1, dtype=torch.bool), truncated=torch.zeros(3, 1, dtype=torch.bool))
        inactive = {k:v.clone() for k,v in trainer.policy.state_dict().items() if k.startswith('actor_encoders.right.') or k.startswith('actor_heads.right.')}
        trainer.update(batch)
        self.assertEqual(trainer.updates, 1)
        self.assertTrue(all(torch.equal(v, trainer.policy.state_dict()[k]) for k,v in inactive.items()))
        self.assertTrue(trainer.actor_optimizer.state and trainer.value_optimizer.state)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'eight.pt'; trainer.save(path)
            restored = PPOTrainer(SpecialistPolicy(544, size='small', contract=finger_contract()), trainer.config)
            restored.load(path)
            self.assertTrue(all(torch.equal(a, restored.policy.state_dict()[k]) for k,a in trainer.policy.state_dict().items()))
            wrong = torch.load(path, map_location='cpu', weights_only=False)
            wrong['identity']['architecture']['priority_slots'] = tuple(reversed(wrong['identity']['architecture']['priority_slots']))
            bad = Path(directory)/'wrong.pt'; torch.save(wrong, bad)
            before = copy.deepcopy(restored.policy.state_dict())
            actor = copy.deepcopy(restored.actor_optimizer.state_dict())
            value = copy.deepcopy(restored.value_optimizer.state_dict())
            rng = torch.get_rng_state().clone(); py_rng = random.getstate(); np_rng = np.random.get_state()
            with self.assertRaisesRegex(ValueError, 'mismatch'): restored.load(bad)
            self.assertTrue(all(torch.equal(a, restored.policy.state_dict()[k]) for k,a in before.items()))
            assert_tree(self, restored.actor_optimizer.state_dict(), actor)
            assert_tree(self, restored.value_optimizer.state_dict(), value)
            self.assertTrue(torch.equal(rng, torch.get_rng_state()))
            self.assertEqual(py_rng, random.getstate())
            self.assertEqual(np_rng[0], np.random.get_state()[0])
            np.testing.assert_array_equal(np_rng[1], np.random.get_state()[1])
            self.assertEqual(np_rng[2:], np.random.get_state()[2:])


if __name__ == '__main__':
    unittest.main()
