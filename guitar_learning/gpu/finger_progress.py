"""곡 연주에서 네 손가락의 진행 상태를 독립적으로 관측하고 기록한다.

기존 E4 보상·원장·물리·제어를 그대로 상속한다. 아래 상태는 정책에 제공하는
설명 정보이며, 행동을 막거나 관절 목표·물리 상태를 덮어쓰지 않는다.
"""
import torch

from guitar_learning.gpu.finger_reward import finger_target_indices
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment


FINGER_PROGRESS_SCHEMA = 'guitar_learning.per_finger_progress.v1'
PHASE_NAMES = ('idle', 'prepare', 'aligned', 'press', 'hold', 'release')
FINGER_NAMES = ('index', 'middle', 'ring', 'pinky')
FEATURE_NAMES = tuple('phase_'+name for name in PHASE_NAMES)+(
    'target_valid', 'source_target_index', 'onset_delta_s', 'press_delta_s',
    'end_delta_s', 'target_elapsed_s', 'aligned_run_s', 'clean_run_s')
FINGER_PROGRESS_FIELDS = tuple('finger_progress.'+finger+'.'+field
    for finger in FINGER_NAMES for field in FEATURE_NAMES)
# 목표 인덱스 배율만 곡의 M에 따라 바뀐다. 시간 차이는 초 단위다.
FINGER_PROGRESS_SCALES = (1.,)*8+(2., 2., 2., 2., 1., 1.)
RELEASE_SECONDS = .25


def progress_contract(target_count):
    scales = list(FINGER_PROGRESS_SCALES)
    scales[7] = float(max(target_count-1, 1))
    return dict(schema=FINGER_PROGRESS_SCHEMA, shape='N,4,14; index/middle/ring/pinky',
        fields=list(FINGER_PROGRESS_FIELDS), scales=scales*4,
        phase_names=list(PHASE_NAMES), feature_names=list(FEATURE_NAMES), dimension=56,
        source_target_index='zero-based compiled task.targets index; -1 invalid; target_id mapping in episode log',
        selection='audible current note first; else existing E4 preparation selector; next preparation beats old release',
        aligned='own unchanged E4 hover ready AND shared wrist guide ready; no action lock',
        hold='own selected target: onset<=score_time<end AND candidate AND NOT wrong',
        release='previous own target ended less than0.25s ago, only when no current/preparing own target',
        target_timer='seconds since this finger selected this target; only this target replacement/reset clears it',
        target_changes='source-index changes including entering/leaving no-target state',
        aligned_timer='continuous own alignment before press; own readiness/phase loss clears it',
        clean_timer='continuous own audible clean; own loss/target replacement clears it',
        episode_seconds='actual240Hz samples per finger and phase; target changes do not clear totals',
        sampling_hz=240, release_s=RELEASE_SECONDS,
        behavior='observation and diagnostics only; no reward, action gate, PD or physical-state mutation')


def allocate_progress(count, device='cpu'):
    """원장과 분리된 상태를 만든다. 목표·timer의 두 번째 축은 항상 손가락이다."""
    zeros = torch.zeros(count, 4, dtype=torch.float64, device=device)
    return dict(target=torch.full((count, 4), -1, dtype=torch.long, device=device),
        phase=torch.zeros(count, 4, dtype=torch.long, device=device),
        target_elapsed=zeros.clone(), aligned_run=zeros.clone(), clean_run=zeros.clone(),
        episode_seconds=torch.zeros(count, 4, 6, dtype=torch.float64, device=device),
        target_changes=torch.zeros(count, 4, dtype=torch.long, device=device),
        last_time=torch.zeros(count, dtype=torch.float64, device=device))


def reset_progress(state, indices, now):
    """실제 에피소드를 재시작한 행만 지운다. H32 수집창 경계에서는 호출하지 않는다."""
    for key, value in state.items():
        value[indices] = -1 if key == 'target' else 0
    state['last_time'][indices] = now[indices].to(state['last_time'].dtype)


