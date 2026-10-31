"""One offline XML classification; original native parity remains untouched."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import torch._dynamo

from guitar_learning.imitation.imitation import dataset_manifest
from guitar_learning.tool.experiments.transition import train, train_with_teacher_proof as wrapper

PHASE=Path(__file__).resolve().parents[2]/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_long_v1'


class TeacherProofTests(unittest.TestCase):
    def test_only_exact_offline_XML_is_classified(self):
        evidence=dict(source_pins={wrapper.TEACHER_XML:wrapper.TEACHER_SHA256,
            '/other/unknown.xml':'unknown','/native/actual.xml':'native','/capture/result.json':'proof'})
        before=copy.deepcopy(evidence)
        result=wrapper.projected_evidence(evidence,{'/auxiliary-proof.json':'sha'})
        self.assertNotIn(wrapper.TEACHER_XML,result['source_pins'])
        self.assertEqual(result['source_pins']['/other/unknown.xml'],'unknown')
        self.assertEqual(result['source_pins']['/native/actual.xml'],'native')
        self.assertEqual(evidence,before)
        evidence['source_pins'][wrapper.TEACHER_XML]='changed'
        with self.assertRaisesRegex(ValueError,'exact audited'):wrapper.projected_evidence(evidence,{})

    def test_original_validator_and_actual_generic_native_parity_preflight(self):
        # Real BC, real four completed policy gates, real source hashes and
        # original generic model/config parity; stop before any native scene.
        from guitar_learning.training import parallel, persistent_audit
        original_validator=train.initialization_evidence
        value=train.settings_document(json.loads((PHASE/'single_a_ppo_settings_v1.json').read_text()))
        value['device']='cpu';value['num_envs']=1;value['horizon']=2;value['updates']=1
        reached=[]
        class PreflightBoundary:
            def __init__(self,specs,**kwargs):
                reached.append(specs)
                raise RuntimeError('CPU_PREFLIGHT_PASSED_NO_NATIVE')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);config=root/'settings.json';config.write_text(json.dumps(value))
            args=types.SimpleNamespace(settings=config,out=root/'run',resume=None)
            with patch.dict('sys.modules',{'isaacgym':types.ModuleType('isaacgym')}), \
                    patch.object(parallel,'Pool',PreflightBoundary), \
                    patch.object(persistent_audit,'finalize_persistent_run',return_value=True), \
                    patch('guitar_learning.training.monitoring.available_memory_bytes',return_value=16*1024**3):
                with self.assertRaisesRegex(RuntimeError,'CPU_PREFLIGHT_PASSED_NO_NATIVE'):
                    wrapper.run(value,args)
            report=json.loads((args.out/'report.json').read_text())
            self.assertEqual(len(reached),1)
            self.assertEqual(report['failure']['message'],'CPU_PREFLIGHT_PASSED_NO_NATIVE')
            self.assertFalse(report['completed']);self.assertEqual(report['optimizer_updates'],None)
            pins=json.loads((args.out/'inputs_before.json').read_text())
            self.assertNotIn(wrapper.TEACHER_XML,pins)
            proof=root/'run_teacher_auxiliary_inputs.json'
            document=json.loads(proof.read_text())
            self.assertEqual(document['full_initialization_inputs'][wrapper.TEACHER_XML],wrapper.TEACHER_SHA256)
            self.assertEqual(dataset_manifest([proof])[str(proof)],pins[str(proof)])
            audit=json.loads((root/'run_teacher_auxiliary_final_audit.json').read_text())
            self.assertTrue(audit['source_unchanged']);self.assertIsNone(audit['runner_completed'])
            self.assertEqual(audit['full_inputs_before'],audit['full_inputs_after'])
            # The original validator binding is restored even after a failed
            # generic run; no strict source parser or native parity was patched.
            self.assertIs(train.initialization_evidence,original_validator)

    def test_full_proof_tamper_fails_final_audit_and_primary_is_preserved(self):
        for primary in (False,True):
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);data=root/'gate.json';data.write_text('original')
                pins=dataset_manifest([data,wrapper.TEACHER_XML]);evidence=dict(source_pins=pins)
                args=types.SimpleNamespace(settings=root/'settings.json',out=root/'run',resume=None)
                def fail(value,arguments):
                    train.initialization_evidence(value,require_gate=True)
                    data.write_text('tampered')
                    if primary:raise ValueError('primary training failure')
                    return dict(completed=True)
                original=train.initialization_evidence
                with patch.dict('sys.modules',{'isaacgym':types.ModuleType('isaacgym')}), \
                        patch.object(train,'initialization_evidence',return_value=evidence),patch.object(train,'run',side_effect=fail):
                    expected=ValueError if primary else RuntimeError
                    with self.assertRaises(expected):wrapper.run({},args)
                audit=json.loads((root/'run_teacher_auxiliary_final_audit.json').read_text())
                self.assertFalse(audit['source_unchanged']);self.assertFalse(audit['completed'])
                if primary:self.assertEqual(audit['failure']['message'],'primary training failure')
                self.assertIs(train.initialization_evidence,original)

    def test_unknown_XML_still_fails_original_generic_native_parity(self):
        from guitar_learning.training import parallel
        value=train.settings_document(json.loads((PHASE/'single_a_ppo_settings_v1.json').read_text()))
        value['device']='cpu';value['num_envs']=1;value['horizon']=2;value['updates']=1
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);unknown=root/'unknown.xml';unknown.write_text('<mujoco/>')
            config=root/'settings.json';config.write_text(json.dumps(value))
            args=types.SimpleNamespace(settings=config,out=root/'run',resume=None)
            evidence=dict(source_pins=dataset_manifest([wrapper.TEACHER_XML,unknown]))
            with patch.dict('sys.modules',{'isaacgym':types.ModuleType('isaacgym')}), \
                    patch.object(train,'initialization_evidence',return_value=evidence), \
                    patch.object(parallel,'Pool') as pool, \
                    patch('guitar_learning.training.monitoring.available_memory_bytes',return_value=16*1024**3):
                with self.assertRaisesRegex(RuntimeError,'original model/config parity failed'):
                    wrapper.run(value,args)
                pool.assert_not_called()
            pins=json.loads((args.out/'inputs_before.json').read_text())
            self.assertIn(str(unknown),pins)
            self.assertNotIn(wrapper.TEACHER_XML,pins)

    def test_existing_outputs_or_proof_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'run_teacher_auxiliary_inputs.json').write_text('preserved')
            args=types.SimpleNamespace(out=root/'run')
            with patch.dict('sys.modules',{'isaacgym':types.ModuleType('isaacgym')}),self.assertRaises(FileExistsError):
                wrapper.run({},args)
            self.assertEqual((root/'run_teacher_auxiliary_inputs.json').read_text(),'preserved')

    def test_new_native_CLI_imports_Isaac_before_numerical_libraries(self):
        script='''
import builtins,runpy,sys
original=builtins.__import__
def checked(name,*args,**kwargs):
    if name=='isaacgym':
        assert 'torch'not in sys.modules and 'numpy'not in sys.modules
        raise RuntimeError('ISAAC_FIRST')
    return original(name,*args,**kwargs)
builtins.__import__=checked
sys.argv=['wrapper','--settings','/tmp/unused.json','--out','/tmp/unused-out']
try:runpy.run_module('guitar_learning.tool.experiments.transition.train_with_teacher_proof',run_name='__main__')
except RuntimeError as error:assert str(error)=='ISAAC_FIRST'
else:raise AssertionError('Isaac never imported')
'''
        result=subprocess.run([sys.executable,'-c',script],cwd=Path(__file__).resolve().parents[2],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
