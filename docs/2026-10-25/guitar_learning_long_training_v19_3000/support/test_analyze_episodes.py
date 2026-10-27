"""Independent small checks for derived-report denominators and zero handling."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

path = Path(__file__).with_name('analyze_episodes.py')
spec = importlib.util.spec_from_file_location('episode_analysis', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def targets():
    result = []
    for finger, count in enumerate((25, 18, 12, 12), 1):
        for i in range(count):
            result.append(dict(target_id=str(len(result)), finger=finger, fret=4, string=0,
                press_s=3., onset_s=3.1, end_s=3.3))
    return result


def episode(safe):
    return dict(reason='timeline_complete' if safe else 'terminal_failure',
        left_curriculum={'full_safe':safe}, failure_reasons=[] if safe else ['guitar_displacement', 'ground'],
        song=dict(safety_invalidated=not safe, left_success_count=2, stage_success=False,
            mean_clean_audible_fraction=.2), reward=1., cost=2., task_time_s=3.,
        reward_components={'song_left_contact':.3})


class AnalysisTests(unittest.TestCase):
    def test_exact_integer_histogram_quantiles(self):
        values = [0, 0, 1, 2, 5, 10, 67]
        hist = np.bincount(values, minlength=68)
        result = module.distribution(hist)
        for name, q in (('median', .5), ('p10', .1), ('p90', .9), ('p95', .95)):
            self.assertEqual(result[name], float(np.quantile(values, q)))
        self.assertEqual(result['maximum'], 67)
        self.assertEqual(result['zero_fraction'], 2/7)

    def test_no_exposure_zero_excluded_and_only_curriculum_zeros_failures(self):
        aggregate = module.Aggregate(0, 100, targets())
        arrays = {key:np.zeros(67) for key in module.FIELDS+('surface_min',)}
        fingers = np.full((4, 4), .5)
        aggregate.add(episode(False), arrays, fingers)
        arrays['exposure_time'][0] = 1.
        arrays['surface_min'][0] = .02
        aggregate.add(episode(True), arrays, fingers)
        result = aggregate.result([25, 18, 12, 12])
        self.assertEqual(result['successful_notes']['mean'], 2.)
        self.assertEqual(result['targets'][0]['surface_min_mean_exposed_m'], .02)
        self.assertIsNone(result['targets'][1]['surface_min_mean_exposed_m'])
        self.assertEqual(result['targets'][0]['exposure_episode_count'], 1)
        self.assertEqual(result['fingers'][0]['raw_all_ended']['near_fraction'], .5)
        self.assertEqual(result['fingers'][0]['curriculum_failures_zeroed']['near_fraction'], .25)
        self.assertEqual(sum(result['failure_reason_counts'].values()), 2)
        self.assertEqual(result['physical_failures'], 1)

    def test_completed_fraction_just_below_one_is_not_partial(self):
        aggregate = module.Aggregate(0, 100, targets())
        arrays = {key:np.zeros(67) for key in module.FIELDS+('surface_min',)}
        arrays['contact_progress'][0] = .9999999999999964
        arrays['contact_done'][0] = 1
        arrays['contact_progress'][1] = .5
        aggregate.add(episode(True), arrays, np.zeros((4, 4)))
        result = aggregate.result([25, 18, 12, 12])
        self.assertEqual(result['contact_progress']['mean_partial_notes'], 1.)
        self.assertEqual(result['contact_progress']['mean_complete_notes'], 1.)
        self.assertEqual(result['targets'][0]['contact_partial_fraction'], 0.)
        self.assertEqual(result['targets'][1]['contact_partial_fraction'], 1.)


if __name__=='__main__':
    unittest.main()
