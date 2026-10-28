"""Soft wrist, contact and timed-song reward blending for the left hand."""
import copy

import numpy as np

from guitar_learning.song.hand_environment import HandSongEnvironment, SHARED_TERMS
from guitar_learning.song.curriculum import CPULeftCurriculum as CurriculumState, CPU_SCHEMA as SCHEMA, cpu_default_config as default_config
from guitar_learning.song.task import WristGuide


from guitar_learning.core.geometry import LEFT_FIELDS, LEFT_SCALES
_GROUPS = dict(song_wrist_position='wrist', song_left_contact='contact',
               song_wrong_press='contact', song_clean_hold='timing',
               song_left_success='timing', song_missing_press='timing',
               song_left_missed='timing', song_left_approach='approach')


class LeftSongEnvironment(HandSongEnvironment):
    def __init__(self, *args, bundle, **kwargs):
        if kwargs.get('role') != 'left':
            raise ValueError('left curriculum requires left hand role')
        self.bundle = bundle
        self.curriculum = CurriculumState()
        self.wristguide = None
        self.curriculum_notes = {}
        self._previous_guide = self._previous_measured = None
        super().__init__(*args, **kwargs)

    def reset(self):
        self.wristguide = None
        try:
            _, info = super().reset()
            scene = self.control.session.scene
            self.wristguide = WristGuide(self.bundle, self.last_sample,
                scene.human_bodies, scene.guitar_bodies,
                pre_roll_s=self.song_config['pre_roll_s'])
            self.curriculum_notes = {t.target_id: dict(reached_s=0.,
                reach_achieved=False, clean_press_s=0., contact_achieved=False)
                for t in self.task.targets}
            self._previous_guide = self.wristguide.measure(self.last_sample, 0.)
            self._previous_measured = copy.deepcopy(self.last_measured)
            obs = self.contract['observation']
            obs['fields'] += ['left_curriculum.'+name for name in LEFT_FIELDS]
            obs['scales'] += list(LEFT_SCALES)
            obs['dimension'] += len(LEFT_FIELDS)
            self.contract['reward']['left_curriculum'] = dict(default_config(),
                guide=self.wristguide.metadata(), wrist_second=1.,
                contact_second=.5, contact_first_bonus=.5,
                reach_dwell_s=.1, contact_dwell_s=.05,
                reach_window='max(0,press_s-2)..end_s',
                contact_window='press_s..end_s',
                scope='posture and clean-contact shaping; original song success unchanged')
            self.contract['task']['left_curriculum'] = self.wristguide.metadata()
            info['training_contract'] = self.contract
            self._curriculum_info(info)
            return self._observation(), info
        except BaseException:
            self.finished = True
            raise

    def _observation(self):
        observation = super()._observation()
        if self.wristguide is not None:
            guide = self.wristguide.measure(self.last_sample,
                                            self.last_measured['task_time_s'])
            weights = self.curriculum.weights()
            now = self.last_measured['task_time_s']
            current = [t for t in self.task.targets if t.press_s <= now <= t.end_s]
            upcoming = [t for t in self.task.targets if now < t.press_s <= now+2.]
            focus = (min(current, key=lambda t: (t.end_s, t.target_id)) if current else
                     min(upcoming, key=lambda t: (t.press_s, t.target_id)) if upcoming else None)
            note = self.curriculum_notes.get(focus.target_id) if focus is not None else None
            fraction = (min(1., note['clean_press_s']/min(.05, focus.end_s-focus.press_s))
                        if note is not None else 0.)
            achieved = (sum(n['contact_achieved'] for n in self.curriculum_notes.values())/
                        len(self.curriculum_notes) if self.curriculum_notes else 0.)
            values = (guide['delta_G_m'] + guide['rotation_error_rad'] +
                [fraction, float(note['contact_achieved']) if note is not None else 0., achieved,
                 self.curriculum.progress, weights['contact'], weights['timing']])
            observation['state'] = np.r_[observation['state'],
                np.clip(np.asarray(values)/LEFT_SCALES, -10., 10.)].astype(np.float32)
        return observation

    def set_curriculum(self, progress):
        if (isinstance(progress, (bool, np.bool_)) or
                not isinstance(progress, (int, float, np.integer, np.floating)) or
                not np.isfinite(progress) or not 0. <= progress <= 2.):
            raise ValueError('left curriculum progress must be finite in0..2')
        self.curriculum.progress = float(progress)
        return self._observation()

    def _curriculum_info(self, info, raw_terms=None):
        count = len(self.curriculum_notes)
        value = dict(schema=SCHEMA, progress=self.curriculum.progress,
            weights=self.curriculum.weights(),
            guide=copy.deepcopy(self._previous_guide),
            full_safe=bool(info.get('termination_reason') == 'timeline_complete' and
                info['song']['completed'] and not info['song']['safety_invalidated']),
            reach_fraction=sum(n['reach_achieved'] for n in self.curriculum_notes.values())/count,
            contact_fraction=sum(n['contact_achieved'] for n in self.curriculum_notes.values())/count)
        if raw_terms is not None:
            value['raw_reward_terms'] = copy.deepcopy(raw_terms)
        info['left_curriculum'] = value
        if 'episode' in info:
            info['episode']['left_curriculum'] = copy.deepcopy(value)
            info['episode']['left_curriculum']['per_note'] = copy.deepcopy(self.curriculum_notes)

    def _substep(self, measured, sample):
        before, now = self._previous_measured['task_time_s'], measured['task_time_s']
        guide = self.wristguide.measure(sample, now)
        contact, eligible = 0., False
        for target in self.task.targets:
            identity, note = target.target_id, self.curriculum_notes[target.target_id]
            start = max(0., target.press_s-2.)
            reach_s = max(0., min(now, target.end_s)-max(before, start))
            eligible = eligible or reach_s > 0.
            if self._previous_guide['ready'] and guide['ready']:
                note['reached_s'] += reach_s
            note['reach_achieved'] = (note['reach_achieved'] or
                note['reached_s']+1e-12 >= min(.1, target.end_s-start))
            clean = (self._previous_measured['targets'][identity]['candidate'] and
                     measured['targets'][identity]['candidate'])
            clean_s = (max(0., min(now, target.end_s)-max(before, target.press_s))
                       if clean else 0.)
            note['clean_press_s'] += clean_s
            contact += .5*clean_s
            if (not note['contact_achieved'] and
                    note['clean_press_s']+1e-12 >= min(.05, target.end_s-target.press_s)):
                note['contact_achieved'] = True
                contact += .5
        wrist = (guide['position_score']*(.8+.2*guide['orientation_score'])/240.
                 if eligible else 0.)
        self._previous_guide = guide
        self._previous_measured = measured
        return dict(song_wrist_position=float(wrist), song_left_contact=float(contact))

    def step(self, action):
        try:
            _, old_reward, terminated, truncated, info = super().step(action)
            weights, additions = self.curriculum.weights(), {}
            raw_terms = dict(info['reward_terms'])
            for row, sample in zip(info['physics_measurements'],
                                   info['native_control']['physics_samples240']):
                raw = dict(row['song_reward_terms'])
                extra = self._substep(row['music'], sample)
                if info['failure_reasons']:
                    extra = {key: min(0., value) for key, value in extra.items()}
                raw.update(extra)
                row['song_reward_terms_unweighted'] = raw
                row['song_reward_terms'] = {
                    key: value*weights[_GROUPS[key]] for key, value in raw.items()}
                for key, value in extra.items():
                    raw_terms[key] = raw_terms.get(key, 0.)+value
                for key, value in row['song_reward_terms'].items():
                    additions[key] = additions.get(key, 0.)+value
            additions.update({key: info['reward_terms'][key] for key in SHARED_TERMS})
            reward = float(sum(additions.values()))
            if not np.isfinite(reward):
                raise ValueError('finite left curriculum reward required')
            info['reward_terms'] = additions
            self.total_reward += reward-old_reward
            if 'episode' in info:
                info['episode']['reward'] = self.total_reward
            self._curriculum_info(info, raw_terms)
            return self._observation(), reward, terminated, truncated, info
        except BaseException:
            self.finished = True
            raise
