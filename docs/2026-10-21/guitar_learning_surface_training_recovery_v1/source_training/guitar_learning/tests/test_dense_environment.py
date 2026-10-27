import copy
import pickle
from pathlib import Path
import tempfile
import unittest
import numpy as np
import torch
from guitar_learning.core.dense_environment import DenseTrainingEnvironment, pick_guide, pick_guide_evidence, shaping_sample
from guitar_learning.core.training_environment import TrainingEnvironment
from guitar_learning.music_task import ScoreTask, ScoreTarget
from guitar_learning.core.strike import StrikeDetector
from guitar_learning.training.policy import Policy
from guitar_learning.training.ppo import PPOTrainer
from guitar_learning.tests.test_training_environment import RecordedSession


def target():
    return ScoreTarget('t','e',1,7,3,1,1.12,1.35,1.,1.12,1.35)


def geometry(step=1):
    return dict(physics_step=step,starts_G_m=np.array([[i*.01,-.5,0.] for i in range(6)]),
                ends_G_m=np.array([[i*.01,.1,0.] for i in range(6)]),pick_G_m=np.zeros(3))


class DenseTests(unittest.TestCase):
    def test_signed_depth_zone_guide_and_wrong_direction_or_timing(self):
        t=target(); task=ScoreTask((t,))
        before,_=pick_guide(geometry(),t,t.onset_s-.08)
        center,_=pick_guide(geometry(),t,t.onset_s)
        after,_=pick_guide(geometry(),t,t.onset_s+.08)
        np.testing.assert_allclose(center,[.01,-.32,-.008])
        self.assertLess(before[0],center[0]); self.assertGreater(after[0],center[0])
        totals={}
        for mode in ('correct','wrong_direction','late'):
            total=0.; previous=None; detector=StrikeDetector(); events=[]
            for step in range(1,42):
                now=1.035+step/240.
                g=geometry(step)
                phase=2*t.onset_s-now if mode=='wrong_direction' else now-.09 if mode=='late' else now
                g['pick_G_m']=pick_guide(g,t,phase)[0]
                measured=dict(task_time_s=now,geometry={'t':dict(delta=[.02,0,0])})
                if previous is not None:
                    raw=pickle.dumps((g,measured,previous))
                    terms=shaping_sample(task,{'geometry':g},measured,previous)
                    self.assertEqual(pickle.dumps((g,measured,previous)),raw)
                    total+=sum(terms.values())/240.
                    events.extend(detector.update(previous,g)['events'])
                previous=g
            totals[mode]=total
            selected=[e for e in events if e['string_number']==2]
            if mode=='correct':
                self.assertEqual(len(selected),1)
                self.assertEqual(selected[0]['direction'],1)
                self.assertAlmostEqual(selected[0]['depth_m'],.008)
            if mode=='wrong_direction':
                self.assertEqual(selected[0]['direction'],-1)
        self.assertGreater(totals['correct'],totals['wrong_direction'])
        self.assertGreater(totals['correct'],totals['late'])
        g=geometry()
        self.assertIsNone(pick_guide_evidence(task,{'geometry':g},1.3))

    def test_early_left_active_before_press_and_off_after(self):
        task=ScoreTask((target(),)); g=geometry()
        measured=dict(task_time_s=.2,geometry={'t':dict(delta=[0.,0.,0.])})
        early=shaping_sample(task,{'geometry':g},measured,g)
        self.assertAlmostEqual(early['dense_left_early'],.2)
        measured['task_time_s']=1.01
        self.assertEqual(shaping_sample(task,{'geometry':g},measured,g)['dense_left_early'],0.)

    def test_actual_four_sample_integration_contract_and_terminal_total(self):
        with tempfile.TemporaryDirectory() as folder:
            sessions=[]
            def factory(config,out):
                session=RecordedSession(config,out); sessions.append(session); return session
            def contacts(scene): return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
            legacy=TrainingEnvironment({},Path(folder)/'legacy',task=ScoreTask((target(),)),
                session_factory=factory,contact_reader=contacts,time_limit_s=2/60)
            try:
                _,legacy_reset=legacy.reset()
                legacy_contract=copy.deepcopy(legacy_reset['training_contract'])
                legacy_steps=[legacy.step(np.zeros(39)) for _ in range(2)]
            finally: legacy.close()
            env=DenseTrainingEnvironment({},Path(folder),task=ScoreTask((target(),)),
                session_factory=factory,contact_reader=contacts,time_limit_s=2/60)
            try:
                obs,reset=env.reset()
                self.assertIn('dense_v2',reset['training_contract']['reward'])
                old_compatible=copy.deepcopy(reset['training_contract'])
                del old_compatible['reward']['dense_v2']
                self.assertEqual(old_compatible,legacy_contract)
                self.assertEqual(obs['state'].shape,(468,))
                torch.set_num_threads(1)
                legacy_trainer=PPOTrainer(Policy(468,size='small',contract=legacy_contract))
                checkpoint=Path(folder)/'legacy.pt'
                legacy_trainer.save(checkpoint)
                compatible=PPOTrainer(Policy(468,size='small',contract=legacy_contract))
                compatible.load(checkpoint)
                dense_trainer=PPOTrainer(Policy(468,size='small',contract=env.contract))
                with self.assertRaisesRegex(ValueError,'mismatch'):
                    dense_trainer.load(checkpoint)
                cumulative=0.
                for index in range(2):
                    obs,reward,terminated,truncated,info=env.step(np.zeros(39))
                    cumulative+=reward
                    self.assertAlmostEqual(reward,sum(info['reward_terms'].values()))
                    self.assertGreater(info['reward_terms']['dense_left_early'],0.)
                    self.assertGreater(info['reward_terms']['dense_right_guide'],0.)
                    self.assertEqual(info['music']['matched50'],0)
                    self.assertEqual(info['music']['held_total_s'],0)
                    self.assertEqual(info['music'],legacy_steps[index][-1]['music'])
                    self.assertEqual(info['cost'],legacy_steps[index][-1]['cost'])
                    self.assertEqual(info['failure_reasons'],legacy_steps[index][-1]['failure_reasons'])
                    self.assertTrue(np.array_equal(obs['state'],legacy_steps[index][0]['state']))
                    guide=info['pick_guide']
                    self.assertEqual(guide['physics_step'],info['physics_measurements'][-1]['physics_step'])
                    self.assertEqual(guide['task_time_s'],info['task_time_s'])
                    np.testing.assert_allclose(guide['pick_G_m'],env.last_sample['geometry']['pick_G_m'])
                    self.assertAlmostEqual(guide['distance_m'],np.linalg.norm(np.array(guide['pick_G_m'])-guide['goal_G_m']))
                self.assertTrue(truncated)
                self.assertAlmostEqual(cumulative,info['episode']['reward'])
                self.assertAlmostEqual(cumulative,env.total_reward)
                self.assertEqual(len(info['physics_measurements']),4)
            finally: env.close()


if __name__=='__main__': unittest.main()
