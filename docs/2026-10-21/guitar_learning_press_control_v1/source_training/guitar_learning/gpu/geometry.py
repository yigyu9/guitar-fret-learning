"""Batched xyzw quaternion geometry; all operations retain tensor devices."""
import torch


def conjugate(q):
    return torch.cat((-q[..., :3], q[..., 3:]), -1)


def multiply(a, b):
    xyz = a[..., 3:]*b[..., :3] + b[..., 3:]*a[..., :3] + torch.cross(a[..., :3], b[..., :3], dim=-1)
    return torch.cat((xyz, a[..., 3:]*b[..., 3:]-(a[..., :3]*b[..., :3]).sum(-1, keepdim=True)), -1)


def apply(q, value):
    q = q/torch.linalg.vector_norm(q, dim=-1, keepdim=True).clamp_min(1e-12)
    xyz, value = torch.broadcast_tensors(q[..., :3], value)
    uv = torch.cross(xyz, value, dim=-1)
    return value + 2*(q[..., 3:]*uv + torch.cross(xyz, uv, dim=-1))


def rotvec(q):
    q = q/torch.linalg.vector_norm(q, dim=-1, keepdim=True).clamp_min(1e-12)
    q = torch.where(q[..., 3:] < 0, -q, q)
    size = torch.linalg.vector_norm(q[..., :3], dim=-1, keepdim=True)
    angle = 2*torch.atan2(size, q[..., 3:].clamp_min(0))
    return q[..., :3]*torch.where(size > 1e-7, angle/size.clamp_min(1e-12), 2.)


def origin_velocity(state, com):
    return state[..., 7:10] + torch.cross(state[..., 10:13], apply(state[..., 3:7], -com), dim=-1)


def relative_point(point, velocity, body, com):
    delta = point-body[..., :3]
    local = apply(conjugate(body[..., 3:7]), delta)
    relative = velocity-origin_velocity(body, com)-torch.cross(body[..., 10:13], delta, dim=-1)
    return local, apply(conjugate(body[..., 3:7]), relative)


def surface_target_geometry(points, velocities, valid, starts, ends, low, high,
                            strings, fingers, margin=.002):
    """Nearest designated finger surface to a finite target string/cell segment.

    Points/velocities are guitar-local [N,10,S,3], ordered thumb2, thumb3,
    index2, index3, ..., pinky3; valid is [10,S]. Target strings are zero-based,
    fingers are 1=index through 4=pinky, and cell y bounds are [N,M]. No load
    condition is applied. Delta points from the selected surface to the segment.
    Relative velocity is minus that surface point's actual relative velocity,
    not a finite difference of the minimum distance or of changing sample IDs.
    Exact ties select the first flattened body*S+sample index.
    """
    count, bodies, samples, xyz = points.shape
    targets = strings.numel()
    if (bodies != 10 or samples == 0 or xyz != 3 or velocities.shape != points.shape or
            valid.shape != (10, samples) or valid.dtype != torch.bool or
            starts.shape != (count, 6, 3) or ends.shape != starts.shape or
            low.shape != (count, targets) or high.shape != low.shape or
            fingers.shape != strings.shape or strings.ndim != 1):
        raise ValueError('Aligned surface [N,10,S,3], valid[10,S] and target bounds[N,M] required')
    torch._assert_async(((fingers >= 1) & (fingers <= 4) &
                         (strings >= 0) & (strings < 6)).all(), 'Invalid target finger/string')
    delta = points.new_empty(count, targets, 3)
    relative_velocity = torch.empty_like(delta)
    distance = points.new_empty(count, targets)
    sample_index = torch.empty((count, targets), dtype=torch.long, device=points.device)
    for finger in range(1, 5):
        indices = (fingers == finger).nonzero().flatten()
        if indices.numel() == 0:
            continue
        surface = points[:, 2*finger:2*finger+2].flatten(1, 2)
        speed = velocities[:, 2*finger:2*finger+2].flatten(1, 2)
        usable = valid[2*finger:2*finger+2].flatten()
        torch._assert_async(usable.any(), 'Designated finger has no valid surface samples')
        start = starts[:, strings[indices]]
        line = ends[:, strings[indices]]-start
        torch._assert_async((line[..., 1] != 0).all(), 'Target strings must span the fret y axis')
        a = (low[:, indices]-margin-start[..., 1])/line[..., 1]
        b = (high[:, indices]+margin-start[..., 1])/line[..., 1]
        lower = torch.minimum(a, b).clamp_min(0)
        upper = torch.maximum(a, b).clamp_max(1)
        torch._assert_async(((low[:, indices] <= high[:, indices]) &
                             (lower <= upper)).all(), 'Target cell must intersect its finite string')
        projection = (torch.einsum('nsc,nkc->nks', surface, line)-
                      (start*line).sum(-1)[..., None])/line.square().sum(-1)[..., None]
        projection = torch.maximum(torch.minimum(projection, upper[..., None]), lower[..., None])
        # Only N * this finger's targets * 2S scalars, never all-target/all-body xyz.
        squared = torch.zeros_like(projection)
        for axis in range(3):
            squared += (start[..., axis, None]+projection*line[..., axis, None]-
                        surface[:, None, :, axis]).square()
        nearest = squared.masked_fill(~usable[None, None], torch.inf).argmin(-1)
        gather = nearest[..., None].expand(-1, -1, 3)
        selected = surface.gather(1, gather)
        closest = start+projection.gather(-1, nearest[..., None])*line
        delta[:, indices] = closest-selected
        relative_velocity[:, indices] = -speed.gather(1, gather)
        distance[:, indices] = torch.linalg.vector_norm(closest-selected, dim=-1)
        sample_index[:, indices] = nearest+2*finger*samples
    return delta, relative_velocity, distance, sample_index


