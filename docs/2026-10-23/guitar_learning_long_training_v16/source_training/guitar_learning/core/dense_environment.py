"""Read-only guitar-frame shaping; musical success remains native measured.

The left distal-body origin and right pick marker are geometric proxies, not
pressure, contact, or sound. No control targets or native states are modified.
"""
from dataclasses import asdict, dataclass
import copy
import numpy as np
from guitar_learning.core.training_environment import TrainingEnvironment


@dataclass(frozen=True)
class DenseRewardConfig:
    left_early_second: float = .2
    left_scale_m: float = .03
    right_guide_second: float = .2
    right_direction_second: float = .1
    right_scale_m: float = .05
    sweep_half_window_s: float = .08
    sweep_half_width_m: float = .006
    strike_y_m: float = -.32
    depth_m: float = .008

    def __post_init__(self):
        if not np.isfinite(list(asdict(self).values())).all():
            raise ValueError('finite dense reward configuration required')
        if (min(self.left_early_second,self.right_guide_second,self.right_direction_second) < 0 or
                min(self.left_scale_m,self.right_scale_m,self.sweep_half_window_s,self.sweep_half_width_m) <= 0 or
                not -.385 <= self.strike_y_m <= -.255 or not .001 <= self.depth_m <= .015):
            raise ValueError('invalid dense reward configuration')


def pick_guide(geometry, target, now_s, config=DenseRewardConfig()):
    """A short signed sweep through the live finite string at target onset."""
    start=np.asarray(geometry['starts_G_m'][target.string],dtype=float)
    end=np.asarray(geometry['ends_G_m'][target.string],dtype=float)
    line=end-start
    length=np.linalg.norm(line[:2])
    if length <= 1e-12 or abs(line[1]) <= 1e-12:
        raise ValueError('nondegenerate string spanning strike zone required')
    fraction=(config.strike_y_m-start[1])/line[1]
    if not 0 <= fraction <= 1:
        raise ValueError('strike zone center outside measured finite string')
    normal=np.array([-line[1],line[0]])/length
    if normal[0] < 0:
        normal=-normal
    phase=float(np.clip((now_s-target.onset_s)/config.sweep_half_window_s,-1.,1.))
    goal=start+fraction*line
    goal[:2]+=target.direction*config.sweep_half_width_m*phase*normal
    goal[2]-=config.depth_m
    if not np.isfinite(goal).all():
        raise ValueError('finite measured pick guide required')
    return goal,normal


def pick_guide_evidence(task,sample,now_s,config=DenseRewardConfig()):
    eligible=[t for t in task.targets if 0 <= now_s <= t.onset_s+config.sweep_half_window_s]
    if not eligible:
        return None
    target=min(eligible,key=lambda t:(abs(t.onset_s-now_s),t.target_id))
    goal,normal=pick_guide(sample['geometry'],target,now_s,config)
    pick=np.asarray(sample['geometry']['pick_G_m'],dtype=float)
    distance=float(np.linalg.norm(pick-goal))
    if not np.isfinite(distance):
        raise ValueError('finite measured pick guide distance required')
    return dict(target_id=target.target_id,task_time_s=now_s,
        physics_step=sample['geometry']['physics_step'],goal_G_m=goal.tolist(),pick_G_m=pick.tolist(),
        distance_m=distance,normal_G_xy=normal.tolist(),direction=target.direction,
        phase=float(np.clip((now_s-target.onset_s)/config.sweep_half_window_s,-1.,1.)),
        sweep_active=bool(abs(now_s-target.onset_s)<=config.sweep_half_window_s),
        scope='read-only guitar-frame marker shaping proxy; not contact or musical success')


def shaping_sample(task, sample, measured, previous_geometry, config=DenseRewardConfig()):
    """Per-second extra terms, integrated by the caller at actual 240Hz."""
    now=measured['task_time_s']
    terms=dict(dense_left_early=0.,dense_right_guide=0.,dense_right_direction=0.)
    early=[t for t in task.targets if t.fret and 0 <= now < t.press_s]
    if early:
        terms['dense_left_early']=config.left_early_second*float(np.mean([
            np.exp(-(np.linalg.norm(measured['geometry'][t.target_id]['delta'])/config.left_scale_m)**2)
            for t in early]))
    # Before the short sweep this is its front-side preparation point. Only
    # the nearest upcoming/active sweep owns the guide; no contradictory mean.
    evidence=pick_guide_evidence(task,sample,now,config)
    if evidence is not None:
        geometry=sample['geometry']
        pick=np.asarray(geometry['pick_G_m'],dtype=float)
        normal=np.asarray(evidence['normal_G_xy'])
        credit=float(np.exp(-(evidence['distance_m']/config.right_scale_m)**2))
        terms['dense_right_guide']=config.right_guide_second*credit
        if evidence['sweep_active']:
            velocity=(pick[:2]-np.asarray(previous_geometry['pick_G_m'])[:2])*240.
            desired_speed=config.sweep_half_width_m/config.sweep_half_window_s
            alignment=float(np.clip(evidence['direction']*(velocity@normal)/desired_speed,0.,1.))
            terms['dense_right_direction']=config.right_direction_second*credit*alignment
    if not np.isfinite(list(terms.values())).all():
        raise ValueError('nonfinite shaping invalidates collection')
    return terms


class DenseTrainingEnvironment(TrainingEnvironment):
    def __init__(self,*args,dense_reward_config=DenseRewardConfig(),**kwargs):
        self.dense_reward_config=dense_reward_config
        super().__init__(*args,**kwargs)

    def reset(self):
        observation,info=super().reset()
        self.contract['reward']['dense_v2']=dict(**asdict(self.dense_reward_config),
            integration='actual 240Hz post-fetch sample seconds',
            left_scope='distal body origin proxy; early [0,press), legacy approach unchanged',
            right_scope='live guitar-frame pick marker follows finite string sweep; geometric proxy only',
            success='legacy contact-conditioned matching/hold/release unchanged')
        self._dense_previous_geometry=copy.deepcopy(self.last_sample['geometry'])
        info['training_contract']=self.contract
        info['pick_guide']=pick_guide_evidence(self.task,self.last_sample,0.,self.dense_reward_config)
        return observation,info

    def step(self,action):
        observation,reward,terminated,truncated,info=super().step(action)
        additions=dict(dense_left_early=0.,dense_right_guide=0.,dense_right_direction=0.)
        samples=info['native_control']['physics_samples240']
        measurements=info['physics_measurements']
        if len(samples) != 4 or len(measurements) != 4:
            self.finished=True
            raise ValueError('four actual physics samples and measurements required')
        try:
            previous=self._dense_previous_geometry
            for sample,row in zip(samples,measurements):
                step=sample['native']['physics_step']
                if (step != row['physics_step'] or step != row['music']['physics_step'] or
                        sample['geometry']['physics_step'] != step or previous['physics_step']+1 != step):
                    raise ValueError('consecutive same-step shaping evidence required')
                rates=shaping_sample(self.task,sample,row['music'],previous,self.dense_reward_config)
                for key,value in rates.items(): additions[key]+=value/240.
                previous=sample['geometry']
            extra=float(sum(additions.values()))
            self._dense_previous_geometry=copy.deepcopy(previous)
            info['reward_terms'].update(additions)
            info['pick_guide']=pick_guide_evidence(self.task,samples[-1],measurements[-1]['music']['task_time_s'],
                                                   self.dense_reward_config)
            reward+=extra
            self.total_reward+=extra
            if 'episode' in info:
                info['episode']['reward']=self.total_reward
            return observation,reward,terminated,truncated,info
        except BaseException:
            self.finished=True
            raise
