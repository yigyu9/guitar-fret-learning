"""Strict proven-source loading and actor-only563-to569 expansion."""
import copy
import json
from pathlib import Path

import torch

from guitar_learning.imitation.imitation import dataset_manifest
from guitar_learning.imitation.imitation_v2 import canonical_contract
from guitar_learning.tool.experiments.joint.spec import SCHEMA, ACTOR_STATE_DIM, HAND_STATE_DIM, STATE_DIM


def _merge(pins, additional):
    for path, sha in additional.items():
        if path in pins and pins[path] != sha:
            raise RuntimeError('conflicting source input digest: '+path)
        pins[path] = sha


def validate_experts(settings):
    """Revalidate both original4/4 gates and every consumed source input."""
    from guitar_learning.tool.experiments.local_skills.learning import settings_document, load_initialization
    from guitar_learning.tool.experiments.local_skills.train import validate_gate
    experts = settings.get('joint_experts', {})
    if set(experts) != {'left_settings', 'right_settings'}:
        raise ValueError('both explicit local expert settings required')
    pins, parsed, payloads = {}, {}, {}
    for role in ('left', 'right'):
        path = Path(experts[role+'_settings'])
        if not path.is_absolute() or not path.is_file():
            raise ValueError('absolute source settings file required')
        first = dataset_manifest([path])
        source = settings_document(json.loads(path.read_text()))
        if source['specialist']['role'] != role:
            raise ValueError('source settings hand role mismatch')
        proof = validate_gate(source)
        payload = load_initialization(source['actor_initialization'])
        _merge(pins, first); _merge(pins, proof)
        _merge(pins, dataset_manifest([source['actor_initialization']]))
        _merge(pins, payload['dataset_manifest'])
        gate = json.loads(Path(source['local_skills']['evaluation_gate']).read_text())
        inputs = json.loads(Path(gate['artifacts']['inputs_before']['path']).read_text())
        _merge(pins, inputs)
        for key in ('size', 'seed', 'stage', 'start_event_index', 'phrase_events', 'tempo_scale', 'music', 'timing'):
            if canonical_contract(source[key]) != canonical_contract(settings.get(key)):
                raise ValueError('joint/source settings mismatch: '+role+'/'+key)
        payloads[role], parsed[role] = payload, source
    left, right = (canonical_contract(payloads[r]['architecture']['contract']) for r in ('left', 'right'))
    for key in ('schema', 'observation', 'action', 'termination'):
        if left[key] != right[key]:
            raise ValueError('expert common native contract mismatch: '+key)
    tasks = [copy.deepcopy(c['task']) for c in (left, right)]
    for task in tasks: task.pop('specialist', None)
    if tasks[0] != tasks[1]:
        raise ValueError('expert targets/timing/physical task must match')
    rewards = [copy.deepcopy(c['reward']) for c in (left, right)]
    for reward in rewards: reward.pop('skill', None)
    if rewards[0] != rewards[1]:
        raise ValueError('expert common reward contract must match')
    if dataset_manifest(pins) != pins:
        raise RuntimeError('expert inputs changed during validation')
    return dict(source_pins=pins, payloads=payloads, settings=parsed)


