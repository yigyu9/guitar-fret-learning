"""Cover actual nvidia-smi CSV memory units without changing sealed v1 code."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import study_queue_v2 as queue


class HostResourceFormatTests(unittest.TestCase):
    def inputs(self, free):
        state = dict(schema='guitar_learning.range336.state.v1', completed=True, status='complete',
            total=336, finished=336, remaining=0,
            results={str(i): dict(status='done') for i in range(336)})
        return state, [dict(uuid=queue.GPU_UUID, **{'memory.free [MiB]': free})], []

    def test_host_units_and_numeric_csv_formats(self):
        for free in ('10970 MiB', '10970'):
            self.assertEqual(queue.gate(*self.inputs(free)), (True, 'ready'))

    def test_low_memory_with_units_blocks(self):
        self.assertEqual(queue.gate(*self.inputs('1024 MiB')), (False, 'waiting_for_gpu_memory'))

    def test_invalid_host_memory_fails_closed(self):
        for free in ('N/A', ''):
            with self.assertRaises((ValueError, IndexError)):
                queue.gate(*self.inputs(free))

    def test_nonfinite_or_negative_memory_cannot_be_ready(self):
        for free in ('NaN MiB', 'Infinity MiB', '-Infinity MiB', '-1 MiB'):
            self.assertEqual(queue.gate(*self.inputs(free)), (False, 'waiting_for_gpu_memory'))

    def test_real_format_cannot_override_incomplete_or_busy(self):
        state, gpu, compute = self.inputs('10970 MiB'); state['completed'] = False
        self.assertFalse(queue.gate(state, gpu, compute)[0])
        state, gpu, _ = self.inputs('10970 MiB')
        self.assertFalse(queue.gate(state, gpu, [dict(gpu_uuid=queue.GPU_UUID)])[0])


if __name__ == '__main__':
    unittest.main()
