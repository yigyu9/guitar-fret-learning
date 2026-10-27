"""Explicit protocols and fresh-process boundaries without a native simulator."""
import copy
import json
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from guitar_learning.tool.experiments.contact_recovery.protocol import protocol_document, SCHEMA
from guitar_learning.tool.experiments.contact_recovery import run
from guitar_learning.tool.experiments.transition_refinement_runtime_v2.serialization import SCHEMA as RUNTIME


def protocol(process='persistent_reset'):
    return dict(schema=SCHEMA,process_mode=process,evaluation_mode='deterministic',
        cases=[dict(seed=7,perturbation=None),dict(seed=11,perturbation=None)])


class RecoveryProtocolTests(unittest.TestCase):
    def test_native_dependency_boundary_resolves_before_argument_guard(self):
        from guitar_learning.tool.experiments.contact_recovery import native
        # No simulator is created. Exercise all function-local integration imports,
        # including the original transition transfer path, before validation stops.
        with patch.dict(sys.modules, {'isaacgym': SimpleNamespace()}):
            with self.assertRaisesRegex(ValueError, 'zero/solver/policy'):
                native.run({}, SimpleNamespace(controller='invalid', episodes=1), {})

    def test_protocol_owns_seeds_and_allows20_persistent_cases(self):
        raw=protocol();raw['cases']=[dict(seed=i,perturbation=None) for i in range(20)]
        actual=protocol_document(raw,'evaluate');raw['cases'][0]['seed']=99
        self.assertEqual(actual['cases'][0]['seed'],0)
        self.assertEqual(len(actual['cases']),20)

    def test_reject_bool_seed_unknown_fields_and_unassisted_overrides(self):
        raw=protocol();raw['cases'][0]['seed']=True
        with self.assertRaises(ValueError):protocol_document(raw,'evaluate')
        raw=protocol();raw['extra']=1
        with self.assertRaises(ValueError):protocol_document(raw,'evaluate')
        raw=protocol();raw['cases'][0]['perturbation']={'channel':'L_Wrist_x'}
        with self.assertRaises(ValueError):protocol_document(raw,'evaluate')

    def test_teacher_is_not_a_stochastic_policy_and_too_many_cases_rejected(self):
        raw=protocol();raw['evaluation_mode']='stochastic'
        with self.assertRaises(ValueError):protocol_document(raw,'collect')
        raw=protocol();raw['cases']*=11
        with self.assertRaises(ValueError):protocol_document(raw,'collect')

    def fresh(self, failure=None):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);settings=root/'settings.json';settings.write_text('{}')
        spec=root/'protocol.json';spec.write_text(json.dumps(protocol('fresh_process')))
        args=SimpleNamespace(out=root/'out',settings=settings,protocol=spec,checkpoint=None,mode='collect')
        calls=[]
        def child(argv,**kwargs):
            calls.append(argv);out=Path(argv[argv.index('--out')+1]);out.mkdir()
            report=dict(schema='guitar_learning.contact_recovery_probe.v1',mode='collect',
                completed=True,source_unchanged=True,physical_flags_ok=True,forbidden_calls=[],
                missing_import_pins=[],failure=None,cleanup_error=None,successful_cases=[])
            (out/'result.json').write_text(json.dumps(report))
            audit=dict(schema='guitar_learning.runtime_json_audit.v1',backend=RUNTIME,
                completed=True,mode='collect',out=str(out),failure=None,anomaly=failure,
                state_mutations=False,checks=1,control_words={'0x37f':1})
            (out.parent/(out.name+'_runtime_json_audit.json')).write_text(json.dumps(audit))
            return SimpleNamespace(returncode=0)
        with patch.object(run.subprocess,'run',side_effect=child):
            if failure:
                with self.assertRaises(ValueError):run._fresh({},args,protocol('fresh_process'))
            else:
                result=run._fresh({},args,protocol('fresh_process'));self.assertTrue(result['completed'])
        return calls,args

    def test_fresh_cases_are_distinct_interpreter_execs_with_original_case_indices(self):
        calls,args=self.fresh()
        self.assertEqual(len(calls),2)
        self.assertEqual([x[x.index('--case-index')+1] for x in calls],['0','1'])
        self.assertNotEqual(calls[0][calls[0].index('--out')+1],calls[1][calls[1].index('--out')+1])
        self.assertEqual(json.loads((args.out/'protocol.json').read_text()),protocol('fresh_process'))

    def test_runtime_anomaly_cannot_be_hidden_by_successful_child_exit(self):
        calls,args=self.fresh('bad-state')
        self.assertEqual(len(calls),1)
        self.assertFalse(json.loads((args.out/'result.json').read_text())['completed'])


if __name__=='__main__':unittest.main()
