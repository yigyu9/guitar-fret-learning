"""Exercise floating-point traps in child processes, never the test runner."""
import json
from pathlib import Path
import signal
import subprocess
import sys
import textwrap
import unittest

from guitar_learning.training import json_io


PRELUDE = '''
import ctypes, io, json, resource, struct, threading
from guitar_learning.training import json_io
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
lib = ctypes.CDLL('libm.so.6')
Env = ctypes.c_uint32*8
for name in ('fegetenv', 'fesetenv'):
    getattr(lib, name).argtypes = [ctypes.c_void_p]
baseline = Env()
assert lib.fegetenv(ctypes.byref(baseline)) == 0
def state():
    return lib.fegetexcept(), lib.fegetround(), lib.fetestexcept(0x3d)
def arm():
    assert lib.fedisableexcept(0x3d) >= 0
    assert lib.feclearexcept(0x3d) == 0
    assert lib.fesetround(0x400) == 0
    sticky = ctypes.c_ushort(0x10)
    assert lib.fesetexceptflag(ctypes.byref(sticky), 0x10) == 0
    assert lib.feenableexcept(0x2d) >= 0
    return state()
'''


class JsonFloatingPointTests(unittest.TestCase):
    def child(self, body):
        return subprocess.run([sys.executable, '-B', '-c', PRELUDE+textwrap.dedent(body)],
                              cwd=str(Path(__file__).resolve().parents[2]),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

    def assert_child_ok(self, body):
        result = self.child(body)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_unprotected_encoder_reproduces_sigfpe(self):
        result = self.child('''
            lib.feclearexcept(0x3d)
            lib.feenableexcept(0x20)
            json.dumps([0.1, 1.2345678912345678, 1e-17], allow_nan=False)
        ''')
        self.assertEqual(result.returncode, -signal.SIGFPE, result.stderr.decode())

    def test_dump_and_dumps_preserve_finite_bits_and_complete_environment(self):
        self.assert_child_ok('''
            values = [0.1, -0.0, 1.2345678912345678, 1e-300, 1e300]
            lib.fesetround(0x400)
            expected = json.dumps(values, allow_nan=False)
            before = arm()
            text = json_io.dumps(values, allow_nan=False)
            after_dumps = state()
            stream = io.StringIO()
            json_io.dump(values, stream, allow_nan=False)
            after_dump = state()
            lib.fesetenv(ctypes.byref(baseline))
            assert before == after_dumps == after_dump, (before, after_dumps, after_dump)
            assert before == (0x2d, 0x400, 0x10)
            assert text == stream.getvalue() == expected
            actual = json.loads(text)
            assert [struct.pack('d', x) for x in actual] == [struct.pack('d', x) for x in values]
        ''')

    def test_nan_and_encoder_errors_restore_environment(self):
        self.assert_child_ok('''
            nan = float('nan')
            for function in (json_io.dump, json_io.dumps):
                for value, error in ((nan, ValueError), (object(), TypeError)):
                    before = arm()
                    try:
                        if function is json_io.dump:
                            function(value, io.StringIO(), allow_nan=False)
                        else:
                            function(value, allow_nan=False)
                    except error:
                        after = state()
                    else:
                        raise AssertionError('Expected JSON error')
                    lib.fesetenv(ctypes.byref(baseline))
                    assert after == before
        ''')

    def test_stream_error_restores_environment(self):
        self.assert_child_ok('''
            class Broken:
                def write(self, text):
                    raise OSError('injected write failure')
            before = arm()
            try:
                json_io.dump([0.1], Broken(), allow_nan=False)
            except OSError:
                after = state()
            else:
                raise AssertionError('Expected write error')
            lib.fesetenv(ctypes.byref(baseline))
            assert after == before
        ''')

    def test_other_thread_environment_and_other_traps_are_unchanged(self):
        self.assert_child_ok('''
            ready, enter, done = threading.Event(), threading.Event(), threading.Event()
            observations = []
            def worker():
                lib.fedisableexcept(0x3d)
                lib.feclearexcept(0x3d)
                lib.fesetround(0x800)
                lib.feenableexcept(0x04)
                observations.append(state())
                ready.set()
                enter.wait()
                observations.append(state())
                lib.fesetenv(ctypes.byref(baseline))
                done.set()
            thread = threading.Thread(target=worker)
            thread.start(); ready.wait()
            before = arm()
            def encode(value):
                # Invalid/divzero/overflow remain enabled in the encoding thread.
                assert lib.fegetexcept() == 0x0d
                enter.set(); done.wait()
                return [0.1]
            text = json_io.dumps(object(), default=encode, allow_nan=False)
            after = state()
            lib.fesetenv(ctypes.byref(baseline))
            thread.join()
            assert before == after
            assert observations == [(0x04, 0x800, 0), (0x04, 0x800, 0)], observations
            assert json.loads(text) == [0.1]
        ''')

    def test_stdlib_functions_and_optional_encoding_arguments_are_preserved(self):
        original = json.dumps
        value = {'unicode': '기타', 'value': .1}
        self.assertEqual(json_io.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False),
                         json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))
        self.assertIs(json.dumps, original)


if __name__ == '__main__':
    unittest.main()
