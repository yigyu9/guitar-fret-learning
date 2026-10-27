"""Split actors and exploration probability contracts; CPU only."""
import copy
import math
import unittest

import torch
from torch.distributions import MultivariateNormal, kl_divergence

from guitar_learning.skills.finger_skill_policy import FingerSkillPolicy, PHASE_FIELDS
from guitar_learning.tests.test_gpu_finger_actor import actor_contract


def contract(phase='F', exploration='independent'):
    value = actor_contract()
    value['observation']['fields'] += list(PHASE_FIELDS)
    value['observation']['scales'] += [1., 1., 1., 6., value['task']['duration_s']]
    value['observation']['dimension'] += 5
    value['task']['finger_skill'] = dict(schema='guitar_learning.finger_skill.v1',
                                       phase=phase, exploration=exploration)
    return value


def policy(phase='F', exploration='independent'):
    return FingerSkillPolicy(557, size='small', contract=contract(phase, exploration),
                             phase=phase, exploration=exploration)


def inputs(count=4):
    return (torch.randn(count, 557), torch.randn(count, 7, 24), torch.ones(count, 7, dtype=torch.bool),
            torch.randn(count, 8, 24), torch.ones(count, 8, dtype=torch.bool))


class FingerSkillPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_phases_active_axes_and_deterministic_inactive_actions(self):
        data = inputs()
        for phase, count in (('R', 17), ('F', 16), ('J', 33)):
            model = policy(phase)
            result = model.act(*data)
            self.assertEqual(int(model._active_mask().sum()), count)
            self.assertTrue(torch.equal(result['latent'][:, ~model._active_mask()],
                                        result['mean'][:, ~model._active_mask()]))
            self.assertTrue(torch.equal(result['action'][:, 33:], torch.zeros(4, 6)))
            changed = result['latent'].clone()
            changed[:, ~model._active_mask()] += 10
            self.assertTrue(torch.equal(result['logp'], model.evaluate(*data, changed)['logp']))
            means = result['mean'].clone(); means[:, ~model._active_mask()] += 10
            self.assertTrue(torch.equal(model.analytic_kl(result['mean'], result['log_std'], means,
                                                         result['log_std']), torch.zeros(4)))
            self.assertTrue(torch.equal(model.act(*data, deterministic=True)['action'], torch.zeros(4, 39)))

    def test_correlated_density_and_kl_match_full_mvn(self):
        model = policy('F', 'correlated').double()
        means = torch.randn(2, 39, dtype=torch.float64)*.2
        std = torch.randn(2, 39, dtype=torch.float64)*.1-2
        other_means, other_std = means+.03, std+.08
        latent = torch.randn(2, 39, dtype=torch.float64)*.3
        transform = torch.eye(39, dtype=torch.float64)
        for indices in model.bend_indices:
            transform[indices[:, None], indices[None, :]] = model.bend_basis
        active = model._active_mask()
        matrix = transform[active][:, active]
        def distribution(mean, log_std):
            covariance = matrix @ torch.diag_embed(log_std[:, active].mul(2).exp()) @ matrix.T
            return MultivariateNormal(mean[:, active], covariance_matrix=covariance)
        original = distribution(means, std)
        updated = distribution(other_means, other_std)
        correction = (2*(math.log(2)-latent[:, active]-torch.nn.functional.softplus(-2*latent[:, active]))).sum(-1)
        expected = original.log_prob(latent[:, active])-correction
        self.assertTrue(torch.allclose(model.log_probability(means, std, latent), expected, atol=1e-7))
        self.assertTrue(torch.allclose(model.analytic_kl(means, std, other_means, other_std),
                                       kl_divergence(original, updated), atol=1e-7))

    def test_basis_full_rank_marginal_variance_and_inverse(self):
        model = policy('F', 'correlated').double()
        basis = model.bend_basis
        self.assertTrue(torch.allclose(basis.T @ basis, torch.eye(3, dtype=torch.float64), atol=1e-7))
        variance = model.finger_log_std[[0, 2, 3]].mul(2).exp()
        covariance = basis @ torch.diag(variance) @ basis.T
        self.assertTrue(torch.allclose(covariance.diag(), torch.full((3,), math.exp(-6), dtype=torch.float64), atol=1e-9))
        self.assertTrue(torch.allclose(covariance[0, 1]/covariance[0, 0], torch.tensor(.5, dtype=torch.float64), atol=1e-7))
        self.assertTrue((torch.linalg.eigvalsh(covariance) > 0).all())
        latent = torch.randn(5, 39, dtype=torch.float64)
        self.assertTrue(torch.allclose(model._from_basis(model._to_basis(latent)), latent, atol=1e-7))

    def test_support_invariant_to_all_fine_only_inputs(self):
        model = policy('J')
        with torch.no_grad():
            model.support_head.weight.normal_(0, .01)
        data = list(inputs())
        before = model(*data)['mean'][:, :17]
        fine = torch.ones(557, dtype=torch.bool); fine[model.support_indices] = False
        data[0][:, fine] = torch.randn(4, int(fine.sum()))*10
        data[1][..., 9:] = torch.randn(4, 7, 15)*10
        data[3][..., 9:] = torch.randn(4, 8, 15)*10
        after = model(*data)['mean'][:, :17]
        self.assertTrue(torch.equal(before, after))
        self.assertTrue(all(not field.startswith(('finger_posture.', 'song.', 'finger_skill.'))
                            for field in model.architecture['support_fields']))

    def test_frozen_actor_parameters_excluded_and_bitwise_unchanged(self):
        for phase, frozen in (('F', ('support_encoder.', 'support_head.', 'support_log_std')),
                              ('R', ('finger_encoder.', 'finger_heads.', 'finger_log_std'))):
            model = policy(phase, 'correlated')
            optimizer = torch.optim.Adam(model.actor_parameters(), lr=.01)
            ids = {id(parameter) for group in optimizer.param_groups for parameter in group['params']}
            old = copy.deepcopy(model.state_dict())
            self.assertTrue(all(id(parameter) not in ids and not parameter.requires_grad
                                for name, parameter in model.named_parameters() if name.startswith(frozen)))
            for _ in range(2):
                data = inputs(); result = model.act(*data)
                loss = -model.evaluate(*data, result['latent'])['logp'].mean()
                optimizer.zero_grad(); loss.backward(); optimizer.step()
            for name, value in model.state_dict().items():
                if name.startswith(frozen): self.assertTrue(torch.equal(old[name], value), name)
            self.assertFalse(ids & {id(parameter) for parameter in model.value_parameters()})

    def test_all_four_heads_grad_and_masked_tokens_safe(self):
        model = policy('F')
        with torch.no_grad():
            for head in model.finger_heads.values(): head[-1].weight.fill_(.01)
        data = list(inputs())
        data[2][:, 3:] = False; data[4][:, 1::2] = False
        expected = model(*data)
        data[1][~data[2]] = float('nan'); data[3][~data[4]] = float('nan')
        actual = model(*data)
        self.assertTrue(all(torch.equal(expected[key], actual[key]) for key in expected))
        actual['mean'][:, 17:33].sum().backward()
        for head in model.finger_heads.values():
            self.assertTrue(all(parameter.grad is not None and torch.isfinite(parameter.grad).all()
                                for parameter in head.parameters()))
            self.assertGreater(float(head[0].weight.grad.abs().sum()), 0)

    def test_transfer_copies_actors_only_and_rejects_incompatible_contract(self):
        source, target = policy('R'), policy('F')
        with torch.no_grad():
            source.support_head.bias.fill_(.1)
            source.finger_heads['index'][-1].bias.fill_(.2)
        critic = {key: value.clone() for key, value in target.state_dict().items()
                  if key.startswith(('value_encoder.', 'reward_critic.', 'cost_critic.'))}
        receipt = target.transfer_from(source)
        self.assertEqual(receipt['source_phase'], 'R')
        self.assertTrue(torch.equal(source.support_head.bias, target.support_head.bias))
        self.assertTrue(torch.equal(source.finger_heads['index'][-1].bias, target.finger_heads['index'][-1].bias))
        self.assertTrue(all(torch.equal(value, target.state_dict()[key]) for key, value in critic.items()))
        with self.assertRaises(ValueError): policy('F', 'correlated').transfer_from(source)
        bad_contract = contract('F'); bad_contract['action']['maximum'] = .5
        with self.assertRaises(ValueError):
            FingerSkillPolicy(557, size='small', contract=bad_contract).transfer_from(source)

    def test_legacy_and_malformed_contract_rejected(self):
        with self.assertRaises(ValueError): FingerSkillPolicy(552, size='small', contract=actor_contract())
        for mutate in (lambda value: value['observation']['fields'].__setitem__(-1, 'missing'),
                       lambda value: value['action']['names'].reverse(),
                       lambda value: value['task']['finger_skill'].__setitem__('phase', 'J')):
            value = contract(); mutate(value)
            with self.assertRaises(ValueError): FingerSkillPolicy(557, size='small', contract=value)


if __name__ == '__main__':
    unittest.main()
