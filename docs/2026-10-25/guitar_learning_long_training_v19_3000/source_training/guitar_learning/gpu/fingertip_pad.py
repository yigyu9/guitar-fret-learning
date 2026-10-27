"""Source-mesh distal flexion-side samples and left-finger target geometry.

This is an engineering patch in the verified model body frame, not an
anatomical annotation or a new collision shape. Physical meshes are untouched.
"""
import copy
import hashlib
import struct
import xml.etree.ElementTree as ET

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from guitar_learning.gpu.finger_reward import (FINGER_REWARD_CONTRACT,
    finger_tracking_reward, source_finger_frame_contract)


FINGERTIP_TRACKING_CONTRACT = copy.deepcopy(FINGER_REWARD_CONTRACT)
FINGERTIP_TRACKING_CONTRACT.update(
    schema='guitar_learning.gpu_finger_tracking_rate.v7',
    error='target minus nearest designated distal flexion-side mesh patch sample',
    quality='(1+distance/0.04)^-2*alignment_factor',
    candidate_multiplier=1., rate_bounds_per_s=[0., 2.],
    legacy_arguments='candidate, velocity and actions are shape-checked only; none changes tracking quality',
    alignment_factor='1-0.2*clamp(1-distance/0.02,0,1)*(1-clamp(normal_cos,0,1))',
    alignment_scope='weak near-only quality modulation; never suppresses approach potential',
    alignment_distance_m=.02, maximum_alignment_reduction=.2,
    normal_cos='nearest sample outward normal dot negative press-plane unit normal')


def _clip_polygon(polygon, axis, upper):
    """Clip a 3D polygon to coordinate<=upper, preserving source surface."""
    clipped = []
    for previous, current in zip(polygon, polygon[1:]+polygon[:1]):
        previous_in, current_in = previous[axis] <= upper, current[axis] <= upper
        if previous_in != current_in:
            fraction = (upper-previous[axis])/(current[axis]-previous[axis])
            crossing = previous+fraction*(current-previous)
            crossing[axis] = upper
            clipped.append(crossing)
        if current_in:
            clipped.append(current)
    return clipped


