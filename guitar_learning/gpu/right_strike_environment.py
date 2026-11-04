"""Diagnostic preparation, one native crossing and recovery for the right hand.

The parent owns all observations, rewards, control and native strike ledgers.
This subclass records stricter quality without gating or changing those ledgers.
"""
import copy
from dataclasses import asdict

import torch

from guitar_learning.core.measurement import StrikeContract
from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.quality.strike_quality import STRIKE_QUALITY_METADATA


RIGHT_STRIKE_QUALITY_CONTRACT = dict(
    schema='guitar_learning.gpu_right_strike_quality.v1',
    target=dict(runtime_string=2, standard_string_1based=3, direction=1,
                onset_s=3., episode_duration_s=5.),
    geometry={key: copy.deepcopy(STRIKE_QUALITY_METADATA[key]) for key in
              ('separation_m', 'required_observations', 'physics_hz', 'preparation',
               'ready', 'recovery', 'recovery_dwell_s')},
    event_accounting='parent native wrong/repeat ledgers preserved; ineligible and wait_rearm-blocked XY passages are raw diagnostics only; no extra quality penalty',
    native_strike=asdict(StrikeContract()),
    sampling='consecutive per-environment native physics_step tensors at240Hz; reset endpoint counted once for readiness',
    accepted='parent right-note false-to-true transition, recorded separately from quality acceptance; readiness must predate its current endpoint',
    recovery='two consecutive separated observations strictly after quality acceptance; current recovery resets on re-approach',
    success='full safe timeline, exactly one prepared expected native hit, currently recovered, no native wrong/repeat; left clean not required',
    effect='diagnostics only; original native strike eligibility, observations, rewards, ledgers, stage_success and control unchanged',
    limitations='point-marker geometry, not physical pick grip, string vibration or sound')


