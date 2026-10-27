"""Finite source thumb-pad / neck-rear proximity; never applies a force.

The patch is a model flexion-side engineering selection. Neither geometric
proximity nor a native body's resultant force certifies a thumb-neck pair.
"""
import hashlib
import json
import struct
import xml.etree.ElementTree as ET

import numpy as np
import torch
from scipy.spatial.transform import Rotation

from guitar_learning.gpu.control import _point_triangle
from guitar_learning.gpu.finger_reward import source_finger_frame_contract
from guitar_learning.gpu.fingertip_pad import _sample_patch


THUMB_SUPPORT_CONTRACT = dict(
    schema='guitar_learning.gpu_thumb_rear_support.v1',
    body='LH:thumb3', samples=128, rate_per_s=.02,
    patch='actual distal flexion-side triangles; same sampled point and outward normal',
    region='finite source neck rear, central 50% width, work-fret center Gy +/-0.04m',
    gap='signed outward rear-plane distance; maximum quality at0..0.003m',
    distance='(1+max(gap-0.003,0)/0.02)^-2',
    penetration='smoothstep from0 at-0.001m to1 at0; zero below-0.001m',
    orientation='smoothstep(clamp(outward_pad_normal dot -rear_normal /0.8,0,1))',
    regional_quality='(1+in-plane distance to finite target region/0.02)^-2',
    selection='maximum joint quality; zero-quality ties use nearest finite-region point; first sample otherwise',
    integration='rate only; caller integrates completed physics dt and failure suppression',
    limitation='finite source samples, not cooked collision geometry, anatomical annotation, contact-pair or pressure certification')


def load_thumb_support():
    """Load pinned thumb3 patch and validate the source rear trapezoid once."""
    from guitar_learning.native.paths import resolve_input_path
    from guitar_learning.gpu.episode_diagnostics import load_thumb_rear_surface
    from guitar_learning.gpu.rigid_guitar import _ASSET_DIR, _REPO_ROOT

    frame = source_finger_frame_contract()
    source = resolve_input_path(frame['source_xml']).resolve()
    xml = ET.parse(source).getroot()
    folder = source.parent/xml.find('compiler').get('meshdir', '.')
    meshes = {m.get('name'): m for m in xml.findall('./asset/mesh')}
    body = next(b for b in xml.findall('.//body') if b.get('name') == 'LH:thumb3')
    geoms = body.findall('geom')
    if len(geoms) != 1 or geoms[0].get('type') != 'mesh':
        raise ValueError('One explicit physical source thumb3 mesh required')
    geom = geoms[0]
    if any(k in geom.attrib for k in ('euler', 'axisangle', 'xyaxes', 'zaxis')):
        raise ValueError('Explicit source thumb geom quaternion required')
    mesh = meshes[geom.get('mesh')]
    path = (folder/mesh.get('file')).resolve()
    payload = path.read_bytes()
    count = struct.unpack_from('<I', payload, 80)[0]
    if len(payload) != 84+50*count:
        raise ValueError('Source thumb mesh must be binary STL')
    layout = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
    triangles = np.frombuffer(payload, dtype=layout, count=count, offset=84)['vertices'].astype(np.float64)
    scale = np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
    if scale.shape != (3,) or not (scale > 0).all():
        raise ValueError('Positive three-axis source thumb scale required')
    triangles *= scale
    quat = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
    position = np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
    triangles = Rotation.from_quat(np.r_[quat[1:], quat[:1]]).apply(triangles.reshape(-1, 3)).reshape(-1, 3, 3)
    triangles += position
    points, normals, diagnostic = _sample_patch(triangles)
    rear, plane = load_thumb_rear_surface()
    vertices = np.unique(rear.reshape(-1, 3), axis=0)
    levels = np.unique(vertices[:, 1])
    if len(vertices) != 4 or len(levels) != 2:
        raise ValueError('Two-level finite source rear trapezoid required')
    low = vertices[vertices[:, 1] == levels[0]]
    high = vertices[vertices[:, 1] == levels[1]]
    if len(low) != 2 or len(high) != 2:
        raise ValueError('Two rear width endpoints at each source y level required')
    ordered = np.stack((low[low[:, 0].argmin()], low[low[:, 0].argmax()],
                        high[high[:, 0].argmax()], high[high[:, 0].argmin()]))
    if not np.allclose(ordered@plane[:3]+plane[3], 0., atol=1e-9, rtol=0):
        raise ValueError('Source rear vertices must share the pinned rear plane')
    pins = dict(frame['source_sha256'])
    pins[str(path)] = hashlib.sha256(payload).hexdigest()
    manifest_path = _ASSET_DIR/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    pins[str(manifest_path.resolve())] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    pins[str((_ASSET_DIR/'guitar_compound.xml').resolve())] = manifest['asset_sha256']
    pins.update({str((_REPO_ROOT/p).resolve()): sha for p, sha in manifest['source_sha256'].items()})
    diagnostic.update(body='LH:thumb3', mesh=str(path), mesh_scale=scale.tolist(),
        geom_quaternion_wxyz=quat.tolist(), geom_position_m=position.tolist())
    contract = dict(THUMB_SUPPORT_CONTRACT, source_sha256=pins,
        patch_diagnostics=diagnostic, rear_vertices_guitar_m=ordered.tolist(), rear_plane_guitar=plane.tolist())
    return dict(points_local=points, normals_local=normals,
        valid=np.ones(len(points), dtype=bool), rear_vertices=ordered, plane=plane, contract=contract)


def _smoothstep(value):
    value = value.clamp(0., 1.)
    return value.square()*(3-2*value)


