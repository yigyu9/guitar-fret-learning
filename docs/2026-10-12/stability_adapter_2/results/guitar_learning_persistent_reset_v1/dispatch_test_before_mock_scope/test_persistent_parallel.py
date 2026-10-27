"""Persistent entry point dispatch leaves original running/fresh code untouched."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch
from guitar_learning import parallel,train_parallel,train_persistent
from guitar_learning.persistent_parallel import PersistentPool,persistent_native_environment


class PersistentDispatchTests(unittest.TestCase):
    def test_default_and_explicit_cpu_factory_dispatch(self):
        def fixture(spec,index):pass
        for factory,expected in ((None,persistent_native_environment),(fixture,fixture)):
            with patch.object(parallel.Pool,'__init__',return_value=None) as base:
                PersistentPool([{'out':'unused'}],timeout_s=37.,worker_factory=factory,wait_callback=fixture)
                self.assertIs(base.call_args.kwargs['worker_factory'],expected)
                self.assertIs(base.call_args.kwargs['wait_callback'],fixture)
                self.assertEqual(base.call_args.kwargs['timeout_s'],37.)

    def test_entry_point_restores_dispatch_after_error(self):
        original=parallel.Pool
        def fail():
            self.assertIs(parallel.Pool,PersistentPool)
            raise KeyboardInterrupt()
        with patch.object(train_parallel,'main',fail):
            with self.assertRaises(KeyboardInterrupt):train_persistent.main()
        self.assertIs(parallel.Pool,original)

    def test_native_factory_passes_base_seed_and_music_to_persistent_builder(self):
        from guitar_learning import persistent_environment
        spec=dict(config='config',out='worker',bundle='bundle',stage='B',seed=7,
                  music=dict(reward_mode='dense_v2',goal_event_indices=[0,1]))
        expected=object()
        with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}):
            with patch.object(persistent_environment,'build_persistent_environment',return_value=expected) as build:
                self.assertIs(persistent_native_environment(spec,3),expected)
        self.assertEqual(build.call_args.args,('config',Path('worker/environment')))
        self.assertEqual(build.call_args.kwargs['seed'],7)
        self.assertEqual(build.call_args.kwargs['worker_id'],3)
        self.assertEqual(build.call_args.kwargs['music'],spec['music'])
        with self.assertRaises(ValueError):persistent_native_environment(dict(spec,headless=False),3)


if __name__=='__main__':unittest.main()
