"""Recorded-body CPU integration; one physical session, no native simulation."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from guitar_learning.core import training_environment
from guitar_learning.tool.experiments.joint.environment import build_environment
from guitar_learning.tool.experiments.joint.spec import STATE_DIM
from guitar_learning.quality.musical_quality_environment import build_environment as hand_environment
from guitar_learning.timing.timing_curriculum import TimingConfig
from guitar_learning.core.task_measurement_v2 import TaskMeasurementV2
from guitar_learning.tests.test_skill_environment import LongRecordedSession


class JointEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.environments=[]
    def tearDown(self):
        for env in self.environments:env.close()
        self.folder.cleanup()
    def environment(self,role=None,**kwargs):
        sessions=[]
        def factory(config,out):
            session=LongRecordedSession(config,out);sessions.append(session);return session
        def contacts(scene):return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        build=build_environment if role is None else hand_environment
        args={} if role is None else dict(role=role)
        env=build({},Path(self.folder.name)/str(len(self.environments)),
            bundle='data/song_bundles/05_BN2-131-B_solo',session_factory=factory,contact_reader=contacts,
            timing=TimingConfig(pre_roll_s=3.,stage_index=1),**args,**kwargs)
        self.environments.append(env);return env

    def test_exact_original_hand_contracts_and_observations_without_second_native_reset(self):
        env=self.environment();observation,reset=env.reset()
        self.assertEqual(observation['state'].shape,(STATE_DIM,))
        self.assertIsInstance(env.measurement,TaskMeasurementV2)
        self.assertEqual(env.control.session.scene.steps,0)
        self.assertEqual(env.control.session.preparation_calls,0)
        self.assertEqual(reset['training_contract']['action']['dimension'],39)
        self.assertEqual(env.task.duration_s,7.)
        self.assertEqual(len(env.contract['observation']['fields']),STATE_DIM)
        self.assertEqual(len(env.contract['observation']['scales']),STATE_DIM)
        for index,role in enumerate(('left','right')):
            hand=self.environment(role);single,info=hand.reset()
            self.assertEqual(env.contract['task']['joint']['hand_contracts'][role],info['training_contract'])
            np.testing.assert_array_equal(observation['state'][index*563:(index+1)*563],single['state'])
            self.assertIsNot(env.hand_views[role].builder,env.builder)
            for key in ('events','mask','priority_events','priority_mask'):
                np.testing.assert_array_equal(observation[key],single[key])
        self.assertIsNot(env.hand_views['left'].contract,env.hand_views['right'].contract)

    def test_both_hand_action_applied_once_four_samples_and_same_tick_histories(self):
        env=self.environment(time_limit_s=1/60.);first,_=env.reset()
        observation,reward,terminated,truncated,info=env.step(np.full(39,.1))
        self.assertFalse(terminated);self.assertTrue(truncated)
        self.assertEqual(env.control.session.policy_calls,1)
        self.assertEqual(env.control.session.scene.steps,4)
        self.assertEqual([row['physics_step'] for row in info['physics_measurements']],[1,2,3,4])
        for role in ('left','right'):
            view=env.hand_views[role]
            self.assertEqual(view.skill_ledger.timed.previous_step,4)
            self.assertEqual(view.timing_ledger.previous_step,4)
            self.assertEqual(view.quality_ledger.previous['physics_step'],4)
            fields=env.contract['observation']['fields']
            value=observation['state'][fields.index(role+'.timing_history.policy_time_s')]
            self.assertAlmostEqual(value,1/60./7.,places=8)
        self.assertEqual(env.coordination_ledger.previous['physics_step'],4)
        self.assertAlmostEqual(reward,sum(info['reward_terms'].values()))
        self.assertEqual(info['episode']['reward'],reward)
        self.assertEqual(info['episode']['musical_quality'],info['musical_quality'])
        self.assertFalse(info['musical_quality']['stage_success'])
        self.assertEqual(info['musical_quality']['role'],'joint')
        self.assertEqual(info['specialist']['role'],'joint')
        # Session reuse clears all two-hand histories and coordination state.
        session=env.control.session
        again,_=env.reset()
        self.assertIs(env.control.session,session)
        self.assertEqual(session.reset_calls,1)
        for key in first:np.testing.assert_array_equal(first[key],again[key])

    def test_failed_control_tick_suppresses_all_positive_terms_and_retains_single_cost(self):
        env=self.environment();env.reset();env.control.session.unsafe_at=1
        _,reward,terminated,_,info=env.step(np.zeros(39))
        self.assertTrue(terminated)
        self.assertTrue(info['failure_reasons'])
        self.assertTrue(all(v<=0 for v in info['reward_terms'].values()))
        self.assertTrue(all(v<=0 for row in info['physics_measurements'] for v in row['joint_reward_terms'].values()))
        expected=sum(row['stability']['cost'] for row in info['physics_measurements'])+env.safety_config.failure_cost
        self.assertAlmostEqual(info['cost'],expected)
        self.assertAlmostEqual(info['episode']['cost'],expected)
        self.assertAlmostEqual(info['episode']['reward'],reward)
        self.assertTrue(info['coordination']['safety_invalidated'])
        self.assertFalse(info['musical_quality']['stage_success'])
        for view in env.hand_views.values():
            self.assertTrue(view.timing_ledger.safety_reasons)
            self.assertTrue(view.skill_ledger.reasons)
        step=env.control.session.scene.steps
        with self.assertRaisesRegex(RuntimeError,'reset required'):env.step(np.zeros(39))
        self.assertEqual(env.control.session.scene.steps,step)

    def test_single_hand_reward_components_preserved_and_shared_cost_paid_once(self):
        env=self.environment();env.reset()
        hands={role:self.environment(role) for role in ('left','right')}
        for hand in hands.values():hand.reset()
        for _ in range(4):
            _,reward,_,_,joint=env.step(np.zeros(39))
            for role,hand in hands.items():
                _,_,_,_,original=hand.step(np.zeros(39))
                for name,value in original['reward_terms'].items():
                    if name not in ('action_change','terminal_failure'):
                        self.assertAlmostEqual(joint['reward_terms'][role+'_'+name],value,places=12)
                self.assertEqual(joint['reward_terms']['action_change'],original['reward_terms']['action_change'])
                self.assertEqual(joint['cost'],original['cost'])
            self.assertAlmostEqual(reward,sum(joint['reward_terms'].values()))

    def test_complete_timeline_retains_music_and_cannot_inherit_hand_only_success(self):
        env=self.environment();env.reset()
        for view in env.hand_views.values():view.timing_ledger.achieved=True
        for _ in range(420):_,_,terminated,truncated,info=env.step(np.zeros(39))
        self.assertTrue(terminated);self.assertFalse(truncated)
        self.assertEqual(info['episode']['steps'],420)
        self.assertEqual(info['episode']['task_time_s'],7.)
        self.assertEqual(info['episode']['reason'],'timeline_complete')
        self.assertFalse(info['episode']['joint']['safety_invalidated'])
        self.assertTrue(info['timing']['timing_only_stage_success'])
        self.assertFalse(info['joint']['stage_success'])
        self.assertFalse(info['musical_quality']['stage_success'])
        self.assertEqual(info['music'],info['episode']['music'])
        self.assertIn('matched50',info['music']);self.assertIn('matched100',info['music'])
        self.assertEqual(info['episode']['joint'],info['joint'])

    def test_ledger_exception_requires_reset_and_prevents_second_physics_step(self):
        env=self.environment();env.reset()
        with patch.object(env.coordination_ledger,'update',side_effect=ValueError('injected coordination failure')):
            with self.assertRaisesRegex(ValueError,'injected coordination'):env.step(np.zeros(39))
        self.assertTrue(env.finished);step=env.control.session.scene.steps
        with self.assertRaisesRegex(RuntimeError,'reset required'):env.step(np.zeros(39))
        self.assertEqual(env.control.session.scene.steps,step)


if __name__=='__main__':unittest.main()
