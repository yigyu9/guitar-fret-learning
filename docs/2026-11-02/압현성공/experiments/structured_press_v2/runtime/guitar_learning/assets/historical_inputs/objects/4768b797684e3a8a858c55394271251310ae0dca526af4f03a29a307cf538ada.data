"""Explicit536 actor migration from native settling into actionable preparation.

Only the declared preparation clock/horizon change is accepted. Timing-history
input columns compensate for normalization changes; this cannot guarantee safe
behavior under changed physical initial states or score-time distributions.
Strict PPO resume is untouched.
"""
import copy
from pathlib import Path
import torch
from guitar_learning.imitation.imitation import SCHEMA, _valid_model_state, dataset_manifest
from guitar_learning.imitation.imitation_v2 import canonical_contract
from guitar_learning.timing.timing_transfer import _base_contract, _timing_metadata


def _normalized(contract, role, *, target=False):
    from guitar_learning.quality.actionable_preparation_environment import TASK_METADATA, REWARD_METADATA
    value = canonical_contract(copy.deepcopy(contract))
    metadata, preroll = _timing_metadata(value)
    if metadata is None or value['observation'].get('dimension') != 536:
        raise ValueError('complete timing536 contract required; legacy505 unsupported')
    task, reward, termination = value['task'], value['reward'], value['termination']
    if 'imitation_profile' in task.get('specialist', {}):
        raise ValueError('timing source must not carry a legacy imitation profile')
    modern = 'actionable_preparation' in task or 'actionable_preparation' in reward
    if target and not modern:
        raise ValueError('target must declare actionable preparation')
    if modern:
        if (task.get('actionable_preparation') != canonical_contract(TASK_METADATA) or
                reward.get('actionable_preparation') != canonical_contract(REWARD_METADATA) or
                preroll != 3. or termination.get('preparation_seconds') != 0.):
            raise ValueError('known actionable preparation metadata/native0/pre-roll3 required')
        task.pop('actionable_preparation')
        reward.pop('actionable_preparation')
    elif preroll != 1. or termination.get('preparation_seconds') != 2.:
        raise ValueError('source must be native2/pre-roll1 or known actionable native0/pre-roll3')
    # This validates target offsets, complete timing history/scales and common505.
    base = _base_contract(value, role)
    base['termination']['preparation_seconds'] = 2.
    timing = copy.deepcopy(metadata)
    timing['config']['pre_roll_s'] = 1.
    timing_reward = copy.deepcopy(reward['timing'])
    timing_reward['config']['pre_roll_s'] = 1.
    return base, timing, timing_reward


def validate_contracts(source, target, role):
    """Reject any change beyond the explicitly declared preparation migration."""
    if role not in ('left', 'right'):
        raise ValueError('single left/right hand required')
    if _normalized(source, role) != _normalized(target, role, target=True):
        raise ValueError('preparation migration physics/safety/action/goal/stage/reward contract mismatch')
    if canonical_contract(source['observation']['timing_history']) != canonical_contract(target['observation']['timing_history']):
        raise ValueError('unchanged complete timing history metadata required')
    old = source['observation']['scales']
    new = target['observation']['scales']
    return [float(b)/float(a) for a, b in zip(old, new)]


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
        architecture, source_updates = payload.get('architecture'), 0
    else:
        identity = payload.get('identity', {})
        source_updates = payload.get('updates')
        if (not isinstance(identity, dict) or identity.get('schema') != 'guitar_learning_ppo_v1' or
                not isinstance(identity.get('config'), dict) or type(source_updates) is not int or source_updates < 1):
            raise ValueError('own trained PPO checkpoint required')
        architecture = identity.get('architecture')
    source_architecture = canonical_contract(architecture)
    target_architecture = canonical_contract(model.architecture)
    if not isinstance(source_architecture, dict):
        raise ValueError('complete source architecture required')
    source_contract = source_architecture.pop('contract', None)
    target_contract = target_architecture.pop('contract', None)
    if (source_architecture != target_architecture or source_architecture.get('schema') != 'guitar_specialists39_v1'
            or source_architecture.get('state_dim') != 536 or source_architecture.get('role') != role):
        raise ValueError('same single-hand536 architecture required')
    ratios = validate_contracts(source_contract, target_contract, role)
    values = payload.get('model')
    _valid_model_state(model, values)
    first = 'actor_encoders.'+role+'.state.0.weight'
    scaled = values[first]*values[first].new_tensor(ratios).unsqueeze(0)
    if not torch.isfinite(scaled).all():
        raise ValueError('normalization compensation must remain finite')
    if dataset_manifest([path]) != manifest:
        raise RuntimeError('actor checkpoint changed during loading')
    expected = model.state_dict()
    with torch.no_grad():
        for key, value in values.items():
            if key.startswith(('actor_encoders.'+role+'.', 'actor_heads.'+role+'.')):
                expected[key].copy_(scaled if key == first else value)
        selection = model.role_slices[role]
        model.log_std[selection].copy_(values['log_std'][selection])
    changed = [dict(index=i, field=target_contract['observation']['fields'][i],
        source_scale=source_contract['observation']['scales'][i],
        target_scale=target_contract['observation']['scales'][i], factor=factor)
        for i, factor in enumerate(ratios) if factor != 1.]
    return dict(schema='guitar_learning.actionable_preparation_actor_transfer.v1',kind=kind,
        role=role,path=str(path),sha256=manifest[str(path)],source_updates=source_updates,
        source_architecture=copy.deepcopy(architecture),target_architecture=copy.deepcopy(model.architecture),
        rescaled_input_columns=changed,
        normalization='W_target[:,j]=W_source[:,j]*target_scale[j]/source_scale[j]',
        scope='active actor/std only; fresh critics/optimizer/RNG/update counter; not strict PPO resume',
        limitation='same-raw-value compensation only; shifted score time and changed physical initial state require native validation')
