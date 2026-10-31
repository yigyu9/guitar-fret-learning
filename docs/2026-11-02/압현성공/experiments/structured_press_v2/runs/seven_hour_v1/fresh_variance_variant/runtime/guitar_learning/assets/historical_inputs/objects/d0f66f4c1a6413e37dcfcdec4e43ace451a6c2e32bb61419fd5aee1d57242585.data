"""The native joint factory must own persistent headless reset support."""
from pathlib import Path
import random
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
import torch
from guitar_learning.training import parallel
from guitar_learning.tool.experiments.joint import environment
from guitar_learning.tool.experiments.joint.worker import native_environment, compact
from guitar_learning.runtime.persistent_session import PersistentHeadlessPreparedSession


class JointWorkerTests(unittest.TestCase):
    def test_factory_uses_persistent_headless_session_and_preserves_worker_configuration(self):
        marker=object()
        spec=dict(config='baseline.json',out='/tmp/joint_worker_cpu_test',bundle='song_bundle',
            headless=True,seed=11,timing=dict(stage_index=1,pre_roll_s=3.),stage='B',
            start_event_index=0,phrase_events=8,tempo_scale=1.,music={},
            env_kwargs=dict(session_factory=object(),contact_reader=marker))
        sentinel=object();random_state=random.getstate();numpy_state=np.random.get_state()
        try:
            with patch.dict('sys.modules',{'isaacgym':SimpleNamespace()}), \
                    patch.object(environment,'build_environment',return_value=sentinel) as build, \
                    patch.object(parallel,'_compact'),torch.random.fork_rng(devices=[]):
                result=native_environment(spec,worker_id=2)
                self.assertIs(parallel._compact,compact)
            self.assertIs(result,sentinel)
            args,kwargs=build.call_args
            self.assertEqual(args,('baseline.json',Path('/tmp/joint_worker_cpu_test/environment')))
            self.assertIs(kwargs['session_factory'],PersistentHeadlessPreparedSession)
            self.assertTrue(callable(getattr(kwargs['session_factory'],'reset_episode',None)))
            self.assertIs(kwargs['contact_reader'],marker)
            self.assertEqual(kwargs['worker_id'],2);self.assertEqual(kwargs['seed'],11)
            self.assertEqual(kwargs['timing'].stage_index,1);self.assertEqual(kwargs['timing'].pre_roll_s,3.)
            self.assertEqual(kwargs['bundle'],'song_bundle')
        finally:
            random.setstate(random_state);np.random.set_state(numpy_state)

    def test_nonheadless_request_rejected_before_environment_creation(self):
        with patch.dict('sys.modules',{'isaacgym':SimpleNamespace()}), \
                patch.object(environment,'build_environment') as build:
            with self.assertRaisesRegex(ValueError,'headless native scenes'):
                native_environment(dict(headless=False),worker_id=0)
        build.assert_not_called()


if __name__=='__main__':unittest.main()
