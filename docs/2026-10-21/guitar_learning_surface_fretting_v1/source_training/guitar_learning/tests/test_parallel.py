"""Spawned CPU fake workers exercise IPC and PPO without importing Isaac Gym."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
import numpy as np
import torch
from guitar_learning.training.parallel import Pool, Collector, _native_environment
from guitar_learning.training.policy import Policy
from guitar_learning.training.ppo import PPOTrainer, PPOConfig


def observation(value):
    return dict(state=np.full(5,value,np.float32),events=np.zeros((2,24),np.float32),
                mask=np.zeros(2,bool),priority_events=np.zeros((2,24),np.float32),priority_mask=np.zeros(2,bool))


CONTRACT={'schema':'guitar_learning.training.v1','observation':{'dimension':5},'action':{'dimension':39},
          'task':{'source':'fake_cpu'},'reward':{},'termination':{}}


class FakeEnvironment:
    def __init__(self,spec,worker_id):
        self.spec,self.worker_id=spec,worker_id
        self.contract=copy.deepcopy(CONTRACT)
        if spec.get('mismatch'): self.contract['reward']['wrong']=True
        self.steps=0
        self.resets=0
    def reset(self):
        self.resets+=1
        if self.resets>1 and self.spec.get('reset_sleep'): time.sleep(self.spec['reset_sleep'])
        self.steps=0
        return observation(-10),{}
    def step(self,action):
        if self.spec.get('crash'):
            import os
            os._exit(13)
        if self.spec.get('fault'): raise RuntimeError('injected worker guard fault')
        if self.spec.get('sleep'): time.sleep(2. if self.spec['sleep'] is True else self.spec['sleep'])
        if self.spec.get('delay'): time.sleep(self.spec['delay'])
        self.steps+=1
        done=self.steps==2
        terminated=done and self.worker_id==0
        truncated=done and self.worker_id!=0
        info=dict(cost=.25,termination_reason='terminal_failure' if terminated else 'time_limit' if truncated else None)
        if done: info['episode']=dict(valid=True)
        marker=self.spec.get('marker',0)
        return observation(self.steps+3+marker),float(self.steps+marker),terminated,truncated,info
    def close(self): pass


def fake_factory(spec,worker_id): return FakeEnvironment(spec,worker_id)


def failed_factory(spec,worker_id): raise ValueError('injected startup failure')


class ParallelTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        self.folder=tempfile.TemporaryDirectory()
        self.specs=[dict(out=str(Path(self.folder.name)/str(i))) for i in range(2)]
    def tearDown(self): self.folder.cleanup()

    def test_native_factory_selects_declared_headless_session_without_native_execution(self):
        import sys
        from types import ModuleType
        from unittest.mock import patch
        from guitar_learning.runtime.headless_session import HeadlessPreparedSession
        from guitar_learning.core import task_sampling
        spec=dict(config={'cpu':True},out=self.specs[0]['out'],bundle='score',stage='B',seed=7,headless=True)
        marker=object()
        with patch.dict(sys.modules,{'isaacgym':ModuleType('isaacgym')}), \
             patch.object(task_sampling,'build_environment',return_value=marker) as constructor:
            self.assertIs(_native_environment(spec,1),marker)
        self.assertIs(constructor.call_args.kwargs['session_factory'],HeadlessPreparedSession)
        self.assertEqual(constructor.call_args.kwargs['seed'],7)
        self.assertEqual(constructor.call_args.kwargs['worker_id'],1)
        self.assertIsNone(constructor.call_args.kwargs['music'])
        self.assertEqual(constructor.call_args.args[1],Path(spec['out'])/'environment')
        # One factory selection test supports all pool sizes without starting 16 children.
        with patch('guitar_learning.training.parallel.mp.get_context',side_effect=RuntimeError('accepted size')):
            with self.assertRaisesRegex(RuntimeError,'accepted size'):
                Pool([dict(out=str(Path(self.folder.name)/str(i))) for i in range(16)])

    def test_partial_reset_preserves_other_worker_and_contract(self):
        with Pool(self.specs,timeout_s=15,worker_factory=fake_factory) as pool:
            obs,infos=pool.reset()
            self.assertEqual(obs['state'].shape,(2,5))
            self.assertEqual(pool.contract,CONTRACT)
            self.assertEqual([i['worker_id'] for i in infos],[0,1])
            obs,*_=pool.step(np.zeros((2,39)))
            other=obs['state'][1].copy()
            obs,infos=pool.reset([0])
            np.testing.assert_array_equal(obs['state'][1],other)
            np.testing.assert_array_equal(obs['state'][0],np.full(5,-10,np.float32))
            self.assertIsNone(infos[1])
        self.assertTrue(all(not process.is_alive() for process in pool.processes))
        for spec in self.specs:
            audit=json.loads((Path(spec['out'])/'worker_final_audit.json').read_text())
            self.assertIsNone(audit['failure'])
            self.assertGreater(audit['resource']['rss_peak_kib'],0)
            self.assertEqual(audit['resource']['torch_cuda_allocated_bytes'],0)
            self.assertTrue(any(p.endswith('/guitar_learning/training/parallel.py') for p in audit['actual_imported_sources']))
            self.assertIn('thread_environment',audit['runtime'])

    def test_terminal_truncated_final_bootstrap_cost_and_n2_update(self):
        with Pool(self.specs,timeout_s=15,worker_factory=fake_factory) as pool:
            model=Policy(5,size='small',contract=CONTRACT)
            collector=Collector(model,pool)
            data,episodes=collector.collect(1)
            self.assertEqual(episodes,[])
            data,episodes=collector.collect(3)
            self.assertEqual(data['state'].shape,(3,2,5))
            self.assertEqual([e['cost'] for e in episodes],[.5,.5,.5,.5])
            self.assertEqual([e['worker_id'] for e in episodes],[0,1,0,1])
            self.assertEqual(data['next_reward_value'][0,0].item(),0.)
            with torch.no_grad():
                final=observation(5)
                final_batch={k:np.stack([v,v]) for k,v in final.items()}
                expected=model(*collector._inputs(final_batch))['reward_value'][1].item()
            self.assertAlmostEqual(data['next_reward_value'][0,1].item(),expected)
            self.assertEqual(data['state'][1,1,0].item(),-10.)
            before=[p.detach().clone() for p in model.actor_parameters()]
            metrics=PPOTrainer(model,PPOConfig(actor_lr=1e-6,target_kl=.1,epochs=1)).update(data,episodes)
            self.assertTrue(np.isfinite(metrics['actor_loss']))
            self.assertTrue(any(not torch.equal(a,b) for a,b in zip(before,model.actor_parameters())))

    def test_worker_fault_invalidates_whole_collection_and_closes_children(self):
        self.specs[1]['fault']=True
        pool=Pool(self.specs,timeout_s=15,worker_factory=fake_factory)
        collector=Collector(Policy(5,size='small',contract=CONTRACT),pool)
        with self.assertRaisesRegex(RuntimeError,'injected worker guard fault'): collector.collect(3)
        audit=json.loads((Path(self.specs[1]['out'])/'worker_final_audit.json').read_text())
        self.assertIn('injected worker guard fault',audit['failure']['message'])
        self.assertFalse(collector.dataset_valid)
        self.assertFalse(pool.valid)
        self.assertTrue(pool.closed)
        self.assertTrue(all(not process.is_alive() for process in pool.processes))
        with self.assertRaises(RuntimeError): collector.collect(1)

    def test_startup_failure_and_contract_mismatch_abort(self):
        with self.assertRaisesRegex(RuntimeError,'injected startup failure'):
            Pool(self.specs,timeout_s=15,worker_factory=failed_factory)
        for spec in self.specs:
            audit=json.loads((Path(spec['out'])/'worker_final_audit.json').read_text())
            self.assertIn('injected startup failure',audit['failure']['message'])
            spec['out']=str(Path(spec['out'])/'next_pool')
        self.specs[1]['mismatch']=True
        pool=Pool(self.specs,timeout_s=15,worker_factory=fake_factory)
        with self.assertRaisesRegex(ValueError,'contract mismatch'): pool.reset()
        self.assertTrue(pool.closed)
        self.assertTrue(all(not process.is_alive() for process in pool.processes))

    def test_ipc_timeout_aborts_and_reaps_worker(self):
        slow=[dict(self.specs[0],sleep=10.)]
        pool=Pool(slow,timeout_s=15,worker_factory=fake_factory)
        pool.reset()
        pool.timeout_s=.01
        with self.assertRaises(TimeoutError): pool.step(np.zeros((1,39)))
        self.assertFalse(pool.valid)
        self.assertTrue(all(not process.is_alive() for process in pool.processes))
        self.assertTrue(pool.close_diagnostics[0]['terminate_sent'])
        self.assertIsNotNone(pool.close_diagnostics[0]['final_exitcode'])

    def test_crashed_worker_detected_before_slow_worker_timeout(self):
        self.specs[0]['sleep']=True
        self.specs[1]['crash']=True
        pool=Pool(self.specs,timeout_s=15,worker_factory=fake_factory)
        pool.reset()
        started=time.monotonic()
        with self.assertRaisesRegex(RuntimeError,r'worker=1 pid=\d+ exitcode=13'):
            pool.step(np.zeros((2,39)))
        self.assertLess(time.monotonic()-started,4.)  # Includes graceful cleanup of the 2 s sleeper.
        self.assertFalse(pool.valid)
        self.assertEqual(pool.close_diagnostics[1]['final_exitcode'],13)
        self.assertTrue(all(not row['final_alive'] for row in pool.close_diagnostics))

    def test_wait_callback_observes_only_remaining_workers_and_output_order(self):
        calls=[]
        self.specs[0]['delay']=.8
        self.specs[0]['marker']=10
        self.specs[1]['marker']=20
        with Pool(self.specs,timeout_s=15,worker_factory=fake_factory,wait_callback=calls.append) as pool:
            pool.reset()
            calls.clear()
            pool._last_wait_callback=0.
            obs,reward,*_=pool.step(np.zeros((2,39)))
            self.assertEqual(reward.tolist(),[11.,21.])
            self.assertEqual(obs['state'][:,0].tolist(),[14.,24.])
        step_calls=[row for row in calls if row['operation']=='step']
        self.assertTrue(any(row['pending_workers']==[0] for row in step_calls))
        self.assertTrue(all(len(row['worker_status'])==2 for row in step_calls))
        self.assertTrue(all(row['elapsed_s']>=0 for row in step_calls))

    def test_wait_callback_failure_discards_collection_and_reaps_children(self):
        self.specs[0]['sleep']=True
        pool=Pool(self.specs,timeout_s=15,worker_factory=fake_factory)
        collector=Collector(Policy(5,size='small',contract=CONTRACT),pool)
        collector.observation=pool.reset()[0]
        def stop(context):
            if context['operation']=='step': raise MemoryError('injected memory guard')
        pool.wait_callback=stop
        pool._last_wait_callback=0.
        with self.assertRaisesRegex(MemoryError,'injected memory guard'): collector.collect(2)
        self.assertFalse(collector.dataset_valid)
        self.assertFalse(pool.valid)
        self.assertTrue(pool.closed)
        self.assertTrue(all(not process.is_alive() for process in pool.processes))

    def test_progress_callback_counts_complete_ticks_and_failure_discards_buffer(self):
        with Pool(self.specs,timeout_s=15,worker_factory=fake_factory) as pool:
            collector=Collector(Policy(5,size='small',contract=CONTRACT),pool)
            calls=[]
            collector.collect(3,progress_callback=calls.append)
            self.assertEqual([row['ticks'] for row in calls],[1,2,3])
            self.assertEqual([row['transitions'] for row in calls],[2,4,6])
            self.assertEqual([row['episodes_completed'] for row in calls],[0,2,2])
            self.assertTrue(all(row['horizon']==3 for row in calls))
            def stop(context): raise RuntimeError('injected progress stop')
            with self.assertRaisesRegex(RuntimeError,'injected progress stop'):
                collector.collect(2,progress_callback=stop)
            self.assertFalse(collector.dataset_valid)
            self.assertTrue(pool.closed)

    def test_terminal_tick_count_survives_partial_reset_guard_and_timeout(self):
        for kind in ('guard','timeout'):
            with self.subTest(kind=kind):
                specs=[dict(self.specs[0],out=str(Path(self.specs[0]['out'])/kind),reset_sleep=10.)]
                pool=Pool(specs,timeout_s=15,worker_factory=fake_factory)
                collector=Collector(Policy(5,size='small',contract=CONTRACT),pool)
                collector.observation=pool.reset()[0]
                calls=[]
                def progress(context):
                    calls.append(context)
                    if context['pending_reset_workers']:
                        if kind=='timeout': pool.timeout_s=.01
                        else:
                            def stop(context):
                                if context['operation']=='reset': raise MemoryError('partial reset memory guard')
                            pool.wait_callback=stop
                            pool._last_wait_callback=0.
                with self.assertRaises(MemoryError if kind=='guard' else TimeoutError):
                    collector.collect(3,progress_callback=progress)
                self.assertEqual([row['ticks'] for row in calls],[1,2])
                self.assertEqual(calls[-1]['transitions'],2)
                self.assertEqual(calls[-1]['pending_reset_workers'],[0])
                self.assertEqual(calls[-1]['phase'],'step_complete')
                self.assertFalse(collector.dataset_valid)
                self.assertTrue(pool.closed)
