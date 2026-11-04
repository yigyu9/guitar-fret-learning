"""S3 계수·성분 합계·실패 대체와 60Hz potential을 검사한다."""
import unittest

import torch

from guitar_learning.gpu.strike_reward import compute_s3_reward, S3_WEIGHTS


class StrikeRewardTests(unittest.TestCase):
    def inputs(self, count=2):
        ones = torch.ones(count)
        zeros = torch.zeros(count)
        return dict(terms={name: zeros.clone() for name in S3_WEIGHTS},
            grip_quality=ones.clone(), ready_quality=ones.clone(),
            pending_ready=torch.zeros(count, dtype=torch.bool),
            phi_before=zeros.clone(), phi_after=zeros.clone(),
            same_target=torch.ones(count, dtype=torch.bool), wait_quality=zeros.clone(),
            joint_limit_usage=torch.zeros(count, 27), failed=torch.zeros(count, dtype=torch.bool))

    def test_ready_crossing_recovery_are_distinct_pulses(self):
        args = self.inputs()
        for name in ('ready', 'crossing', 'recovery_progress', 'recovery_complete'):
            args['terms'][name][:] = 1
        reward, components = compute_s3_reward(**args)
        torch.testing.assert_close(reward, torch.full((2,), 1.85))
        torch.testing.assert_close(sum(components.values()), reward)

    def test_failure_replaces_reward_and_components_still_sum(self):
        args = self.inputs()
        args['terms']['crossing'][:] = 1
        args['failed'][0] = True
        reward, components = compute_s3_reward(**args)
        torch.testing.assert_close(reward, torch.tensor([-10., 1.]))
        torch.testing.assert_close(sum(components.values()), reward)

    def test_same_event_potential_and_idle_ready_penalties(self):
        args = self.inputs()
        args['phi_before'][:] = .5
        args['phi_after'][:] = .8
        args['same_target'][1] = False
        args['pending_ready'][:] = True
        args['ready_quality'][:] = .25
        args['grip_quality'][:] = .5
        reward, _ = compute_s3_reward(**args)
        torch.testing.assert_close(reward, torch.tensor([.104-.025, -.025]))

    def test_joint_limit_and_wrong_cost_use_s3_coefficients(self):
        args = self.inputs()
        args['terms']['wrong'][:] = 2
        args['joint_limit_usage'][:] = 1.
        reward, _ = compute_s3_reward(**args)
        torch.testing.assert_close(reward, torch.full((2,), -.71))

    def test_shape_nonfinite_and_term_schema_rejected(self):
        for change in ('missing', 'nan', 'shape', 'mask'):
            args = self.inputs()
            if change == 'missing':
                args['terms'].pop('ready')
            elif change == 'nan':
                args['terms']['crossing'][0] = float('nan')
            elif change == 'shape':
                args['joint_limit_usage'] = torch.zeros(1, 27)
            else:
                args['failed'] = torch.zeros(2)
            with self.subTest(change=change), self.assertRaises(ValueError):
                compute_s3_reward(**args)


if __name__ == '__main__':
    unittest.main()
