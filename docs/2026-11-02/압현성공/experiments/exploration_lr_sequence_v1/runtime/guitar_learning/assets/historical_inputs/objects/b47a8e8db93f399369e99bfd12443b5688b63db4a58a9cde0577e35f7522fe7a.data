"""Load v1 actor initialization across equivalent JSON/native contract containers.

Only contract tuple/list representation is normalized. Model metadata remains
unchanged and all tensor, role, architecture and contract values stay strict.
"""
import copy
import json
from pathlib import Path
import torch
from .imitation import SCHEMA, _model, _valid_model_state, dataset_manifest


def canonical_contract(contract):
    def require_string_keys(value):
        if isinstance(value, dict):
            if any(not isinstance(key, str) for key in value):
                raise ValueError('string contract field names required')
            for child in value.values():
                require_string_keys(child)
        elif isinstance(value, (tuple, list)):
            for child in value:
                require_string_keys(child)
    require_string_keys(contract)
    try:
        return json.loads(json.dumps(contract, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise ValueError('finite JSON-compatible contract required') from error


def apply_actor_initialization(model, path):
    role = _model(model)
    path = Path(path)
    manifest = dataset_manifest([path])
    payload = torch.load(path, map_location='cpu', weights_only=False)
    if (not isinstance(payload, dict) or payload.get('schema') != SCHEMA or
            payload.get('role') != role or not isinstance(payload.get('architecture'), dict) or
            not isinstance(payload.get('dataset_manifest'), dict) or not payload['dataset_manifest'] or
            not isinstance(payload.get('training'), dict) or 'updates' in payload or 'identity' in payload):
        raise ValueError('own architecture/contract imitation initialization required')
    source = copy.deepcopy(payload['architecture'])
    target = copy.deepcopy(model.architecture)
    source['contract'] = canonical_contract(source.get('contract'))
    target['contract'] = canonical_contract(target.get('contract'))
    if source != target:
        raise ValueError('exact architecture/contract mismatch after JSON container normalization')
    _valid_model_state(model, payload.get('model'))
    if dataset_manifest([path]) != manifest:
        raise RuntimeError('imitation initialization changed during loading')
    expected = model.state_dict()
    with torch.no_grad():
        for prefix in ('actor_encoders.'+role+'.', 'actor_heads.'+role+'.'):
            for key, value in payload['model'].items():
                if key.startswith(prefix):
                    expected[key].copy_(value)
        selection = model.role_slices[role]
        model.log_std[selection].copy_(payload['model']['log_std'][selection])
    return dict(schema=SCHEMA, path=str(path.resolve()), sha256=manifest[str(path.resolve())],
        role=role, dataset_manifest=copy.deepcopy(payload['dataset_manifest']),
        training=copy.deepcopy(payload['training']),
        contract_comparison='v2 JSON roundtrip; equivalent tuple/list containers only',
        scope='actor/std only; fresh PPO critics/optimizers/update counter')