class RightStrikeEnvironment(TensorSongEnvironment):
    """Single downstroke on canonical string3 with the original right-hand task."""
    def __init__(self, metadata, *, bundle, song, hand='right', device='cuda:0'):
        if hand != 'right':
            raise ValueError('RightStrikeEnvironment requires hand=right')
        super().__init__(metadata, bundle=bundle, song=song, hand=hand, device=device)
        if (len(self.task.targets) != 1 or self.task.targets[0].string != 2 or
                self.task.targets[0].direction != 1 or self.task.targets[0].onset_s != 3. or
                self.task.duration_s != 5.):
            raise ValueError('One canonical string3/down/onset3s target in a5s task required')
        self.contract.setdefault('diagnostics', {})['right_strike_quality'] = copy.deepcopy(
            RIGHT_STRIKE_QUALITY_CONTRACT)

    def _allocate(self, count):
        super()._allocate(count)
        self.strike_quality = {}
        for name in ('preparation_samples', 'native_expected_hits', 'accepted', 'unprepared_hits',
                     'recovery_samples', 'raw_xy_crossings', 'raw_target_xy_crossings', 'physics_samples'):
            self.strike_quality[name] = torch.zeros(count, dtype=torch.long, device=self.device)
        for name in ('ready', 'preparation_previous', 'prepared_before_hit', 'recovered',
                     'ever_recovered', 'unsafe_seen'):
            self.strike_quality[name] = torch.zeros(count, dtype=torch.bool, device=self.device)
        for name in ('preparation_total_s', 'preparation_longest_s', 'recovery_dwell_s'):
            self.strike_quality[name] = torch.zeros(count, dtype=torch.float64, device=self.device)
        for name in ('prepared_at_s', 'first_hit_at_s', 'first_hit_error_s'):
            self.strike_quality[name] = torch.full((count,), torch.nan, dtype=torch.float64, device=self.device)

    def reset(self, indices, snapshot):
        observation = super().reset(indices, snapshot)
        self._reset_quality(torch.as_tensor(indices, dtype=torch.long, device=self.device))
        return observation

    def _reset_quality(self, rows):
        for name, value in self.strike_quality.items():
            value[rows] = torch.nan if name in ('prepared_at_s', 'first_hit_at_s', 'first_hit_error_s') else 0
        self._observe_quality(rows, torch.zeros(self.N, dtype=torch.bool, device=self.device), initial=True)

    def _quality_geometry(self):
        start, end = self.starts[:, 2], self.ends[:, 2]
        line = end-start
        xy2 = line[:, :2].square().sum(-1)
        length2 = line.square().sum(-1)
        valid = (xy2 > 1e-12) & (length2 > 1e-12)
        normal = torch.stack((-line[:, 1], line[:, 0]), -1)/xy2.sqrt().clamp_min(1e-12)[:, None]
        normal = torch.where(normal[:, :1] < 0, -normal, normal)
        u = ((self.pick[:, :2]-start[:, :2])*line[:, :2]).sum(-1)/xy2.clamp_min(1e-12)
        depth = (start+u[:, None]*line)[:, 2]-self.pick[:, 2]
        signed = ((self.pick[:, :2]-start[:, :2])*normal).sum(-1)
        preparation = (valid & (u >= 0) & (u <= 1) & (-signed >= .003) &
            (depth >= .001) & (depth <= .015) & (self.pick[:, 1] >= -.385) & (self.pick[:, 1] <= -.255))
        nearest_u = (((self.pick-start)*line).sum(-1)/length2.clamp_min(1e-12)).clamp(0, 1)
        separated = valid & (torch.linalg.vector_norm(self.pick-(start+nearest_u[:, None]*line), dim=-1) >= .003)
        return preparation, separated

    def _observe_quality(self, rows, recovery, initial=False):
        preparation, separated = self._quality_geometry()
        q = self.strike_quality
        if not initial:
            q['preparation_total_s'][rows] += (q['preparation_previous'][rows] & preparation[rows]).double()/240.
        q['preparation_previous'][rows] = preparation[rows]
        q['preparation_samples'][rows] = torch.where(preparation[rows], q['preparation_samples'][rows]+1, 0)
        q['preparation_longest_s'][rows] = torch.maximum(q['preparation_longest_s'][rows],
            (q['preparation_samples'][rows]-1).clamp_min(0).double()/240.)
        now_ready = q['preparation_samples'][rows] >= 2
        first = now_ready & ~q['ready'][rows]
        q['prepared_at_s'][rows] = torch.where(first, self._score_time()[rows], q['prepared_at_s'][rows])
        q['ready'][rows] |= now_ready
        q['recovery_samples'][rows] = torch.where(recovery[rows],
            torch.where(separated[rows], q['recovery_samples'][rows]+1, 0), q['recovery_samples'][rows])
        q['recovery_dwell_s'][rows] = (q['recovery_samples'][rows]-1).clamp_min(0).double()/240.
        q['recovered'][rows] = q['recovery_samples'][rows] >= 2
        q['ever_recovered'][rows] |= q['recovered'][rows]

    def _strike(self, before, now, both):
        q = self.strike_quality
        ready_before = q['ready'].clone()
        accepted_before = q['accepted'] > 0
        right_before = self.note['right'][:, 0].clone()
        # Raw XY intersections include ineligible lifted/slow/deep passages.
        # The parent's geometric_crossings is native eligible/rearmed events.
        delta = self.pick-self.previous_pick
        line = self.ends-self.starts
        cross = lambda a, b: a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]
        denominator = cross(delta[:, None, :2], line[..., :2])
        safe = torch.where(denominator.abs() > 1e-12, denominator, torch.ones_like(denominator))
        offset = self.starts-self.previous_pick[:, None]
        alpha = cross(offset[..., :2], line[..., :2])/safe
        fraction = cross(offset[..., :2], delta[:, None, :2])/safe
        raw = ((denominator.abs() > 1e-12) & (alpha > 0) & (alpha <= 1) &
               (fraction >= 0) & (fraction <= 1))
        q['raw_xy_crossings'] += raw.sum(-1)
        q['raw_target_xy_crossings'] += raw[:, 2]
        super()._strike(before, now, both)
        expected = self.note['right'][:, 0] & ~right_before
        q['native_expected_hits'] += expected
        q['accepted'] += expected & ready_before
        q['unprepared_hits'] += expected & ~ready_before
        q['prepared_before_hit'] = torch.where(expected, ready_before, q['prepared_before_hit'])
        q['first_hit_error_s'] = torch.where(expected, self.note['error'][:, 0], q['first_hit_error_s'])
        q['first_hit_at_s'] = torch.where(expected, self.onset[0]+self.note['error'][:, 0], q['first_hit_at_s'])
        q['physics_samples'] += 1
        self._observe_quality(torch.arange(self.N, device=self.device), accepted_before)

    def substep(self, snapshot):
        if self._substeps is None or self._substeps >= 4:
            raise RuntimeError('Exactly four native snapshots per control tick required')
        step = snapshot.get('physics_step')
        if (not isinstance(step, torch.Tensor) or step.dtype != torch.long or
                step.shape != self.clock.shape or step.device != self.device):
            raise ValueError('Consecutive per-environment native physics_step long tensors required')
        torch._assert_async((step == self.clock+1).all(), 'Consecutive right-strike native snapshots required')
        super().substep(snapshot)
        self.strike_quality['unsafe_seen'] |= (self._control_failures() | self.control_invalid |
                                              self.invalid | self.failure.any(-1))

    def _episode(self, index, failed):
        result = super()._episode(index, failed)
        q = {name: value[index].item() for name, value in self.strike_quality.items()}
        full = not failed and float(self._local_time()[index])+1e-9 >= self.task.duration_s
        safe = not (failed or q['unsafe_seen'] or bool(self.invalid[index]) or
                    bool(self.failure[index].any()) or bool(self.control_invalid[index]))
        wrong, repeat = int(self.wrong_crossings[index]), int(self.repeat_crossings[index])
        success = bool(full and safe and q['native_expected_hits'] == q['accepted'] == 1 and
                       q['prepared_before_hit'] and q['recovered'] and wrong == repeat == 0)
        result['right_strike_quality'] = dict(
            schema=RIGHT_STRIKE_QUALITY_CONTRACT['schema'], target_id=self.task.targets[0].target_id,
            prepared=q['ready'], preparation_observed=q['ready'],
            preparation_dwell_s=q['preparation_longest_s'], preparation_total_s=q['preparation_total_s'],
            prepared_at_s=q['prepared_at_s'] if q['ready'] else None,
            prepared_before_hit=q['prepared_before_hit'], native_expected_hit_count=q['native_expected_hits'],
            accepted_count=q['accepted'], unprepared_hit_count=q['unprepared_hits'],
            first_hit_at_s=q['first_hit_at_s'] if q['native_expected_hits'] else None,
            first_hit_time_error_s=q['first_hit_error_s'] if q['native_expected_hits'] else None,
            recovered=q['recovered'], ever_recovered=q['ever_recovered'],
            recovery_dwell_s=q['recovery_dwell_s'], recovery_consecutive_samples=q['recovery_samples'],
            raw_xy_crossings=q['raw_xy_crossings'], raw_target_xy_crossings=q['raw_target_xy_crossings'],
            native_eligible_crossings=int(self.geometric_crossings[index]), wrong_count=wrong, repeat_count=repeat,
            strict_matched50=bool(self.note['match50'][index, 0]), strict_matched100=bool(self.note['match100'][index, 0]),
            strict_wrong_count=int(self.strict_wrong[index]), completed_physics_samples=q['physics_samples'],
            integration_hz=240, full_timeline=full, full_safe=bool(full and safe), success=success,
            scope=RIGHT_STRIKE_QUALITY_CONTRACT['limitations'])
        return result
