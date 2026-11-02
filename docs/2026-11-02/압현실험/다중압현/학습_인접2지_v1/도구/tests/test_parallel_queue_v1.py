import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parallel_queue_v1 import impact, assess_pilot


class ImpactTests(unittest.TestCase):
    def baseline(self):
        return dict(status='running', results={str(i): dict(status='done', outcome='press_success',
                                                            elapsed_s=64.) for i in range(5)})

    def test_no_new_comparable_case_cannot_approve_expansion(self):
        baseline = self.baseline()
        self.assertFalse(impact(baseline, baseline)['expansion_allowed'])

    def test_nominal_case_and_variable_preparation_failure(self):
        baseline = self.baseline(); current = copy.deepcopy(baseline)
        current['results']['new'] = dict(status='done', outcome='press_success', elapsed_s=66.)
        current['results']['prep'] = dict(status='done', outcome='preparation_failed', elapsed_s=100.)
        self.assertTrue(impact(baseline, current)['expansion_allowed'])
        self.assertEqual(impact(baseline, current)['compared_completed_jobs'], 1)

    def test_delay_thresholds_hold_or_stop_only_new_work(self):
        baseline = self.baseline(); current = copy.deepcopy(baseline)
        for elapsed, severe in ((80., False), (96., True)):
            current['results']['new'] = dict(status='done', outcome='native_press_failed', elapsed_s=elapsed)
            result = impact(baseline, current)
            self.assertFalse(result['expansion_allowed'])
            self.assertEqual(result['severe'], severe)

    def test_new_inspection_error_or_stopped_sweep_is_severe(self):
        baseline = self.baseline(); current = copy.deepcopy(baseline)
        current['results']['bad'] = dict(status='inspection_error')
        self.assertTrue(impact(baseline, current)['severe'])
        current = copy.deepcopy(baseline); current['status'] = 'interrupted'
        self.assertTrue(impact(baseline, current)['severe'])

    def test_each_stage_requires_its_own_new_completed_evidence(self):
        initial = self.baseline(); after_first = copy.deepcopy(initial)
        after_first['results']['first'] = dict(status='done', outcome='press_success', elapsed_s=66.)
        record = dict(baseline_single=copy.deepcopy(after_first), expansion_approved=False)
        self.assertFalse(assess_pilot(record, initial, after_first)[2])
        after_second = copy.deepcopy(after_first)
        after_second['results']['second'] = dict(status='done', outcome='press_success', elapsed_s=67.)
        self.assertTrue(assess_pilot(record, initial, after_second)[2])

    def test_resuming_held_pilot_rechecks_evidence_and_cumulative_delay(self):
        initial = self.baseline(); record = dict(baseline_single=copy.deepcopy(initial), expansion_approved=False)
        self.assertFalse(assess_pilot(record, initial, initial)[2])
        delayed = copy.deepcopy(initial)
        delayed['results']['slow'] = dict(status='done', outcome='press_success', elapsed_s=90.)
        self.assertFalse(assess_pilot(record, initial, delayed)[2])


if __name__ == '__main__':
    unittest.main()