def finger_mesh_surface_samples(names, directions=64):
    """Read real finger mesh vertices once; never construct an invented pad.

    Support vertices in fixed sphere directions form a conservative finite
    sample of the source surface. Gaps between samples may miss a contact.
    """
    from pathlib import Path
    import struct
    import xml.etree.ElementTree as ET
    import numpy as np
    from scipy.spatial.transform import Rotation
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.native.paths import resolve_input_path

    asset = load_prepared_reset_contract()['initial']['loaded_assets'][0]['path']
    path = resolve_input_path(asset)
    xml = ET.parse(path).getroot()
    meshdir = path.parent/xml.find('compiler').get('meshdir', '.')
    meshes = {mesh.get('name'): mesh for mesh in xml.findall('./asset/mesh')}
    bodies = {body.get('name'): body for body in xml.findall('.//body')}
    rows = []
    i = np.arange(directions)
    z = 1-2*(i+.5)/directions
    phi = i*np.pi*(3-np.sqrt(5.))
    sphere = np.stack((np.sqrt(1-z*z)*np.cos(phi), np.sqrt(1-z*z)*np.sin(phi), z), -1)
    sphere = np.r_[sphere, np.eye(3), -np.eye(3)]
    for name in names:
        geom = bodies[name].find('geom')
        if geom is None or geom.get('type') != 'mesh':
            raise ValueError('explicit source finger mesh required: '+name)
        mesh = meshes[geom.get('mesh')]
        payload = (meshdir/mesh.get('file')).read_bytes()
        count = struct.unpack_from('<I', payload, 80)[0]
        if len(payload) != 84+50*count:
            raise ValueError('source finger mesh must be binary STL')
        layout = np.dtype([('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
        vertices = np.frombuffer(payload, dtype=layout, count=count, offset=84)['vertices'].reshape(-1, 3)
        scale = np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
        vertices = vertices*scale
        quat = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
        vertices = Rotation.from_quat(np.r_[quat[1:], quat[:1]]).apply(vertices)
        vertices += np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
        selected = np.unique((vertices@sphere.T).argmax(0))
        rows.append(vertices[selected].astype(np.float32))
    maximum = max(map(len, rows))
    points, valid = np.zeros((len(rows), maximum, 3), np.float32), np.zeros((len(rows), maximum), bool)
    for index, row in enumerate(rows):
        points[index, :len(row)], valid[index, :len(row)] = row, True
    return points, valid
