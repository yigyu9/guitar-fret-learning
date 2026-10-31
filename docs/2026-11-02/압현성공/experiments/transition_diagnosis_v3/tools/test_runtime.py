"""AB 범위·현재 목표·관찰 원장·정책 신원과 공식 factory 복원 CPU 검사."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())))
import torch
from guitar_learning.tests.test_gpu_environment import fixture
from guitar_learning.training import finger_skill_runner as runner,rollout,ppo
from guitar_learning.portability import portable,settings_digest,PATH_SCHEMA

spec=importlib.util.spec_from_file_location('transition_runtime',Path(__file__).with_name('runtime.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def make(condition='E4'):
    settings=r.build_settings(condition,size='small')
    class Environment(r.TransitionEnvironment):
        transition=settings['transition']
        natural_press=settings['natural_press']
        natural_preparation=dict(schema='guitar_learning.natural_preparation.v3',condition=condition)
    metadata,snapshot=fixture(2)
    env=Environment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],
        skill=settings['finger_skill'],hand='left',device='cpu')
    env.reset([0,1],snapshot)
    return settings,env,snapshot


def policy(settings,env):
    return r.TransitionPolicy(601,size='small',contract=env.contract,
        natural_press=settings['natural_press'],transition=settings['transition'])


@unittest.skipUnless((r.ROOT/'data/song_bundles'/r.SONG/'manifest.json').is_file(),'학습 gap 확정 뒤 bundle 생성 필요')
class TransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def test_sequence_full_scope_and_partial_reset(self):
        settings,env,snapshot=make()
        self.assertEqual([t.fret for t in env.task.targets],[6,7])
        self.assertEqual(len({t.target_id for t in env.task.targets}),2)
        self.assertEqual(env.duration_ticks.tolist(),[round(settings['transition']['duration_s']*60)]*2)
        self.assertTrue(env.focus_mask.all());self.assertFalse(env.evaluation)
        self.assertEqual(env.observation()['state'].shape,(2,601))
        env.phase_target.fill_(1);env.first_contact_s.fill_(7.1)
        env._reset_scope(torch.tensor([0]))
        self.assertEqual(env.phase_target.tolist(),[-1,1])
        self.assertEqual(env.first_contact_s[:,0].tolist(),[-1.,7.1])
        self.assertFalse(env.evaluation)
        bad=copy.deepcopy(settings);bad['transition']['schedule'][0]['fret']=7
        with self.assertRaises(ValueError):r.validate(bad)

    def test_current_target_priority_readiness_and_switch_reset(self):
        _,env,_=make()
        for seconds,index in ((3.5,0),(4.6,1),(5.5,1)):
            env.clock.fill_(round(seconds*240))
            selected,valid=env.selected_target()
            self.assertTrue(valid.all());self.assertEqual(selected.tolist(),[index,index])
        env.clock.fill_(1104)  # 4.6초: 목표1을 보고 목표0의 나쁜 기하는 무시한다.
        env.surface_delta.fill_(1);env.surface_delta[:,1]=0
        env.surface_height.fill_(-1);env.surface_height[:,1]=.006
        env.surface_alignment.fill_(-1);env.surface_alignment[:,1]=1
        env.guide['delta'].zero_();self.assertTrue(env.readiness().all())
        env.phase_target.fill_(0);env.motion_phase.fill_(2);env.ready_timers.fill_(1)
        env.candidate.zero_();env.last_phase_time.copy_(env._local_time())
        q=env.snapshot['q'].clone();target=env.snapshot['target'].clone()
        env._advance_phase()
        self.assertEqual(env.phase_target.tolist(),[1,1]);self.assertEqual(env.motion_phase.tolist(),[0,0])
        self.assertTrue((env.ready_timers==0).all())
        self.assertTrue(torch.equal(q,env.snapshot['q']));self.assertTrue(torch.equal(target,env.snapshot['target']))

    def test_distribution_permissions_and_identity(self):
        settings,env,_=make();model=policy(settings,env)
        self.assertEqual(model.architecture['schema'],r.TransitionPolicy.schema)
        self.assertEqual(model._active_mask().nonzero().flatten().tolist(),list(range(12))+list(range(21,25)))
        self.assertTrue(model.core.support_head.weight.requires_grad)
        self.assertTrue(model.core.finger_heads['middle'][-1].weight.requires_grad)
        self.assertFalse(model.core.finger_heads['index'][-1].weight.requires_grad)
        for phase in (0,1,2):
            env.motion_phase.fill_(phase);obs=env.observation()
            result=model.act(*(obs[k] for k in rollout.FIELDS),deterministic=False)
            self.assertTrue(torch.isfinite(result['logp']).all())
            self.assertTrue(torch.equal(result['action'],result['latent'].tanh()))
            self.assertTrue(torch.allclose(result['log_std'][:,21:25].exp(),torch.full((2,4),.15)))
        bad=copy.deepcopy(settings['transition']);bad['sequence_sha256']='wrong'
        with self.assertRaises(ValueError):r.TransitionPolicy(601,size='small',contract=env.contract,
            natural_press=settings['natural_press'],transition=bad)

    def test_timestamp_observer_and_per_episode_nulls(self):
        _,env,_=make();env.clock.fill_(720)
        def native(self,snapshot):
            self.clock+=1;self.candidate.zero_();self.wrong.zero_()
            self.candidate[:,0]=True;self.candidate[:,1]=True  # 목표1은 아직 발음 전이다.
            self.wrong[1,0]=True;self.note['left'][0,0]=True
        with patch.object(r.FingerSkillEnvironment,'substep',native):
            env.substep({});env.substep({})
        self.assertAlmostEqual(env.first_contact_s[0,0].item(),721/240)
        self.assertEqual(env.first_contact_s[1,0].item(),-1)
        self.assertEqual(env.first_contact_s[0,1].item(),-1)
        self.assertAlmostEqual(env.first_achievement_s[0,0].item(),721/240)
        with patch.object(r.natural.NaturalEnvironment,'_episode',return_value={}):row=env._episode(0,False)
        self.assertEqual(row['transition_diagnostics']['target_ids'],[t.target_id for t in env.task.targets])
        self.assertEqual(row['transition_diagnostics']['first_contact_s'][1:], [None])

    def test_trace_separates_repeated_cells_and_arm_joint_axes(self):
        _,env,_=make();env.action=torch.zeros(2,39)
        trace=env.natural_preparation_trace()['transition']
        self.assertEqual(len(trace['goals']),2)
        self.assertNotEqual(trace['goals'][0]['target_id'],trace['goals'][1]['target_id'])
        self.assertNotEqual(trace['goals'][0]['fret'],trace['goals'][1]['fret'])
        for key in ('arm_actual_rad','arm_requested_rad','arm_applied_rad'):self.assertEqual(len(trace[key]),12)
        self.assertEqual(trace['arm_actual_rad'],env.snapshot['q'][0,env.transition_arm_indices].tolist())
        self.assertEqual(len(trace['wrist_error_m']),3)

    def test_factory_restores_and_pins_live_inputs(self):
        settings,_,_=make()
        original=(runner._policy,rollout.GpuPool,ppo.DecisionPPOTrainer,runner._pins,runner.checkpoint_metadata)
        with patch.object(runner,'_pins',lambda current,out,extra:extra):
            for error in (False,True):
                try:
                    with r.transition_runtime(settings):
                        self.assertIs(rollout.GpuPool,r.TransitionPool)
                        paths=runner._pins(settings,Path('/tmp/unused'))
                        self.assertIn(Path(r.__file__).resolve(),paths)
                        self.assertIn(r.ROOT/'data/song_bundles'/r.SONG/'mapping/fingering.json',paths)
                        if error:raise RuntimeError('복구 검사')
                except RuntimeError:pass
                self.assertIs(rollout.GpuPool,original[1]);self.assertIs(runner._policy,original[0])
        self.assertEqual(original,(runner._policy,rollout.GpuPool,ppo.DecisionPPOTrainer,runner._pins,runner.checkpoint_metadata))

    def test_strict_resume_optimizer_rng_and_sequence_rejection(self):
        settings,env,_=make();model=policy(settings,env)
        trainer=r.natural.NaturalTrainer(model,ppo.PPOConfig(**settings['ppo']))
        for optimizer,parameters in ((trainer.actor_optimizer,model.actor_parameters()),(trainer.value_optimizer,model.value_parameters())):
            optimizer.zero_grad();sum(p.square().sum()*1e-7 for p in parameters).backward();optimizer.step()
        trainer.updates=1
        metadata=dict(schema=runner.RESUME_SCHEMA,settings=portable(settings),settings_sha256=settings_digest(settings),
            input_contract=dict(schema=PATH_SCHEMA,required={},lineage=[],run_settings=None))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'resume.pt';trainer.save(path,metadata=metadata)
            saved=torch.load(path,map_location='cpu',weights_only=False)
            restored=r.natural.NaturalTrainer(policy(settings,env),ppo.PPOConfig(**settings['ppo']));restored.load(path)
            self.assertEqual(restored.updates,1);self.assertTrue(torch.equal(torch.get_rng_state(),saved['torch_rng']))
            for name in ('actor_optimizer','value_optimizer'):
                actual=getattr(restored,name).state_dict();self.assertEqual(actual['param_groups'],saved[name]['param_groups'])
                for key,fields in saved[name]['state'].items():
                    for field,value in fields.items():self.assertTrue(torch.equal(value,actual['state'][key][field]))
            saved['identity']['architecture']['transition']['sequence_sha256']='wrong';torch.save(saved,path)
            with self.assertRaises(ValueError):restored.load(path)


class ScheduleTests(unittest.TestCase):
    def test_gaps(self):
        self.assertEqual(r.task_times(.5),((3.,4.5),(5.,6.5)))
        self.assertEqual(r.task_times(.75)[1],(5.25,6.75))
        self.assertEqual(r.task_times(1.)[1],(5.5,7.))
        with self.assertRaises(ValueError):r.task_times(.1)

class DiagnosisTests(unittest.TestCase):
    def test_horizon_and_thumb_axes_are_explicit(self):
        for horizon in (32,128):
            settings=r.build_settings(horizon=horizon,thumb_active=True,size='small')
            r.validate(settings)
            self.assertEqual(settings['horizon'],horizon)
            self.assertEqual(settings['natural_press']['active_axes'],list(range(17))+list(range(21,25)))
        with self.assertRaises(ValueError):r.build_settings(horizon=64)

    def test_eval_scale_and_gauss_hermite(self):
        settings,env,_=make();model=policy(settings,env)
        obs=env.observation();inputs=tuple(obs[k] for k in rollout.FIELDS)
        deterministic=model.act(*inputs,deterministic=True)
        zero=r.evaluation_action(model,inputs,'sampled',0.)
        self.assertTrue(torch.equal(zero['action'],deterministic['action']))
        result=model(*inputs)
        fine,angles=r.expected_requested_action(model,result['mean'],result['log_std'],nodes=32)
        coarse,coarse_angles=r.expected_requested_action(model,result['mean'],result['log_std'],nodes=16)
        self.assertTrue(torch.isfinite(fine).all())
        self.assertTrue((fine.abs()<=1).all())
        active=model._active_mask()
        self.assertTrue(torch.equal(fine[:,~active],result['mean'][:,~active].tanh()))
        self.assertLess((angles[:,active]-coarse_angles[:,active]).abs().max().item(),.002)
        evaluated=r.evaluation_action(model,inputs,'expected-angle',1.)
        self.assertEqual(model.expected_angle_calls,1)
        self.assertTrue(torch.isfinite(evaluated['logp']).all())

if __name__=='__main__':unittest.main()
