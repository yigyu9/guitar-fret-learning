"""Recovery integration uses CPU tensors; no native physics efficacy claim."""
import copy
import unittest
from unittest.mock import patch

import torch

from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.gpu.finger_reward import finger_preparation_reward, finger_recovery_config
from guitar_learning.tests import test_gpu_environment as fixtures
from guitar_learning.tests import test_gpu_preparation_B as preparation_fixtures
from guitar_learning.tests.test_gpu_surface_learning import task
from guitar_learning.tool.training.train_legacy import settings_document
from guitar_learning.training.policy import SpecialistPolicy


class RecoveryEnvironmentTests(unittest.TestCase):
    environment = fixtures.TensorSongTests.environment
    advance = staticmethod(fixtures.TensorSongTests.advance)
    idle_environment = preparation_fixtures.PreparationBTests.idle_environment

    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    @staticmethod
    def gate_columns(env):
        fields = env.contract['observation']['fields']
        return [fields.index('finger_posture.'+f+'.standby_gate') for f in ('index','middle','ring','pinky')]

    def test_reset_observation_uses_actual_pure_gate_and_thumb_augmented_dimension(self):
        env, row = self.idle_environment(task(onset=1.5, end=2.5, press=1.5))
        expected = env._finger_preparation(env.clock.double()/240.)['gate']
        observation = env.observation()
        self.assertEqual(observation['state'].shape, (2,552))
        self.assertEqual(env.contract['reward']['schema'], 'guitar_learning.gpu_tensor_song_reward.v22')
        torch.testing.assert_close(observation['state'][:,self.gate_columns(env)], expected.float())
        self.assertFalse(any(f.endswith('.idle_weight') for f in env.contract['observation']['fields']))

    def test_disappearing_previous_contact_does_not_veto_recovery(self):
        env, row = self.idle_environment(task(onset=1.5, end=2.5, press=1.5))
        snapshot = env._snapshot
        samples = [0]
        def synthetic_contact(value):
            snapshot(value)
            samples[0] += 1
            # A residual event at substep3 disappears at endpoint4. Score-idle
            # recovery remains eligible throughout, including the observation.
            env.candidate[0,0] = samples[0] == 3
        with patch.object(env, '_snapshot', side_effect=synthetic_contact):
            observation, *_ = self.advance(env,row)
        self.assertFalse(env.candidate[0,0])
        self.assertFalse(env.previous_candidate[0,0])
        self.assertEqual(float(env.preparation_gate[0,0]), 1.)
        self.assertEqual(float(observation['state'][0,self.gate_columns(env)[0]]),1.)
        self.assertEqual(float(env._finger_preparation(env.clock.double()/240.)['gate'][0,0]),1.)
        self.advance(env,row)
        self.assertEqual(float(env.preparation_gate[0,0]),1.)

    def test_achieved_note_remains_protected_until_score_end(self):
        env, row = self.idle_environment(task(onset=.5, end=2., press=.4))
        env.clock[:] = 240
        env.note['left'][:] = True  # Success latched, sustained score note remains.
        before = env._finger_preparation(env.clock.double()/240.)
        self.assertFalse(before['gate'].any())
        self.assertTrue((before['tracking_weight'] == 1).all())
        self.advance(env, row)
        self.assertFalse(env.preparation_gate.any())
        env.clock[:] = 240*3
        after = env._finger_preparation(env.clock.double()/240.)
        self.assertTrue((after['gate'] == 1).all())
        self.assertTrue((after['tracking_weight'] == 0).all())

    def test_partial_reset_keeps_other_row_gate_and_observation_queries_pure(self):
        env, row = self.idle_environment(task(onset=1.5, end=2.5, press=1.5))
        env.preparation_gate[1,0] = 0.  # Prior endpoint contact evidence.
        saved_note=copy.deepcopy(env.note)
        saved_previous=env.previous_candidate.clone()
        saved_clock=env.clock.clone()
        for _ in range(3):
            env.observation()
        torch.testing.assert_close(env.clock,saved_clock)
        torch.testing.assert_close(env.previous_candidate,saved_previous)
        for key in saved_note:
            torch.testing.assert_close(env.note[key],saved_note[key])
        env.reset([0],row)
        self.assertEqual(float(env.preparation_gate[1,0]),0.)
        self.assertEqual(float(env.preparation_gate[0,0]),1.)
        env.set_curriculum(1.)
        self.assertEqual(float(env.preparation_gate[1,0]),0.)

    def test_each_physics_reward_integrates_new_rate_and_selected_config(self):
        env,row = self.idle_environment()
        with patch('guitar_learning.gpu.environment.finger_preparation_reward', wraps=finger_preparation_reward) as measure:
            self.advance(env,row)
        self.assertEqual(measure.call_count,4)
        self.assertTrue(all(call.kwargs == dict(rate_per_s=.02) for call in measure.call_args_list))
        torch.testing.assert_close(env.terms['song_finger_standby'],torch.full((2,),.02/60),atol=4e-11,rtol=0)
        self.assertFalse(env.terms['song_finger_coordination'].any())
        self.assertFalse(env.contract['reward']['finger_shape']['enabled'])

    def test_shape_requires_explicit_config_and_has_existing_tracking_gate(self):
        metadata,row = fixtures.fixture()
        song=dict(fixtures.SONG,finger_recovery=finger_recovery_config(dict(
            schema='guitar_learning.left_finger_recovery.v1',standby_rate_per_s=.04,shape_rate_per_s=.004)))
        with patch('guitar_learning.gpu.environment.make_task',return_value=task(onset=1.5,end=2.5,press=1.5)):
            env=TensorSongEnvironment(metadata,bundle=fixtures.BUNDLE,song=song,hand='left',device='cpu')
        env.reset([0,1],row)
        env.clock[:] = 360  # Own press window: tracking, not B recovery.
        self.advance(env,row)
        self.assertTrue((env.terms['song_finger_coordination']>0).all())
        self.assertTrue((env.terms['song_finger_coordination']<=.004/60+1e-10).all())
        self.assertTrue(env.contract['reward']['finger_shape']['enabled'])
        self.assertEqual(env.contract['reward']['finger_posture']['rate_bounds_per_s'],[0.,.04])
        env.clock[:]=240*3
        self.advance(env,row)
        self.assertFalse(env.terms['song_finger_coordination'].any())

    def test_current552_actor_keeps20_local_fields_and_explicit544_v19_legacy(self):
        env,_,_=self.environment()
        new=SpecialistPolicy(552,size='small',role='left',contract=env.contract)
        self.assertEqual(new.architecture['finger_actor']['local_width'],20)
        for names in new.architecture['finger_actor']['local_fields'].values():
            self.assertTrue(names[-1].endswith('.standby_gate'))
        old=copy.deepcopy(env.contract)
        old['reward']['schema']='guitar_learning.gpu_tensor_song_reward.v19'
        old['observation']['dimension']=544
        old['observation']['fields']=old['observation']['fields'][:544]
        old['observation']['scales']=old['observation']['scales'][:544]
        old['observation'].pop('thumb_support')
        old['observation']['fields']=[f.replace('.standby_gate','.idle_weight') for f in old['observation']['fields']]
        legacy=SpecialistPolicy(544,size='small',role='left',contract=old)
        for names in legacy.architecture['finger_actor']['local_fields'].values():
            self.assertTrue(names[-1].endswith('.idle_weight'))
        self.assertEqual(tuple(new.state_dict()),tuple(legacy.state_dict()))

    def test_explicit_settings_are_gpu_left_only_and_preserve_legacy_documents(self):
        default=settings_document('left',device='cuda:0')
        self.assertEqual(default['song']['finger_recovery'],finger_recovery_config())
        optional=settings_document('left',device='cuda:0',finger_standby_rate=.04,finger_shape=True)
        self.assertEqual(optional['song']['finger_recovery']['standby_rate_per_s'],.04)
        self.assertEqual(optional['song']['finger_recovery']['shape_rate_per_s'],.004)
        for hand,device,physics in (('left','cpu','cpu'),('right','cpu','cpu'),('right','cuda:0','gpu')):
            legacy=settings_document(hand,device=device,physics=physics)
            self.assertNotIn('finger_recovery',legacy['song'])
            for flags in (dict(finger_standby_rate=.02),dict(finger_shape=True)):
                with self.assertRaisesRegex(ValueError,'GPU left'):
                    settings_document(hand,device=device,physics=physics,**flags)
        for value in (.01,.03,float('nan'),True):
            with self.assertRaises(ValueError):
                settings_document('left',device='cuda:0',finger_standby_rate=value)


if __name__=='__main__':
    unittest.main()
