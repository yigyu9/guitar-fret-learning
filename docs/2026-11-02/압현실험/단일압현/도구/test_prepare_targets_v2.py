"""보정 후보의 높이 요청과 native 인증 분리를 검사한다."""
import hashlib
import json
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1]

class CorrectedHoverTest(unittest.TestCase):
    def test_corrected_height_and_unverified_native(self):
        paths = list((BASE/'입력/보정후보').glob('*/catalog.json'))
        self.assertTrue(paths)
        for path in paths:
            data = json.loads(path.read_text())
            self.assertEqual(data['native_height_band_m'],[.005,.015])
            self.assertEqual(data['requested_cpu_hover_mm'],17.5)
            for row in data['goals']:
                self.assertFalse(row['native_verified'])
                self.assertEqual(row['nominal_height_m'],.0175)
                if row['candidate_valid']:
                    self.assertLessEqual(abs(row['geometry']['height_m']-.0175),.005)
            pins = data['source_sha256']
            for source,expected in pins.items():
                self.assertEqual(hashlib.sha256(Path(source).read_bytes()).hexdigest(),expected,source)
            provenance = json.loads(path.with_name('provenance.json').read_text())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),provenance['catalog_sha256'])

if __name__ == '__main__':
    unittest.main()
