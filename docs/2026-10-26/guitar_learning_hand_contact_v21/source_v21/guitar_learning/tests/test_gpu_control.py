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
from guitar_learning.core.control import ACTIVE_NAMES, LEFT_HAND_NAMES


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


def legacy_targets(controller, action):
    """The previous absolute-reference law, including its final native limits."""
    action = action.clamp(-1, 1)
    ref = controller.reference[controller.active]
    requested = ref+torch.where(action >= 0, controller.action_high-ref,
                                ref-controller.action_low)*action
    old = controller.target[:, controller.active]
    alpha = torch.full_like(controller.alpha, .2)
    if controller.scene.hand == 'left':
        alpha[[ACTIVE_NAMES.index(n) for n in LEFT_HAND_NAMES]] = .45
    smoothed = old+alpha*(requested-old)
    step = controller.rate[controller.active]/60
    active = torch.maximum(torch.minimum(smoothed, old+step), old-step)
    target = controller.reference.expand(controller.num_envs, -1).clone()
    target[:, controller.active] = torch.maximum(torch.minimum(active, controller.action_high), controller.action_low)
    target = controller._foot_targets(target)
    target = torch.maximum(torch.minimum(target, controller.target+controller.rate/60), controller.target-controller.rate/60)
    target = torch.maximum(torch.minimum(target, controller.upper), controller.lower)
    target[:, controller.zero] = controller.reference[controller.zero]
    return target


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

    def test_incremental_fingers_accumulate_through_h32_and_zero_holds_target(self):
        scene, snapshot = fake_scene()
        controller = BatchedController(scene)
        ids = controller.incremental_actions
        native = controller.active[ids]
        action = torch.zeros(2, 39, dtype=scene.q.dtype)
        action[0, ids] = torch.linspace(-.2, .2, 21, dtype=scene.q.dtype)
        action[1, ids] = torch.linspace(.1, -.3, 21, dtype=scene.q.dtype)
        initial_state = {key: value.clone() for key, value in snapshot.items()}
        for tick in range(1, 65):
            target = controller.targets(action, snapshot)
            expected = controller.reference[native]+tick*(4/60)*action[:, ids]
            expected = torch.maximum(torch.minimum(expected, scene.upper[native]), scene.lower[native])
            torch.testing.assert_close(target[:, native], expected, rtol=0, atol=1e-12)
        held = controller.target[:, native].clone()
        # Physical lag/disturbance cannot recenter a zero action toward q or q_ref.
        snapshot['q'][:, native] += .01
        for _ in range(5):
            controller.targets(torch.zeros_like(action), snapshot)
            self.assertTrue(torch.equal(controller.target[:, native], held))
        snapshot['q'][:, native] -= .01
        for key, value in initial_state.items():
            torch.testing.assert_close(snapshot[key], value, rtol=0, atol=1e-15)
        self.assertTrue(torch.equal(controller.alpha[ids], torch.ones(21, dtype=scene.q.dtype)))
        self.assertTrue(torch.isin(native, controller.position).all())

    def test_incremental_asymmetric_limits_reverse_immediately_without_windup(self):
        scene, snapshot = fake_scene()
        native = torch.tensor([scene.names.index(n) for n in LEFT_HAND_NAMES])
        scene.lower[native] = scene.reference105[native]-torch.linspace(.013, .071, 21)
        scene.upper[native] = scene.reference105[native]+torch.linspace(.032, .009, 21)
        controller = BatchedController(scene)
        ids = controller.incremental_actions
        action = torch.zeros(2, 39, dtype=scene.q.dtype)
        action[0, ids], action[1, ids] = 1, -1
        for _ in range(12):
            controller.targets(action, snapshot)
        self.assertTrue(torch.equal(controller.target[0, native], scene.upper[native]))
        self.assertTrue(torch.equal(controller.target[1, native], scene.lower[native]))
        before = controller.target[:, native].clone()
        action[:, ids] *= -.25
        controller.targets(action, snapshot)
        expected = before+(4/60)*action[:, ids]
        expected = torch.maximum(torch.minimum(expected, scene.upper[native]), scene.lower[native])
        torch.testing.assert_close(controller.target[:, native], expected, rtol=0, atol=1e-15)
        self.assertTrue((controller.target[0, native] < before[0]).all())
        self.assertTrue((controller.target[1, native] > before[1]).all())

    def test_incremental_partial_reset_preserves_other_environment_accumulator_and_state(self):
        scene, snapshot = fake_scene(num_envs=3)
        controller = BatchedController(scene)
        action = torch.full((3, 39), .1, dtype=scene.q.dtype)
        original = {key: value.clone() for key, value in snapshot.items()}
        for _ in range(6):
            controller.targets(action, snapshot)
        before = controller.target.clone()
        controller.reset([1], snapshot)
        self.assertTrue(torch.equal(controller.target[1], controller.reference))
        self.assertTrue(torch.equal(controller.target[[0, 2]], before[[0, 2]]))
        native = controller.active[controller.incremental_actions]
        controller.targets(torch.zeros_like(action), snapshot)
        self.assertTrue(torch.equal(controller.target[1, native], controller.reference[native]))
        self.assertTrue(torch.equal(controller.target[[0, 2]][:, native], before[[0, 2]][:, native]))
        for key, value in original.items():
            self.assertTrue(torch.equal(snapshot[key], value), key)

    def test_other_channels_and_entire_right_path_match_previous_law_exactly(self):
        generator = torch.Generator().manual_seed(7)
        for hand in ('left', 'right'):
            scene, snapshot = fake_scene(hand=hand)
            controller = BatchedController(scene)
            unchanged = torch.ones(105, dtype=torch.bool)
            if hand == 'left':
                unchanged[controller.active[controller.incremental_actions]] = False
            for _ in range(32):
                action = 1.6*torch.rand(2, 39, dtype=scene.q.dtype, generator=generator)-.8
                expected = legacy_targets(controller, action)
                actual = controller.targets(action, snapshot)
                self.assertTrue(torch.equal(actual[:, unchanged], expected[:, unchanged]), hand)
            self.assertEqual(controller.contract['schema'],
                'guitar_learning.gpu_finite_control.v3' if hand == 'left' else 'guitar_learning.gpu_finite_control.v2')
            if hand == 'right':
                self.assertNotIn('action_codec', controller.contract)
                self.assertEqual(controller.incremental_actions.numel(), 0)

    def test_incremental_action_contract_declares_semantics_not_source_identity(self):
        scene, _ = fake_scene()
        controller = BatchedController(scene)
        codec = controller.contract['action_codec']
        self.assertEqual(codec['schema'], 'guitar_learning.gpu_left_incremental_fingers.v1')
        self.assertEqual(codec['incremental_joint_names'], list(LEFT_HAND_NAMES))
        self.assertEqual(codec['incremental_action_indices'], [ACTIVE_NAMES.index(n) for n in LEFT_HAND_NAMES])
        self.assertEqual(codec['velocity_scale_rad_s'], 4.)
        self.assertEqual(codec['control_hz'], 60)
        self.assertEqual(codec['zero_action'], 'hold previous target')
        self.assertIn('no windup', codec['limit_memory'])
        self.assertEqual(controller.contract['native_position_count'], 48)
        self.assertEqual(controller.contract['native_effort_count'], 57)


if __name__ == '__main__':
    unittest.main()
