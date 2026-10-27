"""Fixed native skill profiles shared by demonstration, BC and PPO.

The left hold uses measured contact without the distal-origin approach proxy.
The right crossing guide uses the demonstrated reachable live string region.
Neither profile changes native control, success detection or safety.
"""
import copy
from dataclasses import asdict
from .dense_environment import DenseRewardConfig
from .skill_environment import SkillConfig
from .skill_environment_v2 import build_skill_environment


def profile_settings(role, skill):
    if (role, skill) not in (('left', 'hold'), ('right', 'cross')):
        raise ValueError('imitation profiles require left/hold or right/cross')
    skill_config = SkillConfig(approach_second=0.) if role == 'left' else SkillConfig()
    guide_config = (DenseRewardConfig(strike_y_m=-.36, depth_m=.004,
                    sweep_half_width_m=.008) if role == 'right' else DenseRewardConfig())
    return skill_config, guide_config, dict(
        name='guitar_learning.grounded_imitation.v1', role=role, skill=skill,
        skill_config=asdict(skill_config), guide_config=asdict(guide_config))


class ImitationEnvironment:
    """Attach exact profile identity after every underlying skill reset."""
    def __init__(self, environment, profile):
        self.environment = environment
        self.profile = copy.deepcopy(profile)

    def __getattr__(self, name):
        return getattr(self.environment, name)

    def reset(self):
        observation, info = self.environment.reset()
        self.environment.contract['task']['specialist']['imitation_profile'] = copy.deepcopy(self.profile)
        info['training_contract'] = self.environment.contract
        return observation, info


def build_environment(config, out, *, role, skill, **kwargs):
    skill_config, guide_config, profile = profile_settings(role, skill)
    if 'skill_config' in kwargs or 'guide_config' in kwargs:
        raise ValueError('imitation profile configurations are fixed')
    if kwargs.get('start_event_index', 0) != 0 or kwargs.get('tempo_scale', 1.) != 1.:
        raise ValueError('imitation profile requires first original event at tempo 1')
    environment = build_skill_environment(config, out, role=role, skill=skill,
        skill_config=skill_config, guide_config=guide_config, **kwargs)
    return ImitationEnvironment(environment, profile)
