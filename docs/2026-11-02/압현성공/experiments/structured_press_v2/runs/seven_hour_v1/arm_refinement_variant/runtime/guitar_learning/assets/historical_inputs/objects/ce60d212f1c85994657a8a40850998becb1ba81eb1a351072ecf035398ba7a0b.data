"""Runtime isolation, read-only FP observation and spawn factory coverage."""
from contextlib import contextmanager
import json
import importlib
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from guitar_learning.transition_refinement_runtime import worker, run
from guitar_learning.transition_refinement_runtime.observer import Observer


class RuntimeTests(unittest.TestCase):
    def test_observer_does_not_change_hardware_state(self):
        observer = Observer()
        before = observer.library.read_fp_state()
        for _ in range(200):
            observer.check()
        self.assertEqual(observer.library.read_fp_state(), before)
        self.assertIsNone(observer.summary()['anomaly'])

    def test_bad_masks_rejected_without_replacing_any_state(self):
        observer = Observer()
        bad = (0x1fa0 << 32) | (0x80a0 << 16) | 0x1243
        with patch.object(observer.library, 'read_fp_state', return_value=bad) as probe:
            with self.assertRaises(FloatingPointError):
                observer.check()
            probe.assert_called_once_with()
        self.assertEqual(observer.summary()['anomaly']['control'], 0x1243)
        observer.check()

    def test_unsupported_rounding_and_denormal_modes_fail_without_state_changes(self):
        for control, mxcsr in ((0x77f, 0x1fa0), (0x37f, 0x9fe0), (0x37f, 0x3fa0)):
            observer = Observer()
            value = (mxcsr << 32) | control
            with patch.object(observer.library, 'read_fp_state', return_value=value):
                with self.assertRaises(FloatingPointError):
                    observer.check()

    def test_spawn_factory_restores_backend_and_closes_once(self):
        activation = importlib.import_module('guitar_learning.transition_refinement_runtime.activation')
        state = []
        @contextmanager
        def active(observer):
            state.append('start')
            try:
                for _ in range(4):
                    observer.check()
                yield observer
            finally:
                state.append('stop')
        def base_close():
            self.assertEqual(state, ['start'])
            state.append('close')
        def factory(spec, identity):
            self.assertEqual(state, ['start'])
            self.assertEqual(identity, 3)
            return types.SimpleNamespace(close=base_close)
        with tempfile.TemporaryDirectory() as folder, \
                patch.dict(sys.modules, isaacgym=types.ModuleType('isaacgym')), \
                patch.object(activation, 'activated', active), \
                patch.object(worker, '_base_factory', factory):
            env = worker.native_environment(dict(out=folder), 3)
            self.assertEqual(state, ['start'])
            env.close(); env.close()
            self.assertEqual(state, ['start', 'close', 'stop'])
            self.assertEqual(json.loads((Path(folder)/'runtime_json_audit.json').read_text())['checks'], 4)

    def test_spawn_construction_error_restores_backend(self):
        activation = importlib.import_module('guitar_learning.transition_refinement_runtime.activation')
        state = []
        @contextmanager
        def active(observer):
            try:
                yield None
            finally:
                state.append('restored')
        def fail(*args):
            raise RuntimeError('construction failed')
        with patch.dict(sys.modules, isaacgym=types.ModuleType('isaacgym')), \
                patch.object(activation, 'activated', active), \
                patch.object(worker, '_base_factory', fail):
            with self.assertRaisesRegex(RuntimeError, 'construction failed'):
                with tempfile.TemporaryDirectory() as folder:
                    worker.native_environment(dict(out=folder), 0)
        self.assertEqual(state, ['restored'])

    def test_runner_pins_adapter_and_restores_factory_and_json(self):
        from guitar_learning.transition_refinement import run as original, evidence, worker as original_worker
        old_factory, old_sources, old_dumps = original_worker.native_environment, evidence.source_paths, json.dumps
        def execute(settings, args):
            self.assertIsNot(json.dumps, old_dumps)
            self.assertIs(original_worker.native_environment, worker.native_environment)
            self.assertIs(worker._base_factory, old_factory)
            self.assertTrue(set(run.source_paths()) <= set(evidence.source_paths()))
            self.assertEqual(settings, {'x': 0.003})
            return dict(completed=True)
        with tempfile.TemporaryDirectory() as folder:
            settings = Path(folder)/'settings.json'; settings.write_text('{"x": 0.003}')
            argv = ['runtime', 'eval', '--settings', str(settings), '--out', str(Path(folder)/'out')]
            with patch.dict(sys.modules, isaacgym=types.ModuleType('isaacgym')), \
                    patch.object(sys, 'argv', argv), patch.object(original, 'run', execute):
                run.main()
            audit = json.loads((Path(folder)/'out_runtime_json_audit.json').read_text())
            self.assertIsNone(audit['anomaly'])
            self.assertGreater(audit['checks'], 0)
            self.assertTrue(audit['completed'])
        self.assertIs(original_worker.native_environment, old_factory)
        self.assertIs(evidence.source_paths, old_sources)
        self.assertIsNone(worker._base_factory)
        self.assertIs(json.dumps, old_dumps)

    def test_adapter_pins_include_observer_binary_and_c_source(self):
        paths = run.source_paths()
        self.assertTrue(all(p.is_file() for p in paths))
        self.assertEqual({p.suffix for p in paths}, {'.py', '.so', '.c'})

    def test_first_guard_failure_is_published_as_failed_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = Path(folder)/'settings.json'; settings.write_text('{}')
            argv = ['runtime', 'eval', '--settings', str(settings), '--out', str(Path(folder)/'out')]
            with patch.dict(sys.modules, isaacgym=types.ModuleType('isaacgym')), \
                    patch.object(sys, 'argv', argv), \
                    patch.object(Observer, 'check', side_effect=FloatingPointError('probe rejected')):
                with self.assertRaisesRegex(FloatingPointError, 'probe rejected'):
                    run.main()
            audit = json.loads((Path(folder)/'out_runtime_json_audit.json').read_text())
            self.assertFalse(audit['completed'])
            self.assertEqual(audit['failure']['type'], 'FloatingPointError')

    def test_audit_failure_preserves_primary_but_rejects_otherwise_success(self):
        from guitar_learning.transition_refinement_runtime.audit import publish
        observer = Observer()
        primary = RuntimeError('original failure')
        with patch.object(Path, 'write_text', side_effect=OSError('audit disk error')):
            publish(observer, Path('/tmp/audit.json'), completed=False, mode='test',
                out=Path('/tmp/out'), primary=primary)
            self.assertIsInstance(primary.runtime_audit_error, OSError)
            with self.assertRaisesRegex(OSError, 'audit disk error'):
                publish(observer, Path('/tmp/audit.json'), completed=True, mode='test', out=Path('/tmp/out'))

    def test_runtime_gate_finalization_is_required_and_pinned(self):
        from guitar_learning.transition_refinement_runtime.evidence import validate_gates
        from guitar_learning.transition_refinement_runtime.serialization import SCHEMA
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)/'native'; out.mkdir()
            settings = dict(initialization=dict(gate_evaluations=[str(out/'case_000')]))
            proof = dict(source_pins={})
            audit = out.parent/(out.name+'_runtime_json_audit.json')
            with self.assertRaises(FileNotFoundError):
                validate_gates(proof, settings)
            report = dict(schema='guitar_learning.runtime_json_audit.v1', backend=SCHEMA,
                completed=True, mode='eval', out=str(out), failure=None, anomaly=None,
                state_mutations=False, checks=2, control_words={'0x37f':2})
            audit.write_text(json.dumps(report))
            checked = validate_gates(proof, settings)
            self.assertIn(str(audit), checked['source_pins'])
            report['anomaly'] = dict(control=0x1243)
            audit.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError, 'finalized successful'):
                validate_gates(proof, settings)
            report['anomaly'] = None; report['completed'] = False
            audit.write_text(json.dumps(report))
            with self.assertRaises(ValueError):
                validate_gates(proof, settings)

    def test_every_worker_requires_final_runtime_success_after_cleanup(self):
        from guitar_learning.transition_refinement_runtime.evidence import validate_workers
        from guitar_learning.transition_refinement_runtime.serialization import SCHEMA
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            for index in range(2):
                worker_out = out/('worker_%03d'%index); worker_out.mkdir()
                report = dict(schema='guitar_learning.runtime_json_audit.v1', backend=SCHEMA,
                    completed=True, mode='worker', out=str(worker_out), failure=None, anomaly=None,
                    state_mutations=False, checks=2, control_words={'0x37f':2})
                (worker_out/'runtime_json_audit.json').write_text(json.dumps(report))
            self.assertEqual(len(validate_workers(out, dict(num_envs=2))), 2)
            report['completed'] = False
            (worker_out/'runtime_json_audit.json').write_text(json.dumps(report))
            with self.assertRaises(ValueError):
                validate_workers(out, dict(num_envs=2))


if __name__ == '__main__':
    unittest.main()
