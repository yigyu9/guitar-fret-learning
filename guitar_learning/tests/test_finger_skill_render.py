"""Native render plumbing with fake cameras/pool; no Isaac import required."""
import ast
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.tool.demonstration import render_finger_skill as render


class FakeGym:
    def __init__(self):
        self.colors, self.properties, self.locations, self.graphics = [], [], [], 0

    def set_rigid_body_color(self, *args): self.colors.append(args)
    def create_camera_sensor(self, env, properties):
        self.properties.append(properties)
        return len(self.properties)-1
    def set_camera_location(self, *args): self.locations.append(args)
    def step_graphics(self, sim): self.graphics += 1
    def render_all_camera_sensors(self, sim): pass
    def get_camera_image(self, *args):
        rgba = np.zeros((720, 1280, 4), dtype=np.uint8)
        rgba[0, 0] = (1, 2, 3, 255)
        rgba[-1, 0] = (4, 5, 6, 255)
        return rgba


def fixture():
    gym = FakeGym()
    scene = SimpleNamespace(gym=gym, sim='sim', envs=['env0', 'env1'], actors=[['human0']],
                            human_bodies=['LH:palm', 'LH:index1', 'LH:thumb3', 'RH:index1'])
    data = dict(q=torch.zeros(2, 105), qd=torch.zeros(2, 105), target=torch.zeros(2, 105),
                body_state=torch.zeros(2, 10, 13), contact_force=torch.zeros(2, 10, 3),
                physics_step=torch.zeros(2, dtype=torch.long))
    scene.snapshot = lambda: data
    pool = SimpleNamespace(scene=scene, environment=SimpleNamespace(action=torch.zeros(2, 39)))
    api = SimpleNamespace(CameraProperties=SimpleNamespace, Vec3=lambda *values: values,
                          MESH_VISUAL=7, IMAGE_COLOR=9)
    return pool, api, data


class FingerSkillRenderTests(unittest.TestCase):
    def test_cameras_and_color_only_modify_native_visuals(self):
        pool, api, data = fixture()
        old = {key: value.clone() for key, value in data.items()}
        cameras = render._create_cameras(pool.scene, api)
        self.assertEqual(cameras, dict(hand=0, fullbody=1))
        self.assertEqual(len(pool.scene.gym.colors), 2)
        self.assertEqual([row[2] for row in pool.scene.gym.colors], [1, 2])
        for props in pool.scene.gym.properties:
            self.assertEqual((props.width, props.height, props.horizontal_fov), (1280, 720, 55.))
        self.assertTrue(all(torch.equal(value, data[key]) for key, value in old.items()))

    def test_first_env0_episode_only_no_reset_frames_and_no_vertical_flip(self):
        pool, api, data = fixture()
        videos = dict(hand=SimpleNamespace(stdin=io.BytesIO()), fullbody=SimpleNamespace(stdin=io.BytesIO()))
        capture = render._EnvZeroCapture(pool, api, np, dict(hand=0, fullbody=1), videos)
        for tick in range(1, 4):
            data['physics_step'][:] = tick*4
            pool.environment.action[:] = tick/10
            ended = tick == 3
            episodes = [dict(env_id=0 if ended else 1, song=dict(left_success_count=0))] if tick > 1 else []
            capture.record(tick-1, None, None, torch.tensor([ended, not ended]), torch.zeros(2, dtype=torch.bool), episodes)
        self.assertEqual(len(capture.samples), 3)
        self.assertEqual(capture.frame_times_s, [2/60])
        self.assertEqual(capture.episode['env_id'], 0)
        self.assertEqual([int(row['physics_step']) for row in capture.samples], [4, 8, 12])
        self.assertTrue(np.allclose(capture.samples[0]['action'], .1))
        raw = videos['hand'].stdin.getvalue()
        self.assertEqual(len(raw), 1280*720*3)
        self.assertEqual(raw[:3], bytes((1, 2, 3)))
        self.assertEqual(raw[-1280*3:-1280*3+3], bytes((4, 5, 6)))
        # The collector may reset and continue other rows in the same chunk.
        data['physics_step'][0] = 4
        capture.record(3, None, None, torch.zeros(2, dtype=torch.bool), torch.zeros(2, dtype=torch.bool), [])
        self.assertEqual(len(capture.samples), 3)

    def test_capture_rejects_discontinuous_clock_and_unreported_terminal(self):
        pool, api, data = fixture()
        capture = render._EnvZeroCapture(pool, api, np, {}, {})
        data['physics_step'][0] = 8
        with self.assertRaisesRegex(RuntimeError, 'reset or skipped'):
            capture.record(0, None, None, torch.zeros(2, dtype=torch.bool), torch.zeros(2, dtype=torch.bool), [])
        data['physics_step'][0] = 4
        with self.assertRaisesRegex(RuntimeError, 'without a completed'):
            capture.record(0, None, None, torch.tensor([True, False]), torch.zeros(2, dtype=torch.bool), [])

    def test_new_termination_state_is_captured_at_the_same_endpoint(self):
        pool, api, data = fixture()
        pool.contract = dict(observation=dict(fields=['unused', 'wrist_termination.active',
            'wrist_termination.elapsed_s', 'wrist_termination.preparation_remaining_s',
            'wrist_termination.severe_elapsed_s']))
        pool.observation = dict(state=torch.tensor([[9., 1., .5, 0., .2], [8., 0., 0., 1., 0.]]))
        data['physics_step'][0] = 4
        capture = render._EnvZeroCapture(pool, api, np, {}, {})
        capture.record(0, None, None, torch.zeros(2, dtype=torch.bool), torch.zeros(2, dtype=torch.bool), [])
        np.testing.assert_allclose(capture.samples[0]['wrist_termination_state'], [1., .5, 0., .2])
        pool.observation['state'][0, 2] = .9
        self.assertEqual(float(capture.samples[0]['wrist_termination_state'][1]), .5)

    def test_ffmpeg_never_overwrites_and_encodes_30fps_native_rgb(self):
        with patch.object(render.subprocess, 'Popen') as popen:
            render._encoder(Path('/tmp/new-output/hand.mp4'))
        args = popen.call_args.args[0]
        self.assertIn('-n', args)
        self.assertNotIn('-y', args)
        self.assertEqual(args[args.index('-r')+1], '30')
        self.assertEqual(args[args.index('-pix_fmt')+1], 'rgb24')
        self.assertEqual(args[args.index('-s')+1], '1280x720')

    def test_module_top_level_defers_native_tensor_imports_and_cli_default_scope(self):
        tree = ast.parse(Path(render.__file__).read_text())
        imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        names = [alias.name for node in imports for alias in node.names]
        self.assertFalse(any(name in ('torch', 'numpy', 'isaacgym') for name in names))
        with patch.object(render, 'render') as call, patch('sys.argv', [
                'render_finger_skill', '--checkpoint', '/tmp/current.pt', '--out', '/tmp/new-output']):
            render.main()
        self.assertEqual(call.call_args.kwargs, dict(scope='full_song', num_envs=None))


if __name__ == '__main__':
    unittest.main()
