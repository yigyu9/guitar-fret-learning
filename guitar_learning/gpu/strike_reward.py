"""고정 기타 S3 계수를 새 타현 원장의 측정값에 적용한다."""
import torch


SOURCE_SHA256 = {
    'legacy/env/rewards/strike.py': '30460bbbb7499a06a143bfa8c60b9d5be8d9d8be08c33730082bbce97d9f891a',
    'legacy/strike_cfg.py': '08e1cf5ab9576671af7fef314d220ec9dec9d59c6c68ad6ceef61f868e88d484',
}
S3_WEIGHTS = dict(ready=.25, crossing=1., miss=-1.5, wrong=-.35,
    unprepared=-1., premature=-1., early_timing=-1., timing=.75, zone=.20,
    strum_progress=1., strum_terminal_progress=.75,
    strum_physical_completion=.40, strum_microtiming=.25,
    recovery_progress=.30, recovery_complete=.30, recovery_speed=-.10)
STRIKE_REWARD_CONTRACT = dict(schema='guitar_learning.strike_reward.v1',
    scope='S3 weights; fresh policy; no legacy checkpoint compatibility',
    weights=S3_WEIGHTS, grip=.02, pending_ready=.02, approach=.40,
    approach_discount=.95, wait=.01, joint_limit=.01,
    failure_reward=-10., timing_core_s=.020, duration_core_s=.025,
    early_grace_s=.008, early_scale_s=.030,
    source_sha256=SOURCE_SHA256)


def compute_s3_reward(terms, *, grip_quality, ready_quality, pending_ready,
                      phi_before, phi_after, same_target, wait_quality,
                      joint_limit_usage, failed):
    """60Hz 한 tick의 보상과 가중 성분을 반환한다. 실패는 합계를 대체한다."""
    shape = grip_quality.shape
    if (len(shape) != 1 or not grip_quality.is_floating_point()
            or not torch.isfinite(grip_quality).all()):
        raise ValueError('grip_quality must be a floating tensor [N]')
    vectors = dict(ready_quality=ready_quality, pending_ready=pending_ready,
        phi_before=phi_before, phi_after=phi_after, same_target=same_target,
        wait_quality=wait_quality, failed=failed)
    vectors.update(terms)
    if set(terms) != set(S3_WEIGHTS):
        raise ValueError('strike reward terms differ from the S3 contract')
    for name, value in vectors.items():
        if value.shape != shape or value.device != grip_quality.device:
            raise ValueError(name+' must match grip_quality [N] and device')
        if not torch.isfinite(value).all():
            raise ValueError(name+' must be finite')
    for name in ('pending_ready', 'same_target', 'failed'):
        if vectors[name].dtype != torch.bool:
            raise ValueError(name+' must be bool [N]')
    if (joint_limit_usage.ndim != 2 or joint_limit_usage.shape[0] != shape[0]
            or joint_limit_usage.shape[1] == 0
            or joint_limit_usage.device != grip_quality.device
            or not torch.isfinite(joint_limit_usage).all()):
        raise ValueError('joint_limit_usage must be finite [N,J]')
    components = {name: terms[name]*weight for name, weight in S3_WEIGHTS.items()}
    components['grip'] = -.02*(1.-grip_quality.clamp(0., 1.))
    components['pending_ready'] = -.02*(1.-ready_quality.clamp(0., 1.))*pending_ready
    components['approach'] = .40*(.95*phi_after-phi_before).clamp(-1., 1.)*same_target
    components['wait'] = .01*wait_quality.clamp(0., 1.)
    components['joint_limit'] = -.01*((joint_limit_usage-.95)/.05).clamp_min(0.).square().mean(-1)
    total = sum(components.values())
    # 대체분도 성분으로 기록하여 성분 합계가 최종 보상과 일치한다.
    components['failure_override'] = torch.where(failed, -10.-total, torch.zeros_like(total))
    return torch.where(failed, torch.full_like(total, -10.), total), components
