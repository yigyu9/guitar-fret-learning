"""복합 압현 도구의 CPU 계약 검사. GPU 물리 성공을 인증하지 않는다."""
import copy
import importlib.util
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch
from torch.distributions import Normal
HERE=Path(__file__).resolve().parent
if 'complex_learning_under_test' in sys.modules:
    entry=sys.modules['complex_learning_under_test']
else:
    spec=importlib.util.spec_from_file_location('complex_learning_under_test',HERE/'learning.py')
    entry=importlib.util.module_from_spec(spec);sys.modules[spec.name]=entry;spec.loader.exec_module(entry)
from guitar_learning.tests.test_finger_skill_policy import contract as base_contract
from guitar_learning.tests.test_gpu_environment import fixture
from guitar_learning.training.ppo import DecisionPPOTrainer
from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract


def model(case='B1'):
    config,_,row,_,_=entry.configuration(HERE.parent/'입력'/case)
    contract=base_contract();spec=entry.progress_contract(len(row['compiled_targets']))
    contract['observation']['dimension']=613;contract['observation']['fields']+=spec['fields'];contract['observation']['scales']+=spec['scales']
    contract['finger_progress']=spec;contract['natural_press']=config
    return entry.ComplexPolicy(613,size='small',contract=contract,natural_press=config),config


def data(count=2):
    return (torch.zeros(count,613),torch.zeros(count,3,24),torch.ones(count,3,dtype=torch.bool),
        torch.zeros(count,8,24),torch.ones(count,8,dtype=torch.bool))


class ComplexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def test_all_settings_and_compiled_targets(self):
        for case in ('B1','B2','S1','T1','S2','T2','S3','T3','O1','C1','C2','D1','D2'):
            settings=entry.build_settings(HERE.parent/'입력'/case,updates=2,num_envs=2,size='small')
            config=entry.validate_settings(settings)
            self.assertEqual(settings['song_training']['observation_dimension'],613)
            self.assertEqual(config['finger_initial_std'],.35)
            self.assertEqual(len(config['active_axes']),4 if case=='B1' else 20 if case in ('T3','O1','C1','C2','D1','D2') else 16)
        with self.assertRaises(ValueError):entry.configuration(HERE.parent/'입력/B1','free')

    def test_policy_mask_std_density_and_inactive_sampling(self):
        for case in ('B1','B2','T3','D1'):
            policy,config=model(case);inputs=data();result=policy.act(*inputs);mask=policy._active_mask()
            self.assertEqual(mask.nonzero().flatten().tolist(),config['active_axes'])
            self.assertTrue(all(torch.isfinite(value).all() for value in result.values()))
            self.assertTrue((result['action'][:,33:]==0).all())
            self.assertTrue(torch.equal(result['latent'][:,~mask],result['mean'][:,~mask]))
            finger_axes=[i for i in config['active_axes'] if i>=17]
            torch.testing.assert_close(result['log_std'][:,finger_axes].exp(),torch.full((2,len(finger_axes)),.35))
            if config['arm_mode']=='free':torch.testing.assert_close(result['log_std'][:,:12].exp(),torch.full((2,12),entry.STD_FLOOR))
            evaluated=policy.evaluate(*inputs,result['latent']);torch.testing.assert_close(result['logp'],evaluated['logp'])
            torch.testing.assert_close(evaluated['entropy'],Normal(result['mean'][:,mask],result['log_std'][:,mask].exp()).entropy().sum(-1))
            changed=result['latent'].clone();changed[:,~mask]+=10
            torch.testing.assert_close(policy.log_probability(result['mean'],result['log_std'],changed),result['logp'])
            actor={id(p) for p in policy.actor_parameters()};critic={id(p) for p in policy.value_parameters()};self.assertFalse(actor&critic)
            self.assertIs(policy.support_log_std,policy.core.support_log_std)
            with torch.no_grad():policy.finger_log_std.fill_(-9)
            if config['arm_mode']=='free':
                with torch.no_grad():policy.support_log_std.fill_(-9)
                torch.testing.assert_close(policy(*inputs)['log_std'][:,:12].exp(),torch.full((2,12),math.exp(-5)))
            torch.testing.assert_close(policy(*inputs)['log_std'][:,finger_axes].exp(),torch.full((2,len(finger_axes)),entry.STD_FLOOR))

    def test_strict_checkpoint_mask_and_legacy_rejection(self):
        first,_=model('B1');second,_=model('B1');other,_=model('B2')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'model.pt';DecisionPPOTrainer(first).save(path);DecisionPPOTrainer(second).load(path)
            for name,value in first.state_dict().items():torch.testing.assert_close(value,second.state_dict()[name],rtol=0,atol=0)
            with self.assertRaises(ValueError):DecisionPPOTrainer(other).load(path)
        for schema in ('guitar_learning.aligned_start_goal4_resume.v1','guitar_learning.song_finger_progress_resume.v1'):
            with self.assertRaises(ValueError):entry.validate_metadata(dict(schema=schema,settings={}))
        settings=entry.build_settings(HERE.parent/'입력/B1',updates=2,num_envs=2,size='small')
        changed=copy.deepcopy(settings);changed['natural_press']['active_axes']+=list(range(12))
        with self.assertRaises(ValueError):entry.validate_settings(changed)

    def test_native_root_roundtrip(self):
        contract=load_gpu_prepared_reset_contract('left');rigid=entry.RigidGuitar(contract,'cpu')
        logical=torch.tensor(entry._body_row(contract['state']['guitar_body_states'][0]))
        torch.testing.assert_close(entry.logical_to_root(rigid,logical),rigid.prepared_root,atol=2e-7,rtol=0)

    def test_environment_progress_future_and_partial_reset(self):
        settings=entry.build_settings(HERE.parent/'입력/T3',updates=2,num_envs=2,size='small')
        config=settings['natural_press']
        class Environment(entry.ComplexEnvironment):pass
        Environment.config=config;Environment.measure=True
        metadata,snapshot=fixture(2)
        with entry.runtime():
            env=Environment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],skill=settings['finger_skill'],device='cpu')
        env.set_evaluation(True,full_song=True);obs=env.reset([0,1],snapshot)
        self.assertEqual(obs['state'].shape,(2,613))
        self.assertEqual(env.task.targets[1].finger,3)
        env.clock[:]=int(4.9*240);env._advance_finger_progress(env._score_time(),torch.tensor([True,True]))
        self.assertEqual(env.finger_progress['target'][0,2].item(),1)
        before={k:v[1].clone() for k,v in env.finger_progress.items()}
        env.reset([0],snapshot)
        for key,value in before.items():torch.testing.assert_close(env.finger_progress[key][1],value)
        # 두 번 종료되는 실패 환경도 평가의 첫 환경 에피소드 하나만 기록한다.
        env._episode(0,True);env.reset([0],snapshot);env._episode(0,True);env._episode(1,False)
        self.assertEqual(len(env.diagnostic_episodes),2)
        self.assertEqual({e['env_id'] for e in env.diagnostic_episodes},{0,1})

    def test_pool_partial_reset_rhs_and_factory_restore(self):
        pool=object.__new__(entry.ComplexPool);pool.num_envs=2
        pool.scene=SimpleNamespace(device='cpu',initial_hold=torch.full((2,105),.01),target=torch.ones(2,105))
        pool.controller=SimpleNamespace(active=torch.arange(39),reference=torch.zeros(105),target=torch.ones(2,105),action_low=-torch.ones(39),action_high=torch.ones(39))
        pool.environment=SimpleNamespace(previous_action=torch.ones(2,39),observation=lambda:{'state':torch.zeros(2,613)})
        pool.execution_hold_action=torch.ones(2,39)
        with patch.object(entry.rollout.GpuPool,'reset',return_value=({},[])):pool.reset([0])
        self.assertTrue((pool.execution_hold_action[0,33:]==0).all());self.assertTrue((pool.execution_hold_action[1]==1).all())
        self.assertTrue((pool.scene.target[0,33:39]==0).all());self.assertTrue((pool.scene.target[1]==1).all())
        original=(entry.rollout.GpuPool,entry.runner._policy,entry.gpu_environment.make_task)
        with self.assertRaises(RuntimeError):
            with entry.runtime():raise RuntimeError('예외 복원 검사')
        self.assertEqual(original,(entry.rollout.GpuPool,entry.runner._policy,entry.gpu_environment.make_task))

    def test_timing_union_overlap_and_terminal_release_separation(self):
        targets=[dict(target_id='a',finger=2,string=2,fret=6,onset_s=1.,end_s=2.),
                 dict(target_id='b',finger=3,string=1,fret=7,onset_s=1.,end_s=2.)]
        ledger=entry.TimingTracker(targets,2)
        for tick in range(1,529):
            now=tick/240.;audible=1.<now<=2.;candidate=now<=2.
            credit=1/240. if audible else 0.
            ledger.observe([now,now],[[credit,credit],[0.,0.]],[[candidate,candidate],[True,True]],[True,True],[[audible,audible],[False,False]])
        one=ledger.episode(0);two=ledger.episode(1)
        self.assertTrue(one['timing_pass']);self.assertTrue(one['overlap_pass'])
        self.assertAlmostEqual(one['wrong_press_active_union_s'],1.,places=8)
        self.assertFalse(two['timing_pass']);self.assertFalse(two['overlap_pass'])
        ledger.reset([0]);self.assertEqual(ledger.rows[1]['samples'],528)
        # 마지막 해제만 실패하는 경우 연결용 내부값과 엄격값을 구분한다.
        ledger.rows[0]['first']=[1.,1.];ledger.rows[0]['release_seen']=[.1,.1]
        item=ledger.episode(0);self.assertTrue(item['internal_timing_pass']);self.assertFalse(item['timing_pass'])

    def test_reference_schema_sha_and_unsupported_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.json';source.write_text('{}')
            config=dict(case_id='C1',geometry_sha256='catalog')
            value=dict(schema='guitar_learning.complex_press_reference.v1',case_id='C1',catalog_sha256='catalog',source_sha256={str(source):entry.digest(source)},candidate_valid=True,waypoints=[])
            path=root/'ref.json';path.write_text(entry.json.dumps(value))
            with patch.object(entry,'ROOT',root):
                document,paths=entry.load_reference(path,config);self.assertEqual(len(paths),2)
                source.write_text('changed')
                with self.assertRaises(ValueError):entry.load_reference(path,config)
        config,catalog,row,known,_=entry.configuration(HERE.parent/'입력/C1')
        controller=SimpleNamespace(active=torch.tensor(catalog['action_indices']),device='cpu',reference=torch.tensor(catalog['reference105']))
        with self.assertRaises(NotImplementedError):entry.replay_targets(row,known,config,controller,5.)


if __name__=='__main__':unittest.main()