def advance_progress(state, *, now, onset, end, press, finger, scope,
                     ready, candidate, wrong, preparation_mask=None, active=None):
    """입력 측정과 기존 목표 선택만 읽고 독립적인 새 진행 상태를 반환한다.

    진행 중인 현재 음은 같은 손가락의 미래 음에게 자리를 빼앗기지 않는다.
    끝난 음의 release보다 이미 준비 가능한 다음 음을 우선한다. 다른 손가락의
    교체·정렬·종료는 해당 손가락의 목표나 timer에 영향을 주지 않는다.
    """
    n = now.numel()
    if (now.shape != (n,) or ready.shape != (n, 4) or ready.dtype != torch.bool or
            candidate.shape != scope.shape or wrong.shape != scope.shape or
            candidate.dtype != torch.bool or wrong.dtype != torch.bool):
        raise ValueError('진행 상태는 now[N], ready bool[N,4], 목표 측정 bool[N,M]이 필요합니다')
    active = torch.ones(n, dtype=torch.bool, device=now.device) if active is None else active
    if active.shape != (n,) or active.dtype != torch.bool:
        raise ValueError('활성 에피소드 행은 bool[N]이어야 합니다')
    selected = finger_target_indices(now, onset, end, press, finger, scope, preparation_mask)
    target = selected['indices'][..., 0]
    valid = selected['valid'][..., 0]
    m = onset.numel()
    if m:
        old = state['target'].clamp_min(0)
        # 끝난 직전 자기 음만 release로 표시한다. 미래 준비가 있으면 즉시 양보한다.
        release = (~valid & (state['target'] >= 0) & scope.gather(1, old) &
                   (now[:, None] >= end[old]) & (now[:, None] < end[old]+RELEASE_SECONDS))
        target = torch.where(release, state['target'], target)
        valid = target >= 0
        index = target.clamp_min(0)
        audible = valid & (now[:, None] >= onset[index]) & (now[:, None] < end[index])
        pressing = valid & ~release & (now[:, None] >= press[index])
        clean = audible & candidate.gather(1, index) & ~wrong.gather(1, index)
        aligned = valid & ~release & ~pressing & ready
    else:
        release = torch.zeros(n, 4, dtype=torch.bool, device=now.device)
        pressing = clean = aligned = release
    phase = torch.where(valid, 1, 0)
    for code, mask in ((2, aligned), (3, pressing), (4, clean), (5, release)):
        phase = torch.where(mask, code, phase)
    changed = target != state['target']
    # 정상 측정은 240Hz다. 이미 처리한 시계나 대기 중인 행은 중복 적분하지 않는다.
    dt = (now-state['last_time']).clamp(0., 1/240.)[:, None]
    dt = dt*active[:, None]
    same = ~changed
    result = dict(target=target, phase=phase,
        target_elapsed=torch.where(valid, torch.where(same, state['target_elapsed'], 0.)+dt, 0.),
        aligned_run=torch.where(aligned, torch.where(same, state['aligned_run'], 0.)+dt, 0.),
        clean_run=torch.where(clean, torch.where(same, state['clean_run'], 0.)+dt, 0.),
        episode_seconds=state['episode_seconds']+torch.nn.functional.one_hot(phase, 6)*dt[..., None],
        target_changes=state['target_changes']+changed.long(), last_time=now.clone())
    # 종료·대기 행은 관측 시계가 바뀌어도 상태 전체를 그대로 보존한다.
    return {key: torch.where(active.reshape((n,)+(1,)*(value.ndim-1)), value, state[key])
            for key, value in result.items()}


