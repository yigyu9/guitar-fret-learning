"""Explicit post-load evaluation RNG and observable reset-state comparisons.

The runner imports Isaac Gym before calling these helpers. No native state is
written, and matching observations do not imply matching hidden solver caches.
"""
import copy
import math
from numbers import Real
import re


_CONTROLLER_FIELDS = ('target_rows', 'right_target', 'right_info', 'play_latch',
                      'release_origin_W', 'release_rotation_W', 'release_delta_W')
_SCOPE = 'Observable native/controller state only; hidden PhysX solver/contact caches are not observed or restored'


def evaluation_case(seed, *, case_index, evaluation_mode, process_mode):
    """Label one explicitly supplied seed; never silently derive another seed."""
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError('evaluation seed must be an integer in [0, 2**32)')
    if type(case_index) is not int or case_index < 0:
        raise ValueError('nonnegative integer case index required')
    if evaluation_mode not in ('deterministic', 'stochastic'):
        raise ValueError('deterministic/stochastic evaluation mode required')
    if process_mode not in ('fresh_process', 'persistent_reset'):
        raise ValueError('fresh_process/persistent_reset label required')
    if process_mode == 'fresh_process' and case_index != 0:
        raise ValueError('fresh-process evaluation contains only its first case')
    return dict(seed=seed, case_index=case_index, evaluation_mode=evaluation_mode,
                process_mode=process_mode, rng_scope='policy/global RNG; native solver determinism is not guaranteed')


def apply_evaluation_seed(case, *, checkpoint_loaded, checkpoint_sha256):
    """Call immediately after strict checkpoint loading restores saved RNG.

    ``checkpoint_loaded`` is a runner assertion, not checkpoint verification;
    the caller must use the existing strict loader and input SHA audit first.
    """
    expected = evaluation_case(case['seed'], case_index=case['case_index'],
        evaluation_mode=case['evaluation_mode'], process_mode=case['process_mode'])
    if case != expected:
        raise ValueError('exact evaluation_case metadata required')
    if checkpoint_loaded is not True:
        raise ValueError('strict checkpoint load must precede evaluation seeding')
    if not isinstance(checkpoint_sha256, str) or re.fullmatch('[0-9a-f]{64}', checkpoint_sha256) is None:
        raise ValueError('strictly loaded checkpoint SHA256 required')
    # Lazy imports preserve the native entry point's Isaac-before-Torch ordering.
    import random
    import numpy as np
    import torch
    random.seed(case['seed'])
    np.random.seed(case['seed'])
    torch.manual_seed(case['seed'])
    cuda = bool(torch.cuda.is_available())
    if cuda:
        torch.cuda.manual_seed_all(case['seed'])
    return dict(expected, checkpoint_sha256=checkpoint_sha256,
                seed_applied_after_checkpoint_load=True,
                seeded_backends=dict(python=True, numpy=True, torch=True, cuda=cuda))


def _plain(value):
    if hasattr(value, 'tolist'):
        return _plain(value.tolist())
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, Real):
        if not math.isfinite(value):
            raise ValueError('finite observable state required')
        return value.item() if hasattr(value, 'item') else value
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise ValueError('string history keys required')
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    raise ValueError('unsupported observable state type: '+type(value).__name__)


def _vector(value, size, label):
    result = _plain(value)
    if not isinstance(result, list) or len(result) != size or any(
            isinstance(v, bool) or not isinstance(v, Real) for v in result):
        raise ValueError(label+' requires finite vector length '+str(size))
    return result


def _xyz(value):
    return [value[k] for k in 'xyz']


def _validate(snapshot):
    if snapshot.get('schema') != 'guitar_learning.contact_recovery.initial_state.v1':
        raise ValueError('initial-state snapshot schema required')
    for field, size in (('human_position105', 105), ('human_velocity105', 105),
            ('target105', 105), ('last_target105', 105), ('codec_target81', 81), ('previous_action39', 39)):
        _vector(snapshot[field], size, field)
    for field, count in (('human_names', 105), ('guitar_names', len(snapshot['guitar_bodies']))):
        names = snapshot[field]
        if not isinstance(names, list) or len(names) != count or count == 0 or any(
                not isinstance(n, str) for n in names) or len(set(names)) != count:
            raise ValueError('unique ordered '+field+' required')
    for body in snapshot['guitar_bodies']:
        for field in ('position_m', 'linear_velocity_m_s', 'angular_velocity_rad_s'):
            _vector(body[field], 3, field)
        q = _vector(body['quaternion_xyzw'], 4, 'quaternion_xyzw')
        if abs(sum(v*v for v in q)-1.) > .001:
            raise ValueError('unit quaternion required')
    for field in ('controller_history', 'contact_history'):
        if not isinstance(snapshot[field], dict):
            raise ValueError(field+' mapping required')
        _plain(snapshot[field])


