"""Single-A preservation experiment: a frozen BC Actor bounds mean changes.

The bound is pointwise at the same observation. Gaussian exploration, resulting
closed-loop trajectories, physical contact and native success are not bounded.
"""
import copy
from pathlib import Path

import torch
from torch import nn

from ..imitation import dataset_manifest
from .policy import SpecialistPolicy as OriginalPolicy, INITIALIZATION
from . import learning

SCHEMA='guitar_learning.frozen_bc_prior.v1'
FORMULA='bc_plus_limit_tanh_normalized_difference'


def prior_document(value):
    if (not isinstance(value,dict) or set(value)!={'schema','checkpoint_sha256','latent_limit','formula'}
            or value['schema']!=SCHEMA or value['formula']!=FORMULA
            or type(value['latent_limit']) not in (int,float) or value['latent_limit']!=.0002
            or not isinstance(value['checkpoint_sha256'],str) or len(value['checkpoint_sha256'])!=64
            or any(c not in '0123456789abcdef' for c in value['checkpoint_sha256'])):
        raise ValueError('explicit frozen BC SHA and latent mean limit0.0002 required')
    return copy.deepcopy(value)


def bounded_mean(raw,prior,limit):
    return prior+limit*torch.tanh((raw-prior)/limit)


class AnchoredPolicy(OriginalPolicy):
    schema='guitar_learning_transition_anchored39_v1'

    def __init__(self,state_dim=500,event_dim=24,size='medium',contract=None,*,behavior_prior):
        config=prior_document(behavior_prior)
        task=(contract or {}).get('task',{}).get('transition',{})
        if task.get('role')!='left' or task.get('mode')!='single_a':
            raise ValueError('anchored experiment supports left single_a only')
        super().__init__(state_dim,event_dim,size,contract)
        self.frozen_actor_encoders=nn.ModuleDict({'left':copy.deepcopy(self.actor_encoders['left'])})
        self.frozen_actor_heads=nn.ModuleDict({'left':copy.deepcopy(self.actor_heads['left'])})
        self.frozen_actor_encoders.requires_grad_(False);self.frozen_actor_heads.requires_grad_(False)
        self.register_buffer('prior_initialized',torch.tensor(False,dtype=torch.bool))
        self.architecture.update(initialization='validated_BC_selected_actor_std_and_frozen_actor_fresh_critic_Adam',
            behavior_prior=config,prior_storage='checkpoint-contained frozen left Actor; no prior critic',
            bound_scope='same-observation deterministic latent mean and tanh action only; not trajectories or success',
            exploration='original trainable log_std clamp[-5,2]; Gaussian draws excluded from mean bound')

    def base_architecture(self):
        value=copy.deepcopy(self.architecture)
        for key in ('behavior_prior','prior_storage','bound_scope','exploration'):value.pop(key)
        value['schema']=OriginalPolicy.schema;value['initialization']=INITIALIZATION
        return value

    def forward(self,state,events,mask,priority_events,priority_mask):
        if not bool(self.prior_initialized):
            raise ValueError('validated BC prior initialization or strict anchored resume required')
        result=super().forward(state,events,mask,priority_events,priority_mask)
        with torch.no_grad():
            prior=self.frozen_actor_heads['left'](self.frozen_actor_encoders['left'](
                state,events,mask,priority_events,priority_mask))
        left=bounded_mean(result['mean'][:,:33],prior,self.architecture['behavior_prior']['latent_limit'])
        result['mean']=torch.cat((left,left.new_zeros((left.shape[0],6))),-1)
        return result


def initialize_actor(model,settings):
    if not isinstance(model,AnchoredPolicy) or settings['initialization']['mode']!='bc':
        raise ValueError('anchored policy and explicit BC initialization required')
    prior=prior_document(settings['behavior_prior'])
    path=Path(settings['initialization']['checkpoint']).resolve()
    pins=dataset_manifest([path])
    if pins[str(path)]!=prior['checkpoint_sha256'] or model.architecture['behavior_prior']!=prior:
        raise ValueError('exact frozen BC checkpoint and prior identity required')
    # The original loader verifies the actual teacher captures, BC format,
    # full source proof and original500-state architecture before any mutation.
    evidence=learning.validate_initialization(path,model.base_architecture())
    source=evidence['payload']['model'];target=model.state_dict()
    with torch.no_grad():
        for prefix in ('actor_encoders.left.','actor_heads.left.'):
            for key,value in source.items():
                if key.startswith(prefix):
                    target[key].copy_(value)
                    target['frozen_'+key].copy_(value)
        model.log_std[:33].copy_(source['log_std'][:33]);model.prior_initialized.fill_(True)
    if dataset_manifest(evidence['source_pins'])!=evidence['source_pins']:
        raise RuntimeError('BC evidence changed during anchored initialization')
    return dict(schema=SCHEMA,checkpoint=str(path),behavior_prior=prior,
        source_pins=evidence['source_pins'],critic='fresh',optimizer='fresh',ppo_updates=0,
        scope='selected Actor/std and frozen Actor only; pointwise deterministic mean bound, no native success inheritance')
