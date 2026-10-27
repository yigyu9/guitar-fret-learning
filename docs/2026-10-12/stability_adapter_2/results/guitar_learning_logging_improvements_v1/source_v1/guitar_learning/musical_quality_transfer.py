"""Explicit actor-only536 -> quality history migration; strict resume unchanged."""
import copy
from pathlib import Path
import torch
from .imitation import dataset_manifest
from .imitation_v2 import canonical_contract
from .musical_quality import HISTORY_FIELDS, metadata, history_scales, preparation_metadata


def apply_actor_initialization(model, path, *, kind):
    if kind != 'ppo' or model.role not in ('left', 'right') or model.frozen_partner:
        raise ValueError('own single-hand actionable536 PPO actor required')
    path = Path(path).resolve(); manifest = dataset_manifest([path])
    payload = torch.load(path, map_location='cpu', weights_only=False)
    identity = payload.get('identity', {}) if isinstance(payload, dict) else {}
    source = canonical_contract(identity.get('architecture'))
    target = canonical_contract(copy.deepcopy(model.architecture))
    if (identity.get('schema') != 'guitar_learning_ppo_v1' or type(payload.get('updates')) is not int
            or payload['updates'] < 1 or not isinstance(source, dict)
            or source.get('schema') != 'guitar_specialists39_v1' or source.get('state_dim') != 536
            or source.get('role') != model.role or target.get('state_dim') != 536+len(HISTORY_FIELDS)):
        raise ValueError('own completed actionable536 source and quality target required')
    old_contract, new_contract = source.pop('contract'), target.pop('contract')
    target['state_dim'] = 536
    if source != target:
        raise ValueError('single-hand architecture mismatch beyond added quality input columns')
    stripped = copy.deepcopy(new_contract)
    expected = canonical_contract(metadata())
    for section in ('task', 'reward'):
        if stripped[section].pop('musical_quality', None) != expected:
            raise ValueError('explicit declared quality semantics required')
    from .actionable_preparation_environment import REWARD_METADATA
    if stripped['reward'].get('actionable_preparation') != canonical_contract(preparation_metadata()):
        raise ValueError('clean preparation contact reward metadata required')
    stripped['reward']['actionable_preparation'] = canonical_contract(REWARD_METADATA)
    obs = stripped['observation']
    if obs.pop('musical_quality_history', None) != dict(fields=list(HISTORY_FIELDS), base_dimension=536):
        raise ValueError('complete appended quality history required')
    if (obs['dimension'] != 536+len(HISTORY_FIELDS) or
            len(obs['fields']) != obs['dimension'] or len(obs['scales']) != obs['dimension'] or
            obs['scales'][536:] != history_scales() or
            obs['fields'][536:] != ['quality_history.'+name for name in HISTORY_FIELDS]):
        raise ValueError('quality history field order mismatch')
    obs['fields'], obs['scales'], obs['dimension'] = obs['fields'][:536], obs['scales'][:536], 536
    if canonical_contract(stripped) != canonical_contract(old_contract):
        raise ValueError('physics/action/goal/timing/base observation contract changed')
    if 'actionable_preparation' not in old_contract['task']:
        raise ValueError('source must be actionable preparation, not legacy timing')
    values, expected_values = payload.get('model'), model.state_dict()
    if not isinstance(values, dict) or values.keys() != expected_values.keys():
        raise ValueError('complete own model state required')
    expandable = {'actor_encoders.left.state.0.weight', 'actor_encoders.right.state.0.weight', 'value_encoder.state.0.weight'}
    for key, value in values.items():
        shape = tuple(expected_values[key].shape)
        if key in expandable: shape = (shape[0], 536)
        if (not isinstance(value, torch.Tensor) or tuple(value.shape) != shape
                or value.dtype != expected_values[key].dtype or not torch.isfinite(value).all()):
            raise ValueError('source state shape/dtype/finite mismatch: '+key)
    if dataset_manifest([path]) != manifest:
        raise RuntimeError('actor source changed while loading')
    with torch.no_grad():
        for key, value in values.items():
            if key.startswith(('actor_encoders.'+model.role+'.', 'actor_heads.'+model.role+'.')):
                if key in expandable:
                    expected_values[key].zero_(); expected_values[key][:, :536].copy_(value)
                else: expected_values[key].copy_(value)
        selection = model.role_slices[model.role]
        model.log_std[selection].copy_(values['log_std'][selection])
    return dict(schema='guitar_learning.musical_quality_actor_transfer.v1', path=str(path),
        sha256=manifest[str(path)], source_updates=payload['updates'],
        source_state_dim=536, target_state_dim=536+len(HISTORY_FIELDS),
        added_columns='zero initialized; original536 columns unchanged',
        scope='selected actor/std only; fresh critics/optimizer/RNG/update counter; quality success not inherited')
