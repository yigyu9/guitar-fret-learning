"""Explicit actor-only migration into the policy pre-roll timing contract.

This does not relax PPO resume. Old actor inputs keep their order/scales, while
new timing-history columns start at zero in the first actor state layer.
"""
import copy
from dataclasses import asdict
from pathlib import Path
import torch
from guitar_learning.imitation.imitation import SCHEMA, dataset_manifest
from guitar_learning.imitation.imitation_v2 import canonical_contract


def _timing_metadata(contract):
    if (not isinstance(contract, dict) or not isinstance(contract.get('task'), dict)
            or not isinstance(contract.get('reward'), dict)):
        raise ValueError('complete native timing contract required')
    metadata = contract['task'].get('timing')
    if metadata is None:
        return None, 0.
    if not isinstance(metadata, dict) or not isinstance(metadata.get('config'), dict):
        raise ValueError('explicit timing configuration contract required')
    from guitar_learning.timing.timing_curriculum import TimingConfig
    config = TimingConfig(**metadata['config'])
    if canonical_contract(asdict(config)) != canonical_contract(metadata['config']):
        raise ValueError('complete fixed timing configuration required')
    # The name is part of the timing configuration API, not inferred from clocks.
    if (metadata.get('schema') != 'guitar_learning.timing.v1' or
            metadata.get('window_s') != config.window_s or
            metadata.get('baseline_normalization_horizon_s') != 4. or
            metadata.get('original_provenance') != contract['task'].get('provenance')):
        raise ValueError('declared timing window, original score and normalization must match')
    reward = contract['reward'].get('timing')
    if (not isinstance(reward, dict) or reward.get('config') != metadata['config']):
        raise ValueError('timing reward and task configuration must match')
    return metadata, float(config.pre_roll_s)


def _base_contract(contract, role):
    result = canonical_contract(copy.deepcopy(contract))
    if not isinstance(result, dict) or result.get('schema') != 'guitar_learning.training.v1' or any(
            not isinstance(result.get(key), dict)
            for key in ('observation', 'action', 'task', 'reward', 'termination')):
        raise ValueError('complete native training contract required')
    metadata, preroll = _timing_metadata(result)
    task = result['task']
    specialist = task.get('specialist', {})
    expected_skill = 'hold' if role == 'left' else 'cross'
    if specialist.get('role') != role or specialist.get('skill') != expected_skill:
        raise ValueError('same-hand grounded hold/cross history contract required')
    profile = specialist.pop('imitation_profile', None)
    if profile is not None:
        from guitar_learning.imitation.imitation_environment import profile_settings
        if canonical_contract(profile) != canonical_contract(profile_settings(role, expected_skill)[2]):
            raise ValueError('known grounded imitation profile required')
    if metadata is None and profile is None:
        raise ValueError('grounded imitation or timing source contract required')
    if abs(float(task['duration_s'])-(4.+preroll)) > 1e-9:
        raise ValueError('only original4s plus declared policy pre-roll duration supported')
    task['duration_s'] = 4.
    for target in task['targets']:
        for key in ('press_s', 'onset_s', 'end_s'):
            target[key] = round(float(target[key])-preroll, 12)
    if metadata is not None and metadata.get('original_targets') != task['targets']:
        # Arithmetic subtraction is rounded, so compare finite values recursively
        # through the same rounding for the declared original target times.
        original = copy.deepcopy(metadata.get('original_targets'))
        if not isinstance(original, list):
            raise ValueError('original timing target provenance required')
        for target in original:
            for key in ('press_s', 'onset_s', 'end_s'):
                target[key] = round(float(target[key]), 12)
        if original != task['targets']:
            raise ValueError('target timing offset does not match declared original score')
    for config in (specialist.get('config'), result['reward'].get('skill', {}).get('config')):
        if not isinstance(config, dict) or abs(float(config.get('horizon_s', -1))-(4.+preroll)) > 1e-9:
            raise ValueError('matching explicit skill horizon required')
        config['horizon_s'] = 4.
    task.pop('timing', None)
    result['reward'].pop('timing', None)
    observation = result['observation']
    dimension = observation.get('dimension')
    if (type(dimension) is not int or dimension < 505 or
            len(observation.get('fields', [])) != dimension or
            len(observation.get('scales', [])) != dimension):
        raise ValueError('complete observable505 prefix and explicit appended dimensions required')
    if metadata is None and dimension != 505:
        raise ValueError('legacy actor must have exactly505 inputs')
    if metadata is not None and (dimension == 505 or not isinstance(observation.get('timing_history'), dict)):
        raise ValueError('timing policy must expose its appended history')
    if metadata is not None:
        from guitar_learning.timing.timing_curriculum import TimingConfig, TIMING_HISTORY_FIELDS, history_scales
        config = TimingConfig(**metadata['config'])
        history = observation['timing_history']
        if (observation['fields'][505:] != ['timing_history.'+name for name in TIMING_HISTORY_FIELDS] or
                observation['scales'][505:] != history_scales(None, config) or
                history.get('schema') != 'guitar_learning.timing_history.v1' or
                history.get('fields') != list(TIMING_HISTORY_FIELDS) or
                history.get('baseline_dimension') != 505 or
                history.get('baseline_normalization_horizon_s') != 4.):
            raise ValueError('declared complete timing history fields and scales required')
    observation['dimension'] = 505
    observation['fields'] = observation['fields'][:505]
    observation['scales'] = observation['scales'][:505]
    observation.pop('timing_history', None)
    return result