def thumb_support_geometry(points, normals, valid, center_y, rear_vertices, plane):
    """Measure [N,P,3] guitar-local samples against a moving finite region.

    ``rear_vertices`` order is low-left, low-right, high-right, high-left.
    Returns one selected point's coherent geometry plus a rate in [0,.02]/s.
    Invalid measurements are finite zeros with valid=False. No input is changed.
    """
    if points.ndim != 3:
        raise ValueError('Thumb pad points[N,P,3] required')
    count, samples, xyz = points.shape
    if (xyz != 3 or not samples or normals.shape != points.shape or valid.shape != (samples,) or
            valid.dtype != torch.bool or center_y.shape != (count,) or
            rear_vertices.shape != (4, 3) or plane.shape != (4,)):
        raise ValueError('Aligned points/normals[N,P,3], bool valid[P], center_y[N], rear[4,3], plane[4] required')
    size = torch.linalg.vector_norm(plane[:3])
    torch._assert_async(torch.isfinite(plane).all() & (size > 1e-6) & (plane[2]/size < -.5),
                        'Finite rear-facing source plane required')
    torch._assert_async(torch.isfinite(rear_vertices).all() &
        (rear_vertices[2, 1] > rear_vertices[0, 1]) &
        (rear_vertices[1, 0] > rear_vertices[0, 0]) &
        (rear_vertices[2, 0] > rear_vertices[3, 0]), 'Finite ordered source rear trapezoid required')
    unit, offset = plane[:3]/size, plane[3]/size
    finite = torch.isfinite(points).all(-1) & torch.isfinite(normals).all(-1)
    norm = torch.linalg.vector_norm(torch.nan_to_num(normals), dim=-1)
    finite &= valid[None] & (norm > 1e-6)
    clean_points = torch.where(finite[..., None], points, 0.)
    clean_normals = torch.where(finite[..., None], normals/norm.clamp_min(1e-12)[..., None], 0.)
    finite_center = torch.isfinite(center_y)
    center = torch.where(finite_center, center_y, 0.)
    ylow = torch.maximum(center-.04, rear_vertices[0, 1])
    yhigh = torch.minimum(center+.04, rear_vertices[2, 1])
    available = finite_center & (yhigh > ylow)
    yhigh = torch.maximum(yhigh, ylow)
    ys = torch.stack((ylow, yhigh), -1)
    fraction = ((ys-rear_vertices[0, 1])/(rear_vertices[2, 1]-rear_vertices[0, 1])).clamp(0, 1)
    left = rear_vertices[0, 0]+fraction*(rear_vertices[3, 0]-rear_vertices[0, 0])
    right = rear_vertices[1, 0]+fraction*(rear_vertices[2, 0]-rear_vertices[1, 0])
    middle, half = (left+right)/2, (right-left)/4  # central half of full width
    xs = torch.stack((middle-half, middle+half), -1)
    corners = points.new_empty(count, 4, 3)
    corners[..., 0] = torch.stack((xs[:, 0, 0], xs[:, 0, 1], xs[:, 1, 1], xs[:, 1, 0]), -1)
    corners[..., 1] = torch.stack((ylow, ylow, yhigh, yhigh), -1)
    corners[..., 2] = -(unit[0]*corners[..., 0]+unit[1]*corners[..., 1]+offset)/unit[2]
    triangles = torch.stack((corners[:, [0, 1, 2]], corners[:, [0, 2, 3]]), 1)
    witness = _point_triangle(clean_points[:, :, None], triangles[:, None])
    squared = (witness-clean_points[:, :, None]).square().sum(-1)
    triangle = squared.argmin(-1)
    closest = witness.gather(2, triangle[..., None, None].expand(-1, -1, 1, 3)).squeeze(2)
    delta = closest-clean_points
    gap = clean_points@unit+offset
    projected = clean_points-gap[..., None]*unit
    excess = torch.linalg.vector_norm(closest-projected, dim=-1)
    facing = -(clean_normals*unit).sum(-1).clamp(-1, 1)
    quality = ((1+(gap-.003).clamp_min(0)/.02).pow(-2)*
               _smoothstep((gap+.001)/.001)*_smoothstep(facing/.8)*
               (1+excess/.02).pow(-2))
    usable = finite & available[:, None]
    quality = torch.where(usable, quality, 0.)
    nearest = delta.square().sum(-1).masked_fill(~usable, torch.inf).argmin(-1)
    selected = torch.where(quality.amax(-1) > 0, quality.argmax(-1), nearest)
    index = selected[:, None]
    selected_valid = usable.gather(1, index).squeeze(1)
    def scalar(value):
        return torch.where(selected_valid, value.gather(1, index).squeeze(1), 0.)
    def vector(value):
        return torch.where(selected_valid[:, None], value.gather(1, index[..., None].expand(-1, -1, 3)).squeeze(1), 0.)
    q = scalar(quality)
    selected_gap, selected_cos, regional = scalar(gap), scalar(facing), scalar(excess)
    return dict(selected_point=vector(clean_points), delta=vector(delta),
        selected_normal=vector(clean_normals), signed_gap=selected_gap, normal_cos=selected_cos,
        region_excess=regional, distance=scalar(torch.linalg.vector_norm(delta, dim=-1)),
        sample_index=torch.where(selected_valid, selected, -1), valid=selected_valid,
        quality=q, rate=.02*q,
        near_geometry=selected_valid & (selected_gap >= 0) & (selected_gap <= .003) &
            (regional <= 1e-6) & (selected_cos >= .1))
