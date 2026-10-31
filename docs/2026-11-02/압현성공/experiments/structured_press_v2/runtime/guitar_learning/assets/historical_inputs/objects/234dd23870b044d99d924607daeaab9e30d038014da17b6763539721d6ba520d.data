"""Read-only checks keep the serialization workaround from hiding bad FP state."""
import ctypes
from pathlib import Path


class Observer:
    def __init__(self):
        self.library = ctypes.CDLL(str(Path(__file__).with_name('fpu_state.so')))
        self.library.read_fp_state.restype = ctypes.c_uint64
        self.library.read_fp_state.argtypes = []
        self.checks = 0
        self.control_words = {}
        self.mxcsr_controls = {}
        self.anomaly = None

    def check(self):
        value = self.library.read_fp_state()
        control, status, mxcsr = value & 65535, value >> 16 & 65535, value >> 32
        self.checks += 1
        name = hex(control)
        self.control_words[name] = self.control_words.get(name, 0)+1
        mode = hex(mxcsr & ~63)
        self.mxcsr_controls[mode] = self.mxcsr_controls.get(mode, 0)+1
        if (control & 63 != 63 or mxcsr >> 7 & 63 != 63
                or control & 0xc00 or mxcsr & 0xe040):
            self.anomaly = dict(control=control, status=status, mxcsr=mxcsr)
            raise FloatingPointError('unsupported floating-point masks/rounding/denormal mode: '+str(self.anomaly))

    def summary(self):
        return dict(checks=self.checks, control_words=dict(self.control_words),
            mxcsr_controls=dict(self.mxcsr_controls),
            anomaly=self.anomaly, state_mutations=False,
            scope='read-only before/after JSON; not continuous observation or a root-cause diagnosis')
