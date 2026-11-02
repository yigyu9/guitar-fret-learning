import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]/'native_finger_response_v1.py'
spec = importlib.util.spec_from_file_location('native_response_tested', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NativeResponseProtocolTests(unittest.TestCase):
    def test_hold_and_return_boundaries(self):
        for time_s, expected in ((0, (0, 0)), (.5, (0, 0)), (1.5, (1, 0)),
                (2.25, (1, 0)), (3.25, (1, 1)), (4.25, (1, 1)),
                (5.25, (0, 0)), (5.5, (0, 0))):
            self.assertEqual(module.fractions(time_s), expected)

    def test_smooth_requests_respect_original_four_rad_per_second(self):
        rows = [module.fractions(i/60.) for i in range(331)]
        self.assertTrue(all(0 <= value <= 1 for row in rows for value in row))
        speed = max(abs(b[j]-a[j])*math.radians(15)*60
                    for a, b in zip(rows, rows[1:]) for j in range(2))
        self.assertLess(speed, .5)
        self.assertLess(speed, 4.)
        self.assertTrue(all(rows[i+1][0] >= rows[i][0] for i in range(30, 90)))
        self.assertTrue(all(rows[i+1][1] >= rows[i][1] for i in range(135, 195)))
        self.assertTrue(all(rows[i+1][j] <= rows[i][j] for i in range(255, 315) for j in range(2)))

    def test_invalid_episode_clock_rejected(self):
        for value in (float('nan'), float('inf'), -.01, 5.6):
            with self.assertRaises(ValueError):
                module.fractions(value)

    def test_pin_or_manifest_changes_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary); source = folder/'input'; source.write_text('frozen')
            manifest = folder/'manifest.json'
            document = dict(schema='multi_press.native_finger_response.v1', num_envs=1,
                controls=330, degrees=15, training_updates=0, pins={str(source): module.sha(source)})
            manifest.write_text(json.dumps(document))
            expected = module.sha(manifest)
            with patch.object(module, 'MANIFEST', manifest):
                self.assertEqual(module.verify(expected)['controls'], 330)
                source.write_text('changed')
                with self.assertRaisesRegex(ValueError, 'input changed'):
                    module.verify(expected)
                source.write_text('frozen')
                document['num_envs'] = 4
                manifest.write_text(json.dumps(document))
                with self.assertRaisesRegex(ValueError, 'manifest identity'):
                    module.verify(expected)
                with self.assertRaisesRegex(ValueError, 'protocol'):
                    module.verify()


if __name__ == '__main__':
    unittest.main()
