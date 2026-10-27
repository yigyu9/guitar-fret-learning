"""Nine-term joint finger learning with one failure cost and observable wrist timers."""
import copy

import torch

from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.gpu.wrong_press import WRONG_PRESS_CONTRACT, pad_contact_cells, wrong_press_sources


WRIST_FIELDS = ('wrist_termination.active', 'wrist_termination.elapsed_s',
                'wrist_termination.preparation_remaining_s', 'wrist_termination.severe_elapsed_s')
NORMAL_WRIST_DURATION_S = 1.5
REWARD_TERMS = ('song_left_approach', 'song_left_contact', 'song_clean_hold',
                'song_left_success', 'song_wrong_press', 'song_performance_deficit',
                'song_finger_standby', 'song_thumb_support', 'action_change')


def performance_settlement(missing, best_streak, required, duration, weights, scope,
                           now, end, paid, settled):
    """Monotone missing payments, then one max(missing, streak deficit) settlement."""
    missing_ratio = (missing/duration).clamp(0, 1)
    streak_deficit = (1-best_streak/required).clamp(0, 1)
    ending = scope & ~settled & (now[:, None]+1e-12 >= end)
    deficit = torch.where(ending, torch.maximum(missing_ratio, streak_deficit), missing_ratio)
    due = .1*weights*deficit
    increment = torch.where(scope & ~settled, (due-paid).clamp_min(0), 0.)
    return paid+increment, settled | ending, increment


def remaining_negative_budget(now, onset, end, weights, scope, paid, settled):
    """Unobserved wrong bound plus unpaid performance bound, selected/unsettled only."""
    remaining = (end-torch.maximum(now[:, None], onset)).clamp_min(0)/(end-onset)
    eligible = scope & ~settled
    return ((.15*weights*remaining+(.1*weights-paid).clamp_min(0))*eligible).sum(-1)


