"""CPU checks for GPU scene property transfer and force ownership."""
import unittest
from types import SimpleNamespace
import torch

from guitar_learning.gpu.scene import GpuScene, _apply_body_properties, _body_row


class GpuSceneTests(unittest.TestCase):
    def test_pinned_body_state_order(self):
        record = dict(pose=dict(p=dict(x=1, y=2, z=3), r=dict(x=4, y=5, z=6, w=7)),
                      vel=dict(linear=dict(x=8, y=9, z=10), angular=dict(x=11, y=12, z=13)))
        self.assertEqual(_body_row(record), list(range(1, 14)))

    def test_body_transfer_preserves_mass_com_and_full_inertia(self):
        vector = lambda: SimpleNamespace(x=0., y=0., z=0.)
        prop = SimpleNamespace(mass=0., com=vector(),
                               inertia=SimpleNamespace(x=vector(), y=vector(), z=vector()), flags=19)
        row = dict(mass_kg=2.5, COM_body_m=[.1, .2, .3],
                   inertia_COM_kg_m2=[[1., .1, .2], [.1, 2., .3], [.2, .3, 3.]])
        _apply_body_properties([prop], [row])
        self.assertEqual(prop.mass, 2.5)
        self.assertEqual(prop.com.y, .2)
        self.assertEqual(prop.inertia.z.y, .3)
        self.assertEqual(prop.flags, 19)
        with self.assertRaises(ValueError):
            _apply_body_properties([], [row])

    def test_step_rejects_position_effort_and_zero_effort_before_native_call(self):
        scene = object.__new__(GpuScene)
        scene.closed, scene.device = False, torch.device('cpu')
        scene.target, scene.efforts = torch.zeros(2, 105), torch.zeros(2, 105)
        scene.lower, scene.upper = torch.full((105,), -1.), torch.ones(105)
        scene.effort_caps = torch.ones(105)
        scene.metadata = dict(position_indices=[0], zero_indices=[1])
        for index in (0, 1):
            effort = scene.efforts.clone()
            effort[:, index] = .5
            with self.assertRaises(ValueError):
                scene.step(scene.target, effort)

    def test_reset_snapshot_uses_saved_pose_and_zero_contact_without_origin_shift(self):
        scene = object.__new__(GpuScene)
        scene._bodies = torch.arange(78, dtype=torch.float32).view(2, 3, 13)
        scene.rigid_guitar = SimpleNamespace(expand=lambda value: value.clone())
        scene.origins = torch.tensor([[100., 200., 0.], [300., 400., 0.]])
        scene._prepared_bodies = torch.full((3, 13), 7.)
        scene._reset_mask = torch.tensor([False, True])
        scene.q = scene.qd = scene.target = torch.zeros(2, 105)
        scene.jacobian = torch.zeros(2, 2, 6, 105)
        scene.contact_force = torch.ones(2, 3, 3)
        scene.episode_steps = torch.tensor([8, 0])
        snap = scene.snapshot()
        self.assertTrue(torch.equal(snap['body_state'][0], scene._bodies[0]))
        self.assertTrue(torch.equal(snap['body_state'][1], scene._prepared_bodies))
        self.assertTrue(torch.equal(snap['contact_force'][0], scene.contact_force[0]))
        self.assertEqual(float(snap['contact_force'][1].abs().sum()), 0.)
        self.assertTrue(torch.equal(scene.contact_force, torch.ones(2, 3, 3)))


if __name__ == '__main__':
    unittest.main()
