import argparse
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from guitar_learning.tool.experiments.transition import probe_contact


class ContactProbeTests(unittest.TestCase):
    def test_real_controller_and_input_paths_survive_shared_module_patches(self):
        import json
        from pathlib import Path
        from guitar_learning.tool.experiments.transition import environment, probe, solver, teacher
        from guitar_learning.tool.experiments.transition.task import make_task
        from guitar_learning.imitation.imitation_io import BUNDLE
        root = Path(__file__).resolve().parents[2]
        case = root/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_v1/single_a_solver_v1/case_000'
        plan = json.loads((case/'plan.json').read_text())
        config = dict(schema='guitar_learning.transition.v1', mode='single_a', tempo_scale=1., role='left')
        task = make_task(BUNDLE, config)
        original_teacher, original_inputs = teacher.Controller, solver.input_paths
        env = object()

        def shared(settings, args):
            environment.build_environment()
            paths = solver.input_paths()
            self.assertTrue(all(Path(path).is_file() for path in paths))
            self.assertTrue(any(path.endswith('guitar_asset.xml') for path in paths))
            controller = teacher.Controller(plan, task, config)
            self.assertIsInstance(controller.controller.schedule, original_teacher)
            self.assertIs(controller.env, env)
            return 'real construction passed'

        with patch.object(environment, 'build_environment', return_value=env), patch.object(probe, 'run', shared):
            self.assertEqual(probe_contact.run({'transition': config}, argparse.Namespace()), 'real construction passed')
        self.assertIs(teacher.Controller, original_teacher)
        self.assertIs(solver.input_paths, original_inputs)

    def test_shared_probe_receives_live_environment_and_restores_patches(self):
        from guitar_learning.tool.experiments.transition import contact_teacher, environment, probe, solver, teacher
        original_teacher = teacher.Controller
        env = object()
        calls = []

        class Controller:
            diagnostic = {'live_guitar_tracking': True}
            def __init__(self, plan, task, transition):
                calls.append(('init', plan, task, transition))
            def action(self, now, env=None):
                calls.append(('action', now, env))
                return [0.] * 39

        def shared(settings, args):
            self.assertEqual(args.controller, 'solver')
            self.assertIs(environment.build_environment('config', x=1), env)
            self.assertEqual(solver.input_paths(), ['/base.xml', '/contact.xml'])
            controller = teacher.Controller('plan', 'task', 'config')
            self.assertEqual(controller.action(0.), [0.] * 39)
            self.assertTrue(controller.diagnostic['live_guitar_tracking'])
            return {'completed': True}

        with patch.object(environment, 'build_environment', return_value=env) as build, \
                patch.object(solver, 'input_paths', return_value=['/base.xml']), \
                patch.object(contact_teacher, 'input_paths', return_value=['/contact.xml']), \
                patch.object(contact_teacher, 'Controller', Controller), \
                patch.object(probe, 'run', shared):
            self.assertEqual(probe_contact.run({'transition': {'role': 'left'}}, argparse.Namespace()), {'completed': True})
            build.assert_called_once_with('config', x=1)
            self.assertIs(environment.build_environment, build)
        self.assertIs(teacher.Controller, original_teacher)
        self.assertEqual(calls[-1], ('action', 0., env))

    def test_partner_and_policy_checkpoint_are_not_silently_reclassified(self):
        with self.assertRaises(ValueError):
            probe_contact.run({'transition': {'role': 'joint'}}, SimpleNamespace())
        with self.assertRaises(ValueError):
            probe_contact.run({'transition': {'role': 'left'}}, SimpleNamespace(checkpoint='policy.pt'))


if __name__ == '__main__':
    unittest.main()
