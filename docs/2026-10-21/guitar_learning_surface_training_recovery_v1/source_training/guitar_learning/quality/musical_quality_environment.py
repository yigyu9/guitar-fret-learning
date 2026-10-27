"""New measured music contract, preserving native physics and old producers."""
import copy
from unittest.mock import patch
import numpy as np
from guitar_learning.quality import actionable_preparation_environment as previous
from guitar_learning.core import training_environment
from guitar_learning.runtime.persistent_environment import _CONSTRUCTION_LOCK
from guitar_learning.core.task_measurement_v2 import TaskMeasurementV2
from guitar_learning.quality.musical_quality import HISTORY_FIELDS, QualityLedger, metadata, history_scales, preparation_metadata


class MusicalQualityEnvironment(previous.ActionablePreparationEnvironment):
    def _observation(self):
        observation = super()._observation()
        ledger = getattr(self, 'quality_ledger', None)
        values = np.zeros(len(HISTORY_FIELDS)) if ledger is None else np.asarray(ledger.history())
        scales = np.asarray(history_scales())
        observation['state'] = np.r_[observation['state'], np.clip(values/scales, -10, 10)].astype(np.float32)
        return observation

    def reset(self):
        self.quality_ledger = None
        with _CONSTRUCTION_LOCK, patch.object(training_environment, 'TaskMeasurement', TaskMeasurementV2):
            _, info = super().reset()
        self.quality_ledger = QualityLedger(self.task, self.last_measured, self.role, self.timing_config.left_fraction)
        info['training_contract'] = self.contract
        self.contract['observation'] = copy.deepcopy(self.contract['observation'])
        spec = self.contract['observation']
        spec['dimension'] += len(HISTORY_FIELDS)
        spec['fields'] += ['quality_history.'+name for name in HISTORY_FIELDS]
        spec['scales'] += history_scales()
        spec['musical_quality_history'] = dict(fields=list(HISTORY_FIELDS), base_dimension=536)
        self.contract['task']['musical_quality'] = metadata()
        self.contract['reward']['musical_quality'] = metadata()
        self.contract['reward']['actionable_preparation'] = preparation_metadata()
        self._quality_info(info)
        return self._observation(), info

    def _quality_info(self, info):
        result = self.quality_ledger.summary(info['timing'])
        info['musical_quality'] = result
        # Retain the original timing achievement explicitly; current success is quality-gated.
        info['timing']['timing_only_stage_success'] = info['timing']['stage_success']
        info['timing']['stage_success'] = result['stage_success']
        info['timing']['provisional_success'] = result['provisional_success']
        info['specialist']['stage_success'] = result['stage_success']
        info['specialist']['provisional_success'] = result['provisional_success']
        info['specialist']['timing'] = copy.deepcopy(info['timing'])
        if 'episode' in info:
            info['episode']['musical_quality'] = copy.deepcopy(result)
            info['episode']['timing'] = copy.deepcopy(info['timing'])
            info['episode']['specialist'] = copy.deepcopy(info['specialist'])

    def step(self, action):
        try:
            _, reward, terminated, truncated, info = super().step(action)
            additions = {}
            for row in info['physics_measurements']:
                measured = row['music']
                previous_measured = self.quality_ledger.previous
                before_audible = self.quality_ledger.clean_audible_s
                terms = self.quality_ledger.update(measured)
                terms['quality_post_note_hold_correction'] = 0.
                terms['quality_audible_success'] = 0.
                if self.role == 'left' and not info['failure_reasons']:
                    target = self.task.targets[0]
                    both = (previous_measured['targets'][target.target_id]['candidate']
                            and measured['targets'][target.target_id]['candidate'])
                    if self.timing_config.stage_index < 4 and both:
                        post = max(0., min(measured['task_time_s'], self.timing_ledger.window_end)
                            - max(previous_measured['task_time_s'], target.end_s, self.timing_ledger.window_start))
                        terms['quality_post_note_hold_correction'] = -self.timing_config.held_second*post
                    required = self.timing_ledger.left_required_dwell_s
                    if before_audible+1e-12 < required <= self.quality_ledger.clean_audible_s+1e-12:
                        terms['quality_audible_success'] = self.timing_config.success_bonus
                row['musical_quality_terms'] = terms
                for key, value in terms.items(): additions[key] = additions.get(key, 0.)+value
            if info['failure_reasons']:
                for row in info['physics_measurements']:
                    row['musical_quality_terms'] = {k: min(0., v) for k,v in row['musical_quality_terms'].items()}
                additions = {key: sum(row['musical_quality_terms'][key] for row in info['physics_measurements']) for key in additions}
            # A relaxed pre-onset/late timing achievement must not pay a second music-success bonus.
            additions['quality_timing_success_correction'] = (-info['reward_terms'].get('timing_success', 0.)
                if self.role == 'left' else 0.)
            extra = float(sum(additions.values()))
            reward += extra; self.total_reward += extra
            info['reward_terms'].update(additions)
            self._quality_info(info)
            if 'episode' in info: info['episode']['reward'] = self.total_reward
            return self._observation(), reward, terminated, truncated, info
        except BaseException:
            self.finished = True
            raise


def build_environment(*args, **kwargs):
    with _CONSTRUCTION_LOCK, patch.object(previous, 'ActionablePreparationEnvironment', MusicalQualityEnvironment):
        return previous.build_environment(*args, **kwargs)
