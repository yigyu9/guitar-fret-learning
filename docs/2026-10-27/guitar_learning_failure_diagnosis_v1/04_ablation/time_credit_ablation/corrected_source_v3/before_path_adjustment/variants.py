"""Two mutually exclusive fresh diagnostic variants; production files untouched."""
import copy
import math


VARIANTS=('A_time_discount_30s','B_zero_cost_head')
LONG_GAMMA=math.exp(-1/(60*30))


def descriptor(variant):
    if variant not in VARIANTS:
        raise ValueError('One separately approved A or B variant required')
    changes=({'ppo.gamma':LONG_GAMMA,'song.surface_approach_gamma':LONG_GAMMA}
             if variant==VARIANTS[0] else {'fresh_policy.cost_critic.weight':0.,'fresh_policy.cost_critic.bias':0.})
    return dict(schema='short_finger_time_credit_ablation.v1',variant=variant,
                changes=changes,fresh_only=True,combined_intervention=False)


def settings_for(base, variant):
    settings=copy.deepcopy(base)
    if 'ablation' in settings['song']['short_learning']:
        raise ValueError('Fresh unmodified baseline settings required')
    if settings['ppo']['gamma']!=.99 or settings['song']['surface_approach_gamma']!=.99:
        raise ValueError('Original .99 reward/PBRS baseline required')
    if variant==VARIANTS[0]:
        settings['ppo']['gamma']=LONG_GAMMA
        settings['song']['surface_approach_gamma']=LONG_GAMMA
    settings['song']['short_learning']['ablation']=descriptor(variant)
    validate_settings(settings,variant)
    return settings


def validate_settings(settings, variant):
    gamma=LONG_GAMMA if variant==VARIANTS[0] else .99
    if (settings['song']['short_learning'].get('ablation')!=descriptor(variant)
            or settings['ppo']['gamma']!=gamma or settings['song']['surface_approach_gamma']!=gamma):
        raise ValueError('Checkpoint/settings ablation identity mismatch')


def policy_type(variant, *, fresh):
    import torch
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPolicy

    expected=descriptor(variant)
    class VariantPolicy(ShortPolicy):
        def __init__(self, *, contract, size='large'):
            if contract['task']['short_learning'].get('ablation')!=expected:
                raise ValueError('Exact variant tag in training contract required')
            super().__init__(contract=contract,size=size)
            if fresh and variant==VARIANTS[1]:
                with torch.no_grad():
                    self.cost_critic.weight.zero_()
                    self.cost_critic.bias.zero_()
    return VariantPolicy
