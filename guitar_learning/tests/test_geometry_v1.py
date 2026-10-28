"""Moving-frame regressions independent of the simulator and chosen posture."""
import copy
import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.core.geometry import frame
from guitar_learning.core.geometry import world_to_guitar
from guitar_learning.core.geometry import guitar_to_world
from guitar_learning.core.geometry import body_point_motion
from guitar_learning.core.geometry import relative_point_motion
from guitar_learning.core.geometry import geometry_snapshot
from guitar_learning.core.geometry import fret_target
from guitar_learning.core.geometry import relative_sweep_inputs


def body(p, q=(0, 0, 0, 1), linear=(0, 0, 0), angular=(0, 0, 0)):
    return dict(pose=dict(p=dict(zip('xyz', p)), r=dict(zip('xyzw', q))),
                vel=dict(linear=dict(zip('xyz', linear)), angular=dict(zip('xyz', angular))))


def fixture():
    names = ['guitar', 'G:nut'] + ['G:fret%d' % n for n in range(1, 23)]
    positions = [[0, 0, 0], [0, 1, 0]] + [[0, 1 - n / 25, 0] for n in range(1, 23)]
    for n in range(1, 7):
        names += ['G:string%d' % n, 'G:string%d_end' % n]
        positions += [[(3.5 - n) * .01, 1, 0], [(3.5 - n) * .01, 0, 0]]
    humans = ['RH:pick'] + ['LH:' + f + '3' for f in ('thumb', 'index', 'middle', 'ring', 'pinky')]
    return dict(physics_step=0, guitar_body_states=[body(p) for p in positions],
                human_body_states=[body([.04, .5, -.002]) for _ in humans]), humans, names


class GeometryTests(unittest.TestCase):
    def test_snapshot_and_targets_invariant_to_joint_world_rigid_motion(self):
        state, humans, guitars = fixture()
        before = geometry_snapshot(state, humans, guitars)
        rot = Rotation.from_rotvec([.3, -.6, .2]); shift = np.array([1., -2., .4])
        moved = copy.deepcopy(state)
        for group in ('human_body_states', 'guitar_body_states'):
            for index, row in enumerate(state[group]):
                p, r = frame(row)
                moved[group][index] = body(shift + rot.apply(p), 3 * (rot * r).as_quat())
        after = geometry_snapshot(moved, humans, guitars)
        for key in ('starts_G_m', 'ends_G_m', 'pick_G_m', 'fret_markers_G_m'):
            np.testing.assert_allclose(before[key], after[key], atol=1e-14)
        np.testing.assert_allclose(fret_target(before, 6, 12), fret_target(after, 6, 12), atol=1e-14)
        goal = fret_target(after, 1, 3)
        np.testing.assert_allclose(world_to_guitar(guitar_to_world(goal, moved['guitar_body_states'][0]),
                                                moved['guitar_body_states'][0]), goal, atol=1e-14)

    def test_com_motion_and_rotating_frame_velocity(self):
        r = Rotation.from_rotvec([.2, .1, -.3]); omega = np.array([0., 0., 2.])
        com = np.array([.1, .2, .3]); origin_v = np.array([.2, -.1, .4])
        row = body([1, 2, 3], r.as_quat(), origin_v + np.cross(omega, r.apply(com)), omega)
        local = np.array([.4, -.2, .1]); p, v = body_point_motion(row, local, com)
        np.testing.assert_allclose(v, origin_v + np.cross(omega, r.apply(local)), atol=1e-14)
        pg, vg = relative_point_motion(p, v, row, com)
        np.testing.assert_allclose(pg, local, atol=1e-14)
        np.testing.assert_allclose(vg, 0, atol=1e-14)

    def test_common_motion_cannot_create_relative_sweep(self):
        state, humans, guitars = fixture(); before = geometry_snapshot(state, humans, guitars)
        moved = copy.deepcopy(state); moved['physics_step'] = 1
        for group in ('human_body_states', 'guitar_body_states'):
            for row in moved[group]:
                row['pose']['p']['x'] += .2
        sweep = relative_sweep_inputs(before, geometry_snapshot(moved, humans, guitars))
        np.testing.assert_allclose(sweep['previous_tip_g'], sweep['current_tip_g'], atol=1e-14)
        # A stationary world pick and translating guitar must produce relative motion.
        moved['human_body_states'] = state['human_body_states']
        sweep = relative_sweep_inputs(before, geometry_snapshot(moved, humans, guitars))
        np.testing.assert_allclose(sweep['current_tip_g'] - sweep['previous_tip_g'], [-.2, 0, 0])

    def test_open_string_and_invalid_legacy_sentinel(self):
        state, humans, guitars = fixture(); sample = geometry_snapshot(state, humans, guitars)
        self.assertIsNone(fret_target(sample, 1, 0))
        for string, fret in ((0, 1), (7, 1), (1, -1), (1, 23), (True, 1)):
            with self.assertRaises(ValueError): fret_target(sample, string, fret)
        with self.assertRaises(ValueError): relative_sweep_inputs(sample, sample)
        broken = copy.deepcopy(sample); broken['physics_step'] = 1; broken['starts_G_m'][0, 0] += .01
        with self.assertRaises(ValueError): relative_sweep_inputs(sample, broken)


if __name__ == '__main__':
    unittest.main()
