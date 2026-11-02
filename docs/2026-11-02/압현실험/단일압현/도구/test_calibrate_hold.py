"""오프라인 팔 유지 보정의 입력 거절·비팔 불변·누적 범위 검사."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('calibrate_hold',Path(__file__).with_name('calibrate_hold.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
BASE=Path(__file__).resolve().parents[1]


class CalibrationTests(unittest.TestCase):
    def load(self):
        catalog=json.loads((BASE/'입력/전체기타후보/middle_s3_f12/catalog.json').read_text())
        folder=BASE/'검증/probe_middle_s3_f12_fullguitar'
        return catalog,json.loads((folder/'report.json').read_text()),json.loads((folder/'native_endpoint_diagnostics.json').read_text())

    def test_reject_incomplete_contact_wrong_and_loaded(self):
        catalog,report,diagnostic=self.load()
        for change in ('incomplete','wrong','candidate','terminated','force'):
            r,d=copy.deepcopy(report),copy.deepcopy(diagnostic)
            if change=='incomplete':r['completed']=False
            elif change=='force':
                index=d['endpoints'][-1]['logical_body_names'].index('human/LH:middle3')
                d['endpoints'][-1]['contact_force'][index]=[1.,0.,0.]
            else:r['samples'][1][change]=[[True]] if change in ('wrong','candidate') else [True]
            with self.assertRaises(ValueError):module.calibrate(catalog,r,d)

    def test_only_arm_hold_changes_initial_q_body_fingers_unchanged(self):
        catalog,report,diagnostic=self.load();before=copy.deepcopy(catalog)
        result=module.calibrate(catalog,report,diagnostic)
        self.assertEqual(catalog,before)
        old,new=catalog['goals'][0],result['goals'][0]
        self.assertEqual(old['q105'],new['q105'])
        self.assertEqual(old['state'],new['state'])
        self.assertEqual(old['body_snapshot'],new['body_snapshot'])
        arm=set(catalog['action_indices'][:12])
        for i in set(range(105))-arm:self.assertEqual(old['hold_target105'][i],new['hold_target105'][i])
        self.assertFalse(new['native_verified'])
        self.assertNotIn('native_validation',new)
        self.assertTrue(any(a!=b for a,b in zip(old['hold_target105'],new['hold_target105'])))

    def test_absolute_and_cumulative_bounds(self):
        catalog,report,diagnostic=self.load()
        row=catalog['goals'][0]
        for i in catalog['action_indices'][:12]:diagnostic['endpoints'][-1]['q105'][i]=row['q105'][i]-10.
        result=module.calibrate(catalog,report,diagnostic)
        new=result['goals'][0]
        self.assertTrue(all(c['clipped'] for c in new['holding_feedforward']['corrections']))
        for slot,i in enumerate(catalog['action_indices'][:12]):
            self.assertLessEqual(abs(new['hold_target105'][i]-row['hold_target105'][i]),.120000001)
            self.assertGreaterEqual(new['hold_target105'][i],catalog['action_lower'][slot])
            self.assertLessEqual(new['hold_target105'][i],catalog['action_upper'][slot])
        # 다음 회차에서도 최초 목표 기준 한도는 누적해서 커지지 않는다.
        report=copy.deepcopy(report);report['candidate_sha256']=module.row_identity(new)
        again=module.calibrate(result,report,diagnostic)
        self.assertEqual(new['hold_target105'],again['goals'][0]['hold_target105'])


if __name__=='__main__':unittest.main()
