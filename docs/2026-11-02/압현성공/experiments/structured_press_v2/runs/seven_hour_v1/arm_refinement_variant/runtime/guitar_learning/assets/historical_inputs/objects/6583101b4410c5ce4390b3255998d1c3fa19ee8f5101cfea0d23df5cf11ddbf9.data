import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from guitar_learning.tests.test_transition_solver import fixture
from guitar_learning.tool.experiments.transition.contact_teacher import Controller, input_paths


def environment():
    sample, codec, targets, initial = fixture()
    names = initial['joint_names']
    scene = SimpleNamespace(names=names, human_bodies=initial['human_body_names'],
        guitar_bodies=initial['guitar_body_names'], target=np.zeros(105))
    env = SimpleNamespace(last_sample=sample,
        last_measured=dict(physics_step=sample['native']['physics_step'], task_time_s=0., targets={}),
        control=SimpleNamespace(contract=codec, codec_previous=codec.q_ref.copy(),
                                session=SimpleNamespace(scene=scene)))
    task = SimpleNamespace(targets=targets[:1], duration_s=4.)
    plan = dict(candidates=[dict(name=name, action39=[0.]*39)
        for name in ('single_a', 'overlap', 'single_b', 'release')], declared_context_blockers=[])
    return env, task, plan


def advance(env, now):
    step = env.last_sample['native']['physics_step'] + 4
    env.last_sample['native']['physics_step'] = step
    env.last_sample['geometry']['physics_step'] = step
    env.last_measured.update(physics_step=step, task_time_s=now)


