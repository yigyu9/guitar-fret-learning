"""GPU 없이 원본 반환 보존·복원·첫episode·할인 대조를 검증한다."""
import copy
from types import SimpleNamespace
import unittest
import torch
import reward_trace_probe as probe


class TraceTests(unittest.TestCase):
    def setup_fake(self):
        class TrainerBase:
            def load(self, *args):
                return 'strict-result'
        class Trainer(TrainerBase):
            pass
        class EnvBase:
            def _reward_components(self, legacy):
                return self.values
        class Env(EnvBase):
            pass
        class Pool:
            def __init__(self):
                self.num_envs = 32
                self.scene = SimpleNamespace(physics_steps=0, initial_hold=torch.zeros(32,105),
                    snapshot=lambda:dict(q=torch.zeros(32,105)))
            def reset(self):
                return 'native-reset'
        official = SimpleNamespace(_pins=lambda *args:args)
        sp = SimpleNamespace(StructuredPool=Pool, StructuredTrainer=Trainer, StructuredEnvironment=Env)
        trainer = Trainer(); trainer.updates=9; trainer.policy=torch.nn.Linear(1,1)
        env=Env();env.values={k:torch.zeros(1) for k in probe.TERMS};env.N=1
        env.steps=torch.tensor([1]);env.invalid=torch.tensor([False]);env.tick_cost=torch.zeros(1)
        env.before_surface_potential=torch.zeros(1);env.approach_gamma=.99
        env._local_time=lambda:torch.tensor([1/60]);env._episode_duration=lambda:torch.tensor([6.])
        return sp,official,trainer,env

    def test_readonly_arming_dedup_and_restore(self):
        sp,o,t,e=self.setup_fake(); original_init=sp.StructuredPool.__init__;seeds=[]
        with self.assertRaisesRegex(ValueError,'duplicate'):
            with probe.trace_context(sp,o,seeds.append,4242) as record:
                self.assertIs(e._reward_components({}), e.values)
                self.assertEqual(record['rows'],[])
                pool=sp.StructuredPool();self.assertEqual(t.load('cp'),'strict-result')
                self.assertEqual(pool.reset(),'native-reset')
                self.assertIs(e._reward_components({}),e.values)
                e.values[probe.TERMS[0]][0]=7
                self.assertEqual(float(record['rows'][0]['terms'][0]),0)
                e._reward_components({})
        self.assertIs(sp.StructuredPool.__init__, original_init)
        self.assertNotIn('load',sp.StructuredTrainer.__dict__)
        self.assertNotIn('_reward_components',sp.StructuredEnvironment.__dict__)
        self.assertEqual(seeds,[4242,4242])

    def test_first_terminal_deduplicated(self):
        sp,o,t,e=self.setup_fake()
        with probe.trace_context(sp,o,lambda seed:None,4242) as record:
            p=sp.StructuredPool();t.load('cp');p.reset();e.invalid[0]=True
            e._reward_components({});e._reward_components({})
            self.assertEqual(len(record['rows']),1);self.assertEqual(record['seen'],{0})
        self.assertNotIn('load',sp.StructuredTrainer.__dict__)

    def test_native_one_based_steps_through_terminal360(self):
        sp,o,t,e=self.setup_fake()
        with probe.trace_context(sp,o,lambda seed:None,4242) as record:
            p=sp.StructuredPool();t.load('cp');p.reset()
            for native_tick in range(1,361):
                e.steps[0]=native_tick
                e._local_time=lambda tick=native_tick:torch.tensor([tick/60.])
                e._reward_components({})
            self.assertEqual([x['tick'] for x in record['rows']],list(range(360)))
            self.assertTrue(record['rows'][-1]['terminal'])
            e.steps[0]=1
            e._reward_components({})
            self.assertEqual(len(record['rows']),360)
        sp,o,t,e=self.setup_fake()
        with probe.trace_context(sp,o,lambda seed:None,4242):
            p=sp.StructuredPool();t.load('cp');p.reset();e._reward_components({})
            e.steps[0]=3
            with self.assertRaisesRegex(ValueError,'missing'):e._reward_components({})

    def test_reconcile_discount_and_failure_gate(self):
        rows=[];episodes=[]
        for i in range(32):
            for tick,value in enumerate((.99,-1.)):
                terms=torch.zeros(9);terms[0]=value
                rows.append(dict(env=i,tick=tick,terms=terms,cost=0.,gamma=.99,
                    phi_before=float(tick),terminal=tick==1))
            expected={k:0. for k in probe.TERMS};expected[probe.TERMS[0]]=float(torch.tensor(.99))-1.
            episodes.append(dict(env_id=i,steps=2,reward_components=expected,
                cost=0.,reward=expected[probe.TERMS[0]]))
        result=probe.reconcile(rows,episodes,reward_gamma=.99,cost_gamma=1.)
        self.assertLess(abs(result[0]['discounted_shaping_terminal_zero_residual']),2e-8)
        with self.assertRaisesRegex(ValueError,'gamma differs'):
            probe.reconcile(rows,episodes,reward_gamma=.98,cost_gamma=1.)
        cost_rows=copy.deepcopy(rows);cost_episodes=copy.deepcopy(episodes)
        for row in cost_rows:row['cost']=2.
        for episode in cost_episodes:episode['cost']=4.
        undiscounted=probe.reconcile(cost_rows,cost_episodes,reward_gamma=.99,cost_gamma=1.)
        discounted=probe.reconcile(cost_rows,cost_episodes,reward_gamma=.99,cost_gamma=.99)
        self.assertEqual(undiscounted[0]['discounted_cost'],4.)
        self.assertAlmostEqual(discounted[0]['discounted_cost'],3.98)
        broken=copy.deepcopy(episodes);broken[0]['reward']=1
        with self.assertRaisesRegex(ValueError,'reconcile'):probe.reconcile(rows,broken,reward_gamma=.99,cost_gamma=1.)
        with self.assertRaisesRegex(ValueError,'incomplete'):probe.reconcile(rows[:-1],episodes,reward_gamma=.99,cost_gamma=1.)
        with self.assertRaisesRegex(ValueError,'first32'):probe.reconcile(rows,episodes[:-1],reward_gamma=.99,cost_gamma=1.)


if __name__=='__main__':unittest.main()
