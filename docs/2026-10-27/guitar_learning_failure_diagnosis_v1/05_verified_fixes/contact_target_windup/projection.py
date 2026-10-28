"""Four-coordinate box + one halfspace projection; no numerical import at load."""


def project(raw, lower, upper, normal, old_error, *, relax):
    """Float64 finite-breakpoint Euclidean projection, batched[...,4]."""
    import torch
    if raw.shape[-1] != 4 or any(v.shape != raw.shape for v in (lower, upper, normal, old_error)):
        raise ValueError('Aligned selected4 tensors required')
    raw, lower, upper, normal, old_error = [v.double() for v in (raw, lower, upper, normal, old_error)]
    if not all(bool(torch.isfinite(v).all()) for v in (raw, lower, upper, normal, old_error)):
        raise ValueError('Finite projection inputs required')
    if not bool(((lower <= 0) & (upper >= 0) & (lower <= upper)).all()):
        raise ValueError('Original zero increment must lie in the box')
    scale = normal.abs().amax(-1)
    nonzero = scale > 0
    row = normal/torch.where(nonzero, scale, torch.ones_like(scale))[..., None]
    corner = torch.where(row > 0, upper, torch.where(row < 0, lower, raw.clamp(lower, upper)))
    maximum = (row*corner).sum(-1)
    beta = torch.minimum((-(row*old_error).sum(-1)).clamp_min(0), maximum) if relax else torch.zeros_like(maximum)
    initial = raw.clamp(lower, upper)
    phi = (row*initial).sum(-1)-beta
    # At beta==maximum every nonzero coordinate must reach its outward bound.
    at_maximum = (beta == maximum) & (phi < 0)
    result = torch.where(at_maximum[..., None], corner, initial)
    done = (phi >= 0) | at_maximum | ~nonzero
    safe = torch.where(row != 0, row, torch.ones_like(row))
    points = torch.cat(((lower-raw)/safe, (upper-raw)/safe), -1)
    points = torch.where(torch.cat((row != 0, row != 0), -1), points, torch.zeros_like(points)).clamp_min(0)
    points = points.sort(-1).values
    if not bool(torch.isfinite(points).all()):
        raise ValueError('Nonfinite clip breakpoint')
    previous = torch.zeros_like(phi)
    lagrange = torch.where(at_maximum, points[..., -1], torch.zeros_like(phi))
    for index in range(8):
        endpoint = points[..., index]
        value = (row*(raw+endpoint[..., None]*row).clamp(lower, upper)).sum(-1)-beta
        found = ~done & (value >= 0)
        difference = value-phi
        fraction = -phi/torch.where(difference > 0, difference, torch.ones_like(difference))
        root = previous+fraction*(endpoint-previous)
        candidate = (raw+root[..., None]*row).clamp(lower, upper)
        result = torch.where(found[..., None], candidate, result)
        lagrange = torch.where(found, root, lagrange)
        done |= found
        previous, phi = endpoint, value
    if not bool(done.all()):
        raise ValueError('Finite halfspace root not reached')
    # A zero normal has no intervention; retain the original increment exactly.
    result = torch.where(nonzero[..., None], result, raw)
    return dict(delta=result, beta_scaled=beta, maximum_scaled=maximum,
        scale=scale, normal_scaled=row, lagrange=lagrange, zero_normal=~nonzero,
        halfspace_residual_scaled=(row*result).sum(-1)-beta)


def rounding_tolerance(old, raw, final, normal_scaled, beta_scaled):
    """Numerical error allowance only: float32 target arithmetic and four-axis dot."""
    import torch
    epsilon = torch.finfo(torch.float32).eps
    target_scale = torch.stack((old.abs(), raw.abs(), final.abs(), torch.ones_like(old)), 0).amax(0).double()
    coordinate = 8*epsilon*target_scale
    # Four multiply-adds plus target subtraction/cast; no physical tolerance.
    halfspace = (normal_scaled.abs()*coordinate).sum(-1)+8*epsilon*beta_scaled.abs()
    return coordinate, halfspace