def _sample_patch(triangles, samples=128):
    """Clip actual triangles, then deterministic stratified area sampling."""
    cross = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    twice_area = np.linalg.norm(cross, axis=-1)
    normals = cross/np.maximum(twice_area[:, None], 1e-30)
    ymin, ymax = triangles[..., 1].min(), triangles[..., 1].max()
    length = ymax-ymin
    if length <= 0 or not np.isfinite(triangles).all():
        raise ValueError('Finite source distal mesh with nonzero longitudinal extent required')
    pieces, source_ids = [], []
    for index, (triangle, normal, area) in enumerate(zip(triangles, normals, twice_area)):
        if area <= 1e-20:
            continue
        if normal[2] <= -.25:
            minimum_u = .25
        elif normal[1] <= -.4 and normal[2] <= 0:
            minimum_u = .75
        else:
            continue
        polygon = _clip_polygon(list(triangle), 2, 0.)
        polygon = _clip_polygon(polygon, 1, ymax-minimum_u*length)
        for vertex in range(1, len(polygon)-1):
            piece = np.asarray((polygon[0], polygon[vertex], polygon[vertex+1]))
            if np.linalg.norm(np.cross(piece[1]-piece[0], piece[2]-piece[0])) > 1e-20:
                pieces.append(piece)
                source_ids.append(index)
    if not pieces:
        raise ValueError('Source distal mesh has no eligible flexion-side patch')
    pieces, source_ids = np.asarray(pieces), np.asarray(source_ids)
    areas = np.linalg.norm(np.cross(pieces[:, 1]-pieces[:, 0], pieces[:, 2]-pieces[:, 0]), axis=-1)/2
    cumulative = np.cumsum(areas)
    # Equal-area strata control triangle counts; irrational barycentric sequences
    # avoid dependence on RNG state and include triangle interiors, not just rims.
    chosen = np.searchsorted(cumulative, (np.arange(samples)+.5)*cumulative[-1]/samples)
    i = np.arange(samples)+.5
    r = np.sqrt(np.mod(i*(np.sqrt(5)-1)/2, 1))
    s = np.mod(i*(np.sqrt(2)-1), 1)
    weights = np.stack((1-r, r*(1-s), r*s), -1)
    points = np.einsum('si,sij->sj', weights, pieces[chosen])
    ids = source_ids[chosen]
    # Preserve original triangle barycentrics as an independently checkable audit.
    original = triangles[ids]
    edge1, edge2 = original[:, 1]-original[:, 0], original[:, 2]-original[:, 0]
    offset = points-original[:, 0]
    a, b, c = (edge1*edge1).sum(-1), (edge1*edge2).sum(-1), (edge2*edge2).sum(-1)
    d, e = (offset*edge1).sum(-1), (offset*edge2).sum(-1)
    denominator = a*c-b*b
    v, w = (c*d-b*e)/denominator, (a*e-b*d)/denominator
    barycentric = np.stack((1-v-w, v, w), -1)
    sample_normals = normals[ids]
    u = (ymax-points[:, 1])/length
    # Mesh-space density diagnostics, not a guarantee of native contact coverage.
    pair_distances = np.linalg.norm(points[:, None]-points[None], axis=-1)
    np.fill_diagonal(pair_distances, np.inf)
    diagnostic = dict(source_triangle_count=len(triangles),
        eligible_source_triangle_count=int(np.unique(source_ids).size),
        clipped_triangle_count=len(pieces), mesh_area_m2=float(twice_area.sum()/2),
        patch_area_m2=float(cumulative[-1]), samples=samples,
        sample_area_m2=float(cumulative[-1]/samples),
        nearest_sample_spacing_m=dict(min=float(pair_distances.min()),
            mean=float(pair_distances.min(-1).mean()), max=float(pair_distances.min(-1).max())),
        sampled_source_triangle_count=int(np.unique(ids).size),
        local_bounds_m=np.stack((points.min(0), points.max(0))).tolist(),
        mesh_y_bounds_m=[float(ymin), float(ymax)],
        u_range=[float(u.min()), float(u.max())],
        distal_quarter_sample_count=int((u >= .75).sum()),
        source_triangle_indices=ids.tolist(), source_barycentric=barycentric.tolist())
    return points.astype(np.float32), sample_normals.astype(np.float32), diagnostic


def load_fingertip_pad():
    """Read the pinned prepared source; return four distal body-local patches.

    Every sample is on an actual triangle after mesh scale and geom transform.
    Positive +x flexion turns the verified -y segment toward -z. The patch uses
    this model-inward side and the adjacent distal lower cap, not an inferred
    skin/nail anatomical segmentation.
    """
    from guitar_learning.native.paths import resolve_input_path

    frame = source_finger_frame_contract()
    source = resolve_input_path(frame['source_xml']).resolve()
    xml = ET.parse(source).getroot()
    meshdir = source.parent/xml.find('compiler').get('meshdir', '.')
    meshes = {mesh.get('name'): mesh for mesh in xml.findall('./asset/mesh')}
    bodies = {body.get('name'): body for body in xml.findall('.//body')}
    points, normals, rows = [], [], []
    pins = dict(frame['source_sha256'])
    for finger in ('index', 'middle', 'ring', 'pinky'):
        name = 'LH:'+finger+'3'
        geoms = bodies[name].findall('geom')
        if len(geoms) != 1 or geoms[0].get('type') != 'mesh':
            raise ValueError('One explicit source distal mesh required: '+name)
        geom = geoms[0]
        if any(key in geom.attrib for key in ('euler', 'axisangle', 'xyaxes', 'zaxis')):
            raise ValueError('Explicit quaternion source geom transform required: '+name)
        mesh = meshes[geom.get('mesh')]
        mesh_path = (meshdir/mesh.get('file')).resolve()
        payload = mesh_path.read_bytes()
        count = struct.unpack_from('<I', payload, 80)[0]
        if len(payload) != 84+50*count:
            raise ValueError('Source distal mesh must be binary STL: '+name)
        layout = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
        triangles = np.frombuffer(payload, dtype=layout, count=count, offset=84)['vertices'].astype(np.float64)
        scale = np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
        if scale.shape != (3,) or not (scale > 0).all():
            raise ValueError('Positive three-axis source mesh scale required: '+name)
        triangles *= scale
        quat = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
        position = np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
        triangles = Rotation.from_quat(np.r_[quat[1:], quat[:1]]).apply(triangles.reshape(-1, 3)).reshape(-1, 3, 3)
        triangles += position
        p, n, row = _sample_patch(triangles)
        pins[str(mesh_path)] = hashlib.sha256(payload).hexdigest()
        row.update(body=name, mesh=str(mesh_path), mesh_scale=scale.tolist(),
                   geom_quaternion_wxyz=quat.tolist(), geom_position_m=position.tolist())
        points.append(p); normals.append(n); rows.append(row)
    contract = dict(schema='guitar_learning.distal_flexion_side_patch.v1',
        fingers=['index', 'middle', 'ring', 'pinky'], body_names=[row['body'] for row in rows],
        samples_per_finger=128, coordinate_frame='distal body local after source mesh scale/geom transform',
        definition='u=(ymax-y)/(ymax-ymin); z<=0,u>=0.25 and (normal_z<=-0.25 or (u>=0.75,normal_y<=-0.4,normal_z<=0))',
        sampling='actual eligible triangle clipping then equal-area CDF strata and deterministic barycentric interiors',
        normals='unit outward triangle cross-product after mesh scale/geom transform',
        frame_source=frame, source_sha256=pins, fingers_diagnostics=rows,
        limitation='model flexion-side engineering patch; not anatomical annotation, native contact location or pressure certification; finite samples may miss contacts')
    return dict(points_local=np.stack(points), normals_local=np.stack(normals),
                valid=np.ones((4, 128), dtype=bool), contract=contract)


