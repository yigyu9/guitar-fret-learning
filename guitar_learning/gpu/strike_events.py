"""240Hz 현 교차와 60Hz 보상을 잇는 이벤트별 타현 원장."""
import math

import torch

from guitar_learning.gpu.strike_reward import S3_WEIGHTS


SOURCE_SHA256 = {
    'legacy/env/strike_events.py': 'ab970cd535d79908387b6e170ceabfdf95c12bb750a751df200469df254eaa9f',
    'legacy/env/strike_detector.py': 'bd872632e6d76c87625bcec396b0cb49752728c17dead3cc4d4229ecc5936882',
    'legacy/env/tasks/task_strike.py': '6368c8623141369de0a51a6719df0888cea8fbd75bffc04f42dbc80a23871a05',
}
STRIKE_LEDGER_CONTRACT = dict(schema='guitar_learning.strike_ledger.v1',
    readiness_s=.10, full_recovery_s=.20, minimum_handoff_s=2./60.,
    readiness='first episode latch; later events inherit the acquired preparation qualification',
    readiness_source='legacy/env/tasks/task_strike.py:2009-2035,3724-3739',
    approach_lead_s=.07, clearance_m=.004, timing_tolerance_s=.05,
    recovery_speed_limit_m_s=.20, recovery_speed_excess_m_s=.50,
    geometry='caller owns 240Hz crossing, depth limits and native rearm',
    source_sha256=SOURCE_SHA256)
CLEAN_TERMS = ('crossing', 'timing', 'strum_terminal_progress',
               'strum_physical_completion', 'strum_microtiming',
               'recovery_progress', 'recovery_complete')


