"""Guitar-local free wrist volume, initialized from pinned score/source geometry.

This is a soft position penalty only. It does not impose a wrist orientation,
move the body, or certify that every allowed point can reach a clean press.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch

from guitar_learning.gpu.press_surface import _extract_plane
from guitar_learning.gpu.rigid_guitar import _ASSET_DIR, _MANIFEST_SHA256, _REPO_ROOT


SCHEMA = 'guitar_learning.gpu_wrist_region.v1'
EXCESS_SCALES_G_M = (.02, .03, .03)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_frames(bundle):
    root = Path(bundle).resolve()
    relative = 'training/hand_position_targets.json'
    path, manifest_path = root/relative, root/'manifest.json'
    payload = path.read_bytes()
    manifest = json.loads(manifest_path.read_text())
    entry = manifest.get('files', {}).get(relative)
    if (not isinstance(entry, dict) or entry.get('bytes') != len(payload) or
            entry.get('sha256') != hashlib.sha256(payload).hexdigest()):
        raise ValueError('wrist region hand-position manifest fingerprint mismatch')
    document = json.loads(payload)
    if (document.get('schema') != 'tab2body.hand_position_targets.v1' or
            document.get('coordinate_frame') != 'guitar local'):
        raise ValueError('guitar-local wrist region hand-position schema required')
    frames = document.get('frames')
    if not isinstance(frames, list) or not frames:
        raise ValueError('nonempty wrist region frames required')
    for index, row in enumerate(frames):
        if not isinstance(row, dict) or type(row.get('frame')) is not int or row['frame'] != index:
            raise ValueError('sequential integer wrist region frames required')
        timestamp, anchor = row.get('t'), row.get('anchor_fret')
        if (type(timestamp) not in (int, float) or not math.isfinite(timestamp) or
                abs(timestamp-index/60.) > 5e-5):
            raise ValueError('wrist region time must match its 60Hz frame')
        if (type(anchor) not in (int, float) or not math.isfinite(anchor) or not 1 <= anchor <= 22):
            raise ValueError('finite wrist region anchor fret in1..22 required')
        span = row.get('allowed_fret_range')
        if (not isinstance(span, list) or len(span) != 2 or
                any(type(fret) is not int or not 1 <= fret <= 22 for fret in span) or
                not span[0] <= anchor <= span[1]):
            raise ValueError('ordered integer allowed_fret_range in1..22 containing anchor required')
    return frames, {str(path): _sha(path), str(manifest_path): _sha(manifest_path)}


def _lower_edges(reference_y, plane, hulls):
    """Maximum source-hull Gx on the playing plane at each reference Gy."""
    z = -(plane[1]*reference_y+plane[3])/plane[2]
    edges = np.full(len(reference_y), -np.inf)
    for hull in hulls:
        low, high = np.full(len(reference_y), -np.inf), np.full(len(reference_y), np.inf)
        valid = np.ones(len(reference_y), dtype=bool)
        for nx, ny, nz, offset in hull:
            rest = ny*reference_y+nz*z+offset
            if nx > 1e-10:
                high = np.minimum(high, -rest/nx)
            elif nx < -1e-10:
                low = np.maximum(low, -rest/nx)
            else:
                valid &= rest <= 1e-8
        edges = np.maximum(edges, np.where(valid & (low <= high), high, -np.inf))
    if not np.isfinite(edges).all():
        raise ValueError('wrist region anchor outside source playing-plane footprint')
    return edges, z


def load_wrist_region_track(bundle, press_surface):
    """CPU initialization; no docs imports, reset-wrist offsets, or live mutation."""
    frames, pins = _load_frames(bundle)
    manifest_path = (_ASSET_DIR/'manifest.json').resolve()
    if _sha(manifest_path) != _MANIFEST_SHA256:
        raise ValueError('wrist region guitar manifest SHA mismatch')
    source_pins = press_surface.get('source_sha256', {})
    if (press_surface.get('schema') != 'guitar_learning.source_neck_press_plane.v1' or
            source_pins.get(str(manifest_path)) != _MANIFEST_SHA256):
        raise ValueError('pinned source press surface required for wrist region')
    manifest = json.loads(manifest_path.read_text())
    expected = {str((_REPO_ROOT/path).resolve()): value for path, value in manifest['source_sha256'].items()}
    expected[str((_ASSET_DIR/'guitar_compound.xml').resolve())] = manifest['asset_sha256']
    plane, hulls, extracted_pins = _extract_plane(_ASSET_DIR/'guitar_compound.xml', expected)
    if any(source_pins.get(path) != value for path, value in extracted_pins.items()):
        raise ValueError('wrist region press-surface source pins mismatch')
    if (not np.allclose(plane, press_surface.get('plane_G'), atol=1e-12, rtol=0) or
            not np.allclose(plane[:3], [0, 0, 1], atol=1e-12, rtol=0)):
        raise ValueError('wrist region requires the pinned Gz playing plane')
    bodies = dict(zip(manifest['logical_body_names'], manifest['logical_position_root_m']))
    fret_y = np.array([bodies['G:nut'][1]]+[bodies['G:fret%d'%i][1] for i in range(1, 23)])
    anchors = np.array([row['anchor_fret'] for row in frames])
    reference_y = np.interp(anchors, np.arange(1, 23), .5*(fret_y[:-1]+fret_y[1:]))
    spans = np.array([row['allowed_fret_range'] for row in frames])
    work_center = .5*(fret_y[spans[:, 0]-1]+fret_y[spans[:, 1]])
    edge, board_z = _lower_edges(reference_y, plane, hulls)
    lower = np.stack((edge+.01, work_center-.06, board_z-.11), axis=-1)
    upper = np.stack((edge+.08, work_center+.06, board_z-.02), axis=-1)
    pins.update(extracted_pins)
    pins[str(manifest_path)] = _MANIFEST_SHA256
    contract = dict(schema=SCHEMA, frame='live guitar local',
        reference='physical midpoint of allowed_fret_range outer cell boundaries; lower source neck edge at anchor-cell midpoint; source playing plane',
        along_half_width_m=.06, below_lower_edge_m=[.01, .08], behind_board_m=[.02, .11],
        widths_G_xyz_m=[.07, .12, .09], excess_scales_G_xyz_m=list(EXCESS_SCALES_G_M),
        track_hz=60, interpolation='linear lower/upper bounds; clamp before/after track; input time excludes policy pre-roll',
        position='zero inside inclusive bounds; outside -q/(1+q), q=sum((excess/scales)^2)',
        delta='nearest allowed point minus wrist; zero inside; no center target',
        orientation='free; rotation error zero and orientation multiplier one',
        stage_weights=[.2, .1, .05], integration_dt_s=1/240., source_sha256=pins,
        ignored_legacy_fields=['wrist_pos_guitar', 'allowed_radius_m', 'offsets_m'],
        scope='soft wrist position guidance only; no reachability, contact, pressure or musical-success certification')
    return dict(times_s=[index/60. for index in range(len(frames))],
                lower_G_m=lower.tolist(), upper_G_m=upper.tolist(), contract=contract)


def measure_wrist_region(wrist_G, timestamp_s, times_s, lower_G_m, upper_G_m):
    """Pure Torch measurement of a validated/cached track, without host copies.

