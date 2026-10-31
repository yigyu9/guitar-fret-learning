"""Strict initial inputs and reproducibility hashes for local diagnostic trials."""
import hashlib
import json
import math
from pathlib import Path

from .physics_presets import leg_indices

from .paths import ROOT, resolve_input_path


def validate_settings(value, require_length=False):
    if not isinstance(value, dict) or set(value)-{'joint_angles_rad','strap_rest_length_m','guitar_initial_z_offset_m'}:
        raise ValueError('settings allows joint_angles_rad, strap_rest_length_m and approved guitar_initial_z_offset_m only')
    angles = value.get('joint_angles_rad', {})
    if not isinstance(angles, dict):
        raise ValueError('joint_angles_rad must be a named absolute-angle map')
    for name, angle in angles.items():
        if not isinstance(name, str) or type(angle) not in (int, float) or not math.isfinite(angle):
            raise ValueError('joint angles must be finite numeric radians')
    length = value.get('strap_rest_length_m')
    if (require_length or length is not None) and (
            type(length) not in (int, float) or not math.isfinite(length) or length <= 0):
        raise ValueError('strap rest length must be a positive finite absolute length in metres')
    offset = value.get('guitar_initial_z_offset_m',0.)
    if type(offset) not in (int,float) or not math.isfinite(offset) or offset not in (0.,.005):
        raise ValueError('approved guitar initial Z offsets are 0 or +0.005 metres only')
    return {'joint_angles_rad':dict(angles), 'strap_rest_length_m':length,
            'guitar_initial_z_offset_m':float(offset)}


def initial_targets(base, names, main_indices, lower, upper, settings):
    target = base.copy()
    allowed = {names[i]:i for i in main_indices}
    lower_initial = {names[i]:i for i in leg_indices(names) if lower[i] < upper[i]}
    allowed.update(lower_initial)
    for name, angle in settings['joint_angles_rad'].items():
        if name not in allowed:
            raise ValueError('initial joint is outside main 66/approved effective lower joints: '+name)
        i = allowed[name]
        if not lower[i] <= angle <= upper[i]:
            raise ValueError('explicit initial angle is outside native model limits: '+name)
        if name in lower_initial and abs(angle-float(base[i])) > .05+1e-12:
            raise ValueError('lower initial angle exceeds approved +/-0.05 radians: '+name)
        target[i] = angle
    return target
