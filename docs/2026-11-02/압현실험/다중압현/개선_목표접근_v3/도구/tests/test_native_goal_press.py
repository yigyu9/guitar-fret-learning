import copy
import importlib.util
import math
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1]/'native_goal_press.py'
spec = importlib.util.spec_from_file_location('native_goal_tested', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class GoalProtocolTests(unittest.TestCase):
    def test_smooth_arrival_hold_and_release(self):
        self.assertEqual(module.fraction(.5), 0)
        for tick in range(150, 292):
            self.assertEqual(module.fraction(tick/60.), 1)
        self.assertEqual(module.fraction(5.5), 0)
        rows = [module.fraction(i/60.) for i in range(331)]
        self.assertTrue(all(0 <= value <= 1 for value in rows))
        self.assertLess(max(abs(b-a)*.7*60 for a,b in zip(rows,rows[1:])), 4.)
        for bad in (-1, 6, float('nan')):
            with self.assertRaises(ValueError):
                module.fraction(bad)

    def test_expansion_requires_completed_prior_and_observed_low_delay(self):
        good = dict(completed=True, capture_completed=True, protocol_completed=True,
            final_state_verified=True, failure=None,
            impact=dict(maximum_elapsed_ratio=1.07, inspection_errors=[], severe=False))
        self.assertTrue(module.expansion_allowed(good))
        for name in ('completed', 'capture_completed', 'protocol_completed', 'final_state_verified'):
            bad = copy.deepcopy(good);bad[name] = False
            self.assertFalse(module.expansion_allowed(bad))
        for ratio in (None, 1.25, 1.42, float('nan')):
            bad = copy.deepcopy(good);bad['impact']['maximum_elapsed_ratio'] = ratio
            self.assertFalse(module.expansion_allowed(bad))
        bad = copy.deepcopy(good);bad['impact']['inspection_errors'] = ['case']
        self.assertFalse(module.expansion_allowed(bad))

    def test_geometry_or_separate_latches_cannot_authorize_teacher(self):
        episode = dict(reason='timeline_complete', simultaneous_press=dict(success=True,
            full_safe=True, source_score_window_s=[3.3,4.8], observed_s=1.5, clean_s=1.5,
            longest_clean_s=1.5, wrong_union_s=0, unsafe_s=0, individual_achievements=[True, True]))
        self.assertTrue(module.teacher_allowed(episode, True, True))
        for field,value in [('clean_s',0), ('longest_clean_s',.2), ('observed_s',1.4),
                ('wrong_union_s',.01), ('unsafe_s',.001), ('full_safe',False),
                ('individual_achievements',[True,False])]:
            bad = copy.deepcopy(episode);bad['simultaneous_press'][field] = value
            self.assertFalse(module.teacher_allowed(bad, True, True))
        self.assertFalse(module.teacher_allowed(episode, False, True))
        self.assertFalse(module.teacher_allowed(episode, True, False))


if __name__ == '__main__':
    unittest.main()
