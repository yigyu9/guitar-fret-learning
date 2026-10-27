"""Bounded episode summaries; no reward, control or physics decisions.

Finger/wrist statistics sample physics endpoints at 240 Hz. Thumb geometry
samples only completed 60 Hz control endpoints and cannot certify contact.
"""
import copy
import json
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import torch

from guitar_learning.gpu.control import _point_triangle
from guitar_learning.gpu.press_surface import _sha
from guitar_learning.gpu.rigid_guitar import _ASSET_DIR, _MANIFEST_SHA256, _REPO_ROOT


DIAGNOSTIC_CONTRACT = dict(
    schema='guitar_learning.gpu_left_episode_diagnostics.v2',
    fingers=['index', 'middle', 'ring', 'pinky'], joints=['MCP', 'PIP', 'DIP'],
    finger_wrist_hz=240, thumb_hz=60, reset_sample_included=False,
    duration='completed physics endpoint count/240; thumb completed control endpoint count/60',
    exclusions='overlapping per-finger seconds; never sum exclusions as disjoint time',
    standby_masks='actual v3 helper masks: imminent own press-0.35..end with0.15s fade; own relevant press-2..end proximity/nonfinite and candidate/wrong only; no netload-only veto',
    idle_angles='gate-weighted valid geometric flexion; denominator per joint valid gate-weighted seconds',
    press_angles='own assigned press..end inclusive, valid geometric flexion; denominator per joint valid seconds',
    standby='actual helper gate and quality; raw .0025*gate*quality/s per finger; weighted reward excludes entire failed control tick exactly as environment',
    wrist='absolute nearest-box delta by live guitar-local Gx/Gy/Gz; inclusive inside region; physics endpoint samples',
    thumb='minimum Euclidean distance from existing finite source thumb2/3 support vertices to finite source convex neck rear facets (outward normal Gz < -0.5); rear-side compatible permits signed plane gap >= -1 mm',
    thumb_limitation='60Hz geometric proximity only, not contact duration, pressure, sound or PhysX cooked geometry; finite support sampling may miss surface proximity; thumb surface normals unavailable, so no facing cosine is claimed')


def load_thumb_rear_surface():
    """Read four pinned source rear facets once; never import result artifacts."""
    manifest_path = _ASSET_DIR/'manifest.json'
    if _sha(manifest_path) != _MANIFEST_SHA256:
        raise ValueError('thumb rear source manifest SHA mismatch')
    manifest = json.loads(manifest_path.read_text())
    xml_path = (_ASSET_DIR/'guitar_compound.xml').resolve()
    expected = {str((_REPO_ROOT/p).resolve()): v for p, v in manifest['source_sha256'].items()}
    expected[str(xml_path)] = manifest['asset_sha256']
    if _sha(xml_path) != expected[str(xml_path)]:
        raise ValueError('thumb rear source XML SHA mismatch')
    root = ET.parse(xml_path).getroot()
    folder = xml_path.parent/root.find('compiler').get('meshdir', '.')
    meshes = {m.get('name'): m for m in root.findall('./asset/mesh')}
    triangles, planes = [], []
    for name in ('guitar_neck1', 'guitar_neck2'):
        geoms = [g for g in root.findall('./worldbody/body/geom') if g.get('mesh') == name and
                 not (g.get('contype') == '0' and g.get('conaffinity') == '0')]
        if len(geoms) != 1:
            raise ValueError('one physical thumb rear neck mesh required')
        geom, mesh = geoms[0], meshes[name]
        path = (folder/mesh.get('file')).resolve()
        if _sha(path) != expected[str(path)]:
            raise ValueError('thumb rear source mesh SHA mismatch')
        vertices = np.array([[float(x) for x in row.split()[1:4]]
                             for row in path.read_text().splitlines() if row.startswith('v ')])
        vertices *= np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
        q = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
        vertices = Rotation.from_quat(np.r_[q[1:], q[:1]]).apply(vertices)
        vertices += np.fromstring(geom.get('pos', '0 0 0'), sep=' ')
        hull = ConvexHull(vertices)
        rear = hull.equations[:, 2] < -.5
        triangles.extend(vertices[hull.simplices[rear]])
        planes.extend(hull.equations[rear])
    if not len(triangles) or not np.allclose(planes, planes[0], atol=1e-10, rtol=0):
        raise ValueError('common source rear neck plane required')
    return np.asarray(triangles), np.asarray(planes[0])


def thumb_rear_distance(points, valid, triangles, plane):
    """Finite source sample distance and rear-side-compatible distance, on device."""
    witness = _point_triangle(points[:, :, None], triangles[None, None])
    squared = (witness-points[:, :, None]).square().sum(-1).amin(-1)
    squared = squared.masked_fill(~valid[None], torch.inf)
    rear_side = points@plane[:3]+plane[3] >= -.001
    return squared.amin(-1).sqrt(), squared.masked_fill(~rear_side, torch.inf).amin(-1).sqrt()


