"""CPU checks for the explicitly declared old-policy/current-physics adapter."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import tempfile
from unittest.mock import patch

FILE=Path(__file__).with_name('evaluate_baseline.py')
spec=importlib.util.spec_from_file_location('v20_A500_evaluate_baseline',FILE)
baseline=importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.old = json.loads((baseline.BASELINE/'train3000/training_contract.json').read_text())
        self.current = json.loads((baseline.ROOT/'docs/2026-10-25/'
            'guitar_learning_finger_recovery_v20/gpu_A/training_contract.json').read_text())

    def test_bridge_accepts_only_exact_declared_contract_differences(self):
        found = baseline.validate_contract_bridge(self.old,self.current)
        self.assertEqual(found,baseline.CONTRACT_DIFFERENCES)
        for section,key,value in [('termination','control_hz',61),('action','dimension',38),
                ('native_backend','pipeline','cpu')]:
            altered = copy.deepcopy(self.current)
            altered[section][key] = value
            with self.assertRaises(ValueError):
                baseline.validate_contract_bridge(self.old,altered)
        altered=copy.deepcopy(self.current)
        altered['observation']['fields'][1]+='_changed'
        with self.assertRaises(ValueError):
            baseline.validate_contract_bridge(self.old,altered)
        altered=copy.deepcopy(self.current)
        altered['observation']['event_scales'][2]=99.
        with self.assertRaises(ValueError):
            baseline.validate_contract_bridge(self.old,altered)

    def test_bridge_rejects_undeclared_reward_or_reference_change(self):
        for path,value in [(('reward','surface_learning','schema'),'changed'),
                (('reward','finger_posture','frame_source','schema'),'changed')]:
            altered=copy.deepcopy(self.current)
            parent=altered
            for key in path[:-1]:parent=parent[key]
            parent[path[-1]]=value
            with self.assertRaises(ValueError):
                baseline.validate_contract_bridge(self.old,altered)

    def test_checkpoint_separates_source3000_from_evaluated500(self):
        self.assertEqual(baseline.checkpoint_path(Path('/source3000'),500),
            Path('/source3000/checkpoint_000499.pt'))
        with self.assertRaises(ValueError):
            baseline.checkpoint_path(Path('/source3000'),3000)

    def test_adapter_changes_only_four_temporal_idle_columns_without_mutation(self):
        import torch
        from guitar_learning.gpu.finger_reward import finger_posture_reward
        n=1024
        body=torch.zeros(n,13,13)
        body[...,6]=1.
        env=SimpleNamespace(clock=torch.arange(n,dtype=torch.long),
            onset=torch.tensor([3.,5.],dtype=torch.float64),end=torch.tensor([4.,6.],dtype=torch.float64),
            press=torch.tensor([2.8,4.8],dtype=torch.float64),finger=torch.tensor([1,3]),
            body=body,finger_palm_index=0,finger_segment_indices=torch.arange(1,13).reshape(4,3))
        observation=dict(state=torch.zeros(n,544),events=torch.ones(n,2,24),mask=torch.ones(n,2,dtype=torch.bool),
            priority_events=torch.ones(n,8,24),priority_mask=torch.ones(n,8,dtype=torch.bool))
        original=copy.deepcopy(observation)
        result=baseline.adapt_observation(env,observation)
        expected=finger_posture_reward(env.clock.double()/240.,env.onset,env.end,env.press,env.finger,
            body[:,0,3:7],body[:,env.finger_segment_indices,3:7])['idle_weight'].float()
        self.assertTrue(torch.equal(result['state'][:,:540],original['state'][:,:540]))
        self.assertTrue(torch.equal(result['state'][:,540:],expected))
        self.assertTrue(torch.equal(observation['state'],original['state']))
        self.assertGreater(float((expected!=0).sum()),0)
        self.assertGreater(float((expected!=1).sum()),0)
        for field in ('events','mask','priority_events','priority_mask'):
            self.assertIs(result[field],observation[field])

    def test_current_old_geometry_definition_is_equal_as_read_only_ast(self):
        relative='guitar_learning/gpu/finger_reward.py'
        self.assertEqual(baseline.ast_definition(baseline.ROOT/relative,'finger_posture_reward'),
            baseline.ast_definition(baseline.ARCHIVE/relative,'finger_posture_reward'))

    def test_actual_old_policy_architecture_and_strict_model_keys(self):
        import torch
        from guitar_learning.skills.specialist_policy import SpecialistPolicy
        payload=torch.load(baseline.BASELINE/'train3000/checkpoint_000499.pt',map_location='cpu',weights_only=False)
        policy=SpecialistPolicy(544,size='large',contract=self.old,role='left')
        self.assertEqual(policy.architecture,payload['identity']['architecture'])
        policy.register_buffer('left_curriculum_state',torch.zeros(3331,dtype=torch.float64))
        policy.load_state_dict(payload['model'],strict=True)
        self.assertEqual(payload['updates'],500)
        self.assertEqual(policy.left_curriculum_state.numel(),3331)
        self.assertEqual(json.loads((baseline.BASELINE/'train3000/report.json').read_text())['optimizer_updates'],3000)

    def test_original459_and_current462_pin_maps_are_separate(self):
        oldpins=json.loads((baseline.BASELINE/'train3000/inputs_before.json').read_text())
        # Native main requires the completed new A500 audit. This CPU test isolates
        # archival/common-definition verification while training is still running.
        with tempfile.TemporaryDirectory() as name:
            phase=Path(name)
            (phase/'train500').mkdir()
            for relative in ('train500/inputs_before.json','training_source_manifest.json'):
                (phase/relative).write_bytes((baseline.PHASE/relative).read_bytes())
            (phase/'log_inspection.json').write_text('{"test_fixture":true}')
            with patch.object(baseline,'PHASE',phase), patch.object(
                    baseline.current,'validate_source_pins',return_value=None):
                pins,adapter=baseline.validate_source_pins(oldpins)
                self.assertEqual(adapter['original_source_count'],459)
                self.assertEqual(adapter['current_source_count'],462)
                rel='guitar_learning/gpu/environment.py'
                self.assertEqual(pins[str(baseline.ARCHIVE/rel)],oldpins[str(baseline.ROOT/rel)])
                self.assertNotEqual(pins[str(baseline.ARCHIVE/rel)],pins[str(baseline.ROOT/rel)])
                wrong=copy.deepcopy(oldpins)
                wrong[str(baseline.ROOT/rel)]='0'*64
                with self.assertRaises(ValueError):
                    baseline.validate_source_pins(wrong)


if __name__=='__main__':
    unittest.main(verbosity=2)
