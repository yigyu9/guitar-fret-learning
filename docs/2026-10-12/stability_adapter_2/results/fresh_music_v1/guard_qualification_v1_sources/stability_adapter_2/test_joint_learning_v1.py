"""CPU contract/optimizer tests; synthetic rewards are not native music training."""
import copy
from pathlib import Path
import tempfile
import unittest
import numpy as np
import torch
from .environment_contract_v1 import EnvironmentContract
from .joint_policy_v1 import AbsoluteTargetCodec, JointActorCritic
from .joint_ppo_v1 import JointPPO,PPOConfig,gae
from .joint_learning_observation_v1 import compose,require_native_training_ready
from .dual_music_clock_v1 import JointMusicClock


class JointLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.contract=EnvironmentContract()

    def setUp(self): torch.manual_seed(17)

    def trainer(self):
        model=JointActorCritic(739,self.contract.groups)
        abi={'observation':{'dimension':739},'action_dimension':81,'joint_names':self.contract.names}
        return JointPPO(model,abi,PPOConfig(epochs=2,minibatch_size=16,learning_rate=1e-5))

    def batch(self,trainer):
        obs=torch.randn(8,4,739)
        sample=trainer.model.sample(obs)
        reward=sample['action'][...,15] * 100 + torch.linspace(0,1,8)[:,None]
        return {'obs':obs,**sample,'reward':reward,'next_value':torch.zeros(8,4),
                'terminated':torch.ones(8,4,dtype=torch.bool),'truncated':torch.zeros(8,4,dtype=torch.bool)}

    def test_81_groups(self):
        self.assertEqual([self.contract.groups.count(k) for k in ('body','head','arm','finger')],[9,6,24,42])

    def test_absolute_anchor_and_endpoints(self):
        codec=AbsoluteTargetCodec(self.contract,self.contract.q_ref)
        np.testing.assert_array_equal(codec.requested(np.zeros(81)),self.contract.q_ref)
        np.testing.assert_allclose(codec.requested(np.ones(81)),self.contract.effective_upper,atol=1e-15)
        np.testing.assert_allclose(codec.requested(-np.ones(81)),self.contract.effective_lower,atol=1e-15)

    def test_boundary_anchor_is_explicit(self):
        codec=AbsoluteTargetCodec(self.contract,self.contract.effective_lower)
        np.testing.assert_array_equal(codec.requested(-np.ones(81)),self.contract.effective_lower)
        self.assertEqual(codec.manifest()['boundary_flat_channels'],list(range(81)))

    def test_bad_anchor_and_action_rejected(self):
        with self.assertRaises(ValueError): AbsoluteTargetCodec(self.contract,self.contract.upper+1)
        codec=AbsoluteTargetCodec(self.contract,self.contract.q_ref)
        with self.assertRaises(ValueError): codec.requested(np.ones(81)*1.1)
        with self.assertRaises(ValueError): codec.requested(np.full(81,np.nan))

    def test_all_targets_rate_bounded(self):
        codec=AbsoluteTargetCodec(self.contract,self.contract.q_ref)
        requested,final=self.contract.targets(codec.owner_action(np.ones(81)),self.contract.q_ref)
        np.testing.assert_allclose(requested,self.contract.effective_upper)
        self.assertTrue(np.all(abs(final-self.contract.q_ref)<=self.contract.rates/60+1e-7))

    def test_model_shape_and_mean_anchor(self):
        model=self.trainer().model
        sample=model.sample(torch.randn(2,739),deterministic=True)
        self.assertEqual(sample['action'].shape,(2,81));self.assertEqual(sample['value'].shape,(2,))
        self.assertTrue(torch.equal(sample['action'],torch.zeros(2,81)))
        self.assertEqual([x.out_features for x in model.actor if isinstance(x,torch.nn.Linear)],[512,256,81])
        self.assertEqual([x.out_features for x in model.critic if isinstance(x,torch.nn.Linear)],[512,256,1])

    def test_sample_likelihood_replays_exactly(self):
        model=self.trainer().model;obs=torch.randn(6,739);sample=model.sample(obs)
        lp,_,_=model.evaluate_latent(obs,sample['latent'])
        self.assertTrue(torch.equal(lp,sample['log_prob']))

    def test_saturated_latent_is_finite(self):
        model=self.trainer().model
        latent=torch.full((2,81),40.);latent[1]*=-1
        lp,entropy,value=model.evaluate_latent(torch.zeros(2,739),latent)
        self.assertTrue(torch.isfinite(lp).all() and torch.isfinite(entropy).all())
        lp.mean().backward()
        self.assertTrue(torch.isfinite(model.log_std.grad).all())

    def test_terminal_stops_bootstrap_and_trace(self):
        r=torch.tensor([[1.],[2.],[100.]])
        z=torch.zeros_like(r);term=torch.tensor([[False],[True],[False]])
        adv,_=gae(r,z,torch.full_like(r,7),term,torch.zeros_like(term),.9,1)
        self.assertAlmostEqual(float(adv[1]),2.)
        self.assertAlmostEqual(float(adv[0]),9.1,places=5)

    def test_truncation_bootstraps_final_but_stops_trace(self):
        r=torch.tensor([[1.],[2.],[100.]])
        z=torch.zeros_like(r);trunc=torch.tensor([[False],[True],[False]])
        adv,_=gae(r,z,torch.full_like(r,7),torch.zeros_like(trunc),trunc,.9,1)
        self.assertAlmostEqual(float(adv[1]),8.3,places=5)
        self.assertAlmostEqual(float(adv[0]),14.77,places=5)

    def test_discount_is_seconds_based(self):
        c=PPOConfig()
        self.assertAlmostEqual(c.gamma**600,.5)
        self.assertAlmostEqual(c.lam**60,.5)

    def test_739_observation_no_future_results(self):
        music=JointMusicClock()
        obs,manifest=compose(np.zeros(548),music,np.zeros((6,22),bool),np.zeros(6),np.zeros(6),np.array([1,2,3]))
        self.assertEqual(obs.shape,(739,))
        self.assertFalse(manifest['teacher_action_inputs']);self.assertFalse(manifest['future_actual_outcome_inputs'])
        np.testing.assert_array_equal(obs[-3:],[1,2,3])
        self.assertEqual([b['offset'] for b in manifest['blocks']],[0,548,576,582,588,590,592,724,730,736])
        obs2,_=compose(np.zeros(548),music,np.eye(6,22,dtype=bool),np.ones(6),np.ones(6),np.array([1,2,3]))
        self.assertNotEqual(float(obs[592:724].sum()),float(obs2[592:724].sum()))

    def test_missing_measured_state_rejected(self):
        with self.assertRaises(ValueError):
            compose(np.zeros(548),JointMusicClock(),np.full((6,22),.5),np.zeros(6),np.zeros(6),np.zeros(3))

    def test_rearm_memory_affects_next_detection_and_observation(self):
        from tab2body.env.strike_detector import PickStrikeDetector,DETECTOR_WAIT_REARM
        first=PickStrikeDetector(1,rearm_min_frames=8)
        second=PickStrikeDetector(1,rearm_min_frames=8)
        for detector in (first,second): detector.state.fill_(DETECTOR_WAIT_REARM)
        second.wait_frames.fill_(7)
        music=JointMusicClock()
        a,_=compose(np.zeros(548),music,np.zeros((6,22)),first.state[0].numpy(),
                    first.wait_frames[0].numpy()/8,np.zeros(3))
        b,_=compose(np.zeros(548),music,np.zeros((6,22)),second.state[0].numpy(),
                    second.wait_frames[0].numpy()/8,np.zeros(3))
        self.assertFalse(np.array_equal(a[730:736],b[730:736]))
        start=torch.zeros(6,3);end=start.clone();end[:,1]=1
        tip=torch.tensor([[0.,0.,1.]])
        first.step(tip,tip,start,end,dt=1/240)
        second.step(tip,tip,start,end,dt=1/240)
        self.assertFalse(torch.equal(first.state,second.state))

    def test_optimizer_updates_actor_and_critic(self):
        trainer=self.trainer();batch=self.batch(trainer)
        actor=trainer.model.actor[-1].weight.detach().clone();critic=trainer.model.critic[-1].weight.detach().clone()
        metrics=trainer.update(batch)
        self.assertGreater(metrics['optimizer_steps'],0)
        self.assertFalse(torch.equal(actor,trainer.model.actor[-1].weight))
        self.assertFalse(torch.equal(critic,trainer.model.critic[-1].weight))
        self.assertEqual(trainer.transitions,32)
        self.assertGreater(float(trainer.model.obs_rms.count),32)

    def test_executed_inverse_not_accepted_as_sample(self):
        trainer=self.trainer();batch=self.batch(trainer);batch['action'].zero_()
        with self.assertRaises(ValueError): trainer.update(batch)

    def test_stale_logprob_rejected_before_update(self):
        trainer=self.trainer();batch=self.batch(trainer);batch['log_prob']+=1
        with self.assertRaises(ValueError): trainer.update(batch)
        self.assertEqual(trainer.updates,0)

    def test_checkpoint_resume_and_no_overwrite(self):
        trainer=self.trainer();trainer.update(self.batch(trainer))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'policy.pt';trainer.save(path)
            expected=torch.rand(4);copy_trainer=self.trainer();copy_trainer.load(path)
            self.assertTrue(torch.equal(torch.rand(4),expected))
            self.assertEqual(copy_trainer.updates,1)
            self.assertTrue(all(torch.equal(v,copy_trainer.model.state_dict()[k]) for k,v in trainer.model.state_dict().items()))
            self.assertEqual(len(copy_trainer.optimizer.state),len(trainer.optimizer.state))
            before=path.read_bytes()
            with self.assertRaises(FileExistsError): trainer.save(path)
            self.assertEqual(path.read_bytes(),before)

    def test_abi_rejected_before_state_load(self):
        trainer=self.trainer()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'policy.pt';trainer.save(path)
            other=JointPPO(JointActorCritic(739,self.contract.groups),
                           {'observation':{'dimension':739},'action_dimension':81,'joint_names':list(reversed(self.contract.names))})
            before=copy.deepcopy(other.model.state_dict())
            with self.assertRaises(ValueError): other.load(path)
            self.assertTrue(all(torch.equal(v,other.model.state_dict()[k]) for k,v in before.items()))

    def test_native_reward_not_faked_as_ready(self):
        with self.assertRaisesRegex(RuntimeError,'SO3_allowed_set_distance_not_certified'):
            require_native_training_ready()

    def test_collect_uses_final_observation_before_reset(self):
        class SyntheticEnv:
            def require_training_ready(self): pass
            def reset(self): self.t=0;return np.zeros(739,dtype=np.float32)
            def step(self,action):
                self.t+=1
                return np.ones(739,dtype=np.float32)*self.t,float(action[15]),False,self.t==2,{}
        trainer=self.trainer();batch=trainer.collect(SyntheticEnv(),3)
        self.assertEqual(batch['truncated'][:,0].tolist(),[False,True,False])
        with torch.no_grad(): expected=trainer.model.value(torch.ones(1,739)*2)[0,0]
        self.assertEqual(float(batch['next_value'][1,0]),float(expected))
        self.assertTrue(torch.equal(batch['obs'][2,0],torch.zeros(739)))
        self.assertGreater(trainer.update(batch)['optimizer_steps'],0)

    def test_collection_continues_across_rollouts(self):
        class SyntheticEnv:
            def require_training_ready(self): pass
            def reset(self): self.t=0;return np.zeros(739,dtype=np.float32)
            def step(self,action):
                self.t+=1
                return np.ones(739,dtype=np.float32)*self.t,0.,False,False,{}
        trainer=self.trainer();env=SyntheticEnv()
        trainer.collect(env,3)
        batch=trainer.collect(env,2)
        self.assertTrue(torch.equal(batch['obs'][0,0],torch.ones(739)*3))
        self.assertEqual(env.t,5)


if __name__=='__main__': unittest.main(verbosity=2)
