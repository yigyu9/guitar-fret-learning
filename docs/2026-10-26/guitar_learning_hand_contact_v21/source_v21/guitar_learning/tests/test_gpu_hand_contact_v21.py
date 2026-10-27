"""Integrated reward/observation accounting, without claiming native contact."""
import copy
import unittest

import torch

from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE


class HandContactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_thumb_observation_and_actual_integrated_reward_share_measurement(self):
        env, row, observation = fixtures.TensorSongTests().environment()
        fields = env.contract['observation']['fields']
        names = ['delta_x','delta_y','delta_z','signed_gap','normal_cos','region_excess','valid']
        values = torch.cat((env.thumb_support['delta'], torch.stack([
            env.thumb_support[k] for k in names[3:]], -1)), -1)
        indices = [fields.index('thumb_support.'+name) for name in names]
        torch.testing.assert_close(observation['state'][:,indices]*env.scales[indices], values)
        self.assertEqual(observation['state'].shape[1],551)
        fixtures.TensorSongTests.advance(env,row)
        expected = .02*env.thumb_support['quality']/60
        torch.testing.assert_close(env.terms['song_thumb_support'],expected)
        summary=env.episode_diagnostics.episode(0)['thumb_support']
        self.assertAlmostEqual(summary['sampled_s'],1/60)

    def test_thumb_ablation_keeps_geometry_and_observation_but_no_payout(self):
        metadata,row=fixture()
        env=TensorSongEnvironment(metadata,bundle=BUNDLE,song=dict(SONG,thumb_support_rate_per_s=0.),
                                 hand='left',device='cpu')
        env.reset([0,1],row)
        fixtures.TensorSongTests.advance(env,row)
        self.assertTrue((env.thumb_support['quality']>0).all())
        self.assertFalse(env.terms['song_thumb_support'].any())
        self.assertFalse(env.episode_reward_terms['song_thumb_support'].any())
        for rate in (True,.01,float('nan'),float('inf')):
            with self.assertRaises(ValueError):
                TensorSongEnvironment(metadata,bundle=BUNDLE,song=dict(SONG,thumb_support_rate_per_s=rate),
                                     hand='left',device='cpu')

    def test_failed_tick_suppresses_all_thumb_credit(self):
        env,row,_=fixtures.TensorSongTests().environment()
        env.begin_control(torch.zeros(2,39))
        for _ in range(4):env.substep(row)
        env.tick_failure[0,0]=True
        env.end_control()
        self.assertEqual(float(env.terms['song_thumb_support'][0]),0.)
        self.assertGreater(float(env.terms['song_thumb_support'][1]),0.)
        self.assertEqual(float(env.episode_reward_terms['song_thumb_support'][0]),0.)

    def test_observation_queries_do_not_accumulate_thumb_time(self):
        env,row,_=fixtures.TensorSongTests().environment()
        before=copy.deepcopy(env.episode_diagnostics.episode(0))
        for _ in range(4):env.observation()
        self.assertEqual(env.episode_diagnostics.episode(0),before)


if __name__=='__main__':unittest.main()
