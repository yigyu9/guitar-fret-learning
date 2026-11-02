"""실제 GPU를 시작하지 않고 후속 연구의 문턱·예산·실패 보존을 검사한다."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name('run_study.py')
spec = importlib.util.spec_from_file_location('f68_study', PATH)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class StudyTests(unittest.TestCase):
    def test_smoke_render_precedes_fresh_long_training(self):
        import ast
        tree = ast.parse(PATH.read_text())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        smoke = [node for node in ast.walk(main) if isinstance(node, ast.Call) and
                 isinstance(node.func, ast.Name) and node.func.id == 'run' and
                 len(node.args) > 3 and isinstance(node.args[2], ast.Constant) and node.args[2].value == 'smoke_render']
        self.assertEqual(len(smoke), 1)
        self.assertEqual(smoke[0].args[3].value, 'render')
        self.assertEqual(ast.literal_eval(smoke[0].args[4].elts[-2]), '--num-envs')
        self.assertEqual(ast.literal_eval(smoke[0].args[4].elts[-1]), 4)
        budget_loop = next(node for node in ast.walk(main) if isinstance(node, ast.For) and
                           isinstance(node.iter, ast.Name) and node.iter.id == 'BUDGETS')
        self.assertLess(smoke[0].lineno, budget_loop.lineno)

    def test_exact_balanced_budgets(self):
        for n in (256, 512, 1024):
            last = 0
            for budget in study.BUDGETS:
                self.assertEqual((budget-last) % (n*32), 0)
                last = budget
        self.assertEqual([study.BUDGETS[0]//(n*32) for n in (256, 512, 1024)], [76, 38, 19])

    def test_early_pass_requires_full_hold_and_timing(self):
        metrics = dict(episodes=128, AB=120, full_duration_pair=120,
                       on_time_with_previous_tail=120, clean_s=[1.45, 1.45], physical=0, wrist=0)
        self.assertTrue(study.passed(metrics))
        metrics['full_duration_pair'] = 25
        self.assertFalse(study.passed(metrics))
        metrics.update(full_duration_pair=120, physical=2)
        self.assertFalse(study.passed(metrics))

    def test_incomplete_benchmark_rejected_before_gpu(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'benchmark.json'
            path.write_text(json.dumps(dict(status='running', selected_envs=1024)))
            with self.assertRaises(ValueError):
                study.verify_gates(path, Path(tmp)/'missing_native.json')

    def test_native_acceptance_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            benchmark = base/'benchmark.json'; native = base/'native.json'
            benchmark.write_text(json.dumps(dict(status='complete', selected_envs=512, source_seal={},
                results=[dict(num_envs=512, eligible=True, completed=True)])))
            native.write_text(json.dumps(dict(accepted=False)))
            with self.assertRaisesRegex(ValueError, 'native accepted'):
                study.verify_gates(benchmark, native)

    def test_train_aggregate_does_not_invent_lifecycle_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); (base/'J').mkdir()
            (base/'report.json').write_text(json.dumps(dict(completed=True, failure=None)))
            report = dict(completed=True, lifecycle_verified=True, updates_in_run=2,
                          changed_inputs=[], missing_import_pins=[], cleanup_errors=[], failure=None)
            (base/'J/report.json').write_text(json.dumps(report))
            study.validate_job(base, 'train', 2)
            report['lifecycle_verified'] = False
            (base/'J/report.json').write_text(json.dumps(report))
            with self.assertRaises(ValueError):
                study.validate_job(base, 'train', 2)

    def test_render_requires_unchanged_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base/'report.json').write_text(json.dumps(dict(completed=True, lifecycle_verified=True,
                policy_unchanged=False, failure=None)))
            with self.assertRaisesRegex(ValueError, '정책 불변'):
                study.validate_job(base, 'render')

    def test_strict_resume_cli_uses_same_environment_and_seed(self):
        state = dict(num_envs=1024)
        with patch.object(study, 'run', return_value=Path('/unused')) as call, patch.object(study.Path, 'read_text', return_value=json.dumps(dict(transitions=622592))):
            checkpoint = study.train(state, Path('/unused'), 17, 1245184, '/preserved.pt', 622592)
        arguments = call.call_args.args[4]
        self.assertEqual(arguments[arguments.index('--num-envs')+1], 1024)
        self.assertEqual(arguments[arguments.index('--seed')+1], 17)
        self.assertEqual(arguments[arguments.index('--resume')+1], '/preserved.pt')
        self.assertEqual(call.call_args.kwargs['updates'], 19)


if __name__ == '__main__':
    unittest.main()
