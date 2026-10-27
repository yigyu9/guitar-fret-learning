"""Source-convex neck plane for approach targets, never a physics override.

The pinned neck has one common playing plane over the requested fret cells.
This initialization proof is not a readback of PhysX cooked collision geometry.
"""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import torch

from guitar_learning.gpu.rigid_guitar import _ASSET_DIR, _MANIFEST_SHA256, _REPO_ROOT


INWARD_MARGIN_M = .002
_TOLERANCE_M = 1e-8


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extract_plane(xml_path, expected_sha256):
    """Read the two physical neck geoms and retain source hull halfspaces."""
    xml_path = Path(xml_path).resolve()
    if _sha(xml_path) != expected_sha256[str(xml_path)]:
        raise ValueError('Press surface XML SHA mismatch')
    root = ET.parse(xml_path).getroot()
    compiler = root.find('compiler')
    folder = xml_path.parent/(compiler.get('meshdir', '.') if compiler is not None else '.')
    meshes = {m.get('name'): m for m in root.findall('./asset/mesh')}
    hulls, planes, pins = [], [], {str(xml_path): _sha(xml_path)}
    for name in ('guitar_neck1', 'guitar_neck2'):
        geoms = [g for g in root.findall('./worldbody/body/geom') if g.get('mesh') == name and
                 not (g.get('contype') == '0' and g.get('conaffinity') == '0')]
        if len(geoms) != 1:
            raise ValueError('One physical neck mesh geom required: '+name)
        geom, mesh = geoms[0], meshes[name]
        path = (folder/mesh.get('file')).resolve()
        if _sha(path) != expected_sha256[str(path)]:
            raise ValueError('Press surface mesh SHA mismatch: '+name)
        pins[str(path)] = _sha(path)
        vertices = np.array([[float(v) for v in line.split()[1:4]]
                             for line in path.read_text().splitlines() if line.startswith('v ')])
        vertices *= np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
        quat = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
        vertices = Rotation.from_quat(np.r_[quat[1:], quat[:1]]).apply(vertices)
        vertices += np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
        hull = ConvexHull(vertices).equations
        # Bevels are allowed away from the playing footprint. The most upward
        # source facets must define one plane; all target endpoints must lie on it.
        upward = hull[:, 2].max()
        candidates = hull[np.abs(hull[:, 2]-upward) <= 1e-9]
        plane = candidates[0]
        if upward <= 1e-6 or not np.allclose(candidates, plane, rtol=0, atol=_TOLERANCE_M):
            raise ValueError('Single upward playing plane required')
        hulls.append(hull)
        planes.append(plane)
    if not np.allclose(planes, planes[0], rtol=0, atol=_TOLERANCE_M):
        raise ValueError('Neck meshes must share one playing plane')
    return planes[0], hulls, pins


def _validate_targets(plane, hulls, starts, ends, low, high, strings):
    """CPU one-time proof of each inward finite segment in a source hull."""
    start, line = starts[strings], ends[strings]-starts[strings]
    if ((high-low <= 2*INWARD_MARGIN_M).any() or (np.abs(line[:, 1]) <= 1e-12).any()):
        raise ValueError('Nonempty inward fret cell and finite fret-spanning string required')
    a = (low+INWARD_MARGIN_M-start[:, 1])/line[:, 1]
    b = (high-INWARD_MARGIN_M-start[:, 1])/line[:, 1]
    lower, upper = np.maximum(np.minimum(a, b), 0), np.minimum(np.maximum(a, b), 1)
    if (lower >= upper).any():
        raise ValueError('Inward cell must intersect its finite string')
    points = start[:, None]+np.stack((lower, upper), -1)[..., None]*line[:, None]
    points[..., 2] = -(points[..., :2]@plane[:2]+plane[3])/plane[2]
    # Both endpoints in the same convex hull proves the entire segment is in it.
    covered = np.zeros(len(strings), dtype=bool)
    for hull in hulls:
        residual = points@hull[:, :3].T+hull[:, 3]
        covered |= (residual <= _TOLERANCE_M).all(axis=(1, 2))
    if not covered.all():
        raise ValueError('Press target outside the source playing-plane footprint')
    return dict(target_count=len(strings), endpoint_count=2*len(strings),
                covered_endpoint_count=2*len(strings),
                maximum_plane_residual_m=float(np.abs(points@plane[:3]+plane[3]).max()))


def load_press_surface(strings, frets):
    """Extract/validate once from CPU target lists; return a strict JSON contract."""
    strings, frets = np.asarray(strings), np.asarray(frets)
    if (strings.ndim != 1 or not len(strings) or frets.shape != strings.shape or
            strings.dtype.kind not in 'iu' or frets.dtype.kind not in 'iu' or
            (strings < 0).any() or (strings > 5).any() or (frets < 1).any() or (frets > 22).any()):
        raise ValueError('Nonempty aligned canonical string0..5/fret1..22 integer lists required')
    manifest_path = _ASSET_DIR/'manifest.json'
    if _sha(manifest_path) != _MANIFEST_SHA256:
        raise ValueError('Press surface manifest SHA mismatch')
    manifest = json.loads(manifest_path.read_text())
    xml_path = (_ASSET_DIR/'guitar_compound.xml').resolve()
    expected = {str((_REPO_ROOT/p).resolve()): value for p, value in manifest['source_sha256'].items()}
    expected[str(xml_path)] = manifest['asset_sha256']
    plane, hulls, pins = _extract_plane(xml_path, expected)
    pins[str(manifest_path.resolve())] = _MANIFEST_SHA256
    bodies = dict(zip(manifest['logical_body_names'], np.asarray(manifest['logical_position_root_m'])))
    starts = np.asarray([bodies['G:string%d'%i] for i in range(1, 7)])
    ends = np.asarray([bodies['G:string%d_end'%i] for i in range(1, 7)])
    fret_y = np.asarray([bodies['G:nut'][1]]+[bodies['G:fret%d'%i][1] for i in range(1, 23)])
    low, high = np.minimum(fret_y[frets-1], fret_y[frets]), np.maximum(fret_y[frets-1], fret_y[frets])
    proof = _validate_targets(plane, hulls, starts, ends, low, high, strings)
    return dict(schema='guitar_learning.source_neck_press_plane.v1', plane_G=plane.tolist(),
                normal_G=plane[:3].tolist(), inward_margin_m=INWARD_MARGIN_M,
                source_sha256=pins, target_validation=proof,
                extraction='two physical source neck mesh convex hulls; common most-upward facet plane; complete inward segments in a source hull',
                projection='Gz only; preserve string x/y; existing surface geometry with negative inward margin',
                scope='Approach observation/reward target only; no contact/success or physics changes. Source convex hull proof, not exact PhysX cooked geometry or pressure certification.')


def project_press_strings(starts, ends, plane):
    """Pure Torch Gz projection; caller caches plane[4] on the tensor device."""
    if (starts.ndim != 3 or starts.shape[1:] != (6, 3) or ends.shape != starts.shape or
            plane.shape != (4,) or starts.device != ends.device or starts.device != plane.device or
            starts.dtype != ends.dtype or starts.dtype != plane.dtype):
        raise ValueError('Aligned starts/ends[N,6,3] and cached plane[4] required')
    torch._assert_async(torch.isfinite(plane).all() & (plane[2] > 1e-6), 'Finite upward press plane required')
    def project(points):
        z = -(points[..., :2]*plane[:2]).sum(-1)-plane[3]
        return torch.cat((points[..., :2], (z/plane[2])[..., None]), -1)
    return project(starts), project(ends)
