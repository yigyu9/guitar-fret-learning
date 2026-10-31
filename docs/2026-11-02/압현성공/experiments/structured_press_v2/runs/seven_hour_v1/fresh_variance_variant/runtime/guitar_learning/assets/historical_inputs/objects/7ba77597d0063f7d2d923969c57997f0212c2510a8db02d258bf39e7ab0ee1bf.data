"""Hand-internal objectives over unchanged native control and safety evidence.

Reach/ready are preparation proxies; contact and crossing retain their original
physical eligibility. Original contact-conditioned music bookkeeping is read-only.
"""
import copy
from dataclasses import asdict, dataclass
from unittest.mock import patch
import numpy as np
from guitar_learning.core import training_environment
from guitar_learning.core.training_environment import TrainingEnvironment
from guitar_learning.runtime.persistent_environment import PersistentContactEnvironment, _CONSTRUCTION_LOCK
from guitar_learning.music_task import ScoreTask, EVENT_DIM, finite
from guitar_learning.skills.specialist_environment import SpecialistLedger, SpecialistRewardConfig
from guitar_learning.core.dense_environment import DenseRewardConfig, pick_guide, pick_guide_evidence


@dataclass(frozen=True)
class SkillConfig:
    horizon_s: float = 4.
    left_reach_m: float = .015
    right_ready_m: float = .010
    dwell_s: float = .05
    left_scale_m: float = .03
    right_scale_m: float = .05
    approach_second: float = .2
    contact_second: float = 2.
    acquisition_bonus: float = .25
    success_bonus: float = 1.

    def __post_init__(self):
        values = asdict(self)
        if (any(isinstance(v, bool) for v in values.values()) or
                not np.isfinite(list(values.values())).all() or
                min(self.horizon_s, self.left_reach_m, self.right_ready_m,
                    self.dwell_s, self.left_scale_m, self.right_scale_m) <= 0 or
                min(self.approach_second, self.contact_second,
                    self.acquisition_bonus, self.success_bonus) < 0 or
                abs(self.horizon_s*60-round(self.horizon_s*60)) > 1e-9):
            raise ValueError('finite positive scales, control-tick horizon and nonnegative rewards required')


@dataclass(frozen=True)
class SkillScoreTask(ScoreTask):
    horizon_s: float = 4.

    def __post_init__(self):
        super().__post_init__()
        if (finite(self.horizon_s, 'horizon_s') < super().duration_s or
                abs(self.horizon_s*60-round(self.horizon_s*60)) > 1e-9):
            raise ValueError('skill horizon must cover original score and whole control ticks')

    @property
    def duration_s(self):
        return self.horizon_s

    def tokens(self, now_s, geometry, ledger):
        # All selected targets remain visible, including after the music deadline.
        # Times, musical ownership flags and ledger evidence retain their meanings.
        now = finite(now_s, 'now_s')
        ledger.require_task(self)
        if len(self.targets) > self.capacity:
            raise ValueError('event token capacity overflow')
        features = []
        for t in self.targets:
            g, p = geometry[t.target_id], ledger.progress[t.target_id]
            delta, velocity = tuple(g['delta']), tuple(g['velocity'])
            if len(delta) != 3 or len(velocity) != 3:
                raise ValueError('geometry delta/velocity must have three components')
            values = tuple(finite(v, 'geometry') for v in delta+velocity)
            duration = t.end_s-t.onset_s
            features.append((t.onset_s-now, t.end_s-now, t.press_s-now,
                float(t.string+1), float(t.fret), float(t.finger), float(t.direction),
                float(t.onset_s <= now < t.end_s), float(t.press_s <= now < t.onset_s),
                float(t.target_id in ledger.matches[.05]), float(t.target_id in ledger.matches[.1]),
                p.dwell_s, p.held_s, p.held_s/duration if duration > 0 else 0.,
                float(p.released), p.release_s-now if p.release_s is not None else 0.,
                *values, t.onset_s+.05-now, t.onset_s+.1-now))
        padding = self.capacity-len(features)
        return (tuple(features)+((0.,)*EVENT_DIM,)*padding,
                (True,)*len(features)+(False,)*padding,
                tuple(t.target_id for t in self.targets)+(None,)*padding)


