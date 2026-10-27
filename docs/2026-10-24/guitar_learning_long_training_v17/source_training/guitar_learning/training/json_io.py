"""JSON writers using NumPy Dragon4 instead of CPython's faulting dtoa path.

This reuses the numeric formatting contract of the existing runtime adapter,
without installing global JSON replacements or changing floating-point state.
The cause of the abnormal x87 state remains unresolved. NumPy is imported only
when formatting a float so importing this module preserves Isaac startup order.
"""
import json
import math


def _float_token(value, allow_nan):
    value = float.__float__(value)
    if not math.isfinite(value):
        if not allow_nan:
            raise ValueError('Out of range float values are not JSON compliant')
        return 'NaN' if math.isnan(value) else 'Infinity' if value > 0 else '-Infinity'
    if value == 0:
        return '-0.0' if math.copysign(1., value) < 0 else '0.0'
    import numpy as np
    if abs(value) < 1e-4 or abs(value) >= 1e16:
        return np.format_float_scientific(value, unique=True, trim='-', exp_digits=2)
    token = np.format_float_positional(value, unique=True, trim='-')
    return token if '.' in token else token+'.0'


class _Dragon4Encoder(json.JSONEncoder):
    def iterencode(self, value, _one_shot=False):
        # The C encoder ignores a custom float formatter and calls dtoa again.
        encoder = (json.encoder.encode_basestring_ascii if self.ensure_ascii
                   else json.encoder.encode_basestring)
        return json.encoder._make_iterencode(
            {} if self.check_circular else None, self.default, encoder,
            self.indent, lambda item: _float_token(item, self.allow_nan),
            self.key_separator, self.item_separator, self.sort_keys,
            self.skipkeys, _one_shot)(value, 0)


def dump(*args, **kwargs):
    """Call json.dump with a Dragon4 default; an explicit custom cls is kept."""
    if kwargs.get('cls') is None:
        kwargs['cls'] = _Dragon4Encoder
    return json.dump(*args, **kwargs)


def dumps(*args, **kwargs):
    """Call json.dumps with a Dragon4 default; an explicit custom cls is kept."""
    if kwargs.get('cls') is None:
        kwargs['cls'] = _Dragon4Encoder
    return json.dumps(*args, **kwargs)
