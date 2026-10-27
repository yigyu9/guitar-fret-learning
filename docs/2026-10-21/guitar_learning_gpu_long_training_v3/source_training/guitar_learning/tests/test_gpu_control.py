"""CPU tensor checks for the new finite GPU control law and batched ownership."""
from types import SimpleNamespace
import unittest

import numpy as np
import torch

from guitar_learning.gpu.control import (
    BatchedController, stable_pd, rotation_error, exp_rotation,
    capsule_triangle_witness, source_capsule_witness,
)
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.core.control import ACTIVE_NAMES


def fake_scene(num_envs=2, hand='left', dtype=torch.float64):
    pinned = load_prepared_reset_contract()
    initial, saved = pinned['initial'], pinned['state']
    def tensor(value): return torch.tensor(value, dtype=dtype)
    bodies = tensor([[*[r['pose']['p'][a] for a in 'xyz'], *[r['pose']['r'][a] for a in 'xyzw'],
                      *[r['vel']['linear'][a] for a in 'xyz'], *[r['vel']['angular'][a] for a in 'xyz']]
                     for kind in ('human', 'guitar', 'chair') for r in saved[kind+'_body_states']])
    rows = initial['human_properties']+initial['guitar_properties']['applied']
    q = tensor([r['pos'] for r in saved['human_dof_states']]).expand(num_envs, -1).clone()
    qd = tensor([r['vel'] for r in saved['human_dof_states']]).expand(num_envs, -1).clone()
    body = bodies.expand(num_envs, -1, -1).clone()
    scene = SimpleNamespace(device=torch.device('cpu'), num_envs=num_envs, hand=hand,
        contract=pinned, names=initial['joint_names'], human_bodies=initial['human_body_names'],
        reference105=tensor(pinned['target105']), q=q, qd=qd,
        lower=tensor(initial['native_PD_properties']['lower']), upper=tensor(initial['native_PD_properties']['upper']),
        native_control_kp=tensor(initial['control_K105']), native_control_kd=tensor(initial['control_D105']),
        mass=tensor([r['mass_kg'] for r in rows]+[1.]),
        com=tensor([r['COM_body_m'] for r in rows]+[[0., 0., 0.]]),
        inertia=tensor([r['inertia_COM_kg_m2'] for r in rows]+[np.eye(3).tolist()]),
        jacobian=torch.zeros(num_envs, 65, 6, 105, dtype=dtype))
    snapshot = dict(q=q, qd=qd, body_state=body, jacobian=scene.jacobian,
                    reset_body_snapshot=torch.ones(num_envs, dtype=torch.bool))
    return scene, snapshot


