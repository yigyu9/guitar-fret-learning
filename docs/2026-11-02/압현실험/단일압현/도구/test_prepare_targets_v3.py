"""안전 후보의 최근접 선택을 실제 활성 접촉 함수와 대조한다."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0,str(ROOT))
BASE = Path(__file__).resolve().parents[1]

class SafeHoverTest(unittest.TestCase):
    def test_native_selector_and_clearance(self):
        import numpy as np
        import torch
        from guitar_learning.gpu.contact import pad_target_geometry
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        from guitar_learning.tool.validation.press_acquisition import source_geometry
        contract = load_gpu_prepared_reset_contract('left')
        paths = list((BASE/'입력/안전후보').glob('*/catalog.json'))
        self.assertTrue(paths)
        for path in paths:
            data = json.loads(path.read_text())
            for source,expected in data['source_sha256'].items():
                self.assertEqual(hashlib.sha256(Path(source).read_bytes()).hexdigest(),expected,source)
            for row in data['goals']:
                self.assertFalse(row['native_verified'])
                starts,ends,low,high,plane,_ = source_geometry(contract,[row])
                sample = torch.tensor(row['pad_points_G_m'],dtype=torch.float64)
                count = len(sample);finger=row['finger_id']-1
                points = torch.zeros(1,4,count,3,dtype=torch.float64)
                points[0,finger]=sample
                normals = torch.zeros_like(points)
                normals[0,finger,:,2] = -torch.tensor(row['normal_cos'])
                result = pad_target_geometry(points,normals,torch.zeros_like(points),
                    torch.ones(4,count,dtype=torch.bool),torch.tensor(starts)[None],
                    torch.tensor(ends)[None],torch.tensor(low)[None],torch.tensor(high)[None],
                    torch.tensor([row['string']]),torch.tensor([row['finger_id']]),
                    torch.zeros(1,4,dtype=torch.bool),torch.tensor(plane))
                metric = row['geometry']
                self.assertEqual(int(result['sample_index'][0,0])-finger*count,metric['selected_sample'])
                self.assertAlmostEqual(float(result['signed_height'][0,0]),metric['height_m'],places=9)
                self.assertTrue(all(x==0. for x in row['target_finger_change_rad']))
                if row['candidate_valid']:
                    self.assertGreaterEqual(min(metric['non_target_min_heights_m']),metric['non_target_clearance_m']-1e-6)
                    self.assertGreaterEqual(metric['normal_cos'],.1)
                    self.assertLessEqual(metric['tangent_error_m'],.005)
                    self.assertTrue(.005<=metric['height_m']<=.015)

if __name__ == '__main__':
    unittest.main()
