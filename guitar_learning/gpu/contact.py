"""원본 넥·손가락 기하로 압현 목표·손목 영역·접촉 후보를 계산한다.

표면 표본·압현면·손목 영역 → 손끝 패드 → 엄지 안내 → 오압현 후보 순서로 읽는다.
검증된 모델 몸체 좌표계의 공학적 표면 패치이며 해부학적 구분이나 새 충돌 형상이 아니다.
물리 메시 자체는 변경하지 않는다."""

import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

import numpy as np
import torch
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation

from guitar_learning.gpu.control import _point_triangle
from guitar_learning.gpu.finger_reward import (FINGER_REWARD_CONTRACT,
    finger_tracking_reward, source_finger_frame_contract)
from guitar_learning.gpu.scene import _ASSET_DIR, _MANIFEST_SHA256, _REPO_ROOT
# 별칭은 기존 해시 검증 지점을 유지하며 같은 스트리밍 구현을 재사용한다.
from guitar_learning.training.training_log_io import digest as _sha
from guitar_learning.training.training_log_io import digest as _wrist_sha


# 원본 표면의 유한 표본·압현면과 악보 기반 손목 허용 영역.
INWARD_MARGIN_M = .002
_TOLERANCE_M = 1e-8
WRIST_REGION_SCHEMA = 'guitar_learning.gpu_wrist_region.v1'
EXCESS_SCALES_G_M = (.02, .03, .03)


def surface_target_geometry(points, velocities, valid, starts, ends, low, high,
                            strings, fingers, margin=.002):
    """지정 손가락 표면에서 유한한 목표 현·셀 선분까지의 최근접 기하를 구한다.
    
    점·속도는 기타 로컬 [N,10,S,3]이며 thumb2, thumb3, index2, index3, ...,
    pinky3 순서다. valid는 [10,S]다. 목표 현 번호는 0부터, 손가락은 검지 1부터
    소지 4까지이며 셀 y 경계는 [N,M]이다. 하중 조건은 적용하지 않는다.
    delta는 선택 표면에서 선분으로 향한다. 상대속도는 해당 표면점의 실제 상대속도에
    음수를 취한 값이며, 최소 거리나 매번 달라지는 표본 ID의 유한차분이 아니다.
    정확히 동률이면 펼친 body*S+sample 인덱스의 첫 번째를 선택한다."""
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
        # N*현재손가락목표*2S 스칼라만 만들고 전체목표*전체몸체*xyz는 만들지 않는다.
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
    """실제 손가락 메시 꼭짓점을 한 번 읽으며 가상의 패드를 만들지 않는다.
    
    고정 구면 방향의 지지 꼭짓점으로 원본 표면의 보수적인 유한 표본을 구성한다.
    표본 사이 간격 때문에 실제 접촉을 놓칠 수 있다."""
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


def _extract_plane(xml_path, expected_sha256):
    """두 물리 넥 형상을 읽고 원본 볼록 껍질의 반공간을 유지한다."""
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
        # 연주 영역 밖의 모서리 경사는 허용한다. 가장 위쪽을 향한 원본 면들은
        # 하나의 평면을 정의해야 하며 모든 목표 끝점이 그 위에 있어야 한다.
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
    """CPU에서 한 번, 안쪽으로 줄인 각 유한 선분이 원본 볼록 껍질 안에 있음을 검증한다."""
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
    # 양 끝점이 같은 볼록 껍질 안에 있으면 선분 전체도 그 안에 있다.
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
    """CPU 목표 목록에서 한 번 추출·검증한 뒤 엄격한 JSON 계약을 반환한다."""
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
    """순수 Torch 연산으로 Gz를 투영하며 호출자가 plane[4]를 텐서 장치에 캐시한다."""
    if (starts.ndim != 3 or starts.shape[1:] != (6, 3) or ends.shape != starts.shape or
            plane.shape != (4,) or starts.device != ends.device or starts.device != plane.device or
            starts.dtype != ends.dtype or starts.dtype != plane.dtype):
        raise ValueError('Aligned starts/ends[N,6,3] and cached plane[4] required')
    torch._assert_async(torch.isfinite(plane).all() & (plane[2] > 1e-6), 'Finite upward press plane required')
    def project(points):
        z = -(points[..., :2]*plane[:2]).sum(-1)-plane[3]
        return torch.cat((points[..., :2], (z/plane[2])[..., None]), -1)
    return project(starts), project(ends)


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
    return frames, {str(path): _wrist_sha(path), str(manifest_path): _wrist_sha(manifest_path)}


