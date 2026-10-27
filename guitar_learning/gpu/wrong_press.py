"""Assigned-pad mistakes and competing higher frets; geometric load candidates only."""
import torch

from guitar_learning.gpu.press_surface import project_press_strings


WRONG_PRESS_CONTRACT = dict(
    schema='guitar_learning.wrong_press_sources.v2',
    causes=['other_higher', 'own_wrong_fret', 'own_wrong_string'],
    effective='selected target geometry: own loaded facing distal pad at an unauthorized string/fret, or another finger at a higher fret on the target string; penalties only on audible overlap',
    own='positive assigned pad takes precedence over incidental own samples; any simultaneous active selected own target cell is authorized',
    other='full thumb/finger2/3 loaded virtual-string samples; same/lower fret is not wrong; higher blocks even with positive assigned pad',
    pad_geometry='finite unique nearest press-plane string within3mm, signed height[-1,3]mm, facing cosine>=0.1, distal netload>=0.01N, fret interior inset2mm',
    times='raw geometry at both physics endpoints, integrated over clipped audible overlap; no time-mask before trapezoid; overlapping sources do not multiply penalty',
    confidence='only unambiguous fret interiors contribute; no inferred wrong from unloaded/absent contact',
    source_fret_range='inclusive min/max contributing source fret per target/body; read only where source time>0',
    next_preparation='matches future scoped own finger/string/fret in press-2..onset; diagnostic only, never exempts current interference',
    scope='GPU left finger-skill only; net body force cannot identify contact partner, calibrated pressure or sound')


def pad_contact_cells(points, normals, valid, loaded, starts, ends, frets, plane):
    """Classify actual distal pad samples independently of their desired targets."""
    starts, ends = project_press_strings(starts, ends, plane)
    unit = plane[:3]/torch.linalg.vector_norm(plane[:3])
    height = (points*unit).sum(-1)+plane[3]/torch.linalg.vector_norm(plane[:3])
    on_plane = points-height[..., None]*unit
    line = ends-starts
    delta = on_plane[..., None, :]-starts[:, None, None]
    fraction = (delta*line[:, None, None]).sum(-1)/line.square().sum(-1)[:, None, None]
    distance = (delta-fraction[..., None]*line[:, None, None]).square().sum(-1)
    nearest = distance.argmin(-1)
    best = distance.gather(-1, nearest[..., None]).squeeze(-1)
    unique = (distance <= best[..., None]+1e-12).sum(-1) == 1
    fraction = fraction.gather(-1, nearest[..., None]).squeeze(-1)
    low = torch.minimum(frets[:, :-1, 1], frets[:, 1:, 1])
    high = torch.maximum(frets[:, :-1, 1], frets[:, 1:, 1])
    interior = ((points[..., 1, None] > low[:, None, None]+.002) &
                (points[..., 1, None] < high[:, None, None]-.002))
    assigned = torch.where(interior.any(-1), interior.long().argmax(-1)+1, 0)
    qualifies = (valid[None] & loaded[..., None] & unique & (best <= .003**2) &
        (fraction >= 0) & (fraction <= 1) & (height >= -.001) & (height <= .003) &
        (-(normals*unit).sum(-1) >= .1) & (assigned > 0))
    return qualifies, assigned, nearest


def wrong_press_sources(*, qualifies, assigned, nearest, source_fingers, surface_count,
                        pad_cells, positive, now, onset, end, press, scope, strings,
                        frets, fingers, fret_count):
    """Return verdict and bounded ten-body/three-cause provenance for each target."""
    count, targets = positive.shape
    active = scope & (now[:, None] >= onset) & (now[:, None] <= end)
    future = scope & (now[:, None] >= press-2) & (now[:, None] < onset)
    keys = (strings*fret_count+frets)*5+fingers
    active_grid = torch.zeros(count, 6*fret_count*5, device=positive.device)
    future_grid = torch.zeros_like(active_grid)
    active_grid.scatter_add_(1, keys.expand(count, -1), active.float())
    future_grid.scatter_add_(1, keys.expand(count, -1), future.float())
    flags = torch.zeros(count, targets, 10, 3, dtype=torch.bool, device=positive.device)
    minima = torch.full((count, targets, 10), fret_count, dtype=torch.int16, device=positive.device)
    maxima = torch.zeros_like(minima)
    preparing = torch.zeros_like(positive)

    other = (qualifies[..., None] & (nearest[..., None] == strings) &
        (assigned[..., None] > frets) & (source_fingers[:, None] != fingers) & scope[:, None])
    other = other.reshape(count, 10, surface_count, targets)
    flags[..., 0] = other.any(2).transpose(1, 2)
    source_frets = assigned.to(torch.int16).reshape(count, 10, surface_count, 1)
    minima[:] = torch.where(other, source_frets, fret_count).amin(2).transpose(1, 2)
    maxima[:] = torch.where(other, source_frets, 0).amax(2).transpose(1, 2)
    source_keys = (nearest*fret_count+assigned)*5+source_fingers
    future_source = future_grid.gather(1, source_keys).reshape(count, 10, surface_count) > 0
    preparing |= (other & future_source[..., None]).any(2).any(1)

    pad_valid, pad_frets, pad_strings = pad_cells
    for finger in range(1, 5):
        indices = (fingers == finger).nonzero().flatten()
        if indices.numel() == 0:
            continue
        pf, ps = pad_frets[:, finger-1], pad_strings[:, finger-1]
        pad_keys = (ps*fret_count+pf)*5+finger
        authorized = active_grid.gather(1, pad_keys) > 0
        # A correct assigned pad is not invalidated by incidental own surface
        # samples. Other fingers' higher frets remain independently blocking.
        wrong_pad = (pad_valid[:, finger-1, :, None] & ~authorized[..., None] &
                     scope[:, None, indices] & ~positive[:, None, indices])
        same_string = ps[..., None] == strings[indices]
        body = 2*finger+1  # thumb2/3,index2/3,...,pinky2/3
        for cause, relation in ((1, same_string & (pf[..., None] != frets[indices])),
                                (2, ~same_string)):
            points = wrong_pad & relation
            flags[:, indices, body, cause] = points.any(1)
            minima[:, indices, body] = torch.minimum(minima[:, indices, body],
                torch.where(points, pf[..., None].to(torch.int16), fret_count).amin(1))
            maxima[:, indices, body] = torch.maximum(maxima[:, indices, body],
                torch.where(points, pf[..., None].to(torch.int16), 0).amax(1))
            preparing[:, indices] |= (points & (future_grid.gather(1, pad_keys) > 0)[..., None]).any(1)
    wrong = flags.any(-1).any(-1)
    minima = torch.where(flags.any(-1), minima, 0)
    return dict(wrong=wrong, flags=flags, fret_min=minima, fret_max=maxima,
                next_preparation=wrong & preparing)
