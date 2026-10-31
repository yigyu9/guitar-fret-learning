"""Dragon4 text/float-bit equivalence without native scenes or global patches."""
import hashlib
import io
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch

from guitar_learning.training import training_log_io as json_io


def bits(value):
    return struct.pack('>d', value)


class JsonWriterTests(unittest.TestCase):
    def test_boundaries_and_100k_random_finite_float64_match_text_and_bits(self):
        patterns = [0, 1, 2, 0x000fffffffffffff, 0x0010000000000000, 0x7fefffffffffffff]
        for value in (1e-4, 1e16, 1., .1):
            center = int.from_bytes(bits(value), 'big')
            patterns += [center-1, center, center+1]
        patterns += [value | (1 << 63) for value in patterns]
        rng = random.Random(735)
        patterns += [rng.getrandbits(64) for _ in range(100000)]
        for pattern in patterns:
            value = struct.unpack('>d', pattern.to_bytes(8, 'big'))[0]
            if math.isfinite(value):
                text = json_io.dumps(value, allow_nan=False)
                self.assertEqual(text, float.__repr__(value))
                self.assertEqual(bits(json.loads(text)), bits(value))

    def test_options_default_unicode_sort_indent_sha_and_dump_match_stdlib(self):
        class Array:
            def tolist(self):
                return [.1, -0., [2.]]
        value = {'z': Array(), 'a': '기타'}
        options = dict(default=lambda v: v.tolist(), allow_nan=False, indent=2,
                       sort_keys=True, ensure_ascii=False, separators=(',', ': '))
        expected = json.dumps(value, **options)
        actual = json_io.dumps(value, **options)
        stream = io.StringIO()
        json_io.dump(value, stream, **options)
        self.assertEqual(actual, stream.getvalue())
        self.assertEqual(actual, expected)
        self.assertEqual(hashlib.sha256(actual.encode()).digest(), hashlib.sha256(expected.encode()).digest())

    def test_float_keys_and_other_key_types_keep_stdlib_behavior(self):
        value = {.1: 'float', -0.: 'zero', 3: 'integer', None: 'none', False: 'false'}
        self.assertEqual(json_io.dumps(value), json.dumps(value))
        self.assertEqual(json_io.dumps({object(): 1}, skipkeys=True), '{}')
        with self.assertRaises(TypeError):
            json_io.dumps({object(): 1})

    def test_nonfinite_rejected_and_allow_nan_behavior_preserved(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                json_io.dumps([value], allow_nan=False)
            with self.assertRaises(ValueError):
                json_io.dump([value], io.StringIO(), allow_nan=False)
        self.assertEqual(json_io.dumps([math.nan, math.inf, -math.inf]), '[NaN, Infinity, -Infinity]')

    def test_container_serialization_and_stream_errors_are_preserved(self):
        circular = []; circular.append(circular)
        with self.assertRaises(ValueError):
            json_io.dumps(circular)
        with self.assertRaises(TypeError):
            json_io.dumps(object())
        class Broken:
            def write(self, text):
                raise OSError('injected write failure')
        with self.assertRaisesRegex(OSError, 'injected write failure'):
            json_io.dump([.1], Broken())

    def test_never_calls_c_encoder_or_float_subclass_format_hooks(self):
        class TrapFloat(float):
            def __repr__(self):
                raise AssertionError('float repr called')
            def __float__(self):
                raise AssertionError('float conversion hook called')
            def __format__(self, spec):
                raise AssertionError('float format called')
        with patch.object(json.encoder, 'c_make_encoder', side_effect=AssertionError('C encoder called')):
            self.assertEqual(json_io.dumps([TrapFloat(.1), TrapFloat(-0.)]), '[0.1, -0.0]')

    def test_none_cls_uses_dragon4_and_explicit_custom_cls_is_preserved(self):
        class Custom(json.JSONEncoder):
            def encode(self, value):
                return '"custom"'
            def iterencode(self, value, _one_shot=False):
                return iter(['"custom"'])
        with patch.object(json.encoder, 'c_make_encoder', side_effect=AssertionError('C encoder called')):
            self.assertEqual(json_io.dumps(.1, cls=None), '0.1')
        self.assertEqual(json_io.dumps(.1, cls=Custom), '"custom"')
        stream = io.StringIO(); json_io.dump(.1, stream, cls=Custom)
        self.assertEqual(stream.getvalue(), '"custom"')

    def test_no_global_json_changes_or_eager_numpy_torch_isaac_import(self):
        original = (json.dump, json.dumps, json.load, json.loads, json.JSONEncoder, json.JSONDecoder)
        json_io.dumps([.1])
        self.assertEqual(original, (json.dump, json.dumps, json.load, json.loads, json.JSONEncoder, json.JSONDecoder))
        result = subprocess.run([sys.executable, '-B', '-c',
            'import sys; from guitar_learning.training import training_log_io as json_io; assert not any(n in sys.modules for n in ("numpy", "torch", "isaacgym"))'],
            cwd=str(Path(__file__).resolve().parents[2]), capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode())


if __name__ == '__main__':
    unittest.main()
