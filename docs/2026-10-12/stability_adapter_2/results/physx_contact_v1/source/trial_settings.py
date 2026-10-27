"""Strict initial inputs and reproducibility hashes for local diagnostic trials."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate_settings(value, require_length=False):
    if not isinstance(value, dict) or set(value)-{'joint_angles_rad','strap_rest_length_m'}:
        raise ValueError('settings must contain only joint_angles_rad and strap_rest_length_m')
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
    return {'joint_angles_rad':dict(angles), 'strap_rest_length_m':length}


def initial_targets(base, names, main_indices, lower, upper, settings):
    target = base.copy()
    allowed = {names[i]:i for i in main_indices}
    for name, angle in settings['joint_angles_rad'].items():
        if name not in allowed:
            raise ValueError('initial joint is unknown or outside the main 66: '+name)
        i = allowed[name]
        if not lower[i] <= angle <= upper[i]:
            raise ValueError('explicit initial angle is outside native model limits: '+name)
        target[i] = angle
    return target


def source_hashes():
    package = Path(__file__).resolve().parent
    config = json.loads((package/'config.json').read_text())
    files = [package/n for n in ('config.json','trial_settings.py','environment.py','control.py',
        'strap.py','run_initialization.py','initial_overlap.py','run_trial.py','run_batch.py',
        'native_contacts.py','run_contact_calibration.py','run_physx_contacts.py')]
    files += [ROOT/config[k] for k in ('humanoid_asset','guitar_asset','pose_source','gain_source')]
    files += sorted(p for p in (ROOT/'tab2body/assets/mesh').glob('*') if p.is_file())
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
