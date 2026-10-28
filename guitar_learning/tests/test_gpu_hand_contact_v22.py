"""CPU reward/observation accounting; candidate net force is not pair contact."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.gpu.control import apply, multiply
from guitar_learning.training.policy import SpecialistPolicy
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests.test_gpu_continuous_clean import ContinuousCleanTests
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE
from guitar_learning.training.ppo import PPOTrainer


class HandContactTests(unittest.TestCase):
    tree_equal = ContinuousCleanTests.tree_equal

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_thumb_observation_and_actual_integrated_reward_share_measurement(self):
        env, row, observation = fixtures.TensorSongTests().environment()
        fields = env.contract['observation']['fields']
        names = ['delta_x','delta_y','delta_z','signed_gap','normal_cos','region_excess','valid',
                 'contact_candidate']
        values = torch.cat((env.thumb_support['delta'], torch.stack([
            env.thumb_support[k] for k in names[3:]], -1)), -1)
        indices = [fields.index('thumb_support.'+name) for name in names]
        torch.testing.assert_close(observation['state'][:,indices]*env.scales[indices], values)
        self.assertEqual(observation['state'].shape[1],552)
        self.assertFalse(env.thumb_support['contact_candidate'].any())
        fixtures.TensorSongTests.advance(env,row)
        expected = .01*env.thumb_support['quality']/60
        torch.testing.assert_close(env.terms['song_thumb_support'],expected)
        summary=env.episode_diagnostics.episode(0)['thumb_support']
        self.assertAlmostEqual(summary['sampled_s'],1/60)

    @staticmethod
    def place_one_thumb_sample(env, snapshot, load):
        """A synthetic source point at the rear; no reachability claim."""
        row = {key: value.clone() for key,value in snapshot.items()}
        env.thumb_support_valid[:] = False
        env.thumb_support_valid[0] = True
        plane = env.thumb_support_plane
        unit = plane[:3]/torch.linalg.vector_norm(plane[:3])
        normal = env.thumb_support_normals[0].cpu().numpy()
        local = Rotation.align_vectors((-unit.cpu().numpy())[None],normal[None])[0].as_quat()
        guitar = row['body_state'][:,env.guitar_index]
        orientation = multiply(guitar[:,3:7],torch.tensor(local,dtype=guitar.dtype).expand(len(guitar),-1))
        center = .5*(env.guide['lower_G_m'][:,1]+env.guide['upper_G_m'][:,1])
        rear = env.thumb_support_rear
        fraction = (center-rear[0,1])/(rear[2,1]-rear[0,1])
        left=rear[0,0]+fraction*(rear[3,0]-rear[0,0])
        right=rear[1,0]+fraction*(rear[2,0]-rear[1,0])
        point = torch.stack(((left+right)/2,center,torch.zeros_like(center)),-1)
        point[:,2]=-(point[:,:2]*plane[:2]).sum(-1)/plane[2]-plane[3]/plane[2]
        point += .0002*unit
        world = guitar[:,:3]+apply(guitar[:,3:7],point)
        thumb = env.thumb_support_index
        row['body_state'][:,thumb,3:7]=orientation
        row['body_state'][:,thumb,:3]=world-apply(orientation,env.thumb_support_local[0].expand(len(guitar),-1))
        row['contact_force'][:,thumb]=apply(guitar[:,3:7],unit.expand(len(guitar),-1)*load)
        return row

    def test_loaded_same_point_candidate_adds_only_capped_half_of_reward(self):
        env,row,_=fixtures.TensorSongTests().environment()
        for load,candidate in ((0.,False),(.02,True),(100.,True),(-.02,False)):
            row=self.place_one_thumb_sample(env,row,load)
            fixtures.TensorSongTests.advance(env,row)
            self.assertEqual(env.thumb_support['contact_candidate'].tolist(),[candidate]*2)
            expected=(.02 if candidate else .01)*env.thumb_support['quality']/60
            torch.testing.assert_close(env.terms['song_thumb_support'],expected)
            self.assertTrue((env.terms['song_thumb_support']<=.02/60+1e-10).all())
            index=env.contract['observation']['fields'].index('thumb_support.contact_candidate')
            self.assertEqual(env.observation()['state'][:,index].tolist(),[float(candidate)]*2)

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

    def test_v21_checkpoint_rejection_preserves_policy_optimizers_and_rng(self):
        env,_,_=fixtures.TensorSongTests().environment()
        def make(contract):
            return PPOTrainer(SpecialistPolicy(contract['observation']['dimension'],size='small',
                                                role='left',contract=contract))
        current=make(env.contract)
        old=copy.deepcopy(env.contract)
        old['reward']['schema']='guitar_learning.gpu_tensor_song_reward.v21'
        old['observation']['dimension']=551
        self.assertEqual(old['observation']['fields'].pop(),'thumb_support.contact_candidate')
        old['observation']['scales'].pop()
        old['observation']['thumb_support']['schema']='guitar_learning.gpu_thumb_rear_support.v1'
        old['reward']['thumb_support']['schema']='guitar_learning.gpu_thumb_rear_support.v1'
        previous=make(old)
        for optimizer in (current.actor_optimizer,current.value_optimizer):
            for group in optimizer.param_groups:
                for parameter in group['params']:parameter.grad=torch.ones_like(parameter)
            optimizer.step();optimizer.zero_grad()
        current.updates,current.cost_weight=7,1.25
        def state():
            return (current.policy.state_dict(),current.actor_optimizer.state_dict(),
                    current.value_optimizer.state_dict(),current.updates,current.cost_weight,
                    torch.get_rng_state(),np.random.get_state())
        with tempfile.TemporaryDirectory() as directory, patch('torch.cuda.is_available',return_value=False):
            path=Path(directory)/'v21.pt';previous.save(path)
            before=copy.deepcopy(state())
            with self.assertRaisesRegex(ValueError,'mismatch'):current.load(path)
            self.tree_equal(before,state())


if __name__=='__main__':unittest.main()
