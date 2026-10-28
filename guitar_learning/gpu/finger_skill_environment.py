"""봉인된 전곡 GPU 측정을 선택 구간·전곡 학습 범위에 맞게 제공한다.

구간 선택·시계 변환 → 목표·보상 범위 제한 → 수행 부족·종료 정산 순서로 읽는다.
악보 시계와 선택 작업 범위만 바꾸며 native 에피소드 시계·준비 상태 복원·제어기·기하·
물리 안전·정확 압현 기준은 TensorSongEnvironment를 따른다."""
import copy

import torch

from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.gpu.episode_diagnostics import LeftEpisodeDiagnostics
from guitar_learning.gpu.episode_diagnostics import SkillEpisodeDiagnostics
from guitar_learning.gpu.control import apply
from guitar_learning.song.finger_phrases import build_phrase_catalog, BalancedPhraseSampler


from guitar_learning.gpu.contact import WRONG_PRESS_CONTRACT, pad_contact_cells, wrong_press_sources


SKILL_FIELDS = ('finger_skill.remaining_s',)
WRIST_FIELDS = ('wrist_termination.active', 'wrist_termination.elapsed_s',
                'wrist_termination.preparation_remaining_s', 'wrist_termination.severe_elapsed_s')
NORMAL_WRIST_DURATION_S = 1.5
REWARD_TERMS = ('song_left_approach', 'song_left_contact', 'song_clean_hold',
                'song_left_success', 'song_wrong_press', 'song_performance_deficit',
                'song_finger_standby', 'song_thumb_support', 'action_change')


def performance_settlement(missing, best_streak, required, duration, weights, scope,
                           now, end, paid, settled):
    """누락 감점을 단조롭게 지급한 뒤 max(누락, 연속 유지 부족)로 한 번 정산한다."""
    missing_ratio = (missing/duration).clamp(0, 1)
    streak_deficit = (1-best_streak/required).clamp(0, 1)
    ending = scope & ~settled & (now[:, None]+1e-12 >= end)
    deficit = torch.where(ending, torch.maximum(missing_ratio, streak_deficit), missing_ratio)
    due = .1*weights*deficit
    increment = torch.where(scope & ~settled, (due-paid).clamp_min(0), 0.)
    return paid+increment, settled | ending, increment


def remaining_negative_budget(now, onset, end, weights, scope, paid, settled):
    """선택되고 미정산인 음의 미관측 오압현 상한과 미지급 수행 부족 상한을 구한다."""
    remaining = (end-torch.maximum(now[:, None], onset)).clamp_min(0)/(end-onset)
    eligible = scope & ~settled
    return ((.15*weights*remaining+(.1*weights-paid).clamp_min(0))*eligible).sum(-1)


