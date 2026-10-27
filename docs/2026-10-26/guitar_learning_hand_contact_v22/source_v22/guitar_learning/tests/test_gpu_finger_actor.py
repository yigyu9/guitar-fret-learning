"""CPU contracts and gradients; no native/GPU performance claims."""
import copy
from pathlib import Path
import tempfile
import unittest

import torch

from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG
from guitar_learning.tests.test_specialist_policy import finger_inputs as legacy_finger_inputs
from guitar_learning.training.ppo import PPOConfig, PPOTrainer, gaussian_kl


def finger_inputs():
    return legacy_finger_inputs(state_dim=552)


def actor_contract():
    metadata, _ = fixture()
    contract = TensorSongEnvironment(metadata, bundle=BUNDLE, song=SONG,
                                     hand='left', device='cpu').contract
    contract = copy.deepcopy(contract)
    return contract


def actor():
    return SpecialistPolicy(552, size='small', contract=actor_contract())


def batch(model, data):
    with torch.no_grad():
        result = model.act(*data)
    output = {key: value[:, None] for key, value in zip(
        ('state', 'events', 'mask', 'priority_events', 'priority_mask'), data)}
    output.update({key: result[key][:, None] for key in
                   ('latent', 'logp', 'reward_value', 'cost_value')})
    output.update(old_mean=result['mean'][:, None], old_log_std=result['log_std'][:, None].clone(),
        next_reward_value=torch.zeros(3, 1), next_cost_value=torch.zeros(3, 1),
        reward=torch.arange(3.).reshape(3, 1)/10, cost=torch.zeros(3, 1),
        terminated=torch.zeros(3, 1, dtype=torch.bool), truncated=torch.zeros(3, 1, dtype=torch.bool))
    return output


class TargetedFingerActorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_explicit_local_fields_order_and_zero_fresh_actions(self):
        model = actor()
        spec = model.architecture['finger_actor']
        fields = model.architecture['contract']['observation']['fields']
        self.assertEqual(tuple(model.finger_heads), ('index', 'middle', 'ring', 'pinky'))
        self.assertEqual(model.actor_heads['left'].out_features, 17)
        self.assertEqual(spec['shared_action_names'], tuple(ACTIVE_NAMES[:17]))
        for finger, head in model.finger_heads.items():
            self.assertEqual(head[0].in_features, 256+256+20)
            self.assertEqual(head[0].out_features, 128)
            self.assertEqual(head[-1].out_features, 4)
            selected = [fields[index] for index in spec['local_indices'][finger]]
            self.assertEqual(selected, spec['local_fields'][finger])
            self.assertEqual(len(selected), 20)
            self.assertEqual(selected[:4], ['q_offset.LH:'+finger+suffix
                                          for suffix in ('1_x', '1_z', '2', '3')])
            self.assertEqual(selected[-2:], ['finger_posture.'+finger+'.'+key
                                            for key in ('valid', 'standby_gate')])
        result = model.act(*finger_inputs(), deterministic=True)
        self.assertTrue(torch.equal(result['action'], torch.zeros(3, 39)))
        self.assertTrue(all(torch.isfinite(value).all() for value in result.values()))
        self.assertEqual(int(model._active_mask().sum()), 33)

    def test_exact_action_reassembly_and_direct_own_inputs(self):
        model = actor()
        data = finger_inputs()
        with torch.no_grad():
            model.actor_heads['left'].bias.copy_(torch.arange(17.))
            for index, head in enumerate(model.finger_heads.values()):
                head[-1].bias.copy_(torch.arange(4.)+17+4*index)
        result = model(*data)
        self.assertTrue(torch.equal(result['mean'][:, :33], torch.arange(33.).expand(3, -1)))
        self.assertTrue(torch.equal(result['mean'][:, 33:], torch.zeros(3, 6)))
        # Remove the global route to isolate direct token/local dependencies.
        for index, (finger, head) in enumerate(model.finger_heads.items()):
            with torch.no_grad():
                head[0].weight.zero_(); head[0].bias.zero_()
                head[0].weight[:, 256:].fill_(.01)
                head[-1].weight.fill_(.01)
            state = data[0].clone().requires_grad_(True)
            priority = data[3].clone().requires_grad_(True)
            mean = model(state, data[1], data[2], priority, data[4])['mean']
            state_grad, token_grad = torch.autograd.grad(mean[:, 17+4*index:21+4*index].sum(), (state, priority))
            expected = torch.zeros(552, dtype=torch.bool)
            expected[model.architecture['finger_actor']['local_indices'][finger]] = True
            self.assertTrue((state_grad.abs().sum(0)[expected] > 0).all())
            self.assertTrue((state_grad[:, ~expected] == 0).all())
            token_used = token_grad.abs().sum((0, 2)) > 0
            expected_tokens = torch.zeros(8, dtype=torch.bool)
            expected_tokens[2*index:2*index+2] = True
            self.assertTrue(torch.equal(token_used, expected_tokens))

    def test_real_cpu_tensor_observation_uses_named_posture_and_joints(self):
        metadata, snapshot = fixture()
        env = TensorSongEnvironment(metadata, bundle=BUNDLE, song=SONG, hand='left', device='cpu')
        observation = env.reset([0, 1], snapshot)
        model = actor()
        inputs = tuple(observation[key] for key in ('state', 'events', 'mask', 'priority_events', 'priority_mask'))
        result = model.act(*inputs, deterministic=True)
        self.assertTrue(torch.equal(result['action'], torch.zeros(2, 39)))
        for finger, indices in model.architecture['finger_actor']['local_indices'].items():
            fields = env.contract['observation']['fields']
            self.assertEqual([fields[index] for index in indices],
                             model.architecture['finger_actor']['local_fields'][finger])
            self.assertTrue(torch.isfinite(observation['state'][:, indices]).all())

    def test_masked_nan_tokens_gradients_and_optimizer_coverage(self):
        model = actor()
        data = list(finger_inputs())
        data[4][:, 1::2] = False
        with torch.no_grad():
            for head in model.finger_heads.values():
                head[-1].weight.fill_(.01)
        expected = model(*data)
        data[3] = data[3].clone(); data[3][~data[4]] = float('nan')
        actual = model(*data)
        self.assertTrue(all(torch.equal(expected[key], actual[key]) for key in expected))
        actual['mean'][:, 17:33].sum().backward()
        for head in model.finger_heads.values():
            self.assertTrue(all(parameter.grad is not None and torch.isfinite(parameter.grad).all()
                                for parameter in head.parameters()))
            self.assertGreater(float(head[0].weight.grad.abs().sum()), 0)
        actor_ids = {id(parameter) for parameter in model.actor_parameters()}
        self.assertTrue(all(id(parameter) in actor_ids for parameter in model.finger_heads.parameters()))
        self.assertFalse(actor_ids & {id(parameter) for parameter in model.value_parameters()})
        self.assertTrue(all(parameter.grad is None for parameter in model.actor_encoders['right'].parameters()))
        data[2].zero_(); data[4].zero_(); data[3].fill_(float('nan'))
        self.assertTrue(all(torch.isfinite(value).all() for value in model(*data).values()))

    def test_ppo_update_roundtrip_and_old_identity_rejection(self):
        model = actor()
        trainer = PPOTrainer(model, PPOConfig(actor_lr=1e-5, epochs=1, target_kl=.1))
        data = finger_inputs()
        old = copy.deepcopy(model.state_dict())
        with torch.no_grad(): before = model(*data)
        trainer.update(batch(model, data))
        after = model(*data)
        for key, value in model.state_dict().items():
            if key.startswith(('actor_encoders.right.', 'actor_heads.right.')):
                self.assertTrue(torch.equal(old[key], value), key)
        for finger in model.finger_heads:
            self.assertFalse(torch.equal(old['finger_heads.'+finger+'.2.bias'],
                                         model.state_dict()['finger_heads.'+finger+'.2.bias']))
        self.assertEqual(float(gaussian_kl(before['mean'][:, 33:], before['log_std'][:, 33:],
                                           after['mean'][:, 33:], after['log_std'][:, 33:])), 0.)
        self.assertTrue(torch.equal(old['log_std'][33:], model.log_std[33:]))
        self.assertEqual(trainer.updates, 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'actor.pt'; trainer.save(path)
            restored = PPOTrainer(actor(), trainer.config); restored.load(path)
            self.assertTrue(all(torch.equal(value, restored.policy.state_dict()[key])
                                for key, value in model.state_dict().items()))
            self.assertTrue(torch.equal(model.act(*data, deterministic=True)['action'],
                                        restored.policy.act(*data, deterministic=True)['action']))
            payload = torch.load(path, map_location='cpu', weights_only=False)
            transferred = actor()
            transferred.transfer_actor(payload, 'left')
            self.assertTrue(torch.equal(model.act(*data, deterministic=True)['action'],
                                        transferred.act(*data, deterministic=True)['action']))
            for key, value in model.state_dict().items():
                if key.startswith('finger_heads.'):
                    self.assertTrue(torch.equal(value, transferred.state_dict()[key]))
            del payload['identity']['architecture']['finger_actor']
            bad = Path(directory)/'old.pt'; torch.save(payload, bad)
            with self.assertRaisesRegex(ValueError, 'mismatch'): restored.load(bad)
            legacy = actor_contract(); legacy['reward']['schema'] = 'guitar_learning.gpu_tensor_song_reward.v7'
            legacy['observation']['dimension'] = 544
            legacy['observation']['fields'] = legacy['observation']['fields'][:544]
            legacy_model = SpecialistPolicy(544, size='small', contract=legacy)
            self.assertFalse(hasattr(legacy_model, 'finger_heads'))
            self.assertNotIn('finger_actor', legacy_model.architecture)
            self.assertEqual(legacy_model.actor_heads['left'].out_features, 33)
            with self.assertRaisesRegex(ValueError, 'mismatch'): PPOTrainer(legacy_model, trainer.config).load(path)

    def test_frozen_partner_mode_and_likelihood_ignore_inactive_channels(self):
        model = SpecialistPolicy(552, size='small', contract=actor_contract(), frozen_partner=True)
        data = finger_inputs()
        with self.assertRaisesRegex(ValueError, 'frozen partner'): model(*data)
        model.partner_initialized[1] = True
        before = copy.deepcopy(model.state_dict())
        result = model.act(*data)
        latent = result['latent'].clone(); latent[:, 33:] = 5.
        self.assertTrue(torch.equal(result['logp'], model.evaluate(*data, latent)['logp']))
        model.evaluate(*data, result['latent'])['logp'].sum().backward()
        self.assertTrue(all(parameter.grad is None for parameter in model.actor_encoders['right'].parameters()))
        self.assertTrue(all(parameter.grad is None for parameter in model.actor_heads['right'].parameters()))
        self.assertTrue(all(torch.equal(value, model.state_dict()[key]) for key, value in before.items()))

    def test_invalid_v8_contract_rejected_and_reordered_named_fields_resolved(self):
        contract = actor_contract()
        cases = []
        for field, value in (('fields', []), ('fields', ['duplicate']*552), ('priority_slots', 2)):
            case = copy.deepcopy(contract); case['observation'][field] = value; cases.append(case)
        case = copy.deepcopy(contract); case['action']['names'] = list(reversed(ACTIVE_NAMES)); cases.append(case)
        case = copy.deepcopy(contract); case['observation']['fields'][0] = 'q_offset.LH:index1_x'; cases.append(case)
        case = copy.deepcopy(contract)
        idx = case['observation']['fields'].index('q_offset.LH:index1_x')
        case['observation']['fields'][idx] = 'renamed'; cases.append(case)
        case = copy.deepcopy(contract); case['native_backend']['pipeline'] = 'cpu'; cases.append(case)
        for case in cases:
            with self.subTest(case=case['observation'].get('priority_slots')):
                with self.assertRaises(ValueError): SpecialistPolicy(552, size='small', contract=case)
        case = copy.deepcopy(contract)
        case['observation']['fields'].reverse()
        reordered = SpecialistPolicy(552, size='small', contract=case)
        indices = reordered.architecture['finger_actor']['local_indices']['index']
        self.assertEqual(indices[0], case['observation']['fields'].index('q_offset.LH:index1_x'))


if __name__ == '__main__':
    unittest.main()