Inputs are wrist[N,3], song timestamp[N], times[T], and lower/upper[T,3].
The environment subtracts its pre-roll before calling this function.
"""
    if (wrist_G.ndim != 2 or wrist_G.shape[1] != 3 or
            timestamp_s.shape != wrist_G.shape[:1] or times_s.ndim != 1 or not len(times_s) or
            lower_G_m.shape != (len(times_s), 3) or upper_G_m.shape != lower_G_m.shape or
            any(value.device != wrist_G.device for value in (timestamp_s, times_s, lower_G_m, upper_G_m)) or
            lower_G_m.dtype != wrist_G.dtype or upper_G_m.dtype != wrist_G.dtype or
            timestamp_s.dtype != times_s.dtype or not wrist_G.is_floating_point() or
            not times_s.is_floating_point()):
        raise ValueError('aligned floating wrist[N,3], timestamp[N], times[T], cached bounds[T,3] required')
    if len(times_s) == 1:
        lower = lower_G_m[0].expand_as(wrist_G)
        upper = upper_G_m[0].expand_as(wrist_G)
    else:
        after = torch.searchsorted(times_s, timestamp_s).clamp(1, len(times_s)-1)
        before = after-1
        alpha = ((timestamp_s-times_s[before])/(times_s[after]-times_s[before])).clamp(0, 1)
        alpha = alpha.to(wrist_G.dtype)[:, None]
        lower = lower_G_m[before]+alpha*(lower_G_m[after]-lower_G_m[before])
        upper = upper_G_m[before]+alpha*(upper_G_m[after]-upper_G_m[before])
    nearest = torch.minimum(torch.maximum(wrist_G, lower), upper)
    delta = nearest-wrist_G
    q = ((delta/wrist_G.new_tensor(EXCESS_SCALES_G_M))**2).sum(-1)
    position = -q/(1+q)
    return dict(delta=delta, rotation=torch.zeros_like(delta), ready=(delta == 0).all(-1),
                position=position, orientation=torch.ones_like(position),
                lower_G_m=lower, upper_G_m=upper, distance_m=torch.linalg.vector_norm(delta, dim=-1))