class StrikeLedger:
    """스트럼의 전체 통과와 음이 나는 현을 구분하고 보상을 한 번만 지급한다."""

    def __init__(self, N, events, device):
        if N < 1 or not events:
            raise ValueError('a strike ledger requires environments and events')
        self.N, self.events, self.E = int(N), tuple(events), len(events)
        self.device = torch.device(device)
        self.rows = torch.arange(self.N, device=self.device)
        self.traversal = torch.zeros(self.E, 6, dtype=torch.bool, device=self.device)
        self.audible = torch.zeros_like(self.traversal)
        self.rank = torch.full((self.E, 6), 6, dtype=torch.long, device=self.device)
        self.expected_times = torch.zeros(self.E, 6, dtype=torch.float64, device=self.device)
        for index, event in enumerate(events):
            strings = tuple(event.traversal_strings)
            if (event.direction not in (-1, 1) or not strings
                    or len(set(strings)) != len(strings)
                    or any(s not in range(6) for s in strings)
                    or not event.audible_strings
                    or not set(event.audible_strings).issubset(strings)
                    or len(strings) != len(event.traversal_offsets_s)
                    or event.gesture not in ('single_pick', 'strum')):
                raise ValueError('invalid strike event traversal')
            expected_order = tuple(sorted(strings, reverse=event.direction == 1))
            if strings != expected_order:
                raise ValueError('traversal order conflicts with direction')
            offsets = tuple(event.traversal_offsets_s)
            if (not all(math.isfinite(x) for x in offsets+(event.onset_s,))
                    or any(b <= a for a, b in zip(offsets, offsets[1:]))
                    or not math.isclose(offsets[-1]-offsets[0], event.sweep_duration_s, abs_tol=1e-9)):
                raise ValueError('invalid strike event timing')
            self.traversal[index, list(strings)] = True
            self.audible[index, list(event.audible_strings)] = True
            self.rank[index, list(strings)] = torch.arange(len(strings), device=self.device)
            self.expected_times[index, list(strings)] = torch.tensor(
                [event.onset_s+x for x in offsets], device=self.device, dtype=torch.float64)
        self.direction = torch.tensor([e.direction for e in events], device=self.device)
        self.is_strum = torch.tensor([e.gesture == 'strum' for e in events], device=self.device)
        self.sweep_duration = torch.tensor([e.sweep_duration_s for e in events],
                                           dtype=torch.float64, device=self.device)
        self.onset = torch.tensor([e.onset_s for e in events], dtype=torch.float64, device=self.device)
        self.deadline = torch.tensor([e.onset_s+e.traversal_offsets_s[-1]+.05 for e in events],
                                     dtype=torch.float64, device=self.device)
        if torch.any(self.onset[1:] < self.onset[:-1]):
            raise ValueError('strike events must be in onset order')
        self.history = {}
        for name in ('ready', 'wrong', 'unprepared', 'resolved', 'complete', 'missed',
                     'timed_complete', 'clean_complete', 'audible_complete', 'recovered'):
            self.history[name] = torch.zeros(self.N, self.E, dtype=torch.bool, device=self.device)
        for name in ('unplanned', 'wrong_direction', 'order_violation', 'duplicate'):
            self.history[name] = torch.zeros(self.N, self.E, device=self.device)
        self.history['accepted'] = torch.zeros(self.N, self.E, 6, dtype=torch.bool, device=self.device)
        self.history['times'] = torch.zeros(self.N, self.E, 6, dtype=torch.float64, device=self.device)
        self.history['zone'] = torch.ones(self.N, self.E, 6, device=self.device)
        self.active = torch.zeros(self.N, dtype=torch.long, device=self.device)
        self.done = torch.zeros(self.N, dtype=torch.bool, device=self.device)
        self.phase = torch.zeros(self.N, dtype=torch.long, device=self.device)  # 준비0/접근1/회복2
        self.episode_ready = torch.zeros(self.N, dtype=torch.bool, device=self.device)
        self.now = torch.zeros(self.N, dtype=torch.float64, device=self.device)
        self.ready_elapsed = torch.zeros(self.N, device=self.device)
        self.recovery_elapsed = torch.zeros_like(self.ready_elapsed)
        self.recovery_best = torch.zeros_like(self.ready_elapsed)
        self.recovery_required = torch.full_like(self.ready_elapsed, .20)
        self.handoff = torch.zeros_like(self.done)
        self.clearance_required = torch.zeros_like(self.done)
        self.rearm_required = torch.ones_like(self.done)
        self.path_mask = torch.zeros(self.N, 6, dtype=torch.bool, device=self.device)
        self._recovery_fresh = torch.zeros_like(self.done)
        self.terminal_best = torch.zeros_like(self.ready_elapsed)
        self.begin_tick()

    def reset(self, env_ids):
        """지정한 환경만 초기화하고 나머지 원장을 유지한다."""
        ids = torch.as_tensor(env_ids, device=self.device, dtype=torch.long)
        for name, value in self.history.items():
            value[ids] = 1 if name == 'zone' else 0
        for name in ('active', 'done', 'phase', 'now', 'episode_ready', 'ready_elapsed', 'recovery_elapsed',
                     'recovery_best', 'handoff', 'clearance_required', 'path_mask',
                     '_recovery_fresh', 'terminal_best'):
            getattr(self, name)[ids] = 0
        self.rearm_required[ids] = True
        self.recovery_required[ids] = .20
        for value in self.terms.values():
            value[ids] = 0
        for value in self._tick_clean_terms.values():
            value[ids] = 0
        self._tick_zone[ids] = 1
        self._tick_zone_valid[ids] = False

    def current(self, name):
        return self.history[name][self.rows, self.active]

    @property
    def remaining(self):
        return self.traversal[self.active] & ~self.current('accepted') & ~self.done[:, None]

    @property
    def next_string(self):
        rank = self.rank[self.active].masked_fill(~self.remaining, 7)
        return torch.where(self.remaining.any(-1), rank.argmin(-1), torch.full_like(self.active, -1))

    def begin_tick(self):
        """60Hz 순간 항을 비우고 같은 tick의 중복 구역 지급을 막는다."""
        self.terms = {name: torch.zeros(self.N, device=self.device) for name in S3_WEIGHTS}
        self._tick_clean_terms = {name: torch.zeros(self.N, self.E, device=self.device)
                                  for name in CLEAN_TERMS}
        self._tick_zone = torch.ones(self.N, device=self.device)
        self._tick_zone_valid = torch.zeros(self.N, dtype=torch.bool, device=self.device)

    def update_ready(self, ready, dt=1./60.):
        self._vector(ready, 'ready', boolean=True)
        self._dt(dt)
        eligible = ~self.done & ~self.current('resolved') & (self.phase != 2)
        self.ready_elapsed = torch.where(eligible & ready, self.ready_elapsed+dt,
                                          torch.zeros_like(self.ready_elapsed))
        pulse = eligible & ~self.episode_ready & (self.ready_elapsed >= .10-1e-7)
        self.episode_ready |= pulse
        self.history['ready'][self.rows, self.active] |= self.episode_ready
        self.terms['ready'] += pulse
        approach_open = self.now >= self.expected_times[self.active].masked_fill(
            ~self.traversal[self.active], torch.inf).amin(-1)-.07
        self.phase = torch.where(eligible & self.current('ready') & approach_open,
                                 torch.ones_like(self.phase), self.phase)
        return dict(ready=self.current('ready'), pulse=pulse)

    def cross(self, env_ids, string, direction, time, zone_quality):
        """같은 물리 구간의 교차는 환경별 시각순으로 한 건씩 전달한다."""
        ids = torch.as_tensor(env_ids, dtype=torch.long, device=self.device)
        if ids.ndim != 1 or ids.numel() != ids.unique().numel() or torch.any((ids < 0) | (ids >= self.N)):
            raise ValueError('cross requires unique valid environment indices')
        s = torch.as_tensor(string, dtype=torch.long, device=self.device)
        d = torch.as_tensor(direction, dtype=torch.long, device=self.device)
        at = torch.as_tensor(time, dtype=torch.float64, device=self.device)
        zone = torch.as_tensor(zone_quality, dtype=torch.float32, device=self.device)
        for value in (s, d, at, zone):
            if value.shape != ids.shape or not torch.isfinite(value).all():
                raise ValueError('cross inputs must be finite vectors matching env_ids')
        if torch.any((s < 0) | (s >= 6) | ((d != -1) & (d != 1)) | (zone < 0) | (zone > 1)):
            raise ValueError('invalid crossing string, direction or quality')
        e = self.active[ids]
        self._disrupt_recovery(ids)
        live = ~self.done[ids] & ~self.history['resolved'][ids, e]
        target = self.traversal[e, s]
        direction_ok = d == self.direction[e]
        already = self.history['accepted'][ids, e, s]
        correct_order = s == self.next_string[ids]
        unplanned = ~target | ~live
        wrong_direction = live & target & ~direction_ok
        duplicate = live & target & direction_ok & already
        out_of_order = live & target & direction_ok & ~already & ~correct_order
        wrong = unplanned | wrong_direction | duplicate | out_of_order
        for name, flag in (('unplanned', unplanned), ('wrong_direction', wrong_direction),
                           ('duplicate', duplicate), ('order_violation', out_of_order)):
            self.history[name][ids, e] += flag
        self.history['wrong'][ids, e] |= wrong
        self.history['clean_complete'][ids, e] &= ~wrong
        self._invalidate_tick(ids[wrong])
        self.terms['wrong'][ids] += wrong
        accepted = live & target & direction_ok & ~already & correct_order
        prepared = self.history['ready'][ids, e]
        self.history['unprepared'][ids, e] |= accepted & ~prepared
        self.history['accepted'][ids, e, s] |= accepted
        self.history['times'][ids, e, s] = torch.where(accepted, at, self.history['times'][ids, e, s])
        self.history['zone'][ids, e, s] = torch.where(accepted, zone, self.history['zone'][ids, e, s])
        self.now[ids] = torch.maximum(self.now[ids], at)
        clean = ~self.history['wrong'][ids, e]
        quality = 1./(1.+((at-self.expected_times[e, s])/.020).square())
        count = self.traversal[e].sum(-1).float()
        self.terms['strum_progress'][ids] += accepted*prepared*self.is_strum[e]/count
        self._credit('timing', ids, (accepted*prepared*clean*quality/count).float())
        zone_valid = accepted & prepared
        self._tick_zone[ids] = torch.minimum(self._tick_zone[ids],
                                            torch.where(zone_valid, zone, torch.ones_like(zone)))
        self._tick_zone_valid[ids] |= zone_valid
        self.terms['zone'][ids] = self._tick_zone[ids]*self._tick_zone_valid[ids]
        early = ((-at+self.expected_times[e, s]-.008)/.030).clamp(0., 1.).square()
        self.terms['early_timing'][ids] += (accepted*early/count).float()
        all_accepted = self.history['accepted'][ids, e]
        complete = live & accepted & (all_accepted | ~self.traversal[e]).all(-1)
        audible_complete = (all_accepted | ~self.audible[e]).all(-1)
        self.history['audible_complete'][ids, e] |= audible_complete & live
        if complete.any():
            chosen = ids[complete]
            ce = self.active[chosen]
            errors = self.history['times'][chosen, ce]-self.expected_times[ce]
            mask = self.traversal[ce]
            timed = ((errors.abs() <= .05+1e-12) | ~mask).all(-1)
            pre = self.history['ready'][chosen, ce] & ~self.history['unprepared'][chosen, ce]
            clean_full = timed & pre & ~self.history['wrong'][chosen, ce]
            self.history['complete'][chosen, ce] = True
            self.history['timed_complete'][chosen, ce] = timed
            self.history['clean_complete'][chosen, ce] = clean_full
            self.history['resolved'][chosen, ce] = True
            self._credit('crossing', chosen, clean_full.float())
            self.terms['unprepared'][chosen] += ~pre
            self.terms['miss'][chosen] += ~timed
            self.history['missed'][chosen, ce] |= ~timed
            self.terms['premature'][chosen] += ((errors < -.05-1e-12) & mask).any(-1)
            is_strum = self.is_strum[ce]
            self._credit('strum_physical_completion', chosen,
                         (is_strum*pre*~self.history['wrong'][chosen, ce]).float())
            rms = ((errors.square()*mask).sum(-1)/mask.sum(-1)).sqrt()
            actual = (self.history['times'][chosen, ce].masked_fill(~mask, -torch.inf).amax(-1)
                      - self.history['times'][chosen, ce].masked_fill(~mask, torch.inf).amin(-1))
            planned = self.sweep_duration[ce]
            micro = .5*(1./(1.+(rms/.020).square())+1./(1.+((actual-planned)/.025).square()))
            self._credit('strum_microtiming', chosen,
                         (is_strum*pre*~self.history['wrong'][chosen, ce]*micro).float())
            self._start_recovery(chosen)
        return dict(accepted=accepted, wrong=wrong, completed=complete, prepared=prepared)

    def _start_recovery(self, ids):
        self.phase[ids] = 2
        self.recovery_elapsed[ids] = 0
        self.recovery_best[ids] = 0
        self._recovery_fresh[ids] = True
        e = self.active[ids]
        continuing = e+1 < self.E
        next_e = (e+1).clamp_max(self.E-1)
        available = self.expected_times[next_e].masked_fill(~self.traversal[next_e], torch.inf).amin(-1)-self.now[ids]-.07
        self.handoff[ids] = continuing & (available < .20)
        self.recovery_required[ids] = torch.where(self.handoff[ids], available.clamp(2./60., .20),
                                                  torch.full_like(available, .20)).float()
        final_s = self.rank[e].masked_fill(~self.history['accepted'][ids, e], -1).argmax(-1)
        next_s = self.rank[next_e].argmin(-1)
        exit_side = 2*final_s-self.direction[e]
        entry_side = 2*next_s+self.direction[next_e]
        positions = 2*torch.arange(6, device=self.device)[None]
        self.path_mask[ids] = continuing[:, None] & (positions > torch.minimum(exit_side, entry_side)[:, None]) & (positions < torch.maximum(exit_side, entry_side)[:, None])
        self.clearance_required[ids] = self.path_mask[ids].any(-1)
        self.rearm_required[ids] = ~self.handoff[ids] | (final_s == next_s) | self.clearance_required[ids]

    def advance(self, now):
        self._vector(now, 'now')
        if torch.any(now < self.now-1e-9):
            raise ValueError('strike clock cannot run backwards')
        self.now.copy_(now)
        approach_open = now >= self.expected_times[self.active].masked_fill(
            ~self.traversal[self.active], torch.inf).amin(-1)-.07
        self.phase = torch.where(~self.done & ~self.current('resolved')
            & self.current('ready') & approach_open, torch.ones_like(self.phase), self.phase)
        expired = ~self.done & ~self.current('resolved') & (now > self.deadline[self.active]+1e-12)
        self.terms['miss'] += expired
        self.history['missed'][self.rows, self.active] |= expired
        self.history['resolved'][self.rows, self.active] |= expired
        partial = expired & self.current('accepted').any(-1)
        if partial.any():
            self._start_recovery(self.rows[partial])
        self.history['recovered'][self.rows, self.active] |= expired & ~partial
        move = ~self.done & self.current('resolved') & self.current('recovered')
        self.done |= move & (self.active == self.E-1)
        move &= ~self.done
        self.active[move] += 1
        self.history['ready'][self.rows[move], self.active[move]] = self.episode_ready[move]
        self.phase[move] = 0
        self.ready_elapsed[move] = 0
        self.recovery_elapsed[move] = 0
        self.recovery_best[move] = 0
        self.terminal_best[move] = 0
        return dict(missed=expired, moved=move, done=self.done.clone())

    def update_recovery(self, clearance, separated, armed, dt):
        for name, value in (('clearance', clearance), ('separated', separated), ('armed', armed)):
            self._vector(value, name, boolean=name != 'clearance')
        self._dt(dt)
        active = ~self.done & (self.phase == 2) & self.current('resolved') & ~self.current('recovered')
        eligible = (active & ~self._recovery_fresh & separated
                    & (~self.rearm_required | armed)
                    & (~self.clearance_required | (clearance >= .004)))
        self.recovery_elapsed = torch.where(eligible, self.recovery_elapsed+dt,
                                              torch.zeros_like(self.recovery_elapsed))
        progress = (self.recovery_elapsed/self.recovery_required).clamp(0., 1.)
        next_best = torch.maximum(self.recovery_best, progress)
        increment = torch.where(active, next_best-self.recovery_best, torch.zeros_like(progress))
        self.recovery_best.copy_(next_best)
        pulse = eligible & (self.recovery_elapsed >= self.recovery_required-1e-7)
        self.history['recovered'][self.rows, self.active] |= pulse
        reward_eligible = self.current('clean_complete')
        self._credit('recovery_progress', self.rows, increment*reward_eligible)
        self._credit('recovery_complete', self.rows, (pulse*reward_eligible).float())
        self._recovery_fresh[active] = False
        return dict(active=active, progress=progress, pulse=pulse)

    def add_terminal_progress(self, progress):
        """환경이 산출한 마지막 현→exit 투영의 최고 증가분만 반영한다."""
        self._vector(progress, 'terminal progress')
        eligible = ~self.done & self.is_strum[self.active] & ~self.current('resolved')
        eligible &= self.current('ready') & ~self.current('wrong') & (self.remaining.sum(-1) == 1)
        best = torch.maximum(self.terminal_best, progress.clamp(0., 1.))
        self._credit('strum_terminal_progress', self.rows, (best-self.terminal_best)*eligible)
        self.terminal_best = torch.where(eligible, best, self.terminal_best)

    def record_wrong(self, env_ids, count):
        """재무장 대기 중 교차처럼 기하 계층이 차단한 사건도 원장에 기록한다."""
        ids = torch.as_tensor(env_ids, device=self.device, dtype=torch.long)
        values = torch.as_tensor(count, device=self.device, dtype=torch.float32)
        if (ids.ndim != 1 or values.shape != ids.shape or ids.unique().numel() != ids.numel()
                or torch.any((ids < 0) | (ids >= self.N))
                or not torch.isfinite(values).all() or torch.any(values < 0)):
            raise ValueError('wrong counts require unique valid environments and nonnegative counts')
        event = self.active[ids]
        self.terms['wrong'][ids] += values
        self.history['unplanned'][ids, event] += values
        self.history['wrong'][ids, event] |= values > 0
        self.history['clean_complete'][ids, event] &= values == 0
        self._invalidate_tick(ids[values > 0])
        self._disrupt_recovery(ids[values > 0])

    def _disrupt_recovery(self, ids):
        recovering = (self.phase[ids] == 2) & self.current('resolved')[ids] & ~self.done[ids]
        ids = ids[recovering]
        self.recovery_elapsed[ids] = 0
        self._recovery_fresh[ids] = True
        self.history['recovered'][ids, self.active[ids]] = False

    def _invalidate_tick(self, ids):
        # 같은 제어 구간 뒤쪽의 오타현도 앞쪽 잠정 clean 보상을 취소한다.
        event = self.active[ids]
        for key, credited in self._tick_clean_terms.items():
            self.terms[key][ids] -= credited[ids, event]
            credited[ids, event] = 0

    def _credit(self, name, ids, amount):
        self.terms[name][ids] += amount
        self._tick_clean_terms[name][ids, self.active[ids]] += amount

    def _vector(self, value, name, boolean=False):
        if (not isinstance(value, torch.Tensor) or value.shape != (self.N,)
                or value.device != self.device or not torch.isfinite(value).all()
                or (boolean and value.dtype != torch.bool)):
            raise ValueError(name+' must be a finite matching vector [N]')

    @staticmethod
    def _dt(dt):
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError('dt must be finite and positive')