def validate_contracts(source, target, role):
    target_metadata, _ = _timing_metadata(target)
    if target_metadata is None:
        raise ValueError('target must be an explicit timing environment')
    if _base_contract(source, role) != _base_contract(target, role):
        raise ValueError('source/target physics, safety, action or original505 contract mismatch')
    source_observation, target_observation = source['observation'], target['observation']
    if source_observation['dimension'] > 505 and any(
            canonical_contract(source_observation[key][505:]) != canonical_contract(target_observation[key][505:])
            for key in ('fields', 'scales')):
        raise ValueError('existing timing history order/scales cannot change during actor transfer')


def apply_actor_initialization(model, path, *, kind):
    if kind not in ('bc', 'ppo'):
        raise ValueError('explicit bc/ppo initialization kind required')
    role = getattr(model, 'role', None)
    if role not in ('left', 'right') or getattr(model, 'frozen_partner', True):
        raise ValueError('single-hand policy without frozen partner required')
    path = Path(path).resolve()
    manifest = dataset_manifest([path])
    payload = torch.load(path, map_location='cpu', weights_only=False)
    if not isinstance(payload, dict):
        raise ValueError('own checkpoint dictionary required')
    if kind == 'bc':
        if (payload.get('schema') != SCHEMA or payload.get('role') != role or
                not isinstance(payload.get('training'), dict) or
                not isinstance(payload.get('dataset_manifest'), dict) or not payload['dataset_manifest'] or
                'updates' in payload or 'identity' in payload):
            raise ValueError('own BC actor initialization required')
        architecture = payload.get('architecture')
        source_updates = 0
    else:
        identity = payload.get('identity', {})
        source_updates = payload.get('updates')
        if (not isinstance(identity, dict) or identity.get('schema') != 'guitar_learning_ppo_v1' or
                not isinstance(identity.get('config'), dict) or type(source_updates) is not int or source_updates < 1):
            raise ValueError('own trained PPO specialist checkpoint required')
        architecture = identity.get('architecture')
    target_architecture = copy.deepcopy(model.architecture)
    if not isinstance(architecture, dict) or architecture.get('role') != role:
        raise ValueError('matching source hand architecture required')
    source_architecture = copy.deepcopy(architecture)
    source_contract = source_architecture.pop('contract', None)
    target_contract = target_architecture.pop('contract', None)
    source_dimension = source_architecture.pop('state_dim', None)
    target_dimension = target_architecture.pop('state_dim', None)
    if (source_architecture != target_architecture or source_architecture.get('schema') != 'guitar_specialists39_v1'
            or type(source_dimension) is not int or type(target_dimension) is not int or
            not 505 <= source_dimension <= target_dimension):
        raise ValueError('same architecture with only declared input-column expansion required')
    validate_contracts(source_contract, target_contract, role)
    if (source_contract['observation']['dimension'] != source_dimension or
            target_contract['observation']['dimension'] != target_dimension):
        raise ValueError('architecture and observation dimensions differ')
    values, expected = payload.get('model'), model.state_dict()
    if not isinstance(values, dict) or values.keys() != expected.keys():
        raise ValueError('complete own model state required')
    for key, value in values.items():
        shape = list(expected[key].shape)
        if key.endswith('.state.0.weight'):
            shape[1] = source_dimension
        if (not isinstance(value, torch.Tensor) or list(value.shape) != shape or
                value.dtype != expected[key].dtype or not torch.isfinite(value).all()):
            raise ValueError('finite source model shape/dtype mismatch: '+key)
    if dataset_manifest([path]) != manifest:
        raise RuntimeError('actor checkpoint changed during loading')
    expanded = []
    with torch.no_grad():
        for prefix in ('actor_encoders.'+role+'.', 'actor_heads.'+role+'.'):
            for key, value in values.items():
                if not key.startswith(prefix): continue
                if key.endswith('.state.0.weight') and source_dimension != target_dimension:
                    expected[key].zero_()
                    expected[key][:, :source_dimension].copy_(value)
                    expanded.append(dict(key=key, source_columns=source_dimension,
                                         target_columns=target_dimension, new_columns='exact zero'))
                else:
                    expected[key].copy_(value)
        selection = model.role_slices[role]
        model.log_std[selection].copy_(values['log_std'][selection])
    return dict(schema='guitar_learning.timing_actor_transfer.v1', kind=kind,
        role=role, path=str(path), sha256=manifest[str(path)], source_updates=source_updates,
        source_architecture=copy.deepcopy(architecture), target_architecture=copy.deepcopy(model.architecture),
        expanded=expanded, contract_migration='declared policy pre-roll, target offsets, horizon and appended timing history only',
        scope='active actor/std only; critics/optimizers/RNG/update counter remain fresh; not strict PPO resume')
