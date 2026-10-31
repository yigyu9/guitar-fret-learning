"""준비 시간과 접근 기하만 독립 비교하는 연구용 환경이다.

기본 환경·성공 판정·물리·종료는 유지한다. 두 변경을 끄면 부모 계산을 그대로
호출하며, 연구 계약은 다른 학습 설정까지 포함해 모든 비교군에 명시한다.
"""
import copy

import torch

from guitar_learning.gpu.contact import project_press_strings
from guitar_learning.gpu.finger_reward import finger_preparation_gate
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment


FLAGS = ('adaptive_lr', 'exploration', 'preparation', 'geometry', 'separate')


def preparation_gate(now, onset, end, press, finger, contact, distance, target_mask=None):
    """통상 준비만 1초로 늘린다. 현재 압현·짧은 간격·해제 시간은 보존한다."""
    result = finger_preparation_gate(now, onset, end, press, finger, contact, distance, target_mask)
    n, m = now.numel(), onset.numel()
    if not m:
        return result
    owned = (finger[None] == torch.arange(1, 5, device=finger.device)[:, None])[None].expand(n, -1, -1)
    if target_mask is not None:
        owned = owned & target_mask[:, None]
    active = (owned & ((press[None] <= now[:, None]) & (now[:, None] <= end[None]))[:, None]).any(-1)
    past = owned & (end[None, None] < now[:, None, None])
    future = owned & (press[None, None] > now[:, None, None])
    previous = end.expand(n, 4, m).masked_fill(~past, -torch.inf).amax(-1)
    following = press.expand(n, 4, m).masked_fill(~future, torch.inf).amin(-1)
    gap = following-previous
    finite = torch.isfinite(gap)
    short = finite & (gap < .6)
    amount = torch.where(finite, ((gap-.25)/.35).clamp(0, 1), 1.)
    lead = torch.where(short, .4*gap, 1.)
    fade = torch.where(short, now.new_full(short.shape, .1), now.new_full(short.shape, .2))
    releasing = ((now[:, None]-previous-.05)/.1).clamp(0, 1)
    preparing = ((following-now[:, None]-lead)/fade).clamp(0, 1)
    idle = torch.where(active, 0., amount*releasing*preparing).to(now.dtype)
    result.update(idle_weight=idle, tracking_weight=1-idle,
        gate=idle*~(result['contact_veto'] | result['near_veto'] | result['nonfinite_veto']))
    return result


def nearest_pad_quality(delta, alignment, height, string_line, plane):
    """동일 최근접 패드 표본의 줄·셀·높이·방향을 묶는다. 하중은 읽지 않는다.

    delta는 원본 기하의 안쪽2mm 프렛 선분 끝점으로 향한다. 현의 평면 내
    접선 성분은 셀 밖 초과량, 그에 수직인 평면 성분은 현 옆 오차다.
    별도 패드 점에서 좋은 방향을 가져오거나 후보 판정을 완화하지 않는다.
    """
    normal = plane[:3]/torch.linalg.vector_norm(plane[:3])
    tangent = string_line-(string_line*normal).sum(-1, keepdim=True)*normal
    tangent = tangent/torch.linalg.vector_norm(tangent, dim=-1, keepdim=True)
    along = (delta*tangent).sum(-1)
    planar = delta-(delta*normal).sum(-1, keepdim=True)*normal
    lateral = torch.linalg.vector_norm(planar-along[..., None]*tangent, dim=-1)
    outside_height = torch.relu(-.001-height)+torch.relu(height-.003)
    error = (torch.relu(lateral-.003)/.003).square()+(along/.005).square()+(outside_height/.003).square()
    return alignment.clamp(0, 1)/(1+error)


class ResearchEnvironment(FingerSkillEnvironment):
    """실험 설정을 계약에 봉인하고 접근 관련 두 항목만 바꾸는 환경이다."""
    def __init__(self, metadata, **kwargs):
        config = metadata.get('finger_ablation')
        if (not isinstance(config, dict) or set(config) != set(FLAGS) or
                any(type(config[key]) is not bool for key in FLAGS)):
            raise ValueError('finger_ablation requires exactly five boolean research flags')
        self.research_config = copy.deepcopy(config)
        super().__init__(metadata, **kwargs)
        self.contract['reward']['finger_ablation'] = dict(
            schema='guitar_learning.finger_ablation_contact.v1', flags=copy.deepcopy(config),
            preparation=dict(normal_lead_s=1. if config['preparation'] else .35,
                normal_fade_s=.2 if config['preparation'] else .1,
                short_gap='unchanged gap<.6: lead=.4gap, fade=.1; current press protected',
                release='unchanged grace=.05/fade=.1; shared reward and observation gate'),
            geometry=dict(enabled=config['geometry'], near_m=.02,
                maximum_quality_penalty=.7 if config['geometry'] else .2,
                witness='existing same nearest valid distal pad sample delta/normal/height',
                lateral_deadband_m=.003, lateral_scale_m=.003, fret_overflow_scale_m=.005,
                signed_height_band_m=[-.001, .003], height_scale_m=.003,
                quality='clamp(normal_cos,0,1)/(1+lateral_excess^2+fret_overflow^2+height_excess^2)',
                potential='sum valid*b*tracking*exp(-d/.03)*(1-depth*near*(1-quality))',
                unchanged='nine terms, gamma/terminal potential, success/contact/load, safety, native control'))

    def _finger_preparation(self, now):
        result = super()._finger_preparation(now)
        if not self.research_config['preparation']:
            return result
        contact = torch.zeros(now.numel(), 4, dtype=torch.bool, device=now.device)
        gate = preparation_gate(now, self.onset, self.end, self.press, self.finger,
            contact, self.surface_distance, self._preparation_scope())
        per_finger = self.finger_recovery['standby_rate_per_s']*gate['gate']*result['quality']/4
        result.update(gate)
        result.update(per_finger_rate=per_finger, rate=per_finger.sum(-1))
        return result

    def _surface_potential(self):
        if not self.research_config['geometry']:
            return super()._surface_potential()
        now = self._score_time()
        targets = self._finger_targets(now)
        selected = targets['indices'][..., 0].clamp_min(0)
        valid = targets['valid'][..., 0]
        distance = self.surface_distance.gather(1, selected)
        delta = self.surface_delta.gather(1, selected[..., None].expand(-1, -1, 3))
        strings = self.string[selected]
        starts, ends = project_press_strings(self.starts, self.ends, self.press_plane)
        line = ends.gather(1, strings[..., None].expand(-1, -1, 3))-starts.gather(
            1, strings[..., None].expand(-1, -1, 3))
        quality = nearest_pad_quality(delta, self.surface_alignment.gather(1, selected),
            self.surface_height.gather(1, selected), line, self.press_plane)
        near = (1-distance/.02).clamp(0, 1)
        direction = 1-.7*near*(1-quality)
        tracking = self._finger_preparation(now)['tracking_weight']
        value = (valid*self._selected_finger_weights(selected)*tracking*torch.exp(-distance/.03)*direction).sum(-1)
        return value.to(self.surface_distance.dtype)
