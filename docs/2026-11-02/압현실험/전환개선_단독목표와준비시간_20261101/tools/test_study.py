"""조건 통과 기준과 완료 여부·분모 보존을 CPU에서 검사한다."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('single_gap_study',Path(__file__).with_name('run_study.py'))
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)

class StudyTests(unittest.TestCase):
    def test_single_and_pair_gate(self):
        for clean in ([1.35],[1.4,1.35]):
            self.assertTrue(study.passed(dict(episodes=128,joint_achievement=116,clean_s=clean,physical=1,wrist=0)))
    def test_achievement_alone_does_not_pass(self):
        self.assertFalse(study.passed(dict(episodes=128,joint_achievement=128,clean_s=[1.34],physical=0,wrist=0)))
    def test_failures_not_removed_from_gate(self):
        self.assertFalse(study.passed(dict(episodes=128,joint_achievement=128,clean_s=[1.5,1.5],physical=2,wrist=0)))
    def test_budgets_same_as_previous(self):
        self.assertEqual(study.BUDGETS,(19*32768,38*32768,64*32768))
    def test_runtime_and_inputs_in_seal_no_top_archive(self):
        pins=study.seal();root=study.ROOT
        for name in ('tools/runtime.py','tools/run_study.py','geometry/initial_catalog.json'):
            p=study.BASE/name;self.assertEqual(pins[str(p.relative_to(root))],study.study.sha(p))
        self.assertFalse(any(k.startswith('guitar_learning/archive/') for k in pins))

if __name__=='__main__':unittest.main()