class SimplifiedFingerEnvironment(FingerSkillEnvironment):
    def __init__(self, metadata, *, bundle, song, skill, device='cuda:0', hand='left'):
        if (skill.get('schema') != 'guitar_learning.finger_skill.v2' or skill.get('phase') != 'J' or
                skill.get('exploration') != 'independent' or skill.get('hold_ticks') != 1 or
                skill.get('scope') != 'scheduled' or type(skill.get('planned_transitions')) is not int or
                skill['planned_transitions'] < 1 or
                type(skill.get('full_song_after')) is not int or
                skill['full_song_after'] != skill['planned_transitions']//4):
            raise ValueError('explicit v2 joint independent K1 scheduled exposure contract required')
        self.planned_transitions = skill['planned_transitions']
        self.full_song_after = skill['full_song_after']
        self.committed_transitions = 0
        self._initial_scope_reset = True
        compatible = dict(skill, schema='guitar_learning.finger_skill.v1', scope='phrases')
        super().__init__(metadata, bundle=bundle, song=song, skill=compatible, device=device, hand=hand)
        self.training_scope = 'scheduled'
        observation = self.contract['observation']
        observation['fields'] += list(WRIST_FIELDS)
        observation['scales'] += [1., NORMAL_WRIST_DURATION_S, 3., .10]
        observation['dimension'] += 4
        self.scales = self._tensor(observation['scales'])
        self.planned_ticks_index = observation['fields'].index('finger_skill.planned_ticks')
        self.contract['task']['finger_skill'].update(schema=skill['schema'], scope='scheduled',
            planned_transitions=self.planned_transitions, full_song_after=self.full_song_after,
            reset_selection='initial balanced phrase; future resets switch to full song after fixed committed budget')
        reward = self.contract['reward']
        reward['schema'] = 'guitar_learning.simplified_finger_reward.v2'
        self.contact_contract = dict(self.contact_contract,
            schema='guitar_learning.gpu_distal_pad_geometry.v2',
            wrong_press=copy.deepcopy(WRONG_PRESS_CONTRACT))
        self.contract['task']['contact_measurement'] = copy.deepcopy(self.contact_contract)
        self.contract['native_backend']['measurement'] = copy.deepcopy(self.contact_contract)
        self.contract['diagnostics']['wrong_press'] = copy.deepcopy(WRONG_PRESS_CONTRACT)
        reward['active_terms'] = list(REWARD_TERMS)
        reward['safety_cost'] = 'no running physics cost; one unified physical/wrist failure cost'
        reward['left_curriculum'] = None
        reward['finger_tracking']['enabled'] = False
        reward['finger_shape']['enabled'] = False
        reward['finger_skill'].update(purpose='joint selected original task; nine fixed terms; no phase/music-stage gates',
                                      weights='no group weighting; final effective coefficients recorded in simplified',
                                      wrong='assigned-pad error or other-finger higher fret; selected targets, audible overlap penalties')
        reward['surface_learning'].update(schema='guitar_learning.surface_fretting.v9',
            potential='sum b*scheduled_tracking*exp(-d/.03)*(1-.2*near2cm*(1-alignment))',
            contact='0.25*b*increase in best-contact progress', contact_budget='per-note0.25*b; no additional completion payout',
            hold='1.0*b*audible clean increment/D', achievement='0.25*b once at unchanged continuous clean threshold',
            penalties='wrong=-0.15*b*wrong_dt/D; performance=-0.10*b*max(missing_ratio,streak_deficit), incremental plus settlement',
            observation='561state/24event/8priority; positive pad geometry unchanged, wrong rules v2; observable wrist termination4')
        reward['simplified'] = dict(schema='guitar_learning.nine_term_reward.v1',
            contact_budget=.25, clean_budget=1., achievement_budget=.25,
            wrong_budget=.15, performance_deficit_budget=.10,
            balance='selected M/(present selected fingers*selected own-finger count), applied once',
            approach='gamma*nextPhi-Phi; exp(-d/.03)*(1-.2*near*(1-alignment))*scheduled tracking weight*b; terminal nextPhi0',
            performance='incremental missing payments then one max(missing/D,1-best_streak/required) settlement',
            positive_failure_tick='suppressed; negative terminal potential and observed note deficits retained',
            standby_rate_per_s=self.finger_recovery['standby_rate_per_s'],
            thumb_rate_per_s=self.thumb_support_rate, normal_running_physics_cost=0.,
            old_wrist_tracking_missing_missed_failure_reward='inactive; not summed')
        termination = self.contract['termination']
        termination.pop('failure_horizon_cost', None)
        termination['failure_cost'] = dict(schema='guitar_learning.unified_failure_cost.v1',
            base=5., remaining_seconds_rate=2.,
            remaining_note_budget='selected unsettled unobserved wrong .15b plus unpaid performance .10b',
            application='once at failed60Hz boundary; physical and wrist failure share one payment', running_cost=0.)
        termination['wrist'] = dict(schema='guitar_learning.wrist_termination.v2',
            enter_excess_m=.03, release_excess_m=.02, normal_duration_s=NORMAL_WRIST_DURATION_S,
            preparation_s=3., severe_excess_m=.10, severe_duration_s=.10,
            sampling_hz=240, target_transition_grace='none; timers survive source target changes',
            normal_timer='accumulate above3cm; active2..3cm recovery subtracts dt; at/below2cm resets',
            recovery_rate=1., normal_timer_scope='net outside time, not continuous hysteresis-latch time',
            observation_fields=list(WRIST_FIELDS))
        termination['additional_failure_reasons'] += ['wrist_outside', 'wrist_severe']
        self.contract['diagnostics']['simplified_reward'] = copy.deepcopy(reward['simplified'])
        reward['surface_learning']['penalty_window'] = (
            'audible wrong and incremental missing; one max(missing/D,streak deficit) '
            'settlement at note end; no repeated missed penalty or synthetic failure tail')
        inactive = {name: reward.pop(name) for name in ('wrist_region', 'finger_tracking', 'finger_shape')}
        self.contract['diagnostics']['inactive_legacy_reward_reference'] = dict(
            scope='measurement provenance only; these legacy reward formulas are not optimized',
            contracts=inactive)

    def _left_wrong_contacts(self, qualifies, assigned, nearest, same_string,
                             in_goal, same_finger, positive, wrong, pad_points, pad_normals):
        cells = pad_contact_cells(pad_points, pad_normals, self.pad_valid,
            self.loaded[:, self.pad_indices], self.starts, self.ends, self.frets, self.press_plane)
        result = wrong_press_sources(qualifies=qualifies, assigned=assigned, nearest=nearest,
            source_fingers=self.pad_fingers, surface_count=self.surface_count, pad_cells=cells,
            positive=positive, now=self._score_time(), onset=self.onset, end=self.end, press=self.press,
            scope=self._scope_mask(), strings=self.string, frets=self.fret, fingers=self.finger,
            fret_count=self.frets.shape[1])
        self.wrong_source_flags = result['flags']
        self.wrong_source_fret_min = result['fret_min']
        self.wrong_source_fret_max = result['fret_max']
        self.wrong_supported = result['wrong']
        self.wrong_ambiguous = torch.zeros_like(result['wrong'])
        self.wrong_next_preparation = result['next_preparation']
        self.contact_causes = tuple(result['flags'][..., cause].any(-1) for cause in range(3))
        return result['wrong']

    def _allocate(self, count):
        super()._allocate(count)
        self.wrist_active = torch.zeros(count, dtype=torch.bool, device=self.device)
        self.wrist_elapsed = torch.zeros(count, dtype=torch.float64, device=self.device)
        self.wrist_severe_elapsed = self.wrist_elapsed.clone()
        self.wrist_failure = self.wrist_active.clone()
        self.wrist_severe_failure = self.wrist_active.clone()
        self.failure_paid = self.wrist_active.clone()
        self.termination_remaining_time_cost = torch.zeros(count, device=self.device)
        self.termination_note_budget = torch.zeros(count, device=self.device)
        self.note['performance_paid'] = torch.zeros(count, self.M, dtype=torch.float64, device=self.device)
        self.note['performance_settled'] = torch.zeros(count, self.M, dtype=torch.bool, device=self.device)
        self.episode_reward_terms = {key: torch.zeros(count, device=self.device) for key in REWARD_TERMS}
        self.reward_window = {key: torch.zeros((), dtype=torch.float64, device=self.device) for key in REWARD_TERMS}

    def set_training_progress(self, committed):
        if type(committed) is not int or committed < self.committed_transitions or self._substeps is not None:
            raise ValueError('monotone committed raw transitions at a completed control boundary required')
        self.committed_transitions = committed

    def _reset_scope(self, indices):
        full = self.committed_transitions >= self.full_song_after and not self._initial_scope_reset
        self.training_scope = 'full_song' if full else 'phrases'
        try:
            super()._reset_scope(indices)
        finally:
            self.training_scope = 'scheduled'
        self._initial_scope_reset = False
        for value in (self.wrist_active, self.wrist_elapsed, self.wrist_severe_elapsed,
                      self.wrist_failure, self.wrist_severe_failure, self.failure_paid,
                      self.termination_remaining_time_cost, self.termination_note_budget):
            value[indices] = 0

    def _guide_time(self):
        now = torch.maximum(self.view_first, torch.minimum(self._score_time(), self.view_last))
        return now-self.song['pre_roll_s']

    def _surface_potential(self):
        now = self._score_time()
        targets = self._finger_targets(now)
        selected = targets['indices'][..., 0].clamp_min(0)
        valid = targets['valid'][..., 0]
        distance = self.surface_distance.gather(1, selected)
        alignment = self.surface_alignment.gather(1, selected).clamp(0, 1)
        near = (1-distance/.02).clamp(0, 1)
        direction = 1-.2*near*(1-alignment)
        tracking = self._finger_preparation(now)['tracking_weight']
        value = (valid*self._selected_finger_weights(selected)*tracking*torch.exp(-distance/.03)*direction).sum(-1)
        return value.to(self.surface_distance.dtype)

    def _safety(self):
        super()._safety()
        now = self._local_time()
        excess = self.guide['delta'].abs().amax(-1)
        enabled = now+1e-12 >= 3.
        self.wrist_active = enabled & ((self.wrist_active | (excess > .03)) & (excess > .02))
        outside = excess > .03
        elapsed = torch.where(outside, self.wrist_elapsed+1/240.,
                              (self.wrist_elapsed-1/240.).clamp_min(0))
        self.wrist_elapsed = torch.where(self.wrist_active, elapsed, 0.)
        severe = excess >= .10
        self.wrist_severe_elapsed = torch.where(severe, self.wrist_severe_elapsed+1/240., 0.)
        self.wrist_failure |= self.wrist_elapsed+1e-12 >= NORMAL_WRIST_DURATION_S
        self.wrist_severe_failure |= self.wrist_severe_elapsed+1e-12 >= .10

    def _running_safety_cost(self, rate):
        pass

    def _control_failures(self):
        return super()._control_failures() | self.wrist_failure | self.wrist_severe_failure

    def _prepare_control_end(self, failed):
        paid, settled, increment = performance_settlement(self.note['missing'], self.note['best_clean_streak'],
            self.required, self.end-self.onset, self.finger_weights, self.focus_mask,
            self._score_time(), self.end, self.note['performance_paid'], self.note['performance_settled'])
        self.note['performance_paid'].copy_(paid)
        self.note['performance_settled'].copy_(settled)
        self.control_performance_penalty = -increment.sum(-1).float()

    def _apply_failure_cost(self, failed):
        charge = failed & ~self.failure_paid
        remaining = (self._episode_duration()-self._local_time()).clamp_min(0)
        note_budget = remaining_negative_budget(self._score_time(), self.onset, self.end,
            self.finger_weights, self.focus_mask, self.note['performance_paid'], self.note['performance_settled'])
        time_cost = (2*remaining*charge).float()
        budget_cost = (note_budget*charge).float()
        self.tick_cost += 5.*charge+time_cost+budget_cost
        self.failure_horizon_cost += time_cost+budget_cost
        self.termination_remaining_time_cost += time_cost
        self.termination_note_budget += budget_cost
        self.failure_paid |= charge

    def _reward_components(self, components):
        return dict(song_left_approach=self.terms['song_left_approach'],
            song_left_contact=.5*self.terms['song_left_contact'], song_clean_hold=.5*self.terms['song_clean_hold'],
            song_left_success=.5*self.terms['song_left_success'], song_wrong_press=.15*self.terms['song_wrong_press'],
            song_performance_deficit=self.control_performance_penalty,
            song_finger_standby=self.terms['song_finger_standby'],
            song_thumb_support=self.terms['song_thumb_support'], action_change=self.terms['action_change'])

    def _observation_state(self, state):
        state = super()._observation_state(state)
        timers = torch.stack((self.wrist_active.double(), self.wrist_elapsed,
            (3.-self._local_time()).clamp_min(0), self.wrist_severe_elapsed), -1)
        return torch.cat((state, timers.float()), -1)

    def decision_observation(self, planned_ticks, observation=None):
        if (planned_ticks.shape != (self.N,) or planned_ticks.dtype != torch.long or
                bool((planned_ticks != 1).any())):
            raise ValueError('simplified joint K1 planned ticks must be long[N] ones')
        observation = self.observation() if observation is None else observation
        state = observation['state'].clone()
        state[:, self.planned_ticks_index] = planned_ticks.to(state)/6.
        return dict(observation, state=state)

    def _episode(self, index, failed):
        result = super()._episode(index, failed)
        ledger = result['left_note_ledger']
        ledger['schema'] = 'guitar_learning.surface_note_ledger.v8'
        ledger['wrong_press_sources']['contract'] = copy.deepcopy(WRONG_PRESS_CONTRACT)
        ledger['scope'] = ledger['scope'].replace(
            'and wrong causes retain full original virtual-string samples',
            'retain full original virtual-string samples; wrong uses assigned-pad errors and other-finger higher frets v2')
        for old, new in zip(('higher_time', 'lower_time', 'assignment_time'), WRONG_PRESS_CONTRACT['causes']):
            ledger['values'][new+'_time'] = ledger['values'].pop(old)
        result['left_curriculum'].pop('progress', None)
        result['left_curriculum'].pop('weights', None)
        result['left_curriculum']['scope'] = 'diagnostic selected-task metrics; no stage weighting or mastery gate'
        physical = bool(self.failure[index].any())
        normal = bool(self.wrist_failure[index])
        severe = bool(self.wrist_severe_failure[index])
        wrist = normal or severe
        result['termination'] = dict(physical_failure=physical, wrist_failure=wrist,
            primary_reason='physical_failure' if physical else 'wrist_failure' if wrist else 'timeline_complete',
            wrist_outside=normal, wrist_severe=severe)
        if normal: result['failure_reasons'].append('wrist_outside')
        if severe: result['failure_reasons'].append('wrist_severe')
        result['cost_components'] = dict(termination_base=5.*bool(self.failure_paid[index]),
            termination_remaining_time=float(self.termination_remaining_time_cost[index]),
            termination_remaining_negative_note_budget=float(self.termination_note_budget[index]),
            running_physics=0.)
        result['left_note_ledger']['values'].update(
            performance_paid=self.note['performance_paid'][index].cpu().tolist(),
            performance_settled=self.note['performance_settled'][index].cpu().tolist())
        result['finger_skill'].update(schema='guitar_learning.finger_skill.v2',
            committed_transitions_at_end=self.committed_transitions,
            planned_transitions=self.planned_transitions, full_song_after=self.full_song_after)
        now = self._score_time()[index]
        audible = self.focus_mask[index] & (now >= self.onset) & (now < self.end)
        preparing = self.focus_mask[index] & (now >= self.press-2) & (now < self.onset)
        excess = self.guide['delta'][index].abs()
        result['wrist_termination'] = dict(schema='guitar_learning.wrist_termination_diagnostics.v2',
            sample_scope='final240Hz sample at episode60Hz boundary; not a trajectory maximum',
            active=bool(self.wrist_active[index]), elapsed_s=float(self.wrist_elapsed[index]),
            severe_elapsed_s=float(self.wrist_severe_elapsed[index]),
            recovery_band=bool(self.wrist_active[index] & (excess.amax() <= .03)),
            delta_G_m=self.guide['delta'][index].cpu().tolist(),
            wrist_G_m=self.local_bodies[index, self.wrist_index].cpu().tolist(),
            lower_G_m=self.guide['lower_G_m'][index].cpu().tolist(),
            upper_G_m=self.guide['upper_G_m'][index].cpu().tolist(),
            dominant_axis=('Gx', 'Gy', 'Gz')[int(excess.argmax())] if bool(excess.amax() > 0) else None,
            score_time_s=float(now),
            target_index_scope='indices in compiled source score; candidates do not certify sound or pair pressure',
            audible_target_indices=audible.nonzero().flatten().cpu().tolist(),
            preparing_target_indices=preparing.nonzero().flatten().cpu().tolist(),
            audible_pad_distance_m=self.surface_distance[index, audible].cpu().tolist(),
            audible_clean_candidate=(self.candidate[index, audible] & ~self.wrong[index, audible]).cpu().tolist())
        return result
