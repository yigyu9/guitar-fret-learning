import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import numpy as np
import torch

spec = importlib.util.spec_from_file_location('trace_policy', Path(__file__).with_name('trace_policy.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TraceTests(unittest.TestCase):
    def fixture(self):
        n, m = 2, 3
        env = SimpleNamespace(device='cpu', M=m, clock=torch.ones(n,dtype=torch.long),
            finger_joint_indices=torch.arange(21), finger_action_indices=torch.arange(21),
            snapshot={'q':torch.randn(n,21), 'target':torch.randn(n,21)},
            action=torch.randn(n,21), finger_outward=torch.zeros(n,21,dtype=torch.bool),
            surface_distance=torch.rand(n,m), candidate=torch.zeros(n,m,dtype=torch.bool),
            wrong=torch.zeros(n,m,dtype=torch.bool))
        posture = {k:torch.rand(n,4) for k in ('gate','quality','idle_weight')}
        posture.update(angles=torch.randn(n,4,3),valid=torch.ones(n,4,3,dtype=torch.bool))
        posture.update({k:torch.zeros(n,4,dtype=torch.bool) for k in
            ('near_veto','contact_veto','nonfinite_veto')})
        trace = module.PhysicsTrace(env,max_steps=4,count=n)
        trace.last_tracking = dict(indices=torch.zeros(n,4,dtype=torch.long),
            valid=torch.ones(n,4,dtype=torch.bool),quality=torch.rand(n,4))
        return env, posture, trace

    def test_observer_copies_without_mutation_and_keeps_first_prefix(self):
        env, posture, trace = self.fixture()
        before = {k:v.clone() for k,v in posture.items()}
        q0 = env.snapshot['q'].clone()
        pressing = torch.zeros(2,4,dtype=torch.bool)
        for step in range(4):
            env.clock.fill_(step+1)
            trace.record(posture,pressing)
        trace.end_control([{'env_id':0,'steps':1},{'env_id':1,'steps':1}])
        for k,v in posture.items():self.assertTrue(torch.equal(v,before[k]))
        self.assertTrue(torch.equal(q0,env.snapshot['q']))
        posture['angles'].zero_()
        self.assertTrue(torch.equal(trace.arrays['angles'][0],before['angles']))
        with tempfile.TemporaryDirectory() as d:
            paths=trace.save(Path(d)/'trace')
            self.assertEqual(len(paths),2)
            for row in paths:
                z=np.load(Path(d)/'trace'/row['path'])
                np.testing.assert_array_equal(z['clock'],[1,2,3,4])
                np.testing.assert_array_equal(z['q'][0],q0[row['env_id']])
        with self.assertRaises(ValueError):trace.record(posture,pressing)

    def test_boundary_and_incomplete_capture_rejected(self):
        env, posture, trace = self.fixture()
        trace.record(posture,torch.zeros(2,4,dtype=torch.bool))
        with self.assertRaises(ValueError):trace.end_control([{'env_id':0,'steps':1}])
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):trace.save(Path(d)/'trace')


if __name__ == '__main__':
    unittest.main()
