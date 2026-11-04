"""중지 줄·프렛 전환과 immutable snapshot CPU 검사. GPU 성공을 인증하지 않는다."""
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
if 'middle_s3f5_s4f8_learning_under_test' in sys.modules:
    entry=sys.modules['middle_s3f5_s4f8_learning_under_test']
else:
    spec=importlib.util.spec_from_file_location('middle_s3f5_s4f8_learning_under_test',HERE/'learning.py')
    entry=importlib.util.module_from_spec(spec);sys.modules[spec.name]=entry;spec.loader.exec_module(entry)
from guitar_learning.tests.test_finger_skill_policy import contract as base_contract
from guitar_learning.tests.test_gpu_environment import fixture
from guitar_learning.training.ppo import PPOConfig,KLGuardError
DecisionPPOTrainer=entry.ExperimentTrainer
from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract


def model(case='A0',arm_std=.15,lr_mode='recover_floor'):
    config,_,row,_,_=entry.configuration(HERE.parent/'입력'/case,arm_std=arm_std,lr_mode=lr_mode)
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
        for case in ('A0',):
            settings=entry.build_settings(HERE.parent/'입력'/case,updates=2,num_envs=2,size='small')
            config=entry.validate_settings(settings)
            self.assertEqual(settings['song_training']['observation_dimension'],613)
            self.assertEqual(config['finger_initial_std'],.35)
            self.assertEqual(len(config['active_axes']),12+4*len(config['target_fingers']))
        with self.assertRaises(ValueError):entry.configuration(HERE.parent/'입력/A0','hold')

    def test_policy_mask_std_density_and_inactive_sampling(self):
        for case in ('A0',):
            policy,config=model(case);inputs=data();result=policy.act(*inputs);mask=policy._active_mask()
            self.assertEqual(mask.nonzero().flatten().tolist(),config['active_axes'])
            self.assertTrue(all(torch.isfinite(value).all() for value in result.values()))
            self.assertTrue((result['action'][:,33:]==0).all())
            self.assertTrue(torch.equal(result['latent'][:,~mask],result['mean'][:,~mask]))
            finger_axes=[i for i in config['active_axes'] if i>=17]
            torch.testing.assert_close(result['log_std'][:,finger_axes].exp(),torch.full((2,len(finger_axes)),.35))
            if config['arm_mode']=='free':torch.testing.assert_close(result['log_std'][:,:12].exp(),torch.full((2,12),config['arm_initial_std']))
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
        first,_=model('A0');second,_=model('A0');other,_=model('A0',lr_mode='existing')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'model.pt';DecisionPPOTrainer(first).save(path);DecisionPPOTrainer(second).load(path)
            for name,value in first.state_dict().items():torch.testing.assert_close(value,second.state_dict()[name],rtol=0,atol=0)
            with self.assertRaises(ValueError):DecisionPPOTrainer(other).load(path)
        for schema in ('guitar_learning.successor_simultaneous_resume.v1','guitar_learning.a0_exploration_lr_resume.v1','guitar_learning.complex_press_night_resume.v1','guitar_learning.complex_press_resume.v1','guitar_learning.aligned_start_goal4_resume.v1','guitar_learning.song_finger_progress_resume.v1'):
            with self.assertRaises(ValueError):entry.validate_metadata(dict(schema=schema,settings={}))
        settings=entry.build_settings(HERE.parent/'입력/A0',updates=2,num_envs=2,size='small')
        changed=copy.deepcopy(settings);changed['natural_press']['active_axes']+=list(range(12))
        with self.assertRaises(ValueError):entry.validate_settings(changed)


    def test_arm_std_is_only_initial_tensor_difference_and_strict_identity(self):
        states=[];policies=[];settings_list=[]
        for std in entry.ARM_STD_CHOICES:
            torch.manual_seed(7);policy,config=model('A0',arm_std=std)
            states.append({k:v.clone() for k,v in policy.state_dict().items()});policies.append(policy)
            self.assertEqual(config['arm_initial_std'],std)
            settings_list.append(entry.build_settings(HERE.parent/'입력/A0',updates=100,num_envs=64,size='large',seed=7,arm_std=std))
            actual=policy(*data())['log_std'][0]
            torch.testing.assert_close(actual[:12].exp(),torch.full((12,),std))
            torch.testing.assert_close(actual[12:17].exp(),torch.full((5,),entry.STD_FLOOR))
            torch.testing.assert_close(actual[21:25].exp(),torch.full((4,),.35))
        for settings in settings_list[1:]:
            changed=copy.deepcopy(settings);changed['natural_press']['arm_initial_std']=.15
            self.assertEqual(changed,settings_list[0])
        for state in states[1:]:
            self.assertEqual(set(state),set(states[0]))
            self.assertEqual([k for k in state if not torch.equal(state[k],states[0][k])],['core.support_log_std'])
            torch.testing.assert_close(state['core.support_log_std'][12:],states[0]['core.support_log_std'][12:],rtol=0,atol=0)
            self.assertEqual(int((state['core.support_log_std']!=states[0]['core.support_log_std']).sum()),12)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'std.pt';DecisionPPOTrainer(policies[0]).save(path)
            with self.assertRaises(ValueError):DecisionPPOTrainer(policies[1]).load(path)
        with self.assertRaises(ValueError):entry.configuration(HERE.parent/'입력/A0',arm_std=.10)

    def test_transition_and_readonly_native_snapshot(self):
        settings=entry.build_settings(HERE.parent/'입력/A0',updates=200,num_envs=2,size='small')
        class Environment(entry.ComplexEnvironment):pass
        Environment.config=settings['natural_press'];Environment.measure=True
        metadata,snapshot=fixture(2);snapshot['physics_step']=torch.zeros(2,dtype=torch.long)
        with entry.runtime():
            env=Environment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],skill=settings['finger_skill'],device='cpu')
        env.set_evaluation(True,full_song=True);env.reset([0,1],snapshot)
        self.assertEqual([(t.finger,t.onset_s,t.end_s) for t in env.task.targets],[(2,3.,4.5),(2,5.5,7.)])
        self.assertEqual(len(settings['natural_press']['active_axes']),16)
        scene=SimpleNamespace(snapshot=lambda:snapshot,body_names=metadata['body_names'],names=metadata['joint_names'])
        before={k:v.clone() for k,v in snapshot.items()}
        row=entry.replay_snapshot(SimpleNamespace(scene=scene,environment=env),snapshot['target'][0],0.)
        for key,value in before.items():torch.testing.assert_close(value,snapshot[key],atol=0,rtol=0)
        self.assertTrue(row['boundary_before_new_physics']);self.assertEqual(len(row['q105']),105)
        self.assertEqual(len(row['body_state']),len(metadata['body_names']));self.assertEqual(len(row['targets']),2)
        self.assertEqual(row['wrong_source_body_names'][7],'human/LH:ring3')

    def test_snapshot_files_are_unique_and_manifest_written_once(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);snapshots=[];paths=[]
            for i,t in enumerate(entry.REPLAY_CAPTURE_TIMES):
                entry.record_replay_snapshot(out,snapshots,paths,dict(physics_step=round(t*240),requested_time_s=t))
            self.assertEqual(len({p['path'] for p in paths}),9)
            for p in paths:self.assertEqual(entry.digest(p['path']),p['sha256'])
            entry.write_replay_manifest(out,snapshots,paths)
            manifest=out/'replay_snapshots.json';before=manifest.read_bytes()
            self.assertTrue(entry.json.loads(before)['capture_complete'])
            with self.assertRaises(FileExistsError):entry.write_replay_manifest(out,snapshots,paths)
            self.assertEqual(manifest.read_bytes(),before)
            with self.assertRaises(FileExistsError):
                entry.record_replay_snapshot(out,[],[],dict(physics_step=0,requested_time_s=0.))

    def test_large_environment_counts_and_target_identity(self):
        policy,_=model()
        for count in (64,256,512,1024):
            settings=entry.build_settings(HERE.parent/'입력/A0',updates=250,num_envs=count,size='large')
            entry.validate_settings(settings)
            self.assertEqual(settings['num_envs'],count)
            with torch.no_grad():result=policy.act(*data(count))
            self.assertEqual(result['action'].shape,(count,39));self.assertTrue(torch.isfinite(result['logp']).all())
        _,_,row,_,_=entry.configuration(HERE.parent/'입력/A0')
        self.assertEqual([(t['string'],t['fret']) for t in row['compiled_targets']],[(2,5),(3,8)])

    def test_evaluation_policy_seed_mode_and_exception_restore(self):
        class FakePolicy:
            phase='J'
            def act(self,*inputs,deterministic):return dict(deterministic=deterministic,value=torch.rand(3))
        original=entry.runner._DeterministicPolicy
        for stochastic in (False,True):
            with patch.object(torch.cuda,'is_available',return_value=False):
                with entry.evaluation_policy(stochastic,17):
                    torch.manual_seed(999)  # trainer.load이 RNG를 복원한 상황 뒤 wrapper가 seed를 적용한다.
                    first=entry.runner._DeterministicPolicy(FakePolicy()).act()
                    torch.manual_seed(888)
                    second=entry.runner._DeterministicPolicy(FakePolicy()).act()
                    self.assertEqual(first['deterministic'],not stochastic)
                    torch.testing.assert_close(first['value'],second['value'],atol=0,rtol=0)
            self.assertIs(entry.runner._DeterministicPolicy,original)
        with self.assertRaises(RuntimeError):
            with entry.evaluation_policy(True,17):raise RuntimeError('복원 검사')
        self.assertIs(entry.runner._DeterministicPolicy,original)
        # 평가 wrapper는 checkpoint/정책 identity나 metadata 검증 경로를 교체하지 않는다.
        before=(entry.read_checkpoint,entry.validate_metadata,entry.ExperimentTrainer)
        with entry.evaluation_policy(True,17):self.assertEqual(before,(entry.read_checkpoint,entry.validate_metadata,entry.ExperimentTrainer))

    def test_evaluate_returns_original_report_and_records_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);checkpoint=root/'model.pt';checkpoint.write_bytes(b'fixture')
            result=({'completed':True,'lifecycle_verified':True},[{'valid':True}])
            args=SimpleNamespace(checkpoint=checkpoint,out=root/'evaluation',num_envs=2,stochastic=True,evaluation_seed=17)
            def fake_evaluate(*args,**kwargs):
                (root/'evaluation').mkdir();return result
            with patch.object(entry,'read_checkpoint') as strict,patch.object(entry.runner,'evaluate_checkpoint',side_effect=fake_evaluate):
                actual=entry.evaluate(args)
            self.assertIs(actual,result);strict.assert_called_once_with(checkpoint)
            document=entry.json.loads((args.out/'evaluation_mode.json').read_text())
            self.assertEqual(document['mode'],'stochastic');self.assertEqual(document['seed'],17)
            self.assertEqual(document['checkpoint_sha256'],entry.digest(checkpoint));self.assertTrue(document['completed'])

    def test_native_root_roundtrip(self):
        contract=load_gpu_prepared_reset_contract('left');rigid=entry.RigidGuitar(contract,'cpu')
        logical=torch.tensor(entry._body_row(contract['state']['guitar_body_states'][0]))
        torch.testing.assert_close(entry.logical_to_root(rigid,logical),rigid.prepared_root,atol=2e-7,rtol=0)

    def test_environment_progress_future_and_partial_reset(self):
        settings=entry.build_settings(HERE.parent/'입력/A0',updates=2,num_envs=2,size='small')
        config=settings['natural_press']
        class Environment(entry.ComplexEnvironment):pass
        Environment.config=config;Environment.measure=True
        metadata,snapshot=fixture(2)
        with entry.runtime():
            env=Environment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],skill=settings['finger_skill'],device='cpu')
        env.set_evaluation(True,full_song=True);obs=env.reset([0,1],snapshot)
        self.assertEqual(obs['state'].shape,(2,613))
        self.assertEqual(env.task.targets[1].finger,2)
        env.clock[:]=int(4.9*240);env._advance_finger_progress(env._score_time(),torch.tensor([True,True]))
        self.assertEqual(env.finger_progress['target'][0,1].item(),1)
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

    def test_reference_schema_and_sha(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.json';source.write_text('{}')
            config=dict(case_id='C1',geometry_sha256='catalog')
            value=dict(schema='guitar_learning.middle_s3f5_s4f8_reference.v1',case_id='C1',catalog_sha256='catalog',source_sha256={str(source):entry.digest(source)},candidate_valid=True,waypoints=[])
            path=root/'ref.json';path.write_text(entry.json.dumps(value))
            with patch.object(entry,'ROOT',root):
                document,paths=entry.load_reference(path,config);self.assertEqual(len(paths),2)
                source.write_text('changed')
                with self.assertRaises(ValueError):entry.load_reference(path,config)


    def test_lr_modes_initial_tensors_and_context_restore(self):
        torch.manual_seed(7);first,_=model(lr_mode='existing')
        torch.manual_seed(7);second,_=model(lr_mode='recover_floor')
        for key,value in first.state_dict().items():torch.testing.assert_close(value,second.state_dict()[key],atol=0,rtol=0)
        self.assertIs(entry.ExperimentTrainer._retry_actor_lr,entry.BaseDecisionTrainer._retry_actor_lr)
        original=entry.ppo_module.DecisionPPOTrainer
        with self.assertRaises(RuntimeError):
            with entry.runtime():
                self.assertIs(entry.ppo_module.DecisionPPOTrainer,entry.ExperimentTrainer)
                raise RuntimeError('복원 검사')
        self.assertIs(entry.ppo_module.DecisionPPOTrainer,original)

    def ppo_fixture(self,mode):
        from guitar_learning.tests.test_finger_decisions import TinyDecisionPolicy,FakeDecisionPool
        from guitar_learning.training.rollout import DecisionCollector
        torch.manual_seed(7);policy=TinyDecisionPolicy()
        policy.config={'lr_mode':mode,'target_fingers':[2,3]}
        policy.core=SimpleNamespace(support_log_std=torch.full((17,),-2.),finger_log_std=torch.full((16,),-1.))
        batch,_=DecisionCollector(policy,FakeDecisionPool()).collect(5)
        return policy,batch

    def test_existing_ppo_is_numerically_unchanged(self):
        from guitar_learning.tests.test_ppo import assert_tree
        policy,batch=self.ppo_fixture('existing');other=copy.deepcopy(policy)
        config=PPOConfig(epochs=1,target_kl=.1,actor_lr=7.5e-6)
        original=entry.BaseDecisionTrainer(policy,config);local=entry.ExperimentTrainer(other,config)
        torch.manual_seed(71);first=original.update(batch);rng=torch.get_rng_state()
        torch.manual_seed(71);second=local.update(batch)
        assert_tree(self,first,{k:second[k] for k in first})
        assert_tree(self,original.policy.state_dict(),local.policy.state_dict())
        assert_tree(self,original.actor_optimizer.state_dict(),local.actor_optimizer.state_dict())
        assert_tree(self,original.value_optimizer.state_dict(),local.value_optimizer.state_dict())
        self.assertTrue(torch.equal(rng,torch.get_rng_state()))
        self.assertFalse(second['lr_recovery']['recovered'])
        self.assertEqual(second['lr_recovery']['start_lr'],[7.5e-6])

    def test_update_entry_recovery_allows_retry_below_floor_and_rollback(self):
        from guitar_learning.tests.test_ppo import assert_tree
        policy,batch=self.ppo_fixture('recover_floor')
        trainer=entry.ExperimentTrainer(policy,PPOConfig(epochs=1,target_kl=.01,actor_lr=7.5e-6))
        calls=[]
        def kl(*args):
            calls.append(1);return torch.ones(10) if len(calls)==1 else torch.zeros(10)
        with patch.object(policy,'analytic_kl',side_effect=kl):result=trainer.update(batch)
        self.assertTrue(result['lr_recovery']['recovered'])
        self.assertEqual(set(result['lr_recovery']['actual_target_finger_latent_std']),{'middle','ring'})
        self.assertEqual(result['lr_recovery']['start_lr'],[entry.RECOVERY_FLOOR])
        self.assertEqual(result['kl_retries'],1)
        self.assertAlmostEqual(result['actor_lr'],entry.RECOVERY_FLOOR*.25)
        with patch.object(policy,'analytic_kl',return_value=torch.zeros(10)):next_result=trainer.update(batch)
        self.assertTrue(next_result['lr_recovery']['recovered'])
        self.assertEqual(next_result['lr_recovery']['start_lr'],[entry.RECOVERY_FLOOR])
        before=copy.deepcopy(policy.state_dict());actor=copy.deepcopy(trainer.actor_optimizer.state_dict())
        rng=torch.get_rng_state();updates=trainer.updates
        with patch.object(policy,'analytic_kl',return_value=torch.ones(10)):
            with self.assertRaises(KLGuardError):trainer.update(batch)
        assert_tree(self,before,policy.state_dict());assert_tree(self,actor,trainer.actor_optimizer.state_dict())
        self.assertEqual(trainer.updates,updates);self.assertTrue(torch.equal(rng,torch.get_rng_state()))



if __name__=='__main__':unittest.main()
