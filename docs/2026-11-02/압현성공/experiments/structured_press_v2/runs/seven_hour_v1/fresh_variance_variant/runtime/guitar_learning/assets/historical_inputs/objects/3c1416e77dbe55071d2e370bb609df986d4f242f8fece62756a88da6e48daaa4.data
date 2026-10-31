import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from guitar_learning.core.task_sampling import BalancedTaskSampler, build_environment, SampledTaskEnvironment
from guitar_learning.core.training_environment import TrainingEnvironment
from guitar_learning.tests.test_training_environment import RecordedSession

BUNDLE='data/song_bundles/05_BN2-131-B_solo'


class ExtendedRecordedSession(RecordedSession):
    """Repeat the last recorded body state for CPU timeline checks, no dynamics."""
    def row(self):
        return self.rows[min(max(0,self.scene.steps-480),len(self.rows)-1)]


class SamplingTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.environments=[]

    def tearDown(self):
        for env in self.environments: env.close()
        self.folder.cleanup()

    def build(self,*,worker_id=0,time_limit_s=2/60,**music):
        sessions=[]
        def factory(config,out):
            session=ExtendedRecordedSession(config,out)
            sessions.append(session)
            return session
        def contacts(scene):
            return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        env=build_environment({},Path(self.folder.name)/str(len(self.environments)),
            bundle=BUNDLE,stage='B',start_event_index=0,phrase_events=8,tempo_scale=1.,
            seed=7,worker_id=worker_id,music=music,session_factory=factory,
            contact_reader=contacts,time_limit_s=time_limit_s)
        self.environments.append(env)
        return env

    def test_balanced_reproducible_worker_local_cycles(self):
        def sequence(worker):
            sampler=BalancedTaskSampler([0,1,2,3],7,worker)
            return [sampler.next_index() for _ in range(20)]
        first=sequence(0)
        self.assertEqual(first,sequence(0)); self.assertNotEqual(first,sequence(1))
        for start in range(0,20,4): self.assertEqual(sorted(first[start:start+4]),[0,1,2,3])
        for invalid in ([],[0,0],[-1],[True],(0,1)):
            with self.assertRaises(ValueError): BalancedTaskSampler(invalid,7,0)

    def test_legacy_fixed_path_original_class_and_contract(self):
        env=self.build()
        self.assertIs(type(env),TrainingEnvironment)
        self.assertEqual(env.task.targets[0].fret,7)
        obs,info=env.reset()
        self.assertEqual(info['training_contract']['task']['duration_s'],env.task.duration_s)
        for field in ('music.remaining_s','music.held_total_s','music.elapsed_s'):
            i=env.builder.fields.index(field)
            self.assertEqual(env.builder.scales[i],max(env.task.duration_s,1.))
        self.assertEqual(obs['state'][env.builder.fields.index('music.remaining_s')],1.)
        self.assertNotIn('episode_task',info)
        self.assertNotIn('state_scale_overrides',env.contract['task'])

    def test_pool_contract_constant_episode_metadata_and_delegation(self):
        for mode in ('legacy','dense_v2'):
            env=self.build(goal_event_indices=[0,1,2],reward_mode=mode)
            self.assertIsInstance(env,SampledTaskEnvironment)
            contracts=[]; selected=[]
            common=max(task.duration_s for task in env.tasks.values())
            self.assertGreater(len({task.duration_s for task in env.tasks.values()}),1)
            for _ in range(6):
                obs,info=env.reset()
                contracts.append(copy.deepcopy(info['training_contract']))
                selected.append(info['episode_task']['event_index'])
                self.assertIs(env.control,env.environment.control)
                self.assertIs(env.last_measured,env.environment.last_measured)
                actual=env.tasks[info['episode_task']['event_index']]
                self.assertIs(env.task,actual)
                self.assertEqual(info['episode_task']['task']['duration_s'],actual.duration_s)
                for name in ('music.remaining_s','music.held_total_s','music.elapsed_s'):
                    index=env.builder.fields.index(name)
                    self.assertEqual(env.builder.scales[index],common)
                    self.assertEqual(env.builder.spec['scales'][index],common)
                    self.assertEqual(info['training_contract']['observation']['scales'][index],common)
                self.assertAlmostEqual(obs['state'][env.builder.fields.index('music.remaining_s')],actual.duration_s/common,places=6)
                for tick in (1,2):
                    obs,reward,terminated,truncated,step=env.step(np.zeros(39))
                    now=tick/60
                    self.assertAlmostEqual(obs['state'][env.builder.fields.index('music.remaining_s')],(actual.duration_s-now)/common,places=6)
                    self.assertAlmostEqual(obs['state'][env.builder.fields.index('music.elapsed_s')],now/common,places=6)
                    self.assertAlmostEqual(obs['state'][env.builder.fields.index('music.held_total_s')],step['music']['held_total_s']/common,places=6)
                self.assertFalse(terminated); self.assertTrue(truncated)
                self.assertEqual(step['episode']['episode_task'],info['episode_task'])
            self.assertTrue(all(c==contracts[0] for c in contracts))
            self.assertEqual(sorted(selected[:3]),[0,1,2])
            self.assertEqual(sorted(selected[3:]),[0,1,2])
            other=self.build(goal_event_indices=[0,1,2],reward_mode=mode,worker_id=1)
            _,other_info=other.reset()
            self.assertEqual(other_info['training_contract'],contracts[0])
            self.assertNotEqual(other_info['episode_task']['event_index'],selected[0])

    def test_individual_timeline_duration_survives_pool_normalization(self):
        env=self.build(goal_event_indices=[0,1],reward_mode='dense_v2',time_limit_s=None)
        contracts=[]; durations=[]
        for _ in range(2):
            _,info=env.reset()
            contracts.append(copy.deepcopy(info['training_contract']))
            duration=info['episode_task']['task']['duration_s']
            durations.append(duration)
            for tick in range(1,100):
                obs,reward,terminated,truncated,step=env.step(np.zeros(39))
                if terminated or truncated: break
            self.assertTrue(terminated); self.assertFalse(truncated)
            self.assertEqual(step['termination_reason'],'timeline_complete')
            self.assertGreaterEqual(step['task_time_s'],duration)
            self.assertLess(step['task_time_s']-duration,1/60)
            self.assertEqual(step['episode']['episode_task'],info['episode_task'])
        self.assertNotEqual(durations[0],durations[1])
        self.assertEqual(contracts[0],contracts[1])

    def test_reject_every_unsupported_candidate_before_simulator_creation(self):
        with patch('guitar_learning.core.task_sampling.TrainingEnvironment') as constructor:
            with self.assertRaisesRegex(ValueError,'unsupported'):
                self.build(goal_event_indices=[0,42])
            constructor.assert_not_called()
        with self.assertRaises(ValueError): self.build(reward_mode='unknown')
        with self.assertRaises(ValueError): self.build(typo=True)


if __name__=='__main__': unittest.main()