def pad_target_geometry(points, normals, velocities, valid, starts, ends, low,
                        high, strings, fingers, loaded, plane):
    """Nearest eligible distal surface and any-sample contact geometry.

    All vectors are guitar-local. Target segments are already projected to the
    press plane; low/high are unshrunk actual fret-cell y bounds. Distance uses
    that finite segment, inset 2mm at both fret boundaries. Nearest-point
    selection is independent of normal/load. Contact needs *any same sample*
    satisfying position and facing, plus load on its assigned distal body.
    """
    if points.ndim != 4:
        raise ValueError('Distal surfaces[N,4,P,3] required')
    count, bodies, samples, xyz = points.shape
    targets = strings.numel()
    if (bodies != 4 or samples == 0 or xyz != 3 or normals.shape != points.shape or
            velocities.shape != points.shape or valid.shape != (4, samples) or valid.dtype != torch.bool or
            starts.shape != (count, 6, 3) or ends.shape != starts.shape or
            low.shape != (count, targets) or high.shape != low.shape or
            strings.ndim != 1 or fingers.shape != strings.shape or
            strings.dtype != torch.long or fingers.dtype != torch.long or
            loaded.shape != (count, 4) or loaded.dtype != torch.bool or plane.shape != (4,)):
        raise ValueError('Aligned distal surfaces, valid[4,P], string segments[N,6,3], bounds[N,M], load bool[N,4], plane[4] required')
    torch._assert_async(((fingers >= 1) & (fingers <= 4) & (strings >= 0) & (strings < 6)).all(),
                        'Invalid target finger/string')
    plane_size = torch.linalg.vector_norm(plane[:3])
    torch._assert_async(torch.isfinite(plane).all() & (plane_size > 1e-6) & (plane[2] > 0),
                        'Finite upward press plane required')
    unit = plane[:3]/plane_size
    result = dict(delta=points.new_empty(count, targets, 3), velocity=points.new_empty(count, targets, 3),
        distance=points.new_empty(count, targets),
        sample_index=torch.empty((count, targets), dtype=torch.long, device=points.device),
        normal_cos=points.new_empty(count, targets), signed_height=points.new_empty(count, targets),
        position_geometry=torch.zeros(count, targets, dtype=torch.bool, device=points.device),
        facing_geometry=torch.zeros(count, targets, dtype=torch.bool, device=points.device),
        positive=torch.zeros(count, targets, dtype=torch.bool, device=points.device))
    for finger in range(4):
        indices = (fingers == finger+1).nonzero().flatten()
        if indices.numel() == 0:
            continue
        surface, speed, usable = points[:, finger], velocities[:, finger], valid[finger]
        torch._assert_async(usable.any(), 'Designated finger has no eligible distal samples')
        start = starts[:, strings[indices]]
        line = ends[:, strings[indices]]-start
        torch._assert_async((line[..., 1] != 0).all(), 'Target string must span the fret y axis')
        lower_y, upper_y = low[:, indices]+.002, high[:, indices]-.002
        a = (lower_y-start[..., 1])/line[..., 1]
        b = (upper_y-start[..., 1])/line[..., 1]
        lower = torch.minimum(a, b).clamp_min(0)
        upper = torch.maximum(a, b).clamp_max(1)
        torch._assert_async(((lower_y <= upper_y) & (lower <= upper)).all(),
                            'Inset target cell must intersect its finite string')
        line_square = line.square().sum(-1)
        projection = (torch.einsum('nsc,nkc->nks', surface, line)-
                      (start*line).sum(-1)[..., None])/line_square[..., None]
        clipped = torch.maximum(torch.minimum(projection, upper[..., None]), lower[..., None])
        squared = torch.zeros_like(clipped)
        # No N*all-targets*all-fingers*P*xyz temporary.
        lateral_squared = torch.zeros_like(projection)
        height = (surface*unit).sum(-1)+plane[3]/plane_size
        for axis in range(3):
            squared += (start[..., axis, None]+clipped*line[..., axis, None]-surface[:, None, :, axis]).square()
            # Remove signed plane gap before measuring the perpendicular
            # in-plane distance to the infinite target string.
            lateral_squared += (surface[:, None, :, axis]-height[:, None]*unit[axis]-
                start[..., axis, None]-projection*line[..., axis, None]).square()
        nearest = squared.masked_fill(~usable[None, None], torch.inf).argmin(-1)
        gather = nearest[..., None].expand(-1, -1, 3)
        selected = surface.gather(1, gather)
        closest = start+clipped.gather(-1, nearest[..., None])*line
        cosine = -(normals[:, finger]*unit).sum(-1)
        position = (usable[None, None] & (lateral_squared <= .003**2) &
            (surface[:, None, :, 1] >= lower_y[..., None]) &
            (surface[:, None, :, 1] <= upper_y[..., None]) &
            (height[:, None] >= -.001) & (height[:, None] <= .003))
        facing = position & (cosine[:, None] >= .1)
        result['delta'][:, indices] = closest-selected
        result['velocity'][:, indices] = -speed.gather(1, gather)
        result['distance'][:, indices] = torch.linalg.vector_norm(closest-selected, dim=-1)
        result['sample_index'][:, indices] = nearest+finger*samples
        result['normal_cos'][:, indices] = cosine.gather(1, nearest)
        result['signed_height'][:, indices] = height.gather(1, nearest)
        result['position_geometry'][:, indices] = position.any(-1)
        result['facing_geometry'][:, indices] = facing.any(-1)
        result['positive'][:, indices] = facing.any(-1) & loaded[:, finger, None]
    return result


def pad_tracking_reward(now, onset, end, press, finger, delta, velocity,
                        candidate, actions, alignment):
    """Existing motion-cost-free tracking, weakly aligned only within 2cm."""
    if alignment.shape != delta.shape[:2]:
        raise ValueError('Aligned nearest-sample normal cosine[N,M] required')
    # Reuse the legacy selector and distance rate with a neutral contact factor.
    result = finger_tracking_reward(now, onset, end, press, finger, delta, velocity,
        torch.zeros_like(candidate), actions)
    if not onset.numel():
        return result
    selected = result['indices'].clamp_min(0)
    distance = torch.linalg.vector_norm(delta.gather(1, selected[..., None].expand(-1, -1, 3)), dim=-1)
    cosine = alignment.gather(1, selected).clamp(0, 1)
    factor = 1-.2*(1-distance/.02).clamp(0, 1)*(1-cosine)
    quality = result['quality']*factor
    present = (finger[None] == torch.arange(1, 5, device=finger.device)[:, None]).any(-1).sum().clamp_min(1)
    return dict(result, quality=quality, rate=2*quality.sum(-1)/present)
