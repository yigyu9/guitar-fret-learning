"""CPU fixtures for the timing-only fork, shared math and exact-prefix audit."""
import ast
import builtins
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch

import run_probe as driver

spec=importlib.util.spec_from_file_location('preserved_windup_cpu_tests',driver.PREVIOUS/'self_test.py')
fixture=importlib.util.module_from_spec(spec)
sys.path.insert(0,str(driver.PREVIOUS))
try: spec.loader.exec_module(fixture)
finally: sys.path.remove(str(driver.PREVIOUS))
fixture.driver=driver


def function(tree,name):
    return next(n for n in ast.parse(tree).body if isinstance(n,ast.FunctionDef) and n.name==name)


def nested(tree):
    return next(n for n in function(tree,'main').body if isinstance(n,ast.ClassDef) and n.name=='TapePool')


class Checks(unittest.TestCase):
    def test_only_timing_and_explicit_no_relax_changed_in_control_path(self):
        old=(driver.PREVIOUS/'run_probe.py').read_text();new=(driver.HERE/'run_probe.py').read_text()
        expected=old.replace('first & (env.clock >= 480) & ~prior','first & ~prior')
        self.assertEqual(ast.dump(function(expected,'measure')),ast.dump(function(new,'measure')))
        expected=old.replace('relax=args.mode == MODES[2]','relax=False')
        self.assertEqual(ast.dump(nested(expected)),ast.dump(nested(new)))
        self.assertIs(driver.project,driver._projection.project)

    def test_shared_projection_independent_math(self):
        fixture.CPUChecks().test_projection_independent_active_sets()
        fixture.CPUChecks().test_float32_rounding()

    def test_first_loaded_before_480_and_current_not_latched_gate(self):
        pool,trace=fixture.hook(driver.MODES[1])
        pool.snapshot['contact_force'].zero_()
        incoming=torch.full((128,39),.9)
        expected=torch.zeros(128,4)
        for _ in range(5):
            expected+=torch.full((128,4),-.2)*4/60
            pool.step(incoming)
            torch.testing.assert_close(pool.controller.target[:,60:64],expected,atol=0,rtol=0)
        self.assertFalse(trace.values()['gate'].any())
        pool.snapshot['contact_force'][:,1,2]=1
        pool.step(incoming)
        a=trace.values();self.assertTrue(a['gate'][-1].all());self.assertTrue((a['start_clock'][-1]==20).all())
        self.assertTrue(np.any(a['final_target4'][-1]!=a['raw_target4'][-1]))
        self.assertTrue((a['halfspace_residual_m'][-1]>=-a['halfspace_tolerance_m'][-1]).all())
        pool.snapshot['contact_force'].zero_();pool.step(incoming)
        a=trace.values();self.assertFalse(a['gate'][-1].any());np.testing.assert_array_equal(a['final_target4'][-1],a['raw_target4'][-1])
        self.assertFalse(a['memory_submit_error_rad'].any());self.assertFalse(a['other_target_change_rad'].any())
        self.assertTrue((a['box_excess_rad']<=a['coordinate_tolerance_rad']).all())
        np.testing.assert_array_equal(a['tape_action4'],np.full((7,128,4),-.2,dtype=np.float32))

    def test_failure_reset_invalid_and_inactive_before_J(self):
        # Original adversarial q/qd/native-J/reset/failure fixture, now at clock20.
        pool,_=fixture.hook(driver.MODES[1]);pool.environment.clock[:]=20
        snapshot=pool.snapshot;snapshot['reset_body_snapshot'][:]=False
        snapshot['reset_body_snapshot'][0]=True;snapshot['jacobian'][0]=float('nan')
        snapshot['q'][1,0]=float('nan');snapshot['qd'][2,0]=float('nan');snapshot['jacobian'][3]=float('nan')
        pool.environment.failure[4,0]=True;pool.environment.wrist_failure[5]=True
        pool.replay_first[6]=False;snapshot['jacobian'][6]=float('nan')
        m=driver.measure(pool,snapshot,pool.replay_first,pool.material,.01)
        self.assertFalse(bool(m['gate'][:7].any()));self.assertTrue(bool(m['gate'][7:].all()))
        self.assertEqual(m['invalid_state'].nonzero().flatten().tolist(),[1,2])
        self.assertEqual(m['invalid'].nonzero().flatten().tolist(),[3])
        for key in ('J','g','measured','predicted'):self.assertTrue(bool(torch.isfinite(m[key]).all()))
        self.assertTrue(bool(torch.isnan(snapshot['q'][1,0])))
        pool,_=fixture.hook(driver.MODES[1]);pool.replay_first[6]=False;pool.environment.clock[:]=20
        pool.step(torch.full((128,39),.9));self.assertTrue(bool((pool.last_action[6,21:25]==.9).all()))

    def test_environment_prefix_inclusive_physics_exclusive_control(self):
        p=dict(clock=np.tile(np.arange(1,13)[:,None],(1,128)),first_attempt=np.ones((12,128),bool),q=np.zeros((12,128)))
        c=dict(clock=np.tile(np.arange(4,13,4)[:,None],(1,128)),first_attempt=np.ones((3,128),bool),q=np.zeros((3,128)))
        t=dict(first_attempt=c['first_attempt'].copy(),start_clock=c['clock']-4,raw_target4=np.zeros((3,128,4)),final_target4=np.zeros((3,128,4)),gate=np.zeros((3,128),bool))
        t['final_target4'][1,0,0]=1;t['final_target4'][2,1,0]=1;t['gate'][:,0]=True;t['gate'][2,1]=True
        newp={k:v.copy() for k,v in p.items()};newc={k:v.copy() for k,v in c.items()}
        newp['q'][4:,0]=1;newp['q'][8:,1]=1;newc['q'][1:,0]=1;newc['q'][2:,1]=1
        result=driver.prefix_audit(t,newp,newc,p,c)
        self.assertTrue(all(result['checks'].values()));self.assertEqual(result['physics_prefix_endpoints'][:3],[4,8,12])
        self.assertEqual(result['control_prefix_endpoints'][:3],[1,2,3]);self.assertEqual(result['first_gate_start_clock'][0],0)
        self.assertEqual(result['first_changed_target_start_clock'][:3],[4,8,None]);json.dumps(result,allow_nan=False)
        newp['q'][3,0]=9;self.assertFalse(driver.prefix_audit(t,newp,newc,p,c)['checks']['physics_values']);newp['q'][3,0]=0
        newc['q'][0,0]=9;self.assertFalse(driver.prefix_audit(t,newp,newc,p,c)['checks']['control_values']);newc['q'][0,0]=0
        newp['q'][-1,2]=9;self.assertFalse(driver.prefix_audit(t,newp,newc,p,c)['checks']['physics_values'])

    def test_existing_out_before_native_import_and_budget(self):
        original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name.startswith('isaacgym'):raise AssertionError('native import attempted')
            return original(name,*args,**kwargs)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'existing';out.mkdir();sentinel=out/'keep';sentinel.write_bytes(b'unchanged')
            before=(out.stat().st_dev,out.stat().st_ino,sentinel.read_bytes())
            with patch.object(sys,'argv',['run_probe.py','--out',str(out)]),patch.object(builtins,'__import__',guarded),patch.object(driver,'observer',side_effect=AssertionError('producer called')):
                with self.assertRaises(FileExistsError):driver.main()
            self.assertEqual(before,(out.stat().st_dev,out.stat().st_ino,sentinel.read_bytes()))
        driver.observer()
        from protocol import Trace
        source=json.loads((driver.OBSERVER/'run_final300_policy/load_probe_report.json').read_text())
        self.assertLess(Trace(driver.SCHEMA,218).nbytes+source['selected_output_uncompressed_bytes'],100_000_000)
        self.assertFalse(torch.cuda.is_initialized())
        for p in driver.HERE.glob('*.py'):ast.parse(p.read_text())


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    driver.write(driver.HERE/'cpu_verification.json',dict(completed=result.wasSuccessful(),CPU_only=True,tests=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),scope='timing-only AST, independent shared math, actual nested CPU hook, prefix boundary and output protection; no native execution'))
    sys.exit(not result.wasSuccessful())