class ContactTeacherTests(unittest.TestCase):
    def test_bounded_correction_uses_real_source_wire_and_no_state_mutation(self):
        env, task, plan = environment()
        before = copy.deepcopy(env.last_sample)
        previous = env.control.codec_previous.copy()
        target105 = env.control.session.scene.target.copy()
        reference = env.control.contract.q_ref.copy()
        controller = Controller(plan, task)
        action = np.asarray(controller.action(0., env=env))
        self.assertEqual(action.shape, (39,))
        self.assertTrue(np.isfinite(action).all())
        self.assertTrue((np.abs(action) <= 1.).all())
        np.testing.assert_array_equal(action[33:], np.zeros(6))
        self.assertLessEqual(np.max(np.abs(controller.diagnostic['correction_rad33'])), .01000000001)
        self.assertGreater(np.max(np.abs(action[:33])), 0.)
        self.assertEqual(env.last_sample, before)
        np.testing.assert_array_equal(env.control.codec_previous, previous)
        np.testing.assert_array_equal(env.control.session.scene.target, target105)
        np.testing.assert_array_equal(env.control.contract.q_ref, reference)
        geometry = controller.diagnostic['target_geometry'][0]
        self.assertEqual(geometry['fret_body'], 'G:fret7')
        self.assertAlmostEqual(geometry['source_top_G_m'][2], .01123, places=6)
        self.assertAlmostEqual(geometry['desired_vertex_G_m'][2], .01073, places=6)
        self.assertIn('not PhysX', controller.diagnostic['target_scope'])

    def test_live_guitar_frame_changes_world_goal(self):
        env, task, plan = environment()
        first = Controller(plan, task)
        first.action(0., env=env)
        moved = copy.deepcopy(env)
        for body in moved.last_sample['native']['guitar_body_states']:
            body['pose']['p']['x'] += .002
        second = Controller(plan, task)
        second.action(0., env=moved)
        one = np.asarray(first.diagnostic['target_geometry'][0]['desired_vertex_W_m'])
        two = np.asarray(second.diagnostic['target_geometry'][0]['desired_vertex_W_m'])
        np.testing.assert_allclose(two-one, [.002, 0., 0.], atol=1e-12)

    def test_clean_contact_holds_command_and_release_discards_feedback(self):
        env, task, plan = environment()
        controller = Controller(plan, task)
        first = controller.action(0., env=env)
        self.assertTrue(np.any(np.abs(controller.offset) > 0.))
        target_id = task.targets[0].target_id
        env.last_measured['targets'][target_id] = dict(clean_target_candidate=True)
        advance(env, 1/60.)
        held = controller.action(1/60., env=env)
        np.testing.assert_array_equal(first, held)
        self.assertTrue(controller.diagnostic['clean_hold'])
        # Use the actual sequence rather than jumping the controller clock.
        for tick in range(2, 181):
            advance(env, tick/60.)
            controller.action(tick/60., env=env)
        self.assertTrue(controller.diagnostic['feedback_reset_for_release'])
        np.testing.assert_array_equal(controller.offset, np.zeros(33))

    def test_missing_environment_or_stale_native_sample_rejected(self):
        env, task, plan = environment()
        with self.assertRaises(ValueError):
            Controller(plan, task).action(0.)
        controller = Controller(plan, task)
        controller.action(0., env=env)
        env.last_measured['task_time_s'] = 1/60.
        with self.assertRaisesRegex(ValueError, 'same-step'):
            controller.action(1/60., env=env)

    def test_declared_inputs_include_source_fret_and_finger_surfaces(self):
        paths = input_paths()
        self.assertTrue(any(path.endswith('guitar_asset.xml') for path in paths))
        self.assertTrue(any(path.endswith('ring2_left.stl') for path in paths))
        self.assertTrue(any(path.endswith('ring3_left.stl') for path in paths))

    def test_original_schedule_and_input_aliases_survive_probe_scoped_patches(self):
        from guitar_learning.tool.experiments.transition import teacher, solver
        env, task, plan = environment()
        expected_paths = input_paths()
        with patch.object(teacher, 'Controller', side_effect=AssertionError('recursive schedule')), patch.object(solver, 'input_paths', side_effect=AssertionError('recursive inputs')):
            controller = Controller(plan, task)
            self.assertEqual(len(controller.action(0., env=env)), 39)
            self.assertEqual(input_paths(), expected_paths)

    def test_overlap_lower_goal_positive_is_ready_without_impossible_clean(self):
        env, task, plan = environment()
        _, _, targets, _ = fixture()
        task.targets = targets
        env.last_measured['targets'] = {
            targets[0].target_id: dict(clean_target_candidate=True, positive_target_candidate=True),
            targets[1].target_id: dict(clean_target_candidate=False, positive_target_candidate=True)}
        controller = Controller(plan, task)
        command = controller.action(0., env=env)
        for tick in range(1, 85):
            advance(env, tick/60.)
            action = controller.action(tick/60., env=env)
        self.assertEqual(controller.diagnostic['active_target_ids'], [t.target_id for t in targets])
        self.assertTrue(controller.diagnostic['goal_hold'])
        self.assertFalse(controller.diagnostic['clean_hold'])
        self.assertFalse(controller.diagnostic['contact_feedback_applied'])
        np.testing.assert_array_equal(action, command)
        env.last_measured['targets'][targets[0].target_id]['clean_target_candidate'] = False
        advance(env, 85/60.)
        controller.action(85/60., env=env)
        lower_goal = controller.diagnostic['target_geometry'][1]
        self.assertTrue(lower_goal['ready_before'])
        self.assertEqual(lower_goal['readiness_field'], 'positive_target_candidate')
        env.last_measured['targets'][targets[0].target_id]['clean_target_candidate'] = True
        for tick in range(86, 181):
            advance(env, tick/60.)
            controller.action(tick/60., env=env)
        self.assertEqual(controller.diagnostic['active_target_ids'], [targets[1].target_id])
        self.assertFalse(controller.diagnostic['goal_hold'])
        self.assertTrue(controller.diagnostic['contact_feedback_applied'])
        self.assertEqual(controller.diagnostic['target_geometry'][0]['readiness_field'], 'clean_target_candidate')


if __name__ == '__main__':
    unittest.main()
