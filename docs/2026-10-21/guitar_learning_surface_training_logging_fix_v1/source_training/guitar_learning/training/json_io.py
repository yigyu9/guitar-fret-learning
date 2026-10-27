"""JSON encoding with current-thread FE_INEXACT trapping scoped off.

CPython's decimal float formatter can raise an inexact exception. Native code
may leave that trap enabled, making an otherwise finite JSON write SIGFPE.
Only this trap is masked while encoding; the complete prior floating-point
environment (including rounding and sticky flags) is restored even on errors.
This module has no Torch/Isaac imports and never changes process-wide handlers.
"""
import ctypes
import json
import platform
import sys
from contextlib import contextmanager


if sys.platform != 'linux' or platform.machine() != 'x86_64' or platform.libc_ver()[0] != 'glibc':
    raise RuntimeError('JSON floating-point guard requires Linux x86_64 glibc fenv_t')

# glibc bits/fenv.h on Linux x86_64: sizeof(fenv_t)=32, alignment=4.
# Keep the native representation opaque; libc owns both x87 and MXCSR fields.
_Environment = ctypes.c_uint32*8
_FE_INEXACT = 0x20
_libm = ctypes.CDLL('libm.so.6')
for _name in ('fegetenv', 'fesetenv'):
    _function = getattr(_libm, _name)
    _function.argtypes = [ctypes.c_void_p]
    _function.restype = ctypes.c_int
_libm.fedisableexcept.argtypes = [ctypes.c_int]
_libm.fedisableexcept.restype = ctypes.c_int


@contextmanager
def _encoding_environment():
    saved = _Environment()
    if _libm.fegetenv(ctypes.byref(saved)) != 0:
        raise RuntimeError('Could not save JSON caller floating-point environment')
    try:
        if _libm.fedisableexcept(_FE_INEXACT) < 0:
            raise RuntimeError('Could not mask JSON FE_INEXACT trap')
        yield
    finally:
        if _libm.fesetenv(ctypes.byref(saved)) != 0:
            raise RuntimeError('Could not restore JSON caller floating-point environment')


def dump(*args, **kwargs):
    """Call json.dump with its original arguments and scoped FP protection."""
    with _encoding_environment():
        return json.dump(*args, **kwargs)


def dumps(*args, **kwargs):
    """Call json.dumps with its original arguments and scoped FP protection."""
    with _encoding_environment():
        return json.dumps(*args, **kwargs)