def skill_pick_guide(task, sample, now_s, skill, config=DenseRewardConfig()):
    if skill == 'timed':
        return pick_guide_evidence(task, sample, now_s, config)
    target = task.targets[0]
    phase = -1. if skill == 'ready' else 1.
    goal, normal = pick_guide(sample['geometry'], target,
        target.onset_s+phase*config.sweep_half_window_s, config)
    pick = np.asarray(sample['geometry']['pick_G_m'], dtype=float)
    return dict(target_id=target.target_id, task_time_s=now_s,
        physics_step=sample['geometry']['physics_step'], goal_G_m=goal.tolist(),
        pick_G_m=pick.tolist(), distance_m=float(np.linalg.norm(pick-goal)),
        normal_G_xy=normal.tolist(), direction=target.direction, phase=phase,
        sweep_active=skill == 'cross',
        scope='static live guitar-frame marker guide; preparation proxy, not crossing/contact/sound')


class SkillLedger:
    def __init__(self, task, measured, role, skill, config):
        self.task, self.role, self.skill, self.config = task, role, skill, config
        self.timed = SpecialistLedger(task, measured,
            SpecialistRewardConfig(minimum_dwell_s=config.dwell_s))
        self.previous = {t.target_id: bool(measured['targets'][t.target_id]['candidate'])
                         for t in task.targets}
        self.dwell = {t.target_id: 0. for t in task.targets}
        self.longest = {t.target_id: 0. for t in task.targets}
        self.valid_s = {t.target_id: 0. for t in task.targets}
        self.contacts, self.held, self.reached, self.crossed = set(), set(), set(), set()
        self.ready_dwell = 0.
        self.previous_ready = False
        self.ready = set()
        self.first_success_s = None
        self.ids = set()
        self.geometric = self.matching = self.duplicates = 0
        self.reasons = []

    def update(self, measured, guide=None):
        # Timed ledger validates consecutive actual physics time and crossings.
        before = self.provisional()
        timed_terms = self.timed.update(measured)
        cfg, now = self.config, measured['task_time_s']
        terms = dict(approach=0., acquisition=0., hold=0., success=0.)
        distances = []
        for target in self.task.targets:
            identity = target.target_id
            candidate = bool(measured['targets'][identity]['candidate'])
            distance = float(np.linalg.norm(measured['geometry'][identity]['delta']))
            distances.append(distance)
            if distance <= cfg.left_reach_m:
                self.reached.add(identity)
            if candidate:
                if identity not in self.contacts:
                    self.contacts.add(identity)
                    terms['acquisition'] += cfg.acquisition_bonus
                duration = 1/240. if self.previous[identity] else 0.
                self.valid_s[identity] += duration
                self.dwell[identity] += duration
                self.longest[identity] = max(self.longest[identity], self.dwell[identity])
                terms['hold'] += cfg.contact_second*duration
                if self.dwell[identity]+1e-12 >= cfg.dwell_s:
                    self.held.add(identity)
            else:
                self.dwell[identity] = 0.
            self.previous[identity] = candidate
        for crossing in measured['crossings']:
            identity = crossing['crossing_id']
            if identity in self.ids:
                self.duplicates += 1
                continue
            self.ids.add(identity)
            self.geometric += 1
            candidates = [t for t in self.task.targets
                if (t.string+1, t.direction) == (crossing['string_number'], crossing['direction'])]
            if candidates:
                self.matching += 1
                unused = [t for t in candidates if t.target_id not in self.crossed]
                if unused:
                    self.crossed.add(unused[0].target_id)
        if self.role == 'left':
            terms['approach'] = cfg.approach_second*float(np.mean(
                np.exp(-(np.asarray(distances)/cfg.left_scale_m)**2)))/240.
        elif guide is not None:
            terms['approach'] = cfg.approach_second*float(
                np.exp(-(guide['distance_m']/cfg.right_scale_m)**2))/240.
            if guide['distance_m'] <= cfg.right_ready_m:
                self.ready_dwell += 1/240. if self.previous_ready else 0.
                self.previous_ready = True
                if self.ready_dwell+1e-12 >= cfg.dwell_s:
                    self.ready.add(guide['target_id'])
            else:
                self.ready_dwell = 0.
                self.previous_ready = False
        else:
            self.ready_dwell = 0.
            self.previous_ready = False
        after = self.provisional()
        if after and not before:
            terms['success'] = cfg.success_bonus
            if self.first_success_s is None:
                self.first_success_s = now
        if self.skill == 'timed':
            selected = {key: value for key, value in timed_terms.items()
                        if key.startswith(self.role+'_')}
            if self.role == 'right':
                selected['right_approach'] = terms['approach']
            return selected
        if self.role == 'left' and self.skill == 'reach':
            terms['acquisition'] = terms['hold'] = 0.
        if self.role == 'right':
            terms['acquisition'] = terms['hold'] = 0.
        return {self.role+'_'+key: value for key, value in terms.items()}

    def provisional(self):
        count = len(self.task.targets)
        if self.skill == 'timed':
            return (len(self.timed.dwelled) if self.role == 'left'
                    else len(self.timed.right_matches[.05])) == count
        achieved = dict(reach=self.reached, contact=self.contacts, hold=self.held,
                        ready=self.ready, cross=self.crossed)[self.skill]
        return len(achieved) == count

    def invalidate(self, reasons):
        self.timed.invalidate(reasons)
        for reason in reasons:
            if reason not in self.reasons:
                self.reasons.append(reason)
        self.ready_dwell = 0.
        self.dwell = {key: 0. for key in self.dwell}

    def summary(self, *, completed=False, music=None):
        result = self.timed.summary(self.role, False, completed=completed, music=music)
        safe = not self.reasons
        provisional = safe and self.provisional()
        result.update(stage_success=bool(completed and provisional),
            provisional_success=bool(provisional), safety_invalidated=not safe,
            safety_reasons=list(self.reasons),
            success_criterion=dict(reach='distal body origin <= reach threshold; preparation proxy only',
                contact='original native target contact candidate at any time',
                hold='original native target candidate continuous dwell at any time',
                ready='pick marker front-side guide proximity continuous dwell; preparation proxy only',
                cross='unique original eligible string/direction geometric crossing at any time; no LH prerequisite',
                timed='original specialist score window')[self.skill])
        result['skill'] = dict(name=self.skill, config=asdict(self.config),
            first_success_s=self.first_success_s,
            reached_targets=sorted(self.reached), contact_targets=sorted(self.contacts),
            held_targets=sorted(self.held), ready_targets=sorted(self.ready),
            crossed_targets=sorted(self.crossed), longest_dwell_s=dict(self.longest),
            candidate_valid_s=dict(self.valid_s), ready_dwell_s=self.ready_dwell,
            geometric_crossings=self.geometric, matching_crossings=self.matching,
            duplicate_crossings=self.duplicates,
            scope='historical evidence retained after safety invalidation; only stage_success is safe completed skill achievement')
        return result