def progress_observation(state, now, onset, end, press):
    """손가락 순서대로 14개씩 묶은 정규화 전 관측[N,56]을 만든다."""
    target = state['target']; valid = target >= 0
    if onset.numel():
        index = target.clamp_min(0)
        times = torch.stack((onset[index]-now[:, None], press[index]-now[:, None],
                             end[index]-now[:, None]), -1)
        times = torch.where(valid[..., None], times, 0.)
    else:
        times = now.new_zeros(now.numel(), 4, 3)
    values = torch.cat((torch.nn.functional.one_hot(state['phase'], 6),
        valid[..., None], target[..., None], times,
        state['target_elapsed'][..., None], state['aligned_run'][..., None],
        state['clean_run'][..., None]), -1)
    return values.flatten(1).float()


class FingerProgressEnvironment(FingerSkillEnvironment):
    """다음 곡 단계의 관측만 확장한다. 기존 단일 목표 NaturalEnvironment는 보존한다."""
    progress_schema = FINGER_PROGRESS_SCHEMA
    natural_preparation = dict(schema='guitar_learning.natural_preparation.v3', condition='E4')

    def __init__(self, metadata, *, bundle, song, skill, device='cuda:0', hand='left'):
        super().__init__(metadata, bundle=bundle, song=song, skill=skill, device=device, hand=hand)
        spec = progress_contract(self.M)
        observation = self.contract['observation']
        observation['fields'] += spec['fields']
        observation['scales'] += spec['scales']
        observation['dimension'] += spec['dimension']
        self.scales = self._tensor(observation['scales'])
        self.contract['finger_progress'] = spec

    def _allocate(self, count):
        super()._allocate(count)
        self.finger_progress = allocate_progress(count, self.device)

    def _reset_scope(self, indices):
        super()._reset_scope(indices)
        reset_progress(self.finger_progress, indices, self._score_time())

    def _advance_finger_progress(self, now, active):
        state = self._natural_state(now)
        shared_ready = self.guide['ready'][:, None]
        first = self.press.expand(self.N, -1).masked_fill(~self.focus_mask, torch.inf).amin(-1)
        initial = self.focus_mask & (self.press[None] == first[:, None])
        self.finger_progress = advance_progress(self.finger_progress,
            now=now, onset=self.onset, end=self.end, press=self.press, finger=self.finger,
            scope=self.focus_mask, ready=state['ready'] & shared_ready,
            candidate=self.candidate, wrong=self.wrong, preparation_mask=initial, active=active)

    def reset(self, indices, snapshot):
        super().reset(indices, snapshot)
        indices = torch.as_tensor(indices, dtype=torch.long, device=self.device)
        active = torch.zeros(self.N, dtype=torch.bool, device=self.device); active[indices] = True
        self._advance_finger_progress(self._score_time(), active)
        return self.observation()

    def _diagnose_posture(self, posture, pressing, now):
        super()._diagnose_posture(posture, pressing, now)
        self._advance_finger_progress(now, ~self.finished)

    def _observation_state(self, state):
        base = super()._observation_state(state)
        extra = progress_observation(self.finger_progress, self._score_time(), self.onset, self.end, self.press)
        return torch.cat((base, extra), -1)

    def _episode(self, index, failed):
        episode = super()._episode(index, failed)
        state = self.finger_progress
        episode['finger_progress'] = dict(schema=FINGER_PROGRESS_SCHEMA,
            phase_names=list(PHASE_NAMES), source_target_ids=[t.target_id for t in self.task.targets],
            source_target_index=state['target'][index].cpu().tolist(),
            phase=state['phase'][index].cpu().tolist(),
            phase_seconds=state['episode_seconds'][index].cpu().tolist(),
            target_changes=state['target_changes'][index].cpu().tolist(),
            target_elapsed_s=state['target_elapsed'][index].cpu().tolist(),
            aligned_run_s=state['aligned_run'][index].cpu().tolist(),
            clean_run_s=state['clean_run'][index].cpu().tolist(),
            scope='per-finger actual240Hz diagnostic samples; no control gate or reward ledger changes')
        return episode
