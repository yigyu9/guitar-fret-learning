"""새 단음 입력의 번호·시간·해시와 reset FK 일치 계약을 확인한다."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('single18_prepare',HERE/'prepare_targets.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class TargetInputsTest(unittest.TestCase):
    def test_design_coverage(self):
        cases = json.loads((prepare.BASE/'설계/cases.json').read_text())['cases']
        self.assertEqual(len(cases),18)
        self.assertEqual(len({c['case_id'] for c in cases}),18)
        for finger in prepare.FINGERS:
            rows = [c for c in cases if c['finger']==finger]
            self.assertEqual({c['fret'] for c in rows},{1,12,22})
            self.assertEqual({c['string_standard_1based'] for c in rows},{1,3,6})

    def test_catalog_and_source_hashes(self):
        catalogs = list((prepare.BASE/'입력/후보').glob('*/catalog.json'))
        self.assertTrue(catalogs)
        for path in catalogs:
            data = json.loads(path.read_text())
            self.assertEqual(len(data['reference105']),105)
            self.assertEqual(len(data['action_indices']),39)
            self.assertFalse(data['native_verified'])
            for source,expected in data['source_sha256'].items():
                self.assertEqual(prepare.sha(source),expected,source)
            provenance = json.loads(path.with_name('provenance.json').read_text())
            self.assertEqual(prepare.sha(path),provenance['catalog_sha256'])

    def test_generated_task_time_and_numbering(self):
        from guitar_learning.song.task import make_task
        for path in (prepare.BASE/'입력/후보').glob('*/catalog.json'):
            for row in json.loads(path.read_text())['goals']:
                task = make_task(Path(row['bundle']))
                self.assertEqual(len(task.targets),1)
                target = task.targets[0]
                self.assertEqual((target.string,target.fret,target.finger),
                                 (row['string'],row['fret'],row['finger_id']))
                self.assertEqual((target.onset_s,target.end_s,task.duration_s),(3.,4.5,5.))
                self.assertFalse(row['native_verified'])

    def test_snapshot_matches_current_fk(self):
        import numpy as np
        from types import SimpleNamespace
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
        contract = load_gpu_prepared_reset_contract('left')
        q0 = np.array([r['pos'] for r in contract['state']['human_dof_states']])
        fk = full_fk(SimpleNamespace(names=contract['initial']['joint_names'],
                     human_bodies=contract['initial']['human_body_names'],q_ref=q0),contract['state'])
        for path in (prepare.BASE/'입력/후보').glob('*/catalog.json'):
            for row in json.loads(path.read_text())['goals']:
                actual = prepare.snapshot(contract,np.array(row['q105']),fk(np.array(row['q105'])))
                self.assertEqual(actual,row['state'])
                self.assertEqual(actual['guitar_body_states'],contract['state']['guitar_body_states'])
                for state in actual['human_dof_states']:
                    self.assertEqual(state['vel'],0.)


if __name__ == '__main__':
    unittest.main()