def initial_state_snapshot(env):
    """Read the fetched reset state and named target/controller/action histories."""
    scene, controller = env.control.session.scene, env.control.session.controller
    native = env.last_sample['native']
    human = native['human_dof_states']
    bodies = []
    for body in native['guitar_body_states']:
        bodies.append(dict(position_m=_xyz(body['pose']['p']),
            quaternion_xyzw=[body['pose']['r'][k] for k in 'xyzw'],
            linear_velocity_m_s=_xyz(body['vel']['linear']),
            angular_velocity_rad_s=_xyz(body['vel']['angular'])))
    snapshot = _plain(dict(schema='guitar_learning.contact_recovery.initial_state.v1',
        human_names=list(scene.names), guitar_names=list(scene.guitar_bodies),
        human_position105=[v['pos'] for v in human], human_velocity105=[v['vel'] for v in human],
        guitar_bodies=bodies, target105=scene.target, last_target105=scene.last_target,
        codec_target81=env.control.codec_previous, previous_action39=env.previous_action,
        controller_history={k: dict(present=hasattr(controller, k), value=getattr(controller, k, None))
                            for k in _CONTROLLER_FIELDS},
        contact_history=dict(measured=env.last_measured, native_contacts=env.last_sample.get('native_contacts')),
        scope=_SCOPE))
    _validate(snapshot)
    return copy.deepcopy(snapshot)


def compare_initial_states(reference, current, *, scalar_atol=1e-6, rotation_atol_rad=1e-6):
    """Compare saved observable reset state, treating quaternion q and -q equally."""
    for tolerance in (scalar_atol, rotation_atol_rad):
        if isinstance(tolerance, bool) or not isinstance(tolerance, Real) or not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError('finite nonnegative comparison tolerances required')
    _validate(reference)
    _validate(current)
    mismatches = []
    maxima = dict(scalar_abs_error=0., guitar_rotation_error_rad=0.)

    def compare(a, b, path):
        if isinstance(a, dict) and isinstance(b, dict):
            if set(a) != set(b):
                mismatches.append(dict(path=path, kind='mapping_keys'))
            for key in sorted(set(a) & set(b)):
                compare(a[key], b[key], path+'.'+key)
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                mismatches.append(dict(path=path, kind='length'))
            else:
                for i, (x, y) in enumerate(zip(a, b)):
                    compare(x, y, path+'['+str(i)+']')
        elif isinstance(a, Real) and not isinstance(a, bool) and isinstance(b, Real) and not isinstance(b, bool):
            error = abs(a-b)
            maxima['scalar_abs_error'] = max(maxima['scalar_abs_error'], error)
            if error > scalar_atol:
                mismatches.append(dict(path=path, kind='scalar', absolute_error=error))
        elif type(a) is not type(b) or a != b:
            mismatches.append(dict(path=path, kind='value'))

    left, right = copy.deepcopy(reference), copy.deepcopy(current)
    if reference['guitar_names'] == current['guitar_names']:
        for i, (a, b) in enumerate(zip(left['guitar_bodies'], right['guitar_bodies'])):
            qa, qb = a.pop('quaternion_xyzw'), b.pop('quaternion_xyzw')
            na, nb = math.sqrt(sum(v*v for v in qa)), math.sqrt(sum(v*v for v in qb))
            qa, qb = [v/na for v in qa], [v/nb for v in qb]
            # Chord formulation is well conditioned for nearly equal rotations.
            dot = sum(x*y for x, y in zip(qa, qb))
            chord = math.sqrt(sum((x-(-y if dot < 0 else y))**2 for x, y in zip(qa, qb)))
            angle = 4*math.asin(min(1., chord/2))
            maxima['guitar_rotation_error_rad'] = max(maxima['guitar_rotation_error_rad'], angle)
            if angle > rotation_atol_rad:
                mismatches.append(dict(path='guitar_bodies['+str(i)+'].quaternion_xyzw', kind='rotation', angle_rad=angle))
    compare(left, right, 'initial')
    return dict(schema='guitar_learning.contact_recovery.initial_comparison.v1',
        matched=not mismatches, maxima=maxima, mismatches=mismatches,
        scalar_atol=scalar_atol, rotation_atol_rad=rotation_atol_rad, scope=_SCOPE)
