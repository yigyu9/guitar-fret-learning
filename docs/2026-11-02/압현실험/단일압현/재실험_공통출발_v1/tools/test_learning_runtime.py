"""운반 정책 수집기의 배치 장벽·대기 제외·GAE prefix를 CPU로 확인한다."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import torch
spec=importlib.util.spec_from_file_location('transport_learning',Path(__file__).with_name('learning_runtime_v4.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Policy:
    def __call__(self,*inputs):return dict(reward_value=torch.zeros(2),cost_value=torch.zeros(2))
    def act(self,*inputs):
        result=self(*inputs)
        result.update(action=torch.zeros(2,39),latent=torch.zeros(2,39),logp=torch.zeros(2),mean=torch.zeros(2,39),log_std=torch.zeros(2,39))
        return result


class Pool:
    num_envs=2
    def __init__(self):
        self.scene=SimpleNamespace(device='cpu');self.waiting=torch.zeros(2,dtype=torch.bool)
        self.needs_preparation=True;self.preparations=0;self.time=0
        self.observation={name:torch.zeros(2,1) for name in m.FIELDS}
    def prepare(self):
        if self.needs_preparation:
            if self.waiting.any():raise RuntimeError('부분배치운반')
            self.preparations+=1;self.needs_preparation=False;self.time=0
    def step(self,action):
        self.time+=1
        terminated=torch.tensor([self.time==1,self.time==3])&~self.waiting
        episodes=[dict(env_id=int(i)) for i in terminated.nonzero().flatten()]
        return self.observation,torch.ones(2)*~self.waiting,torch.zeros(2),terminated,torch.zeros(2,dtype=torch.bool),episodes
    def reset(self,ids):
        self.waiting[ids]=True
        if self.waiting.all():self.waiting.zero_();self.needs_preparation=True


class LearningTests(unittest.TestCase):
    def test_waiting_excluded_reset_barrier_and_prefix_packing(self):
        pool=Pool();collector=m.Collector(Policy(),pool)
        buffer,episodes=collector.collect(5)
        self.assertEqual(pool.preparations,2)
        self.assertEqual([e['env_id'] for e in episodes],[0,1,0])
        self.assertEqual(buffer['valid'].sum(0).tolist(),[2,5])
        self.assertFalse(bool((buffer['valid'][1:]&~buffer['valid'][:-1]).any()))
        self.assertEqual(buffer['episode_id'][:2,0].tolist(),[0,1])
        advantage,_=m.ppo.compute_decision_gae(buffer['reward'],buffer['reward_value'],buffer['next_reward_value'],
            buffer['terminated'],buffer['truncated'],buffer['duration'],buffer['valid'],.99,.98)
        self.assertEqual(advantage.shape,(5,2))
        self.assertTrue(torch.isfinite(advantage).all())

    def test_waiting_rows_freeze_ledger_totals_and_emit_no_duplicate_episode(self):
        pool=m.LearningPool.__new__(m.LearningPool)
        pool.needs_preparation=False;pool.waiting=torch.tensor([True,False]);pool.num_envs=2
        pool.config=dict(active_axes=[21,22,23,24]);pool.frame_callback=None
        pool.policy_wrist_position=torch.zeros(2,3);pool.policy_wrist_quaternion=torch.tensor([[0.,0.,0.,1.]]*2)
        pool.controller=SimpleNamespace(active=torch.arange(39),target=torch.cat((torch.zeros(2,33),torch.ones(2,6)*.2),-1),reference=torch.zeros(39),
            action_low=-torch.ones(39),action_high=torch.ones(39))
        pool.scene=SimpleNamespace(snapshot=lambda:{})
        pool.wrist_request=lambda desired,goal,rotation,snapshot:desired
        env=SimpleNamespace(note={'clean':torch.tensor([[1.],[2.]])},clock=torch.tensor([5,5]),steps=torch.tensor([1,1]),
            total_reward=torch.tensor([1.,2.]),total_cost=torch.tensor([0.,0.]),finished=torch.tensor([True,False]),
            last_applied_action=torch.zeros(2,39),action_min=torch.cat((torch.zeros(1,39),torch.full((1,39),float('inf')))),
            action_max=torch.cat((torch.zeros(1,39),torch.full((1,39),-float('inf')))),observation=lambda:{name:torch.zeros(2,1) for name in m.FIELDS})
        pool.environment=env
        def physical_step(self,actions,waiting):
            self.assert_inactive=bool((actions[:,33:]==0).all())
            if not self.assert_inactive:raise ValueError('비활성 손 잔차0 필요')
            env.note['clean']+=10;env.clock+=1;env.steps+=1;env.total_reward+=10;env.total_cost+=10
            return {},torch.tensor([9.,8.]),torch.tensor([7.,6.]),torch.tensor([True,True]),torch.tensor([False,False]),[dict(env_id=0),dict(env_id=1)]
        with patch.object(m.LearningPool,'policy_physics_step',physical_step):
            _,reward,cost,terminated,_,episodes=pool.step(torch.zeros(2,39))
        self.assertTrue(pool.assert_inactive)
        self.assertTrue(torch.isfinite(env.action_min).all())
        self.assertTrue(torch.isfinite(env.action_max).all())
        self.assertEqual(env.note['clean'].flatten().tolist(),[1.,12.])
        self.assertEqual(env.total_reward.tolist(),[1.,12.])
        self.assertEqual(env.clock.tolist(),[6,6])
        self.assertEqual(reward.tolist(),[0.,8.]);self.assertEqual(cost.tolist(),[0.,6.])
        self.assertEqual(terminated.tolist(),[False,True]);self.assertEqual(episodes,[dict(env_id=1)])

    def test_preparation_failure_is_per_environment_without_threshold_relaxation(self):
        physical=torch.zeros(3,7,dtype=torch.bool);physical[1,0]=True
        zero=torch.zeros(3);false=torch.zeros(3,dtype=torch.bool)
        failed=m.preparation_failure_mask(physical,zero,zero,false,false)
        self.assertEqual(failed.tolist(),[False,True,False])
        ready=torch.tensor([True,False,True])
        self.assertTrue(bool((ready|failed).all()))
        self.assertTrue(bool(ready.any()))
        self.assertFalse(bool(failed.all()))
        physical.zero_()
        failed=m.preparation_failure_mask(physical,torch.tensor([0.,.1,0.]),torch.tensor([0.,0.,1.5]),false,false)
        self.assertEqual(failed.tolist(),[False,True,True])
        self.assertFalse(bool(m.preparation_failure_mask(physical,zero,zero,false,false).any()))

    def test_native_policy_clock_view_preserves_raw_clock_and_rejects_skips(self):
        env=SimpleNamespace(clock=torch.tensor([3,3]),preparation_physics_offset=torch.tensor([10,10]),
            last_native_policy_step=torch.tensor([13,13]))
        raw=dict(physics_step=torch.tensor([14,14]),q=torch.zeros(2,105))
        view=m.policy_snapshot_view(env,raw)
        self.assertEqual(raw['physics_step'].tolist(),[14,14])
        self.assertEqual(view['physics_step'].tolist(),[4,4])
        self.assertIs(raw['q'],view['q'])
        with self.assertRaises(RuntimeError):m.policy_snapshot_view(env,raw)
        env.clock+=1
        with self.assertRaises(RuntimeError):m.policy_snapshot_view(env,dict(raw,physics_step=torch.tensor([16,16])))

    def test_official_checkpoint_metadata_and_strict_cpu_restore(self):
        import tempfile
        from guitar_learning.tests.test_gpu_environment import fixture
        base=Path(__file__).resolve().parents[1]
        inputs=base/'inputs_v2/middle_s1_f12'
        evidence=base/'로그/retry_failed_C/jobs/middle_s1_f12_C/attempt01/report.json'
        with m.configuration(inputs/'catalog.json',inputs/'provenance.json','middle_s1_f12',evidence) as (config,row):
            settings=m.build_settings(config,row,num_envs=2);settings['size']='small'
            class Environment(m.natural.NaturalEnvironment):
                natural_press=config
                natural_preparation=dict(schema='guitar_learning.natural_preparation.v3',condition='E4')
            metadata,snapshot=fixture(2)
            env=Environment(metadata,bundle=Path(row['bundle']),song=settings['song'],skill=settings['finger_skill'],device='cpu',hand='left')
            env.reset([0,1],snapshot)
            policy=m.natural.NaturalPolicy(601,size='small',contract=env.contract,natural_press=config)
            trainer=m.natural.NaturalTrainer(policy,m.ppo.PPOConfig(**settings['ppo']))
            schedule=m.runner.ExposureSchedule(settings['finger_skill']['planned_transitions'])
            pool=SimpleNamespace(environment=env,preparation_records=[],observation=None,
                reset=lambda:(env.observation(),[]),set_training_progress=env.set_training_progress)
            with m.runtime(config):
                saved=m.training_checkpoint_metadata(settings,schedule,pool,{},None,None,0)
                self.assertEqual(saved['resume_scope'],'J model/Adam/RNG/exposure/sampler; fresh prepared episodes')
                self.assertIn('common-start transport',saved['transport_resume_scope'])
                m.runner._validate_metadata_schema(saved)
                m.runner._validate_pins(saved)
                with tempfile.TemporaryDirectory() as directory:
                    path=Path(directory)/'checkpoint.pt'
                    trainer.save(path,metadata=saved)
                    restored=m.runner.restore_checkpoint(trainer,pool,schedule,path)
                    self.assertEqual(restored['settings_sha256'],saved['settings_sha256'])
                    self.assertEqual(trainer.updates,0)

    def test_new_configuration_strict_validation_and_factory_restore(self):
        base=Path(__file__).resolve().parents[1]
        inputs=base/'inputs_v2/middle_s1_f12'
        evidence=base/'로그/retry_failed_C/jobs/middle_s1_f12_C/attempt01/report.json'
        before=m.rollout.GpuPool,m.rollout.DecisionCollector,m.runner._pins,m.natural.load_configuration
        with m.configuration(inputs/'catalog.json',inputs/'provenance.json','middle_s1_f12',evidence) as (config,row):
            self.assertEqual(config['schema'],m.SCHEMA)
            self.assertEqual(config['distribution'],'v9')
            self.assertEqual(config['initial_distribution']['v9_fraction'],1.)
            self.assertEqual(config['transport']['case'],'middle_s1_f12')
            self.assertEqual(m.natural.validate_config(config),config)
            settings=m.build_settings(config,row,num_envs=1)
            self.assertEqual(settings['finger_skill']['planned_transitions'],100*32)
            with m.runtime(config):
                self.assertIs(m.rollout.GpuPool,m.LearningPool)
                self.assertIs(m.rollout.DecisionCollector,m.Collector)
        self.assertEqual(before,(m.rollout.GpuPool,m.rollout.DecisionCollector,m.runner._pins,m.natural.load_configuration))


if __name__=='__main__':unittest.main()
