"""Counterexamples for asynchronous final-state bootstrap and partial rollouts."""
import copy
import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path
from . import parallel_cpu_env_v1 as pool_module
import numpy as np
import torch
from .parallel_collect_v1 import ParallelPPO
from stability_adapter_2.joint_policy_v1 import JointActorCritic
from stability_adapter_2.joint_ppo_v1 import PPOConfig,gae
from stability_adapter_2.deadline_graphics_migration_v1 import migrate_payload,digest

class FakeEnvironment:
    num_envs=2
    def __init__(self):self.tick=0;self.resets=[]
    def require_training_ready(self):pass
    def reset(self):return np.array([[1.,0,0],[2.,0,0]],dtype=np.float32)
    def step(self,actions):
        self.tick+=1
        obs=np.array([[10.+self.tick,0,0],[20.+self.tick,0,0]],dtype=np.float32)
        return obs,np.array([1.,2.]),np.array([self.tick==1,False]),np.array([False,self.tick==2]),{}
    def reset_done(self,mask):
        self.resets.append(mask.tolist())
        return {i:np.array([100.+i,0,0],dtype=np.float32) for i in np.flatnonzero(mask)}

class ValueModel(torch.nn.Module):
    def __init__(self):super().__init__();self.parameter=torch.nn.Parameter(torch.zeros(()))
    def sample(self,obs):
        latent=torch.zeros((len(obs),81))
        return {'latent':latent,'action':torch.tanh(latent),'log_prob':torch.zeros(len(obs)),'value':obs[:,0].clone()}
    def value(self,obs):return obs[:,:1]

def collector():
    c=ParallelPPO.__new__(ParallelPPO);c.model=ValueModel();c._collection_env=None;c._collection_obs=None
    return c

class CollectorTests(unittest.TestCase):
    def test_bootstrap_before_worker_reset(self):
        env=FakeEnvironment();c=collector();b=c.collect(env,3)
        self.assertEqual(b['reward'].shape,(3,2))
        self.assertEqual(b['action'].shape,(3,2,81))
        self.assertEqual(b['next_value'].tolist(),[[11.,21.],[12.,22.],[13.,23.]])
        self.assertEqual(b['obs'][1,:,0].tolist(),[100.,21.])
        self.assertEqual(b['obs'][2,:,0].tolist(),[12.,101.])
        self.assertEqual(env.resets,[[True,False],[False,True],[False,False]])
    def test_collection_continues_without_global_reset(self):
        env=FakeEnvironment();c=collector();c.collect(env,3);b=c.collect(env,1)
        self.assertEqual(b['obs'][0,:,0].tolist(),[13.,23.]);self.assertEqual(env.tick,4)
    def test_worker_error_rejects_partial_rollout(self):
        class Broken(FakeEnvironment):
            def step(self,actions):raise RuntimeError('worker EOF')
        with self.assertRaisesRegex(RuntimeError,'EOF'):collector().collect(Broken(),2)
    def test_GAE_independent_boundaries(self):
        r=torch.tensor([[1.,10.],[2.,20.],[3.,30.]])
        v=torch.zeros_like(r);nv=torch.ones_like(r)*4
        term=torch.tensor([[True,False],[False,False],[False,False]])
        trunc=torch.tensor([[False,False],[False,True],[False,False]])
        adv,_=gae(r,v,nv,term,trunc,.9,.8)
        self.assertAlmostEqual(float(adv[0,0]),1.,places=5)
        self.assertAlmostEqual(float(adv[1,1]),23.6,places=5)
        self.assertAlmostEqual(float(adv[0,1]),13.6+.72*23.6,places=5)
    def test_actual_multi_environment_PPO_update(self):
        torch.manual_seed(10);groups=['body']*9+['head']*6+['arm']*24+['finger']*42
        model=JointActorCritic(3,groups)
        abi={'observation':{'dimension':3},'action_dimension':81}
        ppo=ParallelPPO(model,abi,PPOConfig(learning_rate=3e-5))
        b=ppo.collect(FakeEnvironment(),4)
        before=copy.deepcopy(model.state_dict());result=ppo.update(b)
        self.assertEqual(result['transitions'],8);self.assertGreater(result['optimizer_steps'],0)
        self.assertLessEqual(result['final_analytic_kl'],.02)
        self.assertTrue(any(not torch.equal(before[k],v) for k,v in model.state_dict().items() if k.startswith('actor.')))
        self.assertTrue(all(torch.equal(before[k],v) for k,v in model.state_dict().items() if k.startswith('obs_rms.')))
    def test_partial_worker_creation_cleans_started_process(self):
        connections=[];processes=[]
        class Connection:
            def __init__(self):self.closed=False;self.sent=[]
            def send(self,value):self.sent.append(value)
            def close(self):self.closed=True
        class Process:
            def __init__(self,index):self.index=index;self.pid=None;self.alive=False;self.joined=False
            def start(self):
                if self.index==1:raise OSError('spawn failed')
                self.pid=123;self.alive=True
            def is_alive(self):return self.alive
            def join(self,timeout):self.joined=True;self.alive=False
        class Context:
            def Pipe(self):
                pair=(Connection(),Connection());connections.extend(pair);return pair
            def Process(self,**kwargs):
                value=Process(len(processes));processes.append(value);return value
        with tempfile.TemporaryDirectory() as directory,patch.object(pool_module.mp,'get_context',return_value=Context()):
            with self.assertRaisesRegex(OSError,'spawn failed'):pool_module.ParallelCPUEnvironment(3,Path(directory)/'workers')
        self.assertTrue(processes[0].joined)
        self.assertEqual(connections[0].sent,[('close',None)])
        self.assertTrue(all(c.closed for c in connections))
    def test_source_addition_preserves_numerics_and_rejects_old_changes(self):
        old={'source_sha256':{'old.py':'old'},'physics':'same'}
        new={'source_sha256':{'old.py':'old','parallel.py':'new'},'physics':'same'}
        original={'schema':'deadline_pilot_ppo_v1','abi':old,'abi_sha256':digest(old),'ppo_config':{},'model':{'weight':[2]},'optimizer':{'state':[3]},'updates':7}
        result=migrate_payload(original,new,{},['parallel.py'])
        self.assertIs(result['model'],original['model']);self.assertIs(result['optimizer'],original['optimizer'])
        self.assertEqual(result['updates'],7)
        new['source_sha256']['old.py']='changed'
        with self.assertRaises(ValueError):migrate_payload(original,new,{},['parallel.py'])

if __name__=='__main__':unittest.main()
