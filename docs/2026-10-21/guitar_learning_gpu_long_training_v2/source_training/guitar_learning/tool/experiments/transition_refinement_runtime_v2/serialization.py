"""Canonical float64 JSON using NumPy Dragon4, without CPython dtoa/strtod.

This adapter avoids a known fault exposure, not the unknown source of abnormal
FPU state. An optional read-only guard must reject that state rather than reset
it. Original JSON functions, classes and caches are restored explicitly.
Numeric value text matches the original CPython repr contract. Floating
dictionary keys remain rejected by the explicit runtime payload contract.
Native payloads use string keys; other standard non-float key handling remains
unchanged.
"""
from fractions import Fraction
from functools import wraps
import json
import math

import numpy as np


SCHEMA = 'guitar_learning.runtime_dragon4_json.v2'
_ENCODER = json.JSONEncoder
_DECODER = json.JSONDecoder
_active = None


def float_token(value, allow_nan=True):
    value = float.__float__(value)
    if not math.isfinite(value):
        if not allow_nan:
            raise ValueError('Out of range float values are not JSON compliant')
        return 'NaN' if math.isnan(value) else 'Infinity' if value > 0 else '-Infinity'
    if value == 0:
        return '-0.0' if math.copysign(1., value) < 0 else '0.0'
    if abs(value) < 1e-4 or abs(value) >= 1e16:
        return np.format_float_scientific(value, unique=True, trim='-', exp_digits=2)
    token = np.format_float_positional(value, unique=True, trim='-')
    return token if '.' in token else token+'.0'


def parse_float(token):
    # Bound only certainly-overflow/underflow exponents before constructing an
    # integer power. Boundary values still use correctly rounded integer division.
    negative = token.startswith('-')
    mantissa, _, exponent = token.lstrip('-').lower().partition('e')
    digits = mantissa.replace('.', '')
    significant = digits.lstrip('0')
    if not significant:
        return -0.0 if negative else 0.0
    point = mantissa.find('.') if '.' in mantissa else len(mantissa)
    adjusted = int(exponent or '0')+point-(len(digits)-len(significant))-1
    if adjusted > 308:
        return -math.inf if negative else math.inf
    if adjusted < -324:
        return -0.0 if negative else 0.0
    ratio = Fraction(token)
    try:
        return ratio.numerator/ratio.denominator
    except OverflowError:
        return -math.inf if negative else math.inf


def _validate_keys(value, seen):
    if not isinstance(value, (dict, list, tuple)) or id(value) in seen:
        return
    seen.add(id(value))
    if isinstance(value, dict):
        for key,item in value.items():
            if isinstance(key, float):
                raise TypeError('runtime JSON adapter rejects floating dictionary keys')
            _validate_keys(item, seen)
    else:
        for item in value:_validate_keys(item, seen)


class JSONEncoder(_ENCODER):
    def iterencode(self, value, _one_shot=False):
        # Always use the standard Python container encoder. Its C fast path
        # would ignore float_token and call PyOS_double_to_string again.
        encoder = (json.encoder.encode_basestring_ascii if self.ensure_ascii
                   else json.encoder.encode_basestring)
        _validate_keys(value, set())
        def default(item):
            result = self.default(item)
            _validate_keys(result, set())
            return result
        return json.encoder._make_iterencode(
            {} if self.check_circular else None, default, encoder,
            self.indent, lambda item:float_token(item, self.allow_nan),
            self.key_separator, self.item_separator, self.sort_keys,
            self.skipkeys, _one_shot)(value, 0)


class JSONDecoder(_DECODER):
    def __init__(self, *, object_hook=None, parse_float=None, parse_int=None,
                 parse_constant=None, strict=True, object_pairs_hook=None):
        super().__init__(object_hook=object_hook,
            parse_float=globals()['parse_float'] if parse_float is None else parse_float,
            parse_int=parse_int, parse_constant=parse_constant, strict=strict,
            object_pairs_hook=object_pairs_hook)


def install(guard=None):
    """Install only for the authorized run; guard performs read-only FPU checks."""
    global _active
    if _active is not None:
        if _active['guard'] is not guard:
            raise RuntimeError('JSON adapter already installed with a different guard')
        return _active
    if guard is not None and not callable(guard):
        raise TypeError('callable read-only guard required')
    replacements = [(json, 'JSONEncoder', JSONEncoder), (json, 'JSONDecoder', JSONDecoder),
        (json.encoder, 'JSONEncoder', JSONEncoder), (json.decoder, 'JSONDecoder', JSONDecoder),
        (json, '_default_encoder', JSONEncoder()), (json, '_default_decoder', JSONDecoder())]
    for name in ('dump', 'dumps', 'load', 'loads'):
        original = getattr(json, name)
        def guarded(function):
            @wraps(function)
            def call(*args, **kwargs):
                if guard is not None:guard()
                try:
                    result = function(*args, **kwargs)
                except BaseException as primary:
                    if guard is not None:
                        try:guard()
                        except BaseException as secondary:primary.json_guard_error = secondary
                    raise
                else:
                    if guard is not None:guard()
                    return result
            return call
        replacements.append((json, name, guarded(original)))
    entries = [(owner, name, getattr(owner, name), value) for owner,name,value in replacements]
    for owner,name,_,value in entries:setattr(owner, name, value)
    _active = dict(guard=guard, entries=entries)
    return _active


def restore(token):
    """Restore exact previous APIs/caches, refusing to overwrite unrelated changes."""
    global _active
    if token is not _active or token is None:
        raise ValueError('active JSON installation token required')
    if any(getattr(owner, name) is not value for owner,name,_,value in token['entries']):
        raise RuntimeError('JSON bindings changed outside this installation')
    for owner,name,original,_ in reversed(token['entries']):setattr(owner, name, original)
    _active = None
