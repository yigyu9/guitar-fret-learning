"""Explicit immutable inputs for a single original-note diagnostic."""
import copy
from dataclasses import asdict, replace
import math
from pathlib import Path
import json

from guitar_learning.core.control import ACTIVE_NAMES, LEFT_ARM_NAMES
from guitar_learning.training.recording import digest
from guitar_learning.song.finger_phrases import FingerPhrase, build_phrase_catalog

SCHEMA = 'guitar_learning.short_finger_learning.v2'
TEACHER_SCHEMA = 'short_finger_teacher.v2'


def read_teacher(path):
    path = Path(path).resolve(strict=True)
    value = json.loads(path.read_text())
    if (value.get('schema') != TEACHER_SCHEMA or type(value.get('finger')) is not int or
            value['finger'] not in range(1, 5) or not isinstance(value.get('source_target_id'), str) or
            value.get('ramp_s') != 2. or value.get('condition') != 'fixed_wrist_pose' or set(value.get('arm_targets_rad', {})) != set(LEFT_ARM_NAMES)):
        raise ValueError('Sealed teacher: schema, target ID, finger1..4, arm12, fixed_wrist_pose and ramp2s required')
    if not all(type(x) in (int, float) and math.isfinite(x) for x in value['arm_targets_rad'].values()):
        raise ValueError('Finite named arm angles required')
    validate_wrist_pose(value)
    evidence = value.get('source_evidence')
    if not isinstance(evidence, dict) or not evidence:
        raise ValueError('Teacher requires source evidence path/SHA pairs')
    for filename, expected in evidence.items():
        source = Path(filename)
        if (not source.is_absolute() or not source.is_file() or digest(source) != expected):
            raise ValueError('Teacher source evidence mismatch: '+str(filename))
    return dict(value, input_path=str(path), input_sha256=digest(path))


def validate_wrist_pose(value):
    if value.get('schema') != TEACHER_SCHEMA or value.get('condition') != 'fixed_wrist_pose' or value.get('ramp_s') != 2.:
        raise ValueError('Explicit v2 fixed wrist pose teacher/ramp2s required')
    for name, length in (('wrist_position_G_m', 3), ('wrist_quaternion_G_xyzw', 4)):
        vector = value.get(name)
        if not isinstance(vector, list) or len(vector) != length or not all(
                type(x) in (int, float) and math.isfinite(x) for x in vector):
            raise ValueError('Finite guitar-local wrist pose required: '+name)
    if abs(sum(x*x for x in value['wrist_quaternion_G_xyzw'])-1.) > 1e-5:
        raise ValueError('Wrist quaternion must be normalized xyzw')


def selected_actions(finger):
    if type(finger) is not int or finger not in range(1, 5):
        raise ValueError('One finger in1..4 required')
    return tuple(range(17+4*(finger-1), 21+4*(finger-1)))


def subset(task, teacher):
    matches = [i for i, t in enumerate(task.targets) if t.target_id == teacher['source_target_id']]
    if len(matches) != 1 or task.targets[matches[0]].finger != teacher['finger']:
        raise ValueError('Teacher target must identify one matching original finger note')
    index = matches[0]
    target = task.targets[index]
    offset = target.onset_s-3.
    preparation = target.press_s-offset
    if preparation < 0:
        raise ValueError('Original press precedes diagnostic reset')
    ticks = max(math.ceil((target.end_s-offset+.5)*60-1e-9),
                math.floor((target.end_s-offset)*60+1e-9)+1)
    opportunities = tuple(int(f == target.finger) for f in range(1, 5))
    phrase = FingerPhrase('diagnostic-'+target.target_id, (index,), target.press_s,
        target.end_s, None, ticks, offset, opportunities)
    original = build_phrase_catalog(task)
    catalog = replace(original, phrases=(phrase,), preparation_s=preparation)
    return index, catalog, dict(source_index=index, source_target=asdict(target),
        score_offset_s=offset, duration_ticks=ticks, local_press_s=preparation,
        local_onset_s=3., local_end_s=target.end_s-offset,
        catalog_sha256=catalog.fingerprint, source_sha256=catalog.source_sha256)


def diagnostic_spec(task, teacher, mode, initial_std):
    validate_wrist_pose(teacher)
    from .wrist import WRIST_CONTROL
    if mode not in ('incremental', 'position'):
        raise ValueError('Explicit incremental/position mode required')
    if not math.isfinite(initial_std) or not math.exp(-5) <= initial_std <= 1:
        raise ValueError('Explicit initial latent std in[exp(-5),1] required (policy clamp)')
    _, _, view = subset(task, teacher)
    return dict(schema=SCHEMA, finger=teacher['finger'], mode=mode, guitar_mode='fixed',
        learned_action_indices=list(selected_actions(teacher['finger'])),
        learned_action_names=[ACTIVE_NAMES[i] for i in selected_actions(teacher['finger'])],
        teacher=copy.deepcopy(teacher), wrist_control=copy.deepcopy(WRIST_CONTROL),
        view=view, initial_std=float(initial_std),
        schedule='fixed_source_subset_no_full_song_switch',
        policy_scope='selected four joints from first tick; finite arm-only wrist-pose teacher and other-finger B',
        preparation='teacher arm ramp2s plus1s finite settling; audible onset3s; original press/onset/end intervals unchanged; no discarded steps',
        result_scope='conditional fixed-guitar teacher-supported task, not free-guitar J33 performance')


def read_reference(path, spec):
    value = json.loads(Path(path).read_text())
    names = set(spec['learned_action_names'])
    if (value.get('schema') != 'short_finger_reference.v2' or
            value.get('source_target_id') != spec['teacher']['source_target_id'] or
            value.get('ramp_s') != 2. or set(value.get('selected_targets_rad', {})) != names):
        raise ValueError('Reference requires matching source target, selected4 and ramp2s')
    if not all(type(x) in (int, float) and math.isfinite(x) for x in value['selected_targets_rad'].values()):
        raise ValueError('Finite selected reference angles required')
    if not value.get('source_evidence'):
        raise ValueError('Sealed reference evidence required')
    for filename, sha in value['source_evidence'].items():
        if not Path(filename).is_absolute() or not Path(filename).is_file() or digest(filename) != sha:
            raise ValueError('Reference evidence mismatch')
    return value
