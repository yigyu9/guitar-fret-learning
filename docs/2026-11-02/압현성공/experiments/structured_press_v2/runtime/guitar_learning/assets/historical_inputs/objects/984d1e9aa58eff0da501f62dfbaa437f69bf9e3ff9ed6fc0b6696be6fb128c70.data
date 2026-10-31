"""CPU evaluator lifecycle with fake recorded rows; no native dynamics claim."""
import copy
from contextlib import ExitStack
import gzip
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
import torch
from guitar_learning.imitation.imitation import dataset_manifest
from guitar_learning.imitation import imitation_io
from guitar_learning.training import monitoring, ppo
from guitar_learning.tool.experiments.joint import environment, policy, transfer, worker
from guitar_learning.tool.experiments.joint.evaluate import evaluate
from guitar_learning.tool.experiments.joint.proofs import validate_preflight
from guitar_learning.runtime.persistent_session import PersistentHeadlessPreparedSession


class RecordedEvaluation:
    """A minimal replay of the evaluator's public environment/scene contract."""
    def __init__(self, *, step_error=False, close_error=False):
        self.contract=dict(schema='guitar_learning.training.v1',observation=dict(dimension=1132))
        self.task=SimpleNamespace(duration_s=7.)
        self.scene=SimpleNamespace(human_root_fixed=True,guitar_root_fixed=False,
            guitar_gravity_disabled=False,pd_properties=np.array([1.,2.]),forbidden_calls=[])
        self.control=SimpleNamespace(session=SimpleNamespace(scene=self.scene),original_properties=np.array([1.,2.]))
        self.step_error,self.close_error=step_error,close_error
        self.close_calls=self.steps=0
    @staticmethod
    def observation():
        return dict(state=np.zeros(1132,np.float32),events=np.zeros((64,24),np.float32),
            mask=np.zeros(64,bool),priority_events=np.zeros((2,24),np.float32),priority_mask=np.zeros(2,bool))
    def reset(self):
        self.steps=0
        return self.observation(),dict(training_contract=copy.deepcopy(self.contract))
    def step(self,action):
        if self.step_error:raise ValueError('primary recorded step error')
        if np.asarray(action).shape != (39,):raise ValueError('action39 required')
        self.steps+=1;done=self.steps==420
        hand=dict(stage_success=False,provisional_success=False)
        quality=dict(role='joint',stage_success=False,left=dict(hand),right=dict(hand))
        joint=dict(safety_invalidated=False,coupled_hit_count=0,stage_success=False)
        info=dict(musical_quality=quality,joint=joint,physics_measurements=[dict(physics_step=self.steps*4)],
            native_control=dict(physics_samples240=[dict(native=dict(physics_step=self.steps*4))]))
        if done:info['episode']=dict(valid=True,reason='timeline_complete',steps=self.steps,task_time_s=7.,
            joint=copy.deepcopy(joint),musical_quality=copy.deepcopy(quality))
        return self.observation(),0.,done,False,info
    def close(self):
        self.close_calls+=1
        if self.close_error:raise RuntimeError('recorded close error')


class RecordedPolicy:
    def __init__(self,state_dim,*,size,contract):
        self.architecture=dict(contract=copy.deepcopy(contract))
    def to(self,device):return self
    def eval(self):return self
    def act(self,*inputs,deterministic):
        if deterministic is not True:raise AssertionError('deterministic preflight required')
        return dict(action=torch.zeros((1,39)))


class JointEvaluateTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.root=Path(self.folder.name)
        self.source=self.root/'expert.pt';self.source.write_bytes(b'expert')
        self.settings_path=self.root/'settings.json';self.settings_path.write_text('{}')
        self.settings=dict(seed=7,size='medium',device='cpu',timing=dict(pre_roll_s=3.,stage_index=1),
            stage='B',start_event_index=0,phrase_events=8,tempo_scale=1.,music={},ppo={})
        self.experts=dataset_manifest([self.source])
    def tearDown(self):self.folder.cleanup()
    def harness(self,env,*,run=None,extra=None):
        stack=ExitStack();self.addCleanup(stack.close)
        stack.enter_context(patch.dict('sys.modules',{'isaacgym':SimpleNamespace()}))
        def build(config,out,**kwargs):
            self.assertIs(kwargs['session_factory'],PersistentHeadlessPreparedSession)
            self.assertTrue(callable(getattr(kwargs['session_factory'],'reset_episode',None)))
            return env
        stack.enter_context(patch('guitar_learning.tool.experiments.joint.environment.build_environment',side_effect=build))
        stack.enter_context(patch('guitar_learning.tool.experiments.joint.policy.JointPolicy',RecordedPolicy))
        stack.enter_context(patch('guitar_learning.tool.experiments.joint.transfer.validate_experts',return_value=dict(source_pins=self.experts)))
        stack.enter_context(patch('guitar_learning.tool.experiments.joint.transfer.apply_experts',return_value=dict(source_pins=self.experts)))
        stack.enter_context(patch('guitar_learning.tool.experiments.joint.worker.compact',side_effect=lambda env,info,action:copy.deepcopy(info)))
        stack.enter_context(patch('guitar_learning.imitation.imitation_io.pin_inputs',side_effect=lambda paths:dataset_manifest(paths)))
        stack.enter_context(patch('guitar_learning.training.monitoring.available_memory_bytes',return_value=16*1024**3))
        if extra:extra(stack)
        return SimpleNamespace(out=self.root/'evaluation',settings=self.settings_path,run=run,episodes=1)

    def test_complete_safe_musical_failure_still_issues_valid_preflight_and_closes_once(self):
        env=RecordedEvaluation();args=self.harness(env)
        result=evaluate(self.settings,args)
        self.assertTrue(result['completed']);self.assertTrue(result['physical_flags_ok'])
        self.assertEqual(result['joint_successful_episodes'],0)
        self.assertEqual(env.close_calls,1);self.assertEqual(env.steps,420)
        gate=json.loads((args.out/'preflight_gate.json').read_text())
        self.assertTrue(gate['passed'])
        proof=validate_preflight(dict(self.settings,joint=dict(preflight_gate=str(args.out/'preflight_gate.json'))))
        self.assertIn(str(self.source),proof['pins'])
        with gzip.open(args.out/'transitions.jsonl.gz','rt') as trace:rows=[json.loads(line) for line in trace]
        self.assertEqual(len(rows),420);self.assertEqual(rows[-1]['native_last_sample']['physics_step'],1680)

    def test_primary_step_error_preserved_when_cleanup_also_fails(self):
        env=RecordedEvaluation(step_error=True,close_error=True);args=self.harness(env)
        with self.assertRaisesRegex(ValueError,'primary recorded step error'):evaluate(self.settings,args)
        self.assertEqual(env.close_calls,1)
        result=json.loads((args.out/'result.json').read_text())
        self.assertFalse(result['completed'])
        self.assertEqual(result['failure']['type'],'ValueError')
        self.assertEqual(result['cleanup_error']['message'],'recorded close error')
        self.assertFalse(json.loads((args.out/'preflight_gate.json').read_text())['passed'])

    def test_close_error_invalidates_otherwise_complete_safe_preflight(self):
        env=RecordedEvaluation(close_error=True);args=self.harness(env)
        with self.assertRaisesRegex(RuntimeError,'recorded close error'):evaluate(self.settings,args)
        result=json.loads((args.out/'result.json').read_text())
        self.assertFalse(result['completed']);self.assertIsNone(result['failure'])
        self.assertEqual(len(result['episodes']),1);self.assertEqual(env.close_calls,1)
        self.assertFalse(json.loads((args.out/'preflight_gate.json').read_text())['passed'])

    def test_low_starting_memory_prevents_environment_creation_and_records_failure(self):
        env=RecordedEvaluation();args=self.harness(env)
        with patch('guitar_learning.training.monitoring.available_memory_bytes',return_value=7*1024**3), \
                patch('guitar_learning.tool.experiments.joint.environment.build_environment') as build:
            with self.assertRaisesRegex(monitoring.LowMemoryError,'available memory below 8.0'):
                evaluate(self.settings,args)
        build.assert_not_called();self.assertEqual(env.close_calls,0)
        result=json.loads((args.out/'result.json').read_text())
        self.assertFalse(result['completed']);self.assertFalse(result['physical_flags_ok'])
        self.assertEqual(result['failure']['type'],'LowMemoryError')
        self.assertFalse((args.out/'preflight_gate.json').exists())

    def test_strict_ppo_uses_ppo_config_and_load_path_without_expert_initialization(self):
        run=self.root/'ppo';run.mkdir();torch.save({},run/'final.pt')
        env=RecordedEvaluation();records={}
        class RecordedTrainer:
            def __init__(self,model,config):records['model']=model;records['config']=config;self.updates=3
            def load(self,path):records['checkpoint']=path
        def extra(stack):stack.enter_context(patch('guitar_learning.training.ppo.PPOTrainer',RecordedTrainer))
        args=self.harness(env,run=run,extra=extra)
        with patch('guitar_learning.tool.experiments.joint.transfer.apply_experts') as transfer:
            result=evaluate(self.settings,args)
        transfer.assert_not_called()
        self.assertEqual(records['checkpoint'],run/'final.pt')
        self.assertEqual(type(records['config']).__name__,'PPOConfig')
        self.assertEqual(result['kind'],'strict_PPO')
        self.assertFalse((args.out/'preflight_gate.json').exists())
        initialization=json.loads((args.out/'initialization.json').read_text())
        self.assertEqual(initialization['optimizer_updates'],3)
        self.assertEqual(env.close_calls,1)


if __name__=='__main__':unittest.main()
