"""Add conservative 240 Hz pair diagnostics to the unchanged J training task.

These metrics describe loaded pad geometry, not string pressure or sound. They
never enter rewards, observations, action decoding, safety or native control.
"""
import torch

from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment


class PairEnvironment(FingerSkillEnvironment):
    measurement_start_s = 3.30
    measurement_end_s = 4.80

    def __init__(self, metadata, **kwargs):
        super().__init__(metadata, **kwargs)
        self._validate_pair()
        self.contract['diagnostics']['simultaneous_press'] = dict(
            schema='guitar_learning.adjacent_pair_measurement.v1',
            source_score_window_s=[self.measurement_start_s, self.measurement_end_s],
            integration_hz=240,
            clean='both targets candidate and not wrong at both adjacent native endpoints; both endpoints safe',
            wrong='union over targets and both endpoints, conservative full interval',
            safety='existing physical, control and wrist failure flags; no threshold changes',
            success='completed safe episode, full 1.5s simultaneous clean with no wrong',
            scope='diagnostics only; original per-note achievement and stage_success unchanged; no pressure or sound certification')

    def _validate_pair(self):
        targets = self.task.targets
        if len(targets) != 2:
            raise ValueError('PairEnvironment requires exactly two targets')
        a, b = targets
        if (abs(a.finger-b.finger) != 1 or abs(a.string-b.string) != 1 or
                abs(a.fret-b.fret) not in (0, 1)):
            raise ValueError('Adjacent distinct fingers/strings and fret difference 0 or 1 required')
        if any(t.onset_s > self.measurement_start_s or
               t.end_s < self.measurement_end_s for t in targets):
            raise ValueError('Both audible target windows must contain the fixed measurement window')
        if (len(self.catalog.closed_groups) != 1 or
                set(self.catalog.closed_groups[0]) != {0, 1} or
                any(set(p.target_indices) != {0, 1} for p in self.catalog.phrases)):
            raise ValueError('Scheduled phrase exposure must never split the chord')

    def _allocate(self, count):
        super()._allocate(count)
        self.pair_values = {
            name: torch.zeros(count, dtype=torch.float64, device=self.device)
            for name in ('observed_s', 'clean_s', 'streak_s', 'longest_s', 'wrong_s', 'unsafe_s')}
        self.pair_individual_clean = torch.zeros(count, 2, dtype=torch.float64, device=self.device)
        self.pair_unsafe_seen = torch.zeros(count, dtype=torch.bool, device=self.device)

    def reset(self, indices, snapshot):
        observation = super().reset(indices, snapshot)
        rows = torch.as_tensor(indices, dtype=torch.long, device=self.device)
        if not bool(self.focus_mask[rows].all()):
            raise ValueError('Both pair targets must be selected by scheduled exposure')
        for value in self.pair_values.values():
            value[rows] = 0
        self.pair_individual_clean[rows] = 0
        self.pair_unsafe_seen[rows] = False
        return observation

    def _pair_safe(self):
        return ~(self.invalid | self.failure.any(-1) | self.tick_failure.any(-1) |
                 self.control_invalid | self.wrist_failure | self.wrist_severe_failure)

    def substep(self, snapshot):
        # Capture before super: it advances the native clock, refreshes contact
        # geometry, evaluates safety and replaces previous_candidate/wrong.
        before = self._score_time().clone()
        clean_before = self.candidate & ~self.wrong
        wrong_before = self.wrong.clone()
        safe_before = self._pair_safe()
        super().substep(snapshot)
        self._measure_pair(before, self._score_time(), clean_before, wrong_before, safe_before)

    def _measure_pair(self, before, now, clean_before, wrong_before, safe_before):
        dt = (torch.minimum(now, now.new_tensor(self.measurement_end_s)) -
              torch.maximum(before, before.new_tensor(self.measurement_start_s))).clamp_min(0)
        safe = safe_before & self._pair_safe()
        clean = clean_before & self.candidate & ~self.wrong
        together = clean.all(-1) & safe
        wrong = (wrong_before | self.wrong).any(-1)
        values = self.pair_values
        values['observed_s'] += dt
        values['clean_s'] += dt*together
        values['streak_s'] = torch.where(together & (dt > 0), values['streak_s']+dt, 0.)
        values['longest_s'] = torch.maximum(values['longest_s'], values['streak_s'])
        values['wrong_s'] += dt*wrong
        values['unsafe_s'] += dt*~safe
        self.pair_individual_clean += dt[:, None]*clean*safe[:, None]
        self.pair_unsafe_seen |= ~safe

    def _pair_episode(self, index, result, failed):
        values = {name: float(value[index]) for name, value in self.pair_values.items()}
        duration = self.measurement_end_s-self.measurement_start_s
        full_safe = bool(result['left_curriculum']['full_safe'] and
                         not failed and not self.pair_unsafe_seen[index])
        achievements = self.note['left'][index].cpu().tolist()
        success = bool(full_safe and values['observed_s']+1e-9 >= duration and
                       values['clean_s']+1e-9 >= duration and
                       values['longest_s']+1e-9 >= duration and values['wrong_s'] == 0.)
        failures = []
        if not full_safe:
            failures.append('incomplete_or_unsafe_episode')
        if values['observed_s']+1e-9 < duration:
            failures.append('measurement_window_incomplete')
        if not all(achievements):
            failures.append('individual_achievement_failed')
        if values['clean_s']+1e-9 < duration:
            failures.append('simultaneous_hold_failed')
        if values['wrong_s'] > 0:
            failures.append('wrong_press')
        return dict(schema='guitar_learning.adjacent_pair_measurement.v1',
            source_score_window_s=[self.measurement_start_s, self.measurement_end_s],
            integration_hz=240, target_ids=[t.target_id for t in self.task.targets],
            observed_s=values['observed_s'], clean_s=values['clean_s'],
            clean_fraction=min(1., values['clean_s']/duration), longest_clean_s=values['longest_s'],
            wrong_union_s=values['wrong_s'], unsafe_s=values['unsafe_s'], full_safe=full_safe,
            individual_clean_s=self.pair_individual_clean[index].cpu().tolist(),
            individual_achievements=achievements, failures=failures, success=success,
            scope='loaded pad geometry and resultant body load; no calibrated string pressure or acoustic success')

    def _episode(self, index, failed):
        result = super()._episode(index, failed)
        result['simultaneous_press'] = self._pair_episode(index, result, failed)
        return result
