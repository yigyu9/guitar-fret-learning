"""J33 정책의 입력 계약·독립 확률·학습 대상과 정보 분리를 검증한다."""
import copy
import math
import unittest

import torch
from torch.distributions import Normal, kl_divergence

from guitar_learning.training.policy import FingerSkillPolicy, SKILL_FIELDS, WRIST_TERMINATION_FIELDS
from guitar_learning.tests.test_gpu_finger_actor import actor_contract


def contract(phase='J', exploration='independent'):
    value = actor_contract()
    value['observation']['fields'] += list(SKILL_FIELDS+WRIST_TERMINATION_FIELDS)
    value['observation']['scales'] += [value['task']['duration_s'], 1., 1.5, 3., .1]
    value['observation']['dimension'] += 5
    value['task']['finger_skill'] = dict(schema='guitar_learning.finger_skill.v3',
                                       phase=phase, exploration=exploration, hold_ticks=1)
    return value


def policy():
    return FingerSkillPolicy(557, size='small', contract=contract())


def inputs(count=4):
    return (torch.randn(count, 557), torch.randn(count, 7, 24), torch.ones(count, 7, dtype=torch.bool),
            torch.randn(count, 8, 24), torch.ones(count, 8, dtype=torch.bool))


class FingerSkillPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_joint_active_axes_inactive_right_hand_and_fresh_zero_means(self):
        model = policy(); data = inputs(); result = model.act(*data)
        self.assertEqual(model.schema, 'guitar_learning.finger_skill_policy.v2')
        self.assertEqual((model.phase, model.exploration), ('J', 'independent'))
        self.assertEqual(int(model._active_mask().sum()), 33)
        self.assertTrue(torch.equal(result['action'][:, 33:], torch.zeros(4, 6)))
        self.assertTrue(torch.equal(model.act(*data, deterministic=True)['action'], torch.zeros(4, 39)))
        changed = result['latent'].clone(); changed[:, 33:] += 10
        self.assertTrue(torch.equal(result['logp'], model.evaluate(*data, changed)['logp']))
        means = result['mean'].clone(); means[:, 33:] += 10
        self.assertTrue(torch.equal(model.analytic_kl(result['mean'], result['log_std'], means,
                                                     result['log_std']), torch.zeros(4)))
        for old_api in ('transfer_from', '_to_basis', '_from_basis', 'bend_basis', 'bend_indices'):
            self.assertFalse(hasattr(model, old_api))

    def test_independent_density_kl_and_entropy_match_distribution(self):
        model = policy().double()
        mean = torch.randn(2, 39, dtype=torch.float64)*.2
        log_std = torch.randn(2, 39, dtype=torch.float64)*.1-2
        latent = torch.randn(2, 39, dtype=torch.float64)*.3
        new_mean, new_std = mean+.03, log_std+.08
        original = Normal(mean[:, :33], log_std[:, :33].exp())
        updated = Normal(new_mean[:, :33], new_std[:, :33].exp())
        correction = 2*(math.log(2)-latent[:, :33]-torch.nn.functional.softplus(-2*latent[:, :33]))
        torch.testing.assert_close(model.log_probability(mean, log_std, latent),
                                   (original.log_prob(latent[:, :33])-correction).sum(-1))
        torch.testing.assert_close(model.analytic_kl(mean, log_std, new_mean, new_std),
                                   kl_divergence(original, updated).sum(-1))
        data = tuple(value.double() if value.dtype == torch.float32 else value for value in inputs())
        action = model.act(*data)
        evaluated = model.evaluate(*data, action['latent'])
        torch.testing.assert_close(evaluated['entropy'],
            Normal(action['mean'][:, :33], action['log_std'][:, :33].exp()).entropy().sum(-1))

    def test_support_invariant_to_finger_only_inputs(self):
        model = policy()
        with torch.no_grad(): model.support_head.weight.normal_(0, .01)
        data = list(inputs()); before = model(*data)['mean'][:, :17]
        fine = torch.ones(557, dtype=torch.bool); fine[model.support_indices] = False
        data[0][:, fine] = torch.randn(4, int(fine.sum()))*10
        data[1][..., 9:] = torch.randn(4, 7, 15)*10
        data[3][..., 9:] = torch.randn(4, 8, 15)*10
        self.assertTrue(torch.equal(before, model(*data)['mean'][:, :17]))
        self.assertTrue(all(not field.startswith(('finger_posture.', 'song.', 'finger_skill.'))
                            for field in model.architecture['support_fields']))

    def test_all_33_actor_axes_train_and_critics_are_separate(self):
        model = policy()
        with torch.no_grad():
            model.support_head.weight.fill_(.01)
            for head in model.finger_heads.values(): head[-1].weight.fill_(.01)
        ids = {id(p) for p in model.actor_parameters()}
        groups = (model.support_encoder, model.support_head, model.finger_encoder, model.finger_heads)
        self.assertTrue(all(p.requires_grad and id(p) in ids for group in groups for p in group.parameters()))
        self.assertTrue(model.support_log_std.requires_grad and model.finger_log_std.requires_grad)
        self.assertFalse(ids & {id(p) for p in model.value_parameters()})
        data = list(inputs()); data[2][:, 3:] = False; data[4][:, 1::2] = False
        expected = model(*data)
        data[1][~data[2]] = float('nan'); data[3][~data[4]] = float('nan')
        actual = model(*data)
        self.assertTrue(all(torch.equal(expected[key], actual[key]) for key in expected))
        loss = actual['mean'][:, :33].sum()+model.evaluate(*data, actual['mean'].detach())['logp'].sum()
        loss.backward()
        for head in (model.support_head, *model.finger_heads.values()):
            self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in head.parameters()))
            self.assertGreater(float(next(head.parameters()).grad.abs().sum()), 0)
        self.assertTrue((model.support_head.bias.grad != 0).all())
        for head in model.finger_heads.values(): self.assertTrue((head[-1].bias.grad != 0).all())
        self.assertTrue((model.support_log_std.grad != 0).all())
        self.assertTrue((model.finger_log_std.grad != 0).all())

    def test_old_contracts_phase_options_and_bad_tail_rejected(self):
        for mutate in (
                lambda v: v['task']['finger_skill'].__setitem__('schema', 'guitar_learning.finger_skill.v2'),
                lambda v: v['task']['finger_skill'].__setitem__('phase', 'R'),
                lambda v: v['task']['finger_skill'].__setitem__('phase', 'F'),
                lambda v: v['task']['finger_skill'].__setitem__('exploration', 'correlated'),
                lambda v: v['task']['finger_skill'].__setitem__('hold_ticks', 3),
                lambda v: v['observation']['fields'].__setitem__(-5, 'finger_skill.phase_J'),
                lambda v: v['action']['names'].reverse()):
            value = contract(); mutate(value)
            with self.assertRaises(ValueError): FingerSkillPolicy(557, size='small', contract=value)
        with self.assertRaises(ValueError): FingerSkillPolicy(561, size='small', contract=contract())
        for kwargs in (dict(phase='J'), dict(exploration='independent')):
            with self.assertRaises(TypeError): FingerSkillPolicy(557, size='small', contract=contract(), **kwargs)
        old = copy.deepcopy(policy().state_dict()); old['bend_basis'] = torch.eye(3)
        with self.assertRaises(RuntimeError): policy().load_state_dict(old)


if __name__ == '__main__':
    unittest.main()
