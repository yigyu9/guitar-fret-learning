"""Synthetic CPU calculations only; never invoke the completed-run analysis."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('press_baseline_tool', Path(__file__).with_name('compare_baseline.py'))
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def episode(left, safe=True):
    return dict(song=dict(left_success_count=sum(left), stage_success=False),
        left_note_ledger=dict(values=dict(left=left, contact_done=[True, True], clean=[.3, .7])),
        left_curriculum=dict(full_safe=safe), task_time_s=2. if safe else .5,
        failure_reasons=[] if safe else ['guitar_rotation'])


class BaselineCalculations(unittest.TestCase):
    def test_episode_and_finger_denominators_do_not_turn_empty_safe_groups_into_zero(self):
        targets = [dict(finger=1), dict(finger=3)]
        result = tool.group([episode([True, True]), episode([True, False], False)], targets)
        self.assertEqual((result['episodes'], result['safe'], result['physical_failures']), (2, 1, 1))
        self.assertEqual(result['mean_achieved_notes'], 1.5)
        self.assertEqual(result['mean_clean_seconds'], 1.)
        self.assertEqual([f['achieved_total'] for f in result['fingers']], [2, 0, 1, 0])
        self.assertEqual(result['fingers'][2]['success_fraction'], .5)
        self.assertIsNone(result['fingers'][1]['success_fraction'])
        self.assertEqual(result['failed_below1s'], 1)
        empty = tool.group([], targets)
        self.assertIsNone(empty['mean_achieved_notes'])
        self.assertNotIn('motion', empty)

    def test_motion_is_equal_episode_and_requires_matching_joint_order(self):
        a, b = episode([True, False]), episode([False, False])
        names = ['LH:axis%d'%i for i in range(21)]
        values = {k:[x]*21 for k,x in [('actual_range_rad', 2.), ('target_range_rad', 3.),
            ('tracking_error_rms_rad', .01), ('limit_outward_command_fraction', .2),
            ('action_zero_fraction', 0.), ('action_positive_fraction', 1.), ('action_negative_fraction', 0.)]}
        a['left_finger_motion'] = dict(joint_names=names, values=values)
        b['left_finger_motion'] = copy.deepcopy(a['left_finger_motion'])
        b['left_finger_motion']['values']['actual_range_rad'] = [4.]*21
        result = tool.group([a, b], [dict(finger=1), dict(finger=3)])
        self.assertEqual(result['motion']['equal_episode_axis_means']['actual_range_rad'], [3.]*21)
        self.assertEqual(result['motion']['all_one_sign_episode_fraction'], [1.]*21)
        b['left_finger_motion']['joint_names'] = names[::-1]
        with self.assertRaises(ValueError): tool.group([a, b], [dict(finger=1), dict(finger=3)])

    def test_old_pin_uses_preserved_copy_while_new_pin_uses_actual_active_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); phase = root/'docs/old'
            active = root/'guitar_learning/gpu/environment.py'
            old = phase/'source_training/guitar_learning/gpu/environment.py'
            active.parent.mkdir(parents=True); old.parent.mkdir(parents=True)
            active.write_text('new source\n'); old.write_text('old source\n')
            pins = {str(active):tool.sha(old)}
            with patch.object(tool, 'ROOT', root):
                self.assertEqual(tool.check_pins(pins, phase, historical=True), 1)
                with self.assertRaises(ValueError): tool.check_pins(pins, phase, historical=False)
                old.write_text('tampered\n')
                with self.assertRaises(ValueError): tool.check_pins(pins, phase, historical=True)
                asset = root/'guitar_learning/asset.json'; asset.write_text('{}\n')
                self.assertEqual(tool.check_pins({str(asset):tool.sha(asset)}, phase, historical=True), 1)

    def test_incomplete_training_or_discarded_transitions_cannot_pass_guard(self):
        report = dict(completed=True, optimizer_updates=100, transitions=tool.TRANSITIONS,
            updates=[None]*100, lifecycle_verified=True, failure=None, cleanup_errors=[], changed_inputs=[], missing_import_pins=[],
            gpu_scene=dict(closed=True, physx_use_gpu=True, use_gpu_pipeline=True, environment_count=1024, physics_steps=12800),
            journal=dict(sampled=tool.TRANSITIONS, logged=tool.TRANSITIONS, durable=tool.TRANSITIONS,
                committed=tool.TRANSITIONS, discarded=0, pending_transitions=0, closed=True, failed=False))
        tool.training_complete(report)
        report['completed'] = False
        with self.assertRaises(ValueError): tool.training_complete(report)
        report['completed'] = True; report['journal']['discarded'] = 1
        with self.assertRaises(ValueError): tool.training_complete(report)


if __name__ == '__main__':
    unittest.main()
