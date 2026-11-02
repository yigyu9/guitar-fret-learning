"""곡 진행 상태 정책·checkpoint·factory 연결을 CPU에서 검증한다.

합성 snapshot은 실제 압현 가능성이나 GPU 물리 성공을 증명하지 않는다.
"""
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch
from torch.distributions import Normal,kl_divergence

from guitar_learning.tool.experiments import song_finger_progress as entry
from guitar_learning.gpu.finger_progress import (
    FingerProgressEnvironment,progress_contract,allocate_progress,advance_progress,reset_progress,
)
from guitar_learning.tests.test_finger_skill_policy import contract as base_contract
from guitar_learning.tests.test_gpu_environment import fixture,SONG,BUNDLE
from guitar_learning.training.ppo import DecisionPPOTrainer
from guitar_learning.training.policy import FingerSkillPolicy


def contract():
    value=base_contract();spec=progress_contract(67)
    value['observation']['fields']+=spec['fields'];value['observation']['scales']+=spec['scales']
    value['observation']['dimension']+=spec['dimension'];value['finger_progress']=spec
    return value


def inputs(count=2):
    return (torch.randn(count,entry.STATE_DIM),torch.randn(count,7,24),torch.ones(count,7,dtype=torch.bool),
        torch.randn(count,8,24),torch.ones(count,8,dtype=torch.bool))


def policy():return entry.SongFingerProgressPolicy(entry.STATE_DIM,size='small',contract=contract())


class SongFingerProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def test_new_policy_density_shapes_and_finite_full_joint_actions(self):
        model=policy();data=inputs();result=model.act(*data)
        self.assertEqual(entry.STATE_DIM,613)
        self.assertEqual(int(model._active_mask().sum()),33)
        self.assertEqual(result['action'].shape,(2,39))
        self.assertTrue((result['action'][:,33:]==0).all())
        self.assertTrue(all(torch.isfinite(value).all() for value in result.values()))
        evaluated=model.evaluate(*data,result['latent'])
        torch.testing.assert_close(result['logp'],evaluated['logp'])
        distribution=Normal(result['mean'][:,:33],result['log_std'][:,:33].exp())
        torch.testing.assert_close(evaluated['entropy'],distribution.entropy().sum(-1))
        shifted=result['mean']+.02
        torch.testing.assert_close(model.analytic_kl(result['mean'],result['log_std'],shifted,result['log_std']),
            kl_divergence(distribution,Normal(shifted[:,:33],result['log_std'][:,:33].exp())).sum(-1))
        bad=list(data);bad[0]=torch.zeros(2,557)
        with self.assertRaises(ValueError):model(*bad)
        bad[0]=torch.zeros(2,613);bad[0][0,-1]=float('nan')
        with self.assertRaises(ValueError):model(*bad)

    def test_progress_branches_affect_outputs_and_actor_critic_are_separate(self):
        model=policy();data=list(inputs());data[0][:,557:]=0
        # 초기 0 출력은 기본 정책과 같지만, 학습 가능한 추가 상태 경로가 실제로 연결된다.
        with torch.no_grad():
            model.support_progress[-1].weight.fill_(.03)
            model.finger_progress['index'][-1].weight.fill_(.03)
            model.value_progress[-1].weight.fill_(.03)
        before=model(*data);data[0][:,557:571]=1;after=model(*data)
        self.assertFalse(torch.equal(before['mean'][:,:17],after['mean'][:,:17]))
        self.assertFalse(torch.equal(before['mean'][:,17:21],after['mean'][:,17:21]))
        torch.testing.assert_close(before['mean'][:,21:33],after['mean'][:,21:33])
        self.assertFalse(torch.equal(before['reward_value'],after['reward_value']))
        actor={id(p) for p in model.actor_parameters()};critic={id(p) for p in model.value_parameters()}
        self.assertFalse(actor&critic)
        result=model.act(*data);loss=result['mean'][:,:33].sum();loss.backward()
        for branch in model.finger_progress.values():
            self.assertTrue(torch.isfinite(branch[-1].bias.grad).all())
            self.assertTrue((branch[-1].bias.grad!=0).all())

    def test_strict_roundtrip_and_legacy_models_rejected_without_weight_changes(self):
        model=policy();trainer=DecisionPPOTrainer(model)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'new.pt';trainer.save(path,metadata={'test':True})
            restored=policy();DecisionPPOTrainer(restored).load(path)
            for key,value in model.state_dict().items():torch.testing.assert_close(value,restored.state_dict()[key],rtol=0,atol=0)
            before=copy.deepcopy(restored.state_dict())
            legacy=FingerSkillPolicy(557,size='small',contract=base_contract())
            old=Path(folder)/'old.pt';DecisionPPOTrainer(legacy).save(old)
            with self.assertRaisesRegex(ValueError,'architecture'):DecisionPPOTrainer(restored).load(old)
            for key,value in before.items():torch.testing.assert_close(value,restored.state_dict()[key],rtol=0,atol=0)
            with self.assertRaises(RuntimeError):restored.load_state_dict(legacy.state_dict(),strict=True)
            with self.assertRaises(ValueError):entry.read_checkpoint(old)
        for schema in ('guitar_learning.finger_skill_resume.v4','guitar_learning.single18.transported_learning.v1'):
            with self.assertRaises(ValueError):entry.validate_metadata(dict(schema=schema,settings={}))

    def test_checkpoint_reader_verifies_real_source_pins_and_settings_snapshot(self):
        from guitar_learning.portability import checkpoint_inputs,portable,settings_digest,ROOT
        from guitar_learning.training.training_log_io import digest,write
        settings=entry.build_settings(updates=2,num_envs=2,size='small')
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as folder:
            folder=Path(folder);source=folder/'probe.txt';source.write_text('original')
            settings_path=folder/'settings.json';write(settings_path,portable(settings))
            metadata=dict(schema=entry.RESUME_SCHEMA,settings=portable(settings),settings_sha256=settings_digest(settings),
                input_contract=checkpoint_inputs({str(source):digest(source),str(settings_path):digest(settings_path)},
                    settings,settings_path=settings_path))
            checkpoint=folder/'new.pt';trainer=DecisionPPOTrainer(policy());trainer.save(checkpoint,metadata=metadata)
            self.assertEqual(entry.read_checkpoint(checkpoint),settings)
            source.write_text('changed')
            with self.assertRaisesRegex(ValueError,'input sources changed'):entry.read_checkpoint(checkpoint)

    def test_runtime_restores_factories_on_exception_and_settings_keep_base_schedule(self):
        from guitar_learning.training import rollout,finger_skill_runner as runner
        before=(rollout.GpuPool,runner._policy,runner.resume_schema,runner._validate_metadata_schema,runner._pins,runner.SCHEMA)
        with self.assertRaisesRegex(RuntimeError,'deliberate'):
            with entry.runtime():
                self.assertIsNot(rollout.GpuPool,before[0]);self.assertEqual(runner.SCHEMA,entry.SCHEMA)
                raise RuntimeError('deliberate')
        self.assertEqual(before,(rollout.GpuPool,runner._policy,runner.resume_schema,runner._validate_metadata_schema,runner._pins,runner.SCHEMA))
        settings=entry.build_settings(updates=4,num_envs=2,size='small')
        self.assertEqual(settings['song_training']['observation_dimension'],613)
        self.assertEqual(settings['finger_skill']['planned_transitions'],4*2*32)
        self.assertNotIn('natural_press',settings)
        self.assertEqual(settings['song']['finger_action_mode'],'position')
        entry.validate_settings(settings)

    def test_new_environment_partial_reset_and_four_simultaneous_fingers(self):
        metadata,snapshot=fixture(2)
        env=FingerProgressEnvironment(metadata,bundle=BUNDLE,song=SONG,device='cpu',
            skill=dict(schema='guitar_learning.finger_skill.v3',phase='J',scope='scheduled',hold_ticks=1,
                exploration='independent',planned_transitions=400,full_song_after=100))
        env.set_evaluation(True,full_song=True);observation=env.reset([0,1],snapshot)
        self.assertEqual(observation['state'].shape,(2,613))
        self.assertTrue(torch.isfinite(observation['state']).all())
        env.finger_progress['target_elapsed'][1]=torch.tensor([1.,2.,3.,4.],dtype=torch.float64)
        before={key:value[1].clone() for key,value in env.finger_progress.items()}
        env.reset([0],snapshot)
        for key,value in before.items():torch.testing.assert_close(env.finger_progress[key][1],value,rtol=0,atol=0)
        state=allocate_progress(2);onset=torch.ones(4,dtype=torch.float64);end=onset+1;press=onset-.5
        result=advance_progress(state,now=torch.full((2,),1.1,dtype=torch.float64),onset=onset,end=end,press=press,
            finger=torch.tensor([1,2,3,4]),scope=torch.ones(2,4,dtype=torch.bool),ready=torch.ones(2,4,dtype=torch.bool),
            candidate=torch.ones(2,4,dtype=torch.bool),wrong=torch.zeros(2,4,dtype=torch.bool))
        self.assertTrue(torch.equal(result['target'],torch.tensor([[0,1,2,3],[0,1,2,3]])))
        self.assertTrue((result['phase']==4).all())
        frozen=result['target_elapsed'][1].clone();reset_progress(result,torch.tensor([0]),torch.zeros(2,dtype=torch.float64))
        torch.testing.assert_close(result['target_elapsed'][1],frozen)


if __name__=='__main__':unittest.main()