class LeftEpisodeDiagnostics:
    def __init__(self, count, device):
        def zeros(*shape):
            return torch.zeros(count, *shape, dtype=torch.float64, device=device)
        self.values = {k: zeros(4) for k in (
            'eligible_s', 'gate_weighted_s', 'quality_integral', 'raw_standby_reward',
            'weighted_standby_reward', 'time_blocked_s', 'time_faded_s',
            'time_unavailable_weighted_s', 'contact_excluded_s', 'proximity_excluded_s',
            'nonfinite_distance_excluded_s', 'invalid_angle_s')}
        self.values.update({k: zeros() for k in ('physics_s', 'wrist_inside_s', 'thumb_s',
            'thumb_distance_sum', 'thumb_rear_within3mm_s', 'thumb_rear_within10mm_s')})
        self.values.update({k: zeros(3) for k in ('wrist_excess_sum', 'wrist_excess_max')})
        self.values['thumb_distance_min'] = torch.full_like(self.values['thumb_s'], torch.inf)
        self.values['thumb_distance_max'] = zeros()
        for condition in ('idle', 'press'):
            for suffix in ('seconds', 'sum', 'min', 'max'):
                self.values[condition+'_'+suffix] = zeros(4, 3)
            self.values[condition+'_min'].fill_(torch.inf)
            self.values[condition+'_max'].fill_(-torch.inf)
        self.tick_standby = zeros(4)

    def reset(self, indices):
        for key, value in self.values.items():
            value[indices] = torch.inf if key.endswith('_min') else -torch.inf if key in ('idle_max', 'press_max') else 0.
        self.tick_standby[indices] = 0.

    def physics(self, posture, pressing, wrist_delta):
        dt = 1/240.
        gate, quality, idle = (posture[k].double() for k in ('gate', 'quality', 'idle_weight'))
        flags = dict(eligible_s=gate > 0, time_blocked_s=idle == 0,
            time_faded_s=(idle > 0) & (idle < 1), contact_excluded_s=posture['contact_veto'],
            proximity_excluded_s=posture['near_veto'], nonfinite_distance_excluded_s=posture['nonfinite_veto'],
            invalid_angle_s=~posture['valid'].all(-1))
        for key, value in flags.items():
            self.values[key] += value.double()*dt
        self.values['gate_weighted_s'] += gate*dt
        self.values['time_unavailable_weighted_s'] += (1-idle)*dt
        self.values['quality_integral'] += gate*quality*dt
        contribution = .0025*gate*quality*dt
        self.values['raw_standby_reward'] += contribution
        self.tick_standby += contribution
        angles = posture['angles'].double()
        for condition, weight in (('idle', gate), ('press', pressing.double())):
            weight = weight[..., None]*posture['valid']
            self.values[condition+'_seconds'] += weight*dt
            self.values[condition+'_sum'] += angles*weight*dt
            self.values[condition+'_min'].copy_(torch.minimum(self.values[condition+'_min'], angles.masked_fill(weight <= 0, torch.inf)))
            self.values[condition+'_max'].copy_(torch.maximum(self.values[condition+'_max'], angles.masked_fill(weight <= 0, -torch.inf)))
        delta = wrist_delta.double().abs()
        self.values['physics_s'] += dt
        self.values['wrist_inside_s'] += (delta == 0).all(-1).double()*dt
        self.values['wrist_excess_sum'] += delta*dt
        self.values['wrist_excess_max'].copy_(torch.maximum(self.values['wrist_excess_max'], delta))

    def control(self, failed, approach_weight, distance, rear_distance):
        self.values['weighted_standby_reward'] += self.tick_standby*approach_weight*(~failed[:, None])
        self.tick_standby.zero_()
        self.values['thumb_s'] += 1/60.
        self.values['thumb_distance_sum'] += distance.double()/60.
        self.values['thumb_distance_min'].copy_(torch.minimum(self.values['thumb_distance_min'], distance.double()))
        self.values['thumb_distance_max'].copy_(torch.maximum(self.values['thumb_distance_max'], distance.double()))
        self.values['thumb_rear_within3mm_s'] += (rear_distance <= .003).double()/60.
        self.values['thumb_rear_within10mm_s'] += (rear_distance <= .01).double()/60.

    def episode(self, index):
        v = {k: value[index] for k, value in self.values.items()}
        seconds, thumb_s = v['physics_s'].clamp_min(1e-30), v['thumb_s'].clamp_min(1e-30)
        output = dict(schema=DIAGNOSTIC_CONTRACT['schema'], contract=copy.deepcopy(DIAGNOSTIC_CONTRACT),
            physics_sampled_s=v['physics_s'],
            physics_endpoint_count=(v['physics_s']*240).round().long(),
            standby={k: v[k] for k in ('eligible_s', 'gate_weighted_s', 'raw_standby_reward',
                'weighted_standby_reward', 'time_blocked_s', 'time_faded_s',
                'time_unavailable_weighted_s', 'contact_excluded_s', 'proximity_excluded_s',
                'nonfinite_distance_excluded_s', 'invalid_angle_s')},
            wrist=dict(inside_fraction=v['wrist_inside_s']/seconds,
                mean_excess_G_xyz_m=v['wrist_excess_sum']/seconds, max_excess_G_xyz_m=v['wrist_excess_max']),
            thumb=dict(sampled_s=v['thumb_s'], endpoint_count=(v['thumb_s']*60).round().long(),
                mean_distance_m=v['thumb_distance_sum']/thumb_s,
                min_distance_m=torch.where(v['thumb_s'] > 0, v['thumb_distance_min'], 0.),
                max_distance_m=v['thumb_distance_max'], rear_side_within3mm_fraction=v['thumb_rear_within3mm_s']/thumb_s,
                rear_side_within10mm_fraction=v['thumb_rear_within10mm_s']/thumb_s))
        output['standby']['eligible_mean_quality'] = v['quality_integral']/v['gate_weighted_s'].clamp_min(1e-30)
        for condition in ('idle', 'press'):
            count = v[condition+'_seconds']
            output[condition+'_angles'] = dict(valid_weighted_s=count,
                mean_rad=v[condition+'_sum']/count.clamp_min(1e-30),
                min_rad=torch.where(count > 0, v[condition+'_min'], 0.),
                max_rad=torch.where(count > 0, v[condition+'_max'], 0.))
        def host(value):
            return {k: host(x) for k, x in value.items()} if isinstance(value, dict) else value.cpu().tolist() if isinstance(value, torch.Tensor) else copy.deepcopy(value)
        return host(output)