def apply_experts(model, settings):
    evidence = validate_experts(settings)
    architecture = model.architecture
    if (architecture.get('schema') != 'guitar_learning_joint39_v1'
            or architecture.get('state_dim') != STATE_DIM
            or architecture.get('actor_state_dim') != ACTOR_STATE_DIM
            or architecture.get('role') != 'joint' or architecture.get('size') != settings['size']):
        raise ValueError('explicit joint1132/569 architecture required')
    target = canonical_contract(architecture['contract'])
    hands = target.get('task', {}).get('joint', {}).get('hand_contracts', {})
    obs = target.get('observation', {})
    task = copy.deepcopy(target.get('task', {}))
    task.pop('joint', None); task.pop('specialist', None)
    expected = model.state_dict(); assignments = []; reports = {}
    for role in ('left', 'right'):
        payload = evidence['payloads'][role]; source = payload['architecture']
        contract = canonical_contract(source['contract'])
        source_task = copy.deepcopy(contract['task']); source_task.pop('specialist', None)
        if task != source_task:
            raise ValueError('joint must preserve source targets/timing/preparation task')
        source_obs = copy.deepcopy(contract['observation'])
        target_obs = copy.deepcopy(obs)
        for key in ('dimension', 'fields', 'scales'):
            source_obs.pop(key, None); target_obs.pop(key, None)
        for key in ('hand_views', 'coordination'): target_obs.pop(key, None)
        if target_obs != source_obs:
            raise ValueError('joint must preserve source observation event semantics')
        if canonical_contract(hands.get(role)) != contract:
            raise ValueError('joint runtime hand view must preserve exact source contract: '+role)
        if (target.get('action') != contract['action'] or target.get('termination') != contract['termination']
                or target.get('schema') != contract['schema']):
            raise ValueError('joint native action/termination contract mismatch')
        if (obs.get('dimension') != STATE_DIM or obs.get('event_dim') != 24
                or obs.get('capacity') != 64 or obs.get('priority_slots') != 2):
            raise ValueError('joint observation token contract mismatch')
        for key in ('event_dim', 'size', 'state_layers', 'event_layers', 'fusion', 'normalization', 'roles', 'priority_slots', 'likelihood'):
            if canonical_contract(source.get(key)) != canonical_contract(architecture.get(key)):
                raise ValueError('joint actor architecture mismatch: '+key)
        for key, value in payload['model'].items():
            if not key.startswith(('actor_encoders.'+role+'.', 'actor_heads.'+role+'.')): continue
            if key not in expected or expected[key].dtype != value.dtype:
                raise ValueError('joint actor key/dtype mismatch: '+key)
            if key == 'actor_encoders.'+role+'.state.0.weight':
                if value.shape != (256, HAND_STATE_DIM) or expected[key].shape != (256, ACTOR_STATE_DIM):
                    raise ValueError('exact563-to569 first-layer expansion required')
                expanded = torch.zeros_like(expected[key]); expanded[:, :HAND_STATE_DIM].copy_(value)
                assignments.append((expected[key], expanded))
            else:
                if expected[key].shape != value.shape: raise ValueError('joint actor shape mismatch: '+key)
                assignments.append((expected[key], value))
        selection = model.role_slices[role]
        assignments.append((model.log_std[selection], payload['model']['log_std'][selection]))
        reports[role] = dict(checkpoint=evidence['settings'][role]['actor_initialization'],
            checkpoint_sha256=evidence['source_pins'][evidence['settings'][role]['actor_initialization']],
            source_checkpoint_sha256=payload['source_checkpoint_sha256'],
            new_coordination_columns='exact_zero', source_state_dim=HAND_STATE_DIM, actor_state_dim=ACTOR_STATE_DIM)
    expected_fields = [role+'.'+name for role in ('left', 'right')
        for name in hands[role]['observation']['fields']]
    expected_scales = sum((list(hands[role]['observation']['scales']) for role in ('left', 'right')), [])
    from guitar_learning.tool.experiments.joint.spec import COORDINATION_FIELDS, COORDINATION_SCALES
    expected_fields += ['coordination.'+name for name in COORDINATION_FIELDS]
    expected_scales += list(COORDINATION_SCALES)
    if obs.get('fields') != expected_fields or obs.get('scales') != expected_scales:
        raise ValueError('joint observation field order/scales must preserve both source views')
    if dataset_manifest(evidence['source_pins']) != evidence['source_pins']:
        raise RuntimeError('expert inputs changed before transfer')
    with torch.no_grad():
        for destination, value in assignments: destination.copy_(value)
    return dict(schema=SCHEMA, source_pins=evidence['source_pins'], actors=reports,
        scope='selected independent actors/std only; new coordination columns zero; fresh central critics/Adam/RNG/counters; no inherited joint success')