class SkillTrainingEnvironment(TrainingEnvironment):
    def __init__(self, *args, role, skill, skill_config=SkillConfig(),
                 guide_config=DenseRewardConfig(), **kwargs):
        valid = dict(left=('reach', 'contact', 'hold', 'timed'),
                     right=('ready', 'cross', 'timed'))
        if role not in valid or skill not in valid[role]:
            raise ValueError('valid hand role and matching internal skill required')
        self.role, self.skill = role, skill
        self.skill_config, self.guide_config = skill_config, guide_config
        task = kwargs['task']
        if not isinstance(task, SkillScoreTask):
            task = SkillScoreTask(task.targets, task.lookahead_s, task.capacity,
                                 copy.deepcopy(task.provenance), skill_config.horizon_s)
            kwargs['task'] = task
        if task.horizon_s != skill_config.horizon_s or len(task.targets) != 1 or not task.targets[0].fret:
            raise ValueError('matching skill horizon and single fretted target required')
        super().__init__(*args, **kwargs)

    def reset(self):
        observation, info = super().reset()
        self.skill_ledger = SkillLedger(self.task, self.last_measured,
                                       self.role, self.skill, self.skill_config)
        self.contract['observation']['skill_token_visibility'] = 'selected target visible for whole shared horizon; original field semantics/times unchanged'
        self.contract['task']['specialist'] = dict(schema='guitar_learning.skill.v1',
            role=self.role, skill=self.skill, config=asdict(self.skill_config),
            inactive_action='other hand action must be zero before physics',
            goal_scope='single original score target; score times unchanged',
            completion='safe full shared horizon; no early success termination')
        self.contract['reward']['skill'] = dict(role=self.role, skill=self.skill,
            config=asdict(self.skill_config), guide=asdict(self.guide_config),
            safety='original240Hz costs/failure conditions; suppress positive skill terms on failed tick',
            guide_rule='ready=static front, cross=static rear, timed=original musical sweep',
            music='original music ledger remains read-only authoritative integrated metric')
        info['training_contract'] = self.contract
        info['specialist'] = self.skill_ledger.summary(music=self.last_measured['summary'])
        if self.role == 'right':
            info['pick_guide'] = skill_pick_guide(self.task, self.last_sample, 0., self.skill, self.guide_config)
        return observation, info

    def step(self, action):
        action = np.asarray(action, dtype=float)
        if action.shape != (39,) or not np.isfinite(action).all() or np.any(np.abs(action) > 1):
            raise ValueError('finite normalized action39 required')
        if np.any((action[33:] if self.role == 'left' else action[:33]) != 0):
            raise ValueError('inactive hand action must be zero before physics')
        observation, base_reward, terminated, truncated, info = super().step(action)
        try:
            samples, rows = info['native_control']['physics_samples240'], info['physics_measurements']
            if len(samples) != 4 or len(rows) != 4:
                raise ValueError('four actual physics samples required')
            additions = {}
            for sample, row in zip(samples, rows):
                if sample['geometry']['physics_step'] != row['physics_step'] or sample['native']['physics_step'] != row['physics_step']:
                    raise ValueError('same-step physical skill evidence required')
                guide = (skill_pick_guide(self.task, sample, row['music']['task_time_s'],
                                         self.skill, self.guide_config) if self.role == 'right' else None)
                terms = self.skill_ledger.update(row['music'], guide)
                for key, value in terms.items():
                    additions[key] = additions.get(key, 0.)+value
            if info['failure_reasons']:
                self.skill_ledger.invalidate(info['failure_reasons'])
                additions = {key: min(0., value) for key, value in additions.items()}
            terms = {key: info['reward_terms'][key] for key in ('action_change', 'terminal_failure')}
            terms.update(additions)
            reward = float(sum(terms.values()))
            if not np.isfinite(reward):
                raise ValueError('finite skill reward required')
            self.total_reward += reward-base_reward
            info['reward_terms'] = terms
            info['specialist'] = self.skill_ledger.summary(
                completed=bool(terminated and info['termination_reason'] == 'timeline_complete'), music=info['music'])
            if self.role == 'right':
                info['pick_guide'] = skill_pick_guide(self.task, samples[-1], info['task_time_s'], self.skill, self.guide_config)
            if 'episode' in info:
                info['episode']['reward'] = self.total_reward
                info['episode']['specialist'] = copy.deepcopy(info['specialist'])
            return observation, reward, terminated, truncated, info
        except BaseException:
            self.finished = True
            raise


def build_skill_environment(config, out, *, role, skill, bundle, stage='B',
        start_event_index=0, phrase_events=8, tempo_scale=1., seed=7,
        worker_id=0, music=None, **kwargs):
    music = dict(music or {})
    if (stage != 'B' or set(music)-{'reward_mode', 'goal_event_indices'} or
            music.get('reward_mode', 'legacy') != 'legacy' or music.get('goal_event_indices') is not None):
        raise ValueError('skill environment requires fixed stage B, legacy setting and no pool')
    task = ScoreTask.from_bundle(bundle, stage=stage, start_event_index=start_event_index,
                                 phrase_events=phrase_events, tempo_scale=tempo_scale)
    with _CONSTRUCTION_LOCK:
        with patch.object(training_environment, 'ContactEnvironment', PersistentContactEnvironment):
            return SkillTrainingEnvironment(config, out, role=role, skill=skill, task=task, **kwargs)