def _lower_edges(reference_y, plane, hulls):
    """각 기준 Gy의 연주면에서 원본 볼록 껍질의 최대 Gx를 구한다."""
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
    """CPU에서 초기화하며 docs import·reset 손목 오프셋·실시간 상태 변경을 사용하지 않는다."""
    frames, pins = _load_frames(bundle)
    manifest_path = (_ASSET_DIR/'manifest.json').resolve()
    if _wrist_sha(manifest_path) != _MANIFEST_SHA256:
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
    contract = dict(schema=WRIST_REGION_SCHEMA, frame='live guitar local',
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
    """검증·캐시된 손목 안내 경로를 호스트 복사 없이 순수 Torch 연산으로 측정한다.
    
    입력은 wrist[N,3], 곡 시각[N], times[T], lower/upper[T,3]이다.
    환경이 정책 준비 시간을 뺀 뒤 이 함수를 호출한다."""
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


# 지정 끝마디 패드의 표집·목표 접근 품질.
FINGERTIP_TRACKING_CONTRACT = copy.deepcopy(FINGER_REWARD_CONTRACT)
FINGERTIP_TRACKING_CONTRACT.update(
    schema='guitar_learning.gpu_finger_tracking_rate.v8',
    error='target minus nearest designated distal flexion-side mesh patch sample',
    quality='(1+distance/0.04)^-2*alignment_factor',
    candidate_multiplier=1., rate_bounds_per_s=[0., 2.],
    legacy_arguments='candidate, velocity and actions are shape-checked only; none changes tracking quality',
    alignment_factor='1-0.2*clamp(1-distance/0.02,0,1)*(1-clamp(normal_cos,0,1))',
    alignment_scope='weak near-only quality modulation; never suppresses approach potential',
    alignment_distance_m=.02, maximum_alignment_reduction=.2,
    normal_cos='nearest sample outward normal dot negative press-plane unit normal',
    recovery='per-finger quality multiplied by shared score-only tracking_weight; zero during full B recovery')


def _clip_polygon(polygon, axis, upper):
    """원본 표면을 유지하며 3차원 다각형을 coordinate <= upper 영역으로 자른다."""
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
    """실제 삼각형을 자른 뒤 면적에 따라 결정론적으로 층화 표집한다."""
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
    # 같은 면적의 층으로 삼각형별 표본 수를 조절하고, 무리수 기반 무게중심 좌표열로
    # 난수 상태 의존을 없애며 가장자리뿐 아니라 삼각형 내부도 포함한다.
    chosen = np.searchsorted(cumulative, (np.arange(samples)+.5)*cumulative[-1]/samples)
    i = np.arange(samples)+.5
    r = np.sqrt(np.mod(i*(np.sqrt(5)-1)/2, 1))
    s = np.mod(i*(np.sqrt(2)-1), 1)
    weights = np.stack((1-r, r*(1-s), r*s), -1)
    points = np.einsum('si,sij->sj', weights, pieces[chosen])
    ids = source_ids[chosen]
    # 독립 검수가 가능하도록 원본 삼각형의 무게중심 좌표를 보존한다.
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
    # 메시 공간 표본 밀도 진단이며 native 접촉 검출 범위를 보장하지 않는다.
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
    """봉인된 준비 자산에서 네 손가락 끝마디의 몸체 로컬 패치를 읽는다.
    
    모든 표본은 메시 크기·형상 변환을 적용한 실제 삼각형 위에 놓인다.
    검증된 -y 마디는 +x 방향 굽힘으로 -z 쪽을 향한다. 패치는 이 모델 안쪽 면과
    인접한 끝마디 하단 면을 사용하며, 피부·손톱을 추정한 해부학적 구분이 아니다."""
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
        triangles = np.frombuffer(
            payload,
            dtype=layout,
            count=count,
            offset=84,
        )['vertices'].astype(np.float64)
        scale = np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
        if scale.shape != (3,) or not (scale > 0).all():
            raise ValueError('Positive three-axis source mesh scale required: '+name)
        triangles *= scale
        quat = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
        position = np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
        triangles = Rotation.from_quat(np.r_[quat[1:], quat[:1]]).apply(triangles.reshape(-1, 3)).reshape(
            -1,
            3,
            3,
        )
        triangles += position
        p, n, row = _sample_patch(triangles)
        pins[str(mesh_path)] = hashlib.sha256(payload).hexdigest()
        row.update(body=name, mesh=str(mesh_path), mesh_scale=scale.tolist(),
                   geom_quaternion_wxyz=quat.tolist(), geom_position_m=position.tolist())
        points.append(p)
        normals.append(n)
        rows.append(row)
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
    """가장 가까운 유효 끝마디 표면과 모든 표본의 접촉 후보 기하를 측정한다.
    
    입력 points/normals/velocities는 [N,4,P,3], 목표별 출력은 [N,M] 또는 [N,M,3]이다.
    벡터는 모두 기타 로컬 좌표다. 목표 선분은 이미 압현면에 투영되어 있으며,
    low/high는 축소하지 않은 실제 프렛 셀의 y 경계다. 거리 계산에는 양쪽 프렛
    경계에서 2mm씩 안으로 줄인 유한 선분을 사용한다. 최근접점 선택은 법선·하중과
    독립적이다. 접촉 후보에는 위치·방향을 함께 만족하는 동일 표본 하나와 그 표본이
    속한 끝마디 몸체의 하중이 필요하다."""
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
        # 이 손가락의 목표 K개 × 패드 P개: 이후 거리/위치 판정은 [N,K,P].
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
        # N*전체목표*전체손가락*P*xyz 크기의 임시 텐서를 만들지 않는다.
        lateral_squared = torch.zeros_like(projection)
        height = (surface*unit).sum(-1)+plane[3]/plane_size
        for axis in range(3):
            squared += (start[..., axis, None]+clipped*line[..., axis, None]-surface[:, None, :, axis]).square()
            # 부호 있는 평면 간격을 먼저 제거한 뒤, 무한 목표 현까지의
            # 평면 내 수직 거리를 측정한다.
            lateral_squared += (surface[:, None, :, axis]-height[:, None]*unit[axis]-
                start[..., axis, None]-projection*line[..., axis, None]).square()
        # 접근용 최근접 표본 하나는 하중·법선과 무관하게 유효 거리만으로 고른다.
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
        # positive는 최근접 표본에 한정하지 않고, 모든 P표본 중 위치·방향을
        # 함께 만족하는 표본이 하나라도 있는지 검사한 뒤 담당 몸체 하중을 결합한다.
        result['position_geometry'][:, indices] = position.any(-1)
        result['facing_geometry'][:, indices] = facing.any(-1)
        result['positive'][:, indices] = facing.any(-1) & loaded[:, finger, None]
    return result


def pad_tracking_reward(now, onset, end, press, finger, delta, velocity,
                        candidate, actions, alignment, tracking_weight=None,
                        target_mask=None):
    """움직임 비용 없는 기존 추종 보상을 계산하고 2cm 이내에서만 방향을 약하게 반영한다."""
    if alignment.shape != delta.shape[:2]:
        raise ValueError('Aligned nearest-sample normal cosine[N,M] required')
    # 접촉 계수를 중립값으로 두고 기존 선택기·거리 보상률을 재사용한다.
    result = finger_tracking_reward(now, onset, end, press, finger, delta, velocity,
        torch.zeros_like(candidate), actions, target_mask)
    if not onset.numel():
        return result
    selected = result['indices'].clamp_min(0)
    distance = torch.linalg.vector_norm(delta.gather(1, selected[..., None].expand(-1, -1, 3)), dim=-1)
    cosine = alignment.gather(1, selected).clamp(0, 1)
    factor = 1-.2*(1-distance/.02).clamp(0, 1)*(1-cosine)
    quality = result['quality']*factor
    if tracking_weight is not None:
        if tracking_weight.shape != quality.shape:
            raise ValueError('Per-finger tracking weight[N,4] required')
        quality = quality*tracking_weight
    assigned = finger[None] == torch.arange(1, 5, device=finger.device)[:, None]
    present = (assigned.any(-1).sum().clamp_min(1) if target_mask is None else
        (assigned[None] & target_mask[:, None]).any(-1).sum(-1).clamp_min(1))
    return dict(result, quality=quality, rate=2*quality.sum(-1)/present)


# 유한 엄지 패드·넥 뒷면 안내와 하중 조건을 둔 접촉 대리지표.


THUMB_SUPPORT_CONTRACT = dict(
    schema='guitar_learning.gpu_thumb_rear_support.v3',
    body='LH:thumb3', samples=128, rate_per_s=.02,
    patch='thumb-specific source -x distal/+z flexion/-y inward-side triangles; same sampled point and outward normal',
    region='face-referenced physical playing-neck1 rear, central 50% width, work-fret center Gy +/-0.04m clipped to neck1; unused OBJ vertices and headstock transition excluded',
    gap='signed outward rear-plane distance; maximum quality at0..0.003m',
    distance='(1+max(gap-0.003,0)/0.02)^-2',
    penetration='smoothstep from0 at-0.001m to1 at0; zero below-0.001m',
    orientation='smoothstep(clamp(outward_pad_normal dot -rear_normal /0.8,0,1))',
    regional_quality='(1+in-plane distance to finite target region/0.02)^-2',
    contact_candidate='same sample signed gap[-0.001,0.0005]m, region excess<=1e-6m, facing>=0.1 and thumb3 rear-normal net load>=0.01N',
    reward='0.01/s geometric quality +0.01/s same-point geometric quality times binary contact candidate; larger loads give no extra reward',
    net_load='relu(thumb3 native resultant force in guitar coordinates dot unit source rear normal); absent/nonfinite input disables contact candidate',
    selection='maximum rate, then maximum geometric quality, then nearest finite-region point; first sample only at exact distance tie',
    integration='rate only; caller integrates completed physics dt and failure suppression',
    limitation='finite source samples, not cooked collision geometry, anatomical annotation, contact-pair or pressure certification')


def load_thumb_support():
    """봉인된 thumb3 패치를 읽고 원본 넥 뒷면 사다리꼴을 한 번 검증한다."""
    from guitar_learning.native.paths import resolve_input_path
    from guitar_learning.gpu.episode_diagnostics import load_thumb_rear_surface
    from guitar_learning.gpu.scene import _ASSET_DIR, _REPO_ROOT

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
    triangles = Rotation.from_quat(np.r_[quat[1:], quat[:1]]).apply(triangles.reshape(-1, 3)).reshape(
        -1,
        3,
        3,
    )
    triangles += position
    # 다른 손가락과 달리 원본 엄지는 -x로 뻗고 +z축으로 굽힌다.
    # 올바른 순환 회전으로 공유 선택기의 -y/+x/-z 좌표계에 맞춘 뒤,
    # 표본·법선을 실제 몸체 좌표계로 되돌린다.
    for segment in (2, 3):
        node = next(b for b in xml.findall('.//body') if b.get('name') == 'LH:thumb'+str(segment))
        position_axis = np.fromstring(node.get('pos'), sep=' ')
        axis = np.fromstring(node.find('joint').get('axis'), sep=' ')
        if (not position_axis[0] < 0 or not np.allclose(position_axis[1:], 0., atol=1e-12) or
                not np.allclose(axis, [0., 0., 1.], atol=1e-12) or
                not np.allclose(np.fromstring(node.get('quat', '1 0 0 0'), sep=' '), [1., 0., 0., 0.])):
            raise ValueError('Verified source thumb -x chain and +z flexion axis required')
    canonical_points, canonical_normals, diagnostic = _sample_patch(triangles[..., [2, 0, 1]])
    points, normals = canonical_points[:, [1, 2, 0]], canonical_normals[:, [1, 2, 0]]
    diagnostic['canonical_mesh_y_bounds_m'] = diagnostic.pop('mesh_y_bounds_m')
    diagnostic['local_bounds_m'] = np.stack((points.min(0), points.max(0))).tolist()
    diagnostic['sampling_frame'] = 'proper rotation: canonical(x,y,z)=body(z,x,y); inverse maps samples/normals to thumb body'
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


def thumb_support_geometry(points, normals, valid, center_y, rear_vertices, plane, net_force_guitar=None):
    """움직이는 유한 넥 뒷면 영역에 대해 기타 로컬 표본 [N,P,3]을 측정한다.
    
    rear_vertices의 순서는 아래 왼쪽·아래 오른쪽·위 오른쪽·위 왼쪽이다.
    선택한 한 점의 일관된 기하 정보와 초당 [0,.02]의 보상률을 반환한다.
    net_force_guitar[N,3]는 기타 축으로 표현한 native thumb3 합력이다.
    이를 생략하면 접촉 가산 없이 기하만 측정한다. 이 대리지표는 엄지-넥 몸체쌍이나
    압력을 인증하지 않는다. 무효 기하는 유한한 0과 valid=False로 반환하고 입력은 바꾸지 않는다."""
    if points.ndim != 3:
        raise ValueError('Thumb pad points[N,P,3] required')
    count, samples, xyz = points.shape
    if (xyz != 3 or not samples or normals.shape != points.shape or valid.shape != (samples,) or
            valid.dtype != torch.bool or center_y.shape != (count,) or
            rear_vertices.shape != (4, 3) or plane.shape != (4,)):
        raise ValueError('Aligned points/normals[N,P,3], bool valid[P], center_y[N], rear[4,3], plane[4] required')
    force_provided = net_force_guitar is not None
    if net_force_guitar is None:
        net_force_guitar = points.new_zeros(count, 3)
    elif net_force_guitar.shape != (count, 3):
        raise ValueError('Native thumb3 net_force_guitar[N,3] required')
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
    middle, half = (left+right)/2, (right-left)/4  # 전체 폭의 중앙 절반
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
    finite_force = torch.isfinite(net_force_guitar).all(-1) & force_provided
    force = torch.where(finite_force[:, None], net_force_guitar, 0.)
    normal_load = (force@unit).clamp_min(0.)
    contact_candidate = (usable & (gap >= -.001) & (gap <= .0005) &
        (excess <= 1e-6) & (facing >= .1) &
        finite_force[:, None] & (normal_load[:, None] >= .01))
    rate = .01*quality*(1+contact_candidate.to(quality.dtype))
    best_rate = rate.amax(-1, keepdim=True)
    rate_tie = usable & (rate == best_rate)
    best_quality = quality.masked_fill(~rate_tie, -1.).amax(-1, keepdim=True)
    tied = rate_tie & (quality == best_quality)
    selected = delta.square().sum(-1).masked_fill(~tied, torch.inf).argmin(-1)
    index = selected[:, None]
    selected_valid = usable.gather(1, index).squeeze(1)
    def scalar(value):
        return torch.where(selected_valid, value.gather(1, index).squeeze(1), 0.)
    def vector(value):
        return torch.where(
            selected_valid[:, None],
            value.gather(1, index[..., None].expand(-1, -1, 3)).squeeze(1),
            0.,
        )
    q = scalar(quality)
    selected_gap, selected_cos, regional = scalar(gap), scalar(facing), scalar(excess)
    return dict(selected_point=vector(clean_points), delta=vector(delta),
        selected_normal=vector(clean_normals), signed_gap=selected_gap, normal_cos=selected_cos,
        region_excess=regional, distance=scalar(torch.linalg.vector_norm(delta, dim=-1)),
        sample_index=torch.where(selected_valid, selected, -1), valid=selected_valid,
        quality=q, rate=scalar(rate),
        normal_load=torch.where(selected_valid, normal_load, 0.),
        normal_load_valid=selected_valid & finite_force,
        contact_candidate=selected_valid & contact_candidate.gather(1, index).squeeze(1),
        near_geometry=selected_valid & (selected_gap >= 0) & (selected_gap <= .003) &
            (regional <= 1e-6) & (selected_cos >= .1))


# 담당 패드 오류·더 높은 프렛의 경합을 검사하며 기하·하중 후보만 뜻한다.


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
    """원하는 목표와 독립적으로 실제 끝마디 패드 표본의 접촉 셀을 분류한다."""
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
    """목표별 판정과 10개 몸체·3개 원인으로 제한된 오압현 출처를 반환한다."""
    count, targets = positive.shape
    active = scope & (now[:, None] >= onset) & (now[:, None] <= end)
    future = scope & (now[:, None] >= press-2) & (now[:, None] < onset)
    # 현(0..5) × 프렛 × 손가락(0..4)의 격자를 1차원으로 펼친 인덱스다.
    keys = (strings*fret_count+frets)*5+fingers
    active_grid = torch.zeros(count, 6*fret_count*5, device=positive.device)
    future_grid = torch.zeros_like(active_grid)
    active_grid.scatter_add_(1, keys.expand(count, -1), active.float())
    future_grid.scatter_add_(1, keys.expand(count, -1), future.float())
    # [N,M,10,3]: 환경 × 목표 × 엄지2/3..소지2/3 × WRONG_PRESS_CONTRACT 원인 순서.
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
        # 올바른 담당 패드는 같은 손가락의 부수적인 표면 표본 때문에 무효화하지 않는다.
        # 다른 손가락의 더 높은 프렛은 별개로 계속 차단 요인이 된다.
        wrong_pad = (pad_valid[:, finger-1, :, None] & ~authorized[..., None] &
                     scope[:, None, indices] & ~positive[:, None, indices])
        same_string = ps[..., None] == strings[indices]
        body = 2*finger+1  # 몸체 순서: 엄지2/3, 검지2/3, ..., 소지2/3
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
