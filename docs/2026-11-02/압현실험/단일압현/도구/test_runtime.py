"""새18조합 계약·격리·100회 일정·엄격 Adam/RNG 복구의 CPU 검사."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import torch

spec=importlib.util.spec_from_file_location('single18_runtime',Path(__file__).with_name('runtime.py'))
runtime=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
from guitar_learning.tool.experiments import natural_press as natural
from guitar_learning.training import finger_skill_runner as runner, rollout, ppo
from guitar_learning.tests.test_gpu_environment import fixture
from guitar_learning.portability import portable, settings_digest, PATH_SCHEMA

BASE=Path(__file__).resolve().parents[1]/'입력/후보/index_s1_f1'


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def config(self):
        return runtime.configuration_runtime(BASE/'catalog.json',BASE/'provenance.json','index_s1_f1',unverified=True)

    def make(self,config,row):
        settings=runtime.build_settings(config,row)
        class Environment(natural.NaturalEnvironment):
            natural_press=config
            natural_preparation=dict(schema='guitar_learning.natural_preparation.v3',condition='E4')
        metadata,snapshot=fixture(2)
        env=Environment(metadata,bundle=Path(row['bundle']),song=settings['song'],skill=settings['finger_skill'],device='cpu',hand='left')
        env.reset([0,1],snapshot)
        policy=natural.NaturalPolicy(601,size='small',contract=env.contract,natural_press=config)
        return settings,policy

    def test_unverified_rejected_and_new_fixed_contract(self):
        with self.assertRaises(ValueError):
            runtime.inputs(BASE/'catalog.json',BASE/'provenance.json','index_s1_f1')
        with self.config() as (config,row):
            settings=runtime.build_settings(config,row)
            self.assertEqual(config['schema'],runtime.SCHEMA)
            self.assertEqual(config['active_axes'],[17,18,19,20])
            self.assertEqual(config['condition'],'E4')
            self.assertEqual(settings['checkpoint_every'],10)
            self.assertEqual(settings['finger_skill']['planned_transitions'],100*64*32)
            self.assertEqual(settings['song_training']['target_count'],1)
            self.assertEqual(settings['song_training']['episode_duration_s'],5.)
            bad=copy.deepcopy(config);bad['finger_std_floor']=0.
            with self.assertRaises(ValueError):natural.validate_config(bad)

    def test_context_restores_on_exception(self):
        original=(natural.load_configuration,natural.verify_catalog,natural.SCHEMA,natural.NaturalPolicy.schema,
            runner._policy,rollout.GpuPool,ppo.DecisionPPOTrainer,runner._pins)
        with self.assertRaisesRegex(RuntimeError,'intentional'):
            with self.config() as (config,row):
                with runtime.experiment_runtime(config):
                    raise RuntimeError('intentional')
        self.assertEqual(original,(natural.load_configuration,natural.verify_catalog,natural.SCHEMA,natural.NaturalPolicy.schema,
            runner._policy,rollout.GpuPool,ppo.DecisionPPOTrainer,runner._pins))

    def test_fresh_policy_and_strict_adam_rng_resume(self):
        with self.config() as (config,row):
            settings,policy=self.make(config,row)
            self.assertEqual(policy.architecture['schema'],runtime.POLICY_SCHEMA)
            self.assertEqual(policy.active_mask.nonzero().flatten().tolist(),[17,18,19,20])
            trainer=natural.NaturalTrainer(policy,ppo.PPOConfig(**settings['ppo']))
            for optimizer,parameters in ((trainer.actor_optimizer,policy.actor_parameters()),(trainer.value_optimizer,policy.value_parameters())):
                optimizer.zero_grad()
                sum(p.square().sum()*1e-7 for p in parameters).backward()
                optimizer.step()
            trainer.updates=25
            trainer.actor_optimizer.param_groups[0]['lr']=1.2e-5
            trainer.actor_optimizer.param_groups[0]['natural_press_stable_updates']=9
            metadata=dict(schema=runner.RESUME_SCHEMA,settings=portable(settings),settings_sha256=settings_digest(settings),
                input_contract=dict(schema=PATH_SCHEMA,required={},lineage=[],run_settings=None))
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'resume.pt';trainer.save(path,metadata=metadata)
                saved=torch.load(path,map_location='cpu',weights_only=False)
                _,policy2=self.make(config,row)
                restored=natural.NaturalTrainer(policy2,ppo.PPOConfig(**settings['ppo']))
                restored.load(path)
                self.assertEqual(restored.updates,25)
                self.assertTrue(torch.equal(torch.get_rng_state(),saved['torch_rng']))
                for name in ('actor_optimizer','value_optimizer'):
                    expected=saved[name];actual=getattr(restored,name).state_dict()
                    self.assertEqual(actual['param_groups'],expected['param_groups'])
                    for key,values in expected['state'].items():
                        for field,value in values.items():self.assertTrue(torch.equal(value,actual['state'][key][field]))
                saved['identity']['architecture']['schema']='guitar_learning.natural_press_policy.v3'
                torch.save(saved,path)
                with self.assertRaises(ValueError):restored.load(path)

    def test_native_snapshot_global_middle_sample_and_all_fields(self):
        from types import SimpleNamespace
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        from guitar_learning.gpu.scene import _body_row
        from guitar_learning.gpu.contact import load_fingertip_pad
        contract=load_gpu_prepared_reset_contract('left')
        state=contract['state'];initial=contract['initial'];human=initial['human_body_names']
        names=['human/'+name for name in human]+['guitar/'+name for name in initial['guitar_body_names']]+['chair/box']
        body=torch.tensor([[_body_row(r) for kind in ('human','guitar','chair') for r in state[kind+'_body_states']]],dtype=torch.float32)
        q=torch.tensor([[r['pos'] for r in state['human_dof_states']]],dtype=torch.float32)
        snapshot=dict(q=q,qd=torch.zeros_like(q),target=q.clone(),body_state=body,
            contact_force=torch.zeros(1,len(names),3),physics_step=torch.tensor([4]))
        pad=load_fingertip_pad();guitar=body[:,len(human)]
        env=SimpleNamespace(body=body,pad_indices=torch.tensor([human.index('LH:'+f+'3') for f in natural.FINGERS]),
            pad_local=torch.tensor(pad['points_local']),pad_normals=torch.tensor(pad['normals_local']),
            guitar_q=guitar[:,3:7],guitar_body=guitar,finger=torch.tensor([2]),surface_sample=torch.tensor([[154]]),
            pad_valid=torch.tensor(pad['valid']),surface_delta=torch.zeros(1,1,3),surface_height=torch.ones(1,1)*.01,
            surface_alignment=torch.ones(1,1),press_plane=torch.tensor([0.,0.,1.,0.]),goals=torch.zeros(1,1,3),
            finger_indices=torch.tensor([human.index('LH:'+finger+str(segment)) for finger in ('thumb',)+natural.FINGERS for segment in (2,3)]),
            wrong_source_flags=torch.zeros(1,1,10,3,dtype=torch.bool),
            wrong_source_fret_min=torch.zeros(1,1,10,dtype=torch.int16),wrong_source_fret_max=torch.zeros(1,1,10,dtype=torch.int16))
        scene=SimpleNamespace(names=initial['joint_names'],human_bodies=human,body_names=names,
            snapshot=lambda:snapshot,_bodies=body)
        row=dict(q105=q[0].tolist(),hold_target105=q[0].tolist())
        result=runtime.probe_snapshot(SimpleNamespace(scene=scene,environment=env),row,1)
        self.assertEqual(result['pad']['selected_sample'],26)
        self.assertEqual(result['pad']['selected_global_sample'],154)
        self.assertEqual(result['pad']['selected_finger_zero_based'],1)
        self.assertEqual(len(result['cpu_vs_native_body']),len(human))
        self.assertEqual(result['physics_step'],4)
        json.dumps(result,allow_nan=False)

    def test_summary_preserves_failures_and_full_vs_ninety_hold(self):
        from guitar_learning.training.training_log_io import EpisodeWriter
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            writer=EpisodeWriter(out)
            for i in range(2):
                row=dict(env_id=i,worker_id=i,reason='terminal_failure' if i else 'timeline_complete',steps=300,
                    valid=True,termination=dict(physical_failure=bool(i),wrist_failure=False),
                    left_note_ledger=dict(schema='one',target_ids=['target'],
                        values=dict(left=[True],contact_done=[True],clean=[1.4],wrong=[0.])))
                writer.append(row,0,0)
            writer.close()
            runtime.write(out/'report.json',dict(completed=True,lifecycle_verified=True,
                failed_episodes_in_denominator=True,first_episode_per_env_per_batch=True,episodes=2))
            result=runtime.summarize(out,1.5,2)
            self.assertEqual(result['achievement'],1)
            self.assertEqual(result['physical'],1)
            self.assertEqual(result['entire_hold'],0)
            self.assertEqual(result['hold90'],1)
            with self.assertRaises(ValueError):runtime.summarize(out,1.5,3)

    def test_identity_ignores_only_validation_flags(self):
        row={'song':'one','q105':[1.],'native_verified':False}
        expected=runtime.row_identity(row)
        row.update(native_verified=True,native_validation={'path':'report'})
        self.assertEqual(expected,runtime.row_identity(row))
        row['q105']=[2.]
        self.assertNotEqual(expected,runtime.row_identity(row))


if __name__=='__main__':unittest.main()
