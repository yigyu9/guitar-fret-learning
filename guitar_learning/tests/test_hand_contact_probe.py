import unittest
from pathlib import Path
import tempfile

from guitar_learning.tool.validation.hand_contact_probe import protocol, smooth_B, GraphicsGym, physics_source_paths, finish_video


class HandContactProbeTests(unittest.TestCase):
    def test_fixed_protocol_boundary_and_reversal(self):
        self.assertEqual(protocol(1), ('initial_hold', 0., 0.))
        self.assertEqual(protocol(2), ('initial_flex_plus', .04, 0.))
        self.assertEqual(protocol(2+1/60), ('initial_flex_minus', -.04, 0.))
        self.assertEqual(protocol(4+1/60), ('initial_spread_minus', 0., -.04))
        self.assertEqual(protocol(9), ('move_B', 0., 0.))
        self.assertEqual(protocol(11+1/60), ('B_flex_minus', -.04, 0.))
        self.assertEqual(protocol(14+1/60), ('final_hold', 0., 0.))

    def test_B_interpolation_has_no_boundary_jump(self):
        self.assertEqual(smooth_B(0), 0)
        self.assertEqual(smooth_B(5), 0)
        self.assertEqual(smooth_B(7), .5)
        self.assertEqual(smooth_B(9), 1)
        self.assertEqual(smooth_B(100), 1)
        self.assertLess(smooth_B(5+1/60), .0001)

    def test_graphics_adapter_leaves_physics_arguments_identical(self):
        class Native:
            def create_sim(self, *args):
                return args
        marker = object()
        result = GraphicsGym(Native()).create_sim(0, -1, 'physx', marker)
        self.assertEqual(result[:3], (0, 0, 'physx'))
        self.assertIs(result[3], marker)
        with self.assertRaises(ValueError):
            GraphicsGym(Native()).create_sim(0, 0, 'physx', marker)

    def test_physics_pins_are_independent_of_reward_and_policy_edits(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('gpu/scene.py', 'gpu/control.py',
                         'gpu/finger_reward.py', 'gpu/environment.py', 'training/policy.py'):
                path = root/'guitar_learning'/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('')
            actual = {p.relative_to(root/'guitar_learning').as_posix() for p in physics_source_paths(root)}
            self.assertEqual(actual, {'gpu/scene.py', 'gpu/control.py'})

    def test_broken_encoder_pipe_still_reaps_process(self):
        class Process:
            waited = False
            @property
            def stdin(self):
                return self
            def close(self):
                raise BrokenPipeError('encoder exited')
            def wait(self):
                self.waited = True
                return 1
        process = Process()
        code, errors = finish_video(process)
        self.assertTrue(process.waited)
        self.assertEqual(code, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn('encoder_stdin', errors[0])
        self.assertEqual(finish_video(None), (None, []))


if __name__ == '__main__':
    unittest.main()
