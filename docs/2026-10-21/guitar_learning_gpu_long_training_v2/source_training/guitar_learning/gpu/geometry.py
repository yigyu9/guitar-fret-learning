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
