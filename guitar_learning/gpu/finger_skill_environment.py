"""Explicit phrase views over the pinned whole-song GPU measurements.

Only the score clock and selected task scope change. Native episode clocks,
prepared resets, controller, geometry, physical safety and clean criteria stay
with TensorSongEnvironment.
"""
import copy

import torch

from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.gpu.episode_diagnostics import LeftEpisodeDiagnostics
from guitar_learning.gpu.finger_skill_diagnostics import SkillEpisodeDiagnostics
from guitar_learning.gpu.geometry import apply
from guitar_learning.song.finger_phrases import build_phrase_catalog, BalancedPhraseSampler


PHASE_FIELDS = ('finger_skill.phase_R', 'finger_skill.phase_F', 'finger_skill.phase_J',
                'finger_skill.planned_ticks', 'finger_skill.remaining_s')


class FingerSkillEnvironment(TensorSongEnvironment):
    allowed_finger_action_modes = ('incremental',)

    def __init__(self, metadata, *, bundle, song, skill, device='cuda:0', hand='left'):
        if hand != 'left' or skill.get('schema') != 'guitar_learning.finger_skill.v1':
            raise ValueError('Explicit GPU left finger-skill contract required')
        self.phase = skill.get('phase')
        self.training_scope = skill.get('scope')
        self.hold_ticks = skill.get('hold_ticks')
        if (self.phase not in ('R', 'F', 'J') or
                self.training_scope not in ('phrases', 'full_song') or
                type(self.hold_ticks) is not int or self.hold_ticks not in (1, 3, 6) or
                skill.get('exploration') not in ('independent', 'correlated')):
            raise ValueError('Explicit phase, scope, exploration and hold_ticks1/3/6 required')
        if song.get('finger_action_mode', 'incremental') not in self.allowed_finger_action_modes:
            raise ValueError('Finger-skill family uses incremental fingers')
        if song.get('pre_roll_s') != 3.:
            raise ValueError('Finger-skill family uses the agreed3s policy preparation')
        super().__init__(metadata, bundle=bundle, song=song, hand=hand, device=device)
        self.catalog = build_phrase_catalog(self.task, preparation_s=3., tail_s=song['tail_s'])
        self.sampler = BalancedPhraseSampler(self.catalog)
        self.evaluation = False
        self.evaluation_full_song = False
        observation = self.contract['observation']
        observation['fields'] += list(PHASE_FIELDS)
        observation['scales'] += [1., 1., 1., 6., self.task.duration_s]
        observation['dimension'] += 5
        self.scales = self._tensor(observation['scales'])
        self.contract['task']['finger_skill'] = dict(
            schema='guitar_learning.finger_skill.v1', phase=self.phase,
            exploration=skill['exploration'], hold_ticks=self.hold_ticks,
            scope=self.training_scope, catalog_sha256=self.catalog.fingerprint,
            source_sha256=self.catalog.source_sha256,
            source_clock='original task time = local physics seconds + score_offset_s',
            reset_selection='balanced original-finger buckets; selected episode boundaries only',
            evaluation='explicit runtime view; original full song or balanced phrases; same policy and control contract')
        self.contract['reward']['schema'] = 'guitar_learning.finger_skill_reward.v1'
        self.contract['reward']['base_measurement_reward'] = 'guitar_learning.gpu_tensor_song_reward.v22'
        self.contract['reward']['finger_skill'] = dict(
            phase=self.phase, fixed_music_progress=0.,
            weights=self._weights(),
            purpose='wrist/thumb/action-change/safety' if self.phase == 'R' else 'selected original musical task and weak own-idle B',
            balance='selected M/(selected present fingers*selected own-finger count)',
            wrong='original physical wrong geometry on selected audible targets; never missing unselected score',
            preparation_boundary='selected notes plus first following original note per finger; no artificial tail rest bonus')
        self.contract['termination']['failure_horizon_cost']['clock'] = 'remaining local view duration after actual control tick'
        self.contract['termination']['finger_skill_terminal'] = 'natural finite view end is terminal; H32 collection boundary is not an episode end'
        self.contract['diagnostics']['finger_skill'] = dict(
            schema='guitar_learning.finger_skill_diagnostics.v1',
            motion='same128 source material points per distal pad; endpoint60Hz vector decomposition only',
            recovery='original fixed source gaps intersected with actual selected performance interval; separate initial3s preparation',
            limitation='geometric motion and contact candidates, not causal force shares, calibrated pressure or sound')

    def _allocate(self, count):
        super()._allocate(count)
        self.score_offset = torch.zeros(count, dtype=torch.float64, device=self.device)
        self.duration_ticks = torch.full((count,), round(self.task.duration_s*60),
                                         dtype=torch.long, device=self.device)
        self.focus_mask = torch.ones(count, self.M, dtype=torch.bool, device=self.device)
        self.recovery_mask = self.focus_mask.clone()
        self.view_first = torch.zeros_like(self.score_offset)
        self.view_last = torch.full_like(self.score_offset, self.task.duration_s)
        self.phrase_ids = ['full_song']*count
        self.finger_weights = self.finger_weights.expand(count, -1).clone()
        # Legacy fixed full-song recovery windows are replaced by view-aware
        # windows; all existing angle, wrist and thumb diagnostics are retained.
        self.episode_diagnostics = LeftEpisodeDiagnostics(count, self.device)
        self.skill_diagnostics = SkillEpisodeDiagnostics(self.task, count, self.device)

    def _reset_scope(self, indices):
        full = self.evaluation_full_song if self.evaluation else self.training_scope == 'full_song'
        for index in indices.cpu().tolist():
            self.focus_mask[index] = full
            if full:
                self.score_offset[index] = 0.
                self.duration_ticks[index] = round(self.task.duration_s*60)
                self.view_first[index] = 3.
                self.view_last[index] = self.task.duration_s
                self.phrase_ids[index] = 'full_song'
            else:
                phrase = self.sampler.next()
                self.focus_mask[index, list(phrase.target_indices)] = True
                self.score_offset[index] = phrase.score_offset_s
                self.duration_ticks[index] = phrase.duration_ticks
                self.view_first[index] = phrase.start_s
                self.view_last[index] = phrase.end_s
                self.phrase_ids[index] = phrase.phrase_id
        selected = self.focus_mask[indices]
        counts = (selected[:, None] & self.preparation_assignment[None]).sum(-1)
        present = (counts > 0).sum(-1).clamp_min(1)
        own_count = counts[:, self.finger-1].clamp_min(1)
        self.finger_weights[indices] = (selected.sum(-1)[:, None]/(present[:, None]*own_count))*selected
        self.recovery_mask[indices] = selected
        # Preserve the next original preparation boundary without grading that
        # unselected note. Past unselected notes cannot create missed penalties.
        for finger in range(1, 5):
            owned = selected & (self.finger == finger)[None]
            last = self.end.expand(len(indices), -1).masked_fill(~owned, -torch.inf).amax(-1)
            last = torch.where(owned.any(-1), last, self.view_first[indices])
            future = ((self.finger == finger)[None] & ~selected &
                      (self.press[None] >= last[:, None]))
            next_index = self.press.expand(len(indices), -1).masked_fill(~future, torch.inf).argmin(-1)
            has_next = future.any(-1)
            self.recovery_mask[indices[has_next], next_index[has_next]] = True

    def reset(self, indices, snapshot):
        observation = super().reset(indices, snapshot)
        indices = torch.as_tensor(indices, dtype=torch.long, device=self.device)
        self.skill_diagnostics.reset(indices, self.score_offset, self.duration_ticks,
            *self._material_points(), self.focus_mask)
        return observation

    def set_evaluation(self, enabled=True, full_song=False):
        if type(enabled) is not bool or type(full_song) is not bool or self._substeps is not None:
            raise ValueError('Evaluation view changes require a completed control boundary')
        self.evaluation, self.evaluation_full_song = enabled, full_song

    def _score_time(self):
        return self._local_time()+self.score_offset

    def _guide_time(self):
        now = self._score_time()
        full = self.evaluation_full_song if self.evaluation else self.training_scope == 'full_song'
        if not full:
            now = torch.maximum(self.view_first, torch.minimum(now, self.view_last))
        return now-self.song['pre_roll_s']

    def _episode_duration(self):
        return self.duration_ticks.double()/60.

    def _target_scope(self):
        return self.focus_mask

    def _preparation_scope(self):
        return self.recovery_mask

    def _selected_finger_weights(self, indices):
        return self.finger_weights.gather(1, indices)

    def _reward_components(self, components):
        if self.phase != 'R':
            return components
        allowed = ('song_wrist_position', 'song_thumb_support', 'action_change', 'terminal_failure')
        return {key: value if key in allowed else torch.zeros_like(value)
                for key, value in components.items()}

    def _observation_state(self, state):
        phase = state.new_zeros(self.N, 3)
        phase[:, ('R', 'F', 'J').index(self.phase)] = 1.
        remaining = (self._episode_duration()-self._local_time()).clamp_min(0)
        return torch.cat((state, phase, state.new_ones(self.N, 1), remaining[:, None].float()), -1)

    def decision_observation(self, planned_ticks, observation=None):
        if (planned_ticks.shape != (self.N,) or planned_ticks.dtype != torch.long or
                bool((planned_ticks < 1).any()) or bool((planned_ticks > 6).any())):
            raise ValueError('Planned decision ticks must be long[N] in1..6')
        observation = self.observation() if observation is None else observation
        state = observation['state'].clone()
        state[:, -2] = planned_ticks.to(state)/6.
        return dict(observation, state=state)

    def plan_decisions(self, remaining_ticks):
        if type(remaining_ticks) is not int or remaining_ticks < 1:
            raise ValueError('Positive remaining control collection ticks required')
        maximum = min(remaining_ticks, self.hold_ticks if self.phase == 'F' else 1)
        local = self.clock//4
        events = torch.stack((self.press, self.onset, self.end), -1)[None]-self.score_offset[:, None, None]
        ticks = events*60.
        # Visit both adjacent control boundaries around an off-grid event. This
        # preserves the original60Hz opportunity before and just after it.
        boundaries = torch.stack((ticks.floor(), ticks.ceil()), -1)
        difference = boundaries-local[:, None, None, None]
        eligible = (difference > 0) & self.focus_mask[:, :, None, None]
        nearest = difference.masked_fill(~eligible, torch.inf).flatten(1).amin(-1)
        duration = torch.minimum(torch.full_like(nearest, maximum), nearest).long()
        return torch.minimum(duration, (self.duration_ticks-local).clamp_min(1)).clamp_min(1)

    def _material_points(self):
        pad = self.body[:, self.pad_indices]
        points = pad[:, :, None, :3]+apply(pad[:, :, None, 3:7], self.pad_local[None])
        return points, self.body[:, self.finger_palm_index, :7], self.guitar_body[:, :7]

    def _diagnose_posture(self, posture, pressing, now):
        super()._diagnose_posture(posture, pressing, now)
        self.skill_diagnostics.physics(self._local_time(), now, posture, pressing)

    def _record_finger_motion(self):
        super()._record_finger_motion()
        self.skill_diagnostics.control(self._local_time(), self._score_time(), *self._material_points())

    def _finger_metrics(self, index):
        metrics = []
        for finger in range(1, 5):
            mask = self.focus_mask[index] & (self.finger == finger)
            count = int(mask.sum().item())
            row = dict(target_count=count)
            for name, key in (('near_fraction', 'near_done'), ('contact_fraction', 'contact_done'),
                              ('success_fraction', 'left')):
                row[name] = float(self.note[key][index, mask].float().mean()) if count else 0.
            row['clean_fraction'] = float((self.note['clean'][index, mask]/(self.end-self.onset)[mask]).clamp_max(1).mean()) if count else 0.
            metrics.append(row)
        return metrics

    def _episode(self, index, failed):
        result = super()._episode(index, failed)
        mask = self.focus_mask[index]
        count = int(mask.sum().item())
        now = float(self._local_time()[index])
        full = not failed and now+1e-9 >= float(self._episode_duration()[index])
        song = result['song']
        song.update(denominator=count, target_count=count, completed=full,
            stage_success=full and not bool(self.invalid[index]) and song['left_success_count'] == count,
            provisional_success=not bool(self.invalid[index]) and song['left_success_count'] == count,
            mean_clean_audible_fraction=float((self.note['clean'][index, mask]/(self.end-self.onset)[mask]).clamp_max(1).mean()))
        result['musical_quality'].update(stage_success=song['stage_success'],
            provisional_success=song['provisional_success'], song=copy.deepcopy(song))
        result['left_curriculum'].update(schema='guitar_learning.finger_skill_metrics.v1',
            full_safe=full and not bool(self.invalid[index]),
            reach_fraction=float(self.note['reach_done'][index, mask].float().mean()),
            contact_fraction=float(self.note['contact_done'][index, mask].float().mean()))
        result['left_note_ledger']['focus_mask'] = mask.cpu().tolist()
        result['left_note_ledger']['selected_target_ids'] = [
            target.target_id for keep, target in zip(mask.cpu().tolist(), self.task.targets) if keep]
        result['finger_skill'] = dict(phase=self.phase, phrase_id=self.phrase_ids[index],
            scope='full_song' if count == self.M else 'phrase',
            score_offset_s=float(self.score_offset[index]), local_duration_s=float(self._episode_duration()[index]),
            original_target_count=self.M, selected_target_count=count,
            source_task_time_s=float(self._score_time()[index]))
        result['evaluation'] = self.evaluation
        result['finger_skill_eval'] = dict(phase=self.phase, scope=result['finger_skill']['scope'],
            wrist_inside_fraction=float(self.episode_diagnostics.values['wrist_inside_s'][index]/
                                        self.episode_diagnostics.values['physics_s'][index].clamp_min(1e-30)))
        result['finger_skill_diagnostics'] = self.skill_diagnostics.episode(index)
        return result