class GpuControlTests(unittest.TestCase):
    def test_stable_pd_matches_independent_backward_euler_and_separates_batches(self):
        mass = torch.tensor([[[2., .1], [.1, 1.]], [[1., 0.], [0., 3.]]], dtype=torch.float64)
        error = torch.tensor([[.2, -.1], [-.3, .4]], dtype=torch.float64)
        velocity = torch.tensor([[.3, .2], [.1, -.2]], dtype=torch.float64)
        kp, kd, gravity = torch.tensor([20., 15.]), torch.tensor([2., 3.]), torch.tensor([[1., 2.], [3., 4.]])
        raw, predicted, feedback = stable_pd(mass, error, velocity, kp, kd, gravity)
        for i in range(2):
            m, e, v, k, d, g = [a.detach().numpy() for a in (mass[i], error[i], velocity[i], kp, kd, gravity[i])]
            lhs = m+np.diag(d/240+k/240**2)
            expected_v = np.linalg.solve(lhs, m@v+k*e/240)
            expected_feedback = k*e-(d+k/240)*expected_v
            np.testing.assert_allclose(predicted[i], expected_v, atol=1e-9)
            np.testing.assert_allclose(feedback[i], expected_feedback, atol=1e-9)
            np.testing.assert_allclose(raw[i], g+expected_feedback, atol=1e-9)

    def test_rotation_error_shortest_path_and_near_zero(self):
        basis = torch.eye(3, dtype=torch.float64)
        q = torch.tensor([[0., 0., 0.], [0., 0., 3.1]], dtype=torch.float64)
        target = torch.tensor([[1e-10, 0., 0.], [0., 0., -3.1]], dtype=torch.float64)
        error = rotation_error(q, target, basis)
        self.assertAlmostEqual(float(error[0, 0]), 1e-10)
        self.assertAlmostEqual(float(error[1, 2]), 2*np.pi-6.2)
        self.assertTrue(torch.isfinite(exp_rotation(torch.zeros(2, 3))).all())

    def test_capsule_triangle_interior_edge_endpoint_and_batch_isolation(self):
        triangles = torch.tensor([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]], dtype=torch.float64)
        a = torch.tensor([[.2, .2, 1.], [2., 0., .5], [.2, .2, -.5]], dtype=torch.float64)
        b = torch.tensor([[.2, .2, 2.], [2., 0., 1.], [.2, .2, .5]], dtype=torch.float64)
        axis, surface = capsule_triangle_witness(a, b, triangles)
        np.testing.assert_allclose(axis[0], a[0], atol=1e-12)
        np.testing.assert_allclose(surface[0], [.2, .2, 0.], atol=1e-12)
        np.testing.assert_allclose(surface[1], [1., 0., 0.], atol=1e-12)
        np.testing.assert_allclose(axis[2], surface[2], atol=1e-12)
        degenerate = torch.tensor([[[3., 3., 3.]]*3], dtype=triangles.dtype)
        repeated_axis, repeated_surface = capsule_triangle_witness(a, b, torch.cat((triangles, degenerate)))
        np.testing.assert_allclose(repeated_axis, axis, atol=1e-12)
        np.testing.assert_allclose(repeated_surface, surface, atol=1e-12)

    def test_finite_mixed_ownership_mass_and_no_state_mutation(self):
        scene, snapshot = fake_scene()
        controller = BatchedController(scene)
        original = {k: v.clone() for k, v in snapshot.items()}
        target = controller.targets(torch.zeros(2, 39, dtype=scene.q.dtype), snapshot)
        effort = controller.efforts(snapshot)
        self.assertEqual(target.shape, (2, 105))
        self.assertEqual(effort.shape, (2, 105))
        self.assertTrue(torch.isfinite(effort).all())
        self.assertTrue((effort.abs() <= controller.caps).all())
        self.assertTrue((effort[:, controller.position] == 0).all())
        self.assertTrue((effort[:, controller.zero] == 0).all())
        self.assertTrue((torch.linalg.eigvalsh(controller.diagnostics['lower_mass']) > 0).all())
        self.assertGreater(float(controller.diagnostics['lower_gravity'].abs().max()), .1)
        self.assertTrue(controller.diagnostics['chest_witness_certified'].all())
        # Independently computed original convex optimizer witness at the pinned pose.
        np.testing.assert_allclose(controller.diagnostics['chest_gap'], -.00022211938115050678, atol=1e-7)
        self.assertLess(float(controller.diagnostics['foot_residual'].abs().max()), 1.)
        for key, value in original.items():
            self.assertTrue(torch.equal(snapshot[key], value), key)
        np.testing.assert_allclose(effort[0], effort[1], atol=1e-10)
        self.assertFalse(controller.contract['native_cpu_parity'])

    def test_uncertified_fast_candidate_uses_full_surface_without_cross_batch_changes(self):
        triangles = torch.tensor([
            [[.1, 1., 0.], [1., .1, 0.], [1., 1., 0.]],
            [[-1., -1., -.1], [1., -1., -.1], [0., 1., -.1]],
        ], dtype=torch.float64)
        a = torch.tensor([[0., 0., 1.], [.8, .8, 1.]], dtype=torch.float64)
        b = a+torch.tensor([0., 0., 1.], dtype=a.dtype)
        axis, surface, certified, fallback, fast = source_capsule_witness(
            a, b, triangles, triangles.amin(1), triangles.amax(1), candidate_count=1)
        expected_axis, expected_surface = capsule_triangle_witness(a, b, triangles)
        np.testing.assert_allclose(axis, expected_axis, atol=1e-12)
        np.testing.assert_allclose(surface, expected_surface, atol=1e-12)
        self.assertEqual(fallback.tolist(), [True, False])
        self.assertEqual(fast.tolist(), [False, True])
        self.assertTrue(certified.all())

    def test_action_rates_full_left_limits_and_partial_reset(self):
        scene, snapshot = fake_scene()
        controller = BatchedController(scene)
        action = torch.ones(2, 39, dtype=scene.q.dtype)
        action[1] = -1
        target = controller.targets(action, snapshot).clone()
        left = [i for i, n in enumerate(ACTIVE_NAMES) if n.startswith('LH:')]
        native = controller.active[left]
        self.assertTrue(torch.equal(controller.action_low[left], scene.lower[native]))
        self.assertTrue(torch.equal(controller.action_high[left], scene.upper[native]))
        self.assertTrue(((target[:, native]-controller.reference[native]).abs() <= 4/60+1e-12).all())
        other = target[1].clone()
        controller.reset(torch.tensor([0]), snapshot)
        self.assertTrue(torch.equal(controller.target[0], controller.reference))
        self.assertTrue(torch.equal(controller.target[1], other))
        self.assertTrue(torch.equal(scene.q, snapshot['q']))


if __name__ == '__main__':
    unittest.main()
