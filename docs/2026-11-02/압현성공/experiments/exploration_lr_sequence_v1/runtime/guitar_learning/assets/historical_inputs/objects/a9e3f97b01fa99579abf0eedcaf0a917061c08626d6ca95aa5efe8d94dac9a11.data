"""Reject changed Strike inputs and source ABI before coupled inference."""
from tab2body.learning.checkpoint_contract import validate_contract_document,file_sha256


def verify_strike_inputs(checkpoint,goal,grip):
    payload=validate_contract_document(checkpoint['checkpoint_contract'])['payload']
    if payload['task']!='strike':raise ValueError('not a Strike checkpoint')
    for key,path in (('goal',goal),('grip_reference',grip)):
        if file_sha256(path)!=payload['inputs'][key+'_sha256']:
            raise ValueError('Strike input changed: '+key)
    return payload


def verify_strike_view(payload,view):
    if list(view.controlled_dof_names)!=payload['control']['controlled_dof_names']:
        raise ValueError('Strike source action ordering changed')
    if list(view.observation_manifest)!=payload['config']['observation_manifest']:
        raise ValueError('Strike source observation layout changed')
