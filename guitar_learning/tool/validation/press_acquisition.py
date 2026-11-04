"""현행 타현·엄지 진단이 사용하는 목표각→직접 위치 행동 역변환."""


def trajectory_actions(desired, reference, low, high):
    """목표각을 준비 기준의 직접 위치 행동으로 역변환한다. 상태는 쓰지 않는다."""
    import torch
    if (desired.ndim != 2 or desired.shape[-1] != 39 or
            reference.shape != low.shape or low.shape != high.shape or low.shape != (39,)):
        raise ValueError('Aligned action39 trajectories required')
    if not all(bool(torch.isfinite(x).all()) for x in (desired, reference, low, high)):
        raise ValueError('Finite inverse-codec inputs required')
    if bool(((desired < low-1e-6) | (desired > high+1e-6)).any()):
        raise ValueError('Trajectory exceeds current controller action bounds')
    delta = desired-reference
    span = torch.where(delta >= 0, high-reference, reference-low)
    actions = torch.where(span > 0, delta/span.clamp_min(1e-30), torch.zeros_like(delta))
    return actions.clamp(-1, 1)