class FingerSkillEnvironment(TensorSongEnvironment):
    """J33 공동 학습만 실행하며 선택 구간과 전곡의 보상·종료를 관리한다."""
    allowed_finger_action_modes = ('incremental',)
    phase = 'J'
    exploration = 'independent'
    hold_ticks = 1

    def __init__(self, metadata, *, bundle, song, skill, device='cuda:0', hand='left'):
        if (hand != 'left' or skill.get('schema') != 'guitar_learning.finger_skill.v3' or
                skill.get('phase') != self.phase or skill.get('exploration') != self.exploration or
                type(skill.get('hold_ticks')) is not int or skill['hold_ticks'] != self.hold_ticks or
                skill.get('scope') != 'scheduled' or type(skill.get('planned_transitions')) is not int or
                skill['planned_transitions'] < 1 or type(skill.get('full_song_after')) is not int or
                skill['full_song_after'] != skill['planned_transitions']//4):
            raise ValueError('explicit v3 joint independent K1 scheduled exposure contract required')
        self.planned_transitions = skill['planned_transitions']
        self.full_song_after = skill['full_song_after']
        self.committed_transitions = 0
        self._initial_scope_reset = True
        self.training_scope = 'scheduled'
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
        observation['fields'] += list(SKILL_FIELDS)+list(WRIST_FIELDS)
        observation['scales'] += [self.task.duration_s, 1., NORMAL_WRIST_DURATION_S, 3., .10]
        observation['dimension'] += 5
        self.scales = self._tensor(observation['scales'])
        self.contract['task']['finger_skill'] = dict(
            schema='guitar_learning.finger_skill.v3', phase=self.phase,
            exploration=self.exploration, hold_ticks=self.hold_ticks,
            scope=self.training_scope, catalog_sha256=self.catalog.fingerprint,
            source_sha256=self.catalog.source_sha256,
            planned_transitions=self.planned_transitions, full_song_after=self.full_song_after,
            source_clock='original task time = local physics seconds + score_offset_s',
            reset_selection='initial balanced phrase; future resets switch to full song after fixed committed budget',
            evaluation='explicit runtime view; original full song or balanced phrases; same policy and control contract')
        self.contract['reward']['base_measurement_reward'] = 'guitar_learning.gpu_tensor_song_reward.v22'
        self.contract['reward']['finger_skill'] = dict(
            phase=self.phase, fixed_music_progress=0.,
            weights='no group weighting; final effective coefficients recorded in simplified',
            purpose='joint selected original task; nine fixed terms; no phase/music-stage gates',
            balance='selected M/(selected present fingers*selected own-finger count)',
            wrong='assigned-pad error or other-finger higher fret; selected targets, audible overlap penalties',
            preparation_boundary='selected notes plus first following original note per finger; no artificial tail rest bonus')
        self.contract['termination']['finger_skill_terminal'] = 'natural finite view end is terminal; H32 collection boundary is not an episode end'
        self.contract['diagnostics']['finger_skill'] = dict(
            schema='guitar_learning.finger_skill_diagnostics.v1',
            motion='same128 source material points per distal pad; endpoint60Hz vector decomposition only',
            recovery='original fixed source gaps intersected with actual selected performance interval; separate initial3s preparation',
            limitation='geometric motion and contact candidates, not causal force shares, calibrated pressure or sound')
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
        reward['surface_learning'].update(schema='guitar_learning.surface_fretting.v9',
            potential='sum b*scheduled_tracking*exp(-d/.03)*(1-.2*near2cm*(1-alignment))',
            contact='0.25*b*increase in best-contact progress', contact_budget='per-note0.25*b; no additional completion payout',
            hold='1.0*b*audible clean increment/D', achievement='0.25*b once at unchanged continuous clean threshold',
            penalties='wrong=-0.15*b*wrong_dt/D; performance=-0.10*b*max(missing_ratio,streak_deficit), incremental plus settlement',
            observation='557state/24event/8priority; positive pad geometry unchanged, wrong rules v2; observable wrist termination4')
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
        # 기존 전곡 고정 회복 시간창을 현재 선택 범위에 맞는 시간창으로 바꾸되,
        # 각도·손목·엄지의 기존 진단은 모두 유지한다.
        self.episode_diagnostics = LeftEpisodeDiagnostics(count, self.device)
        self.skill_diagnostics = SkillEpisodeDiagnostics(self.task, count, self.device)
        self.wrist_active = torch.zeros(count, dtype=torch.bool, device=self.device)
        self.wrist_elapsed = torch.zeros(count, dtype=torch.float64, device=self.device)
        self.wrist_severe_elapsed = self.wrist_elapsed.clone()
        self.wrist_failure = self.wrist_active.clone()
        self.wrist_severe_failure = self.wrist_active.clone()
        self.failure_paid = self.wrist_active.clone()
        self.termination_remaining_time_cost = torch.zeros(count, device=self.device)
        self.termination_note_budget = torch.zeros(count, device=self.device)
        # [N,M] 원장은 선택 음의 에피소드 전체에 걸쳐 유지한다. H 수집창과 별개다.
        self.note['performance_paid'] = torch.zeros(count, self.M, dtype=torch.float64, device=self.device)
        self.note['performance_settled'] = torch.zeros(count, self.M, dtype=torch.bool, device=self.device)
        self.episode_reward_terms = {key: torch.zeros(count, device=self.device) for key in REWARD_TERMS}
        self.reward_window = {key: torch.zeros((), dtype=torch.float64, device=self.device) for key in REWARD_TERMS}

    def _reset_scope(self, indices):
        full = (self.evaluation_full_song if self.evaluation else
                self.committed_transitions >= self.full_song_after and not self._initial_scope_reset)
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
        # 다음 원래 준비 경계는 유지하지만 선택하지 않은 그 음은 평가하지 않는다.
        # 과거의 미선택 음으로 미달성 감점이 생기지 않게 한다.
        for finger in range(1, 5):
            owned = selected & (self.finger == finger)[None]
            last = self.end.expand(len(indices), -1).masked_fill(~owned, -torch.inf).amax(-1)
            last = torch.where(owned.any(-1), last, self.view_first[indices])
            future = ((self.finger == finger)[None] & ~selected &
                      (self.press[None] >= last[:, None]))
            next_index = self.press.expand(len(indices), -1).masked_fill(~future, torch.inf).argmin(-1)
            has_next = future.any(-1)
            self.recovery_mask[indices[has_next], next_index[has_next]] = True
        self._initial_scope_reset = False
        for value in (self.wrist_active, self.wrist_elapsed, self.wrist_severe_elapsed,
                      self.wrist_failure, self.wrist_severe_failure, self.failure_paid,
                      self.termination_remaining_time_cost, self.termination_note_budget):
            value[indices] = 0


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

    def set_training_progress(self, committed):
        if type(committed) is not int or committed < self.committed_transitions or self._substeps is not None:
            raise ValueError('monotone committed raw transitions at a completed control boundary required')
        self.committed_transitions = committed

    def _score_time(self):
        return self._local_time()+self.score_offset

    def _guide_time(self):
        now = torch.maximum(self.view_first, torch.minimum(self._score_time(), self.view_last))
        return now-self.song['pre_roll_s']

    def _episode_duration(self):
        return self.duration_ticks.double()/60.

    def _target_scope(self):
        return self.focus_mask

    def _preparation_scope(self):
        return self.recovery_mask

    def _selected_finger_weights(self, indices):
        return self.finger_weights.gather(1, indices)

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
        # 부모 end_control의 첫 정산 단계: 관측된 누락을 증분 청구하고,
        # 음 종료 시 max(누락 비율, 최장 clean streak 부족률)까지 한 번 정산한다.
        paid, settled, increment = performance_settlement(self.note['missing'], self.note['best_clean_streak'],
            self.required, self.end-self.onset, self.finger_weights, self.focus_mask,
            self._score_time(), self.end, self.note['performance_paid'], self.note['performance_settled'])
        self.note['performance_paid'].copy_(paid)
        self.note['performance_settled'].copy_(settled)
        self.control_performance_penalty = -increment.sum(-1).float()

    def _apply_failure_cost(self, failed):
        # 수행 부족 정산 뒤의 paid/settled를 읽어 아직 관측·청구하지 않은 예산만 더한다.
        # 물리·손목 실패가 겹쳐도 에피소드당 한 번이며 최종 보상 합성보다 먼저 실행된다.
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
        # 부모의 legacy 그룹 components는 사용하지 않고 end_control이 준비한 원시 terms를 읽는다.
        # 원시 contact/hold/success 계수 .5/2/.5에 여기의 .5를 곱해 .25/1/.25가 된다.
        # 원시 wrong 계수 -1에는 .15를 곱한다. 수행 부족은 앞 단계의 정산값을 그대로 쓴다.
        return dict(
            song_left_approach=self.terms['song_left_approach'],
            song_left_contact=.5*self.terms['song_left_contact'],
            song_clean_hold=.5*self.terms['song_clean_hold'],
            song_left_success=.5*self.terms['song_left_success'],
            song_wrong_press=.15*self.terms['song_wrong_press'],
            song_performance_deficit=self.control_performance_penalty,
            song_finger_standby=self.terms['song_finger_standby'],
            song_thumb_support=self.terms['song_thumb_support'],
            action_change=self.terms['action_change'],
        )

    def _observation_state(self, state):
        remaining = (self._episode_duration()-self._local_time()).clamp_min(0)
        timers = torch.stack((self.wrist_active.double(), self.wrist_elapsed,
            (3.-self._local_time()).clamp_min(0), self.wrist_severe_elapsed), -1)
        return torch.cat((state, remaining[:, None].float(), timers.float()), -1)

    def _material_points(self):
        # 목표 최근접점이 아닌 동일 물질점 [N,4,128,3]의 월드 위치를 진단에 전달한다.
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
        if normal:
            result['failure_reasons'].append('wrist_outside')
        if severe:
            result['failure_reasons'].append('wrist_severe')
        result['cost_components'] = dict(termination_base=5.*bool(self.failure_paid[index]),
            termination_remaining_time=float(self.termination_remaining_time_cost[index]),
            termination_remaining_negative_note_budget=float(self.termination_note_budget[index]),
            running_physics=0.)
        result['left_note_ledger']['values'].update(
            performance_paid=self.note['performance_paid'][index].cpu().tolist(),
            performance_settled=self.note['performance_settled'][index].cpu().tolist())
        result['finger_skill'].update(schema='guitar_learning.finger_skill.v3',
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
