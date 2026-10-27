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
    schema='guitar_learning.gpu_left_episode_diagnostics.v3',
    fingers=['index', 'middle', 'ring', 'pinky'], joints=['MCP', 'PIP', 'DIP'],
    finger_wrist_hz=240, thumb_hz=60, reset_sample_included=False,
    duration='completed physics endpoint count/240; thumb completed control endpoint count/60',
    exclusions='overlapping per-finger seconds; never sum exclusions as disjoint time',
    standby_masks='actual v4 helper masks: imminent own press-0.35..end with0.15s fade; own relevant press-2..end proximity/nonfinite and candidate/wrong only; no netload-only veto',
    idle_angles='gate-weighted valid geometric flexion; denominator per joint valid gate-weighted seconds',
    press_angles='own assigned press..end inclusive, valid geometric flexion; denominator per joint valid seconds',
    standby='actual inverse-quadratic helper per_finger_rate integrated at240Hz; weighted reward excludes entire failed control tick exactly as environment',
    initial_quality_decline='quality below reset reference minus1e-6; completed240Hz fullgate==1 samples before own first press-2; absent fingers whole song; invalid reset/current angles excluded; no sample means evaluableFalse',
    recovery='fixed score-only far-idle windows outside own press-2..end; planned/observed/credited denominators separate; stable B entry requires0.2 sampled seconds; no control decisions',
    gate_runs='actual gate>0 and gate==1 completed240Hz endpoint runs; lengths/counts/band occupancy include ongoing runs; thresholds0.5/1/3s; no dynamic per-tick trace',
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


class FingerRecoveryWindows:
    """Bounded score windows prevent policy-dependent eligibility denominators."""
    def __init__(self, count, device, finger, press, end, duration_s):
        windows = []
        assignment, starts, ends = finger.cpu().tolist(), press.cpu().tolist(), end.cpu().tolist()
        for f in range(1, 5):
            busy = sorted((max(0., p-2.), min(duration_s, e))
                          for own, p, e in zip(assignment, starts, ends) if own == f)
            cursor = 0.
            for low, high in busy:
                if low > cursor:
                    windows.append((f-1, cursor, low))
                cursor = max(cursor, high)
            if cursor < duration_s:
                windows.append((f-1, cursor, duration_s))
        self.windows = windows
        last_end = [max((e for own, e in zip(assignment, ends) if own == f), default=None)
                    for f in range(1, 5)]
        self.post_last = torch.tensor([last_end[f] is not None and a >= last_end[f] and b-a >= 5.
            for f, a, b in windows], dtype=torch.bool, device=device)
        self.owner = torch.tensor([w[0] for w in windows], dtype=torch.long, device=device)
        self.start = torch.tensor([w[1] for w in windows], dtype=torch.float64, device=device)
        self.end = torch.tensor([w[2] for w in windows], dtype=torch.float64, device=device)
        self.values = {key: torch.zeros(count, len(windows), dtype=torch.float64, device=device)
                       for key in ('seen_s', 'valid_s', 'band_s', 'band_streak_s')}
        self.initial_valid = torch.zeros(count, len(windows), dtype=torch.bool, device=device)
        self.initial_inside = torch.zeros_like(self.initial_valid)
        self.entry = torch.full_like(self.values['seen_s'], torch.inf)

    def reset(self, indices):
        for value in self.values.values():
            value[indices] = 0.
        self.initial_valid[indices] = False
        self.initial_inside[indices] = False
        self.entry[indices] = torch.inf

    def physics(self, now, inside, valid):
        dt = (torch.minimum(now[:, None], self.end)-
              torch.maximum(now[:, None]-1/240., self.start)).clamp(0., 1/240.)
        active = dt > 0
        good = valid[:, self.owner]
        band = inside[:, self.owner] & good
        first = active & (self.values['seen_s'] == 0)
        self.initial_valid |= first & good
        self.initial_inside |= first & band
        self.values['seen_s'] += dt
        self.values['valid_s'] += dt*good
        self.values['band_s'] += dt*band
        streak = torch.where(active & band, self.values['band_streak_s']+dt, 0.)
        self.values['band_streak_s'] = streak
        confirmed = (streak+1e-12 >= .2) & ~torch.isfinite(self.entry)
        latency = (now[:, None]-streak-self.start).clamp_min(0.)
        self.entry = torch.where(confirmed, latency, self.entry)

    def episode(self, index):
        seen, valid, band = (self.values[k][index] for k in ('seen_s', 'valid_s', 'band_s'))
        nominal = self.end-self.start
        full = seen+1e-8 >= nominal
        started_outside = self.initial_valid[index] & ~self.initial_inside[index]
        entry = self.entry[index]
        success = full & started_outside & (entry <= 3.+1e-9)
        by_finger = []
        for f in range(4):
            selected = (self.owner == f) & (nominal >= 1.)
            planned_s, observed_s = nominal[selected].sum(), seen[selected].sum()
            band_s = band[selected].sum()
            n = selected.sum()
            by_finger.append(dict(
                planned_windows=n, planned_s=planned_s, observed_s=observed_s,
                valid_s=valid[selected].sum(), in_band_s=band_s,
                coverage_fraction=observed_s/planned_s.clamp_min(1e-30),
                credited_in_band_fraction=band_s/planned_s.clamp_min(1e-30),
                observed_in_band_fraction=band_s/observed_s.clamp_min(1e-30),
                complete_windows=(full & selected).sum(),
                incomplete_or_unobserved_windows=(~full & selected).sum(),
                started_outside_windows=(started_outside & selected).sum(),
                return_within3s_windows=(success & selected).sum(),
                started_inside_windows=(self.initial_inside[index] & selected).sum(),
                initially_unobserved_or_invalid_windows=(~self.initial_valid[index] & selected).sum(),
                post_last_ge5s=dict(
                    planned_windows=(selected & self.post_last).sum(),
                    complete_windows=(selected & self.post_last & full).sum(),
                    incomplete_or_unobserved_windows=(selected & self.post_last & ~full).sum(),
                    started_outside_windows=(selected & self.post_last & started_outside).sum(),
                    started_inside_windows=(selected & self.post_last & self.initial_inside[index]).sum(),
                    initially_unobserved_or_invalid_windows=(selected & self.post_last & ~self.initial_valid[index]).sum(),
                    return_within3s_windows=(selected & self.post_last & success).sum(),
                    evaluable=(selected & self.post_last).any()),
                evaluable=n > 0))
        return dict(windows=[dict(finger=f+1, start_s=a, end_s=b) for f, a, b in self.windows],
            sampled_s=seen, valid_s=valid, in_band_s=band, complete=full,
            started_valid=self.initial_valid[index], started_inside=self.initial_inside[index],
            stable_entry_latency_s=torch.where(torch.isfinite(entry), entry, -1.),
            return_within3s=success, by_finger=by_finger,
            scope='No future posture inferred after failure; missing scheduled exposure gets no occupancy credit. No windows means evaluableFalse. Return requires start outside,0.2s stable entry and complete window.')


class LeftEpisodeDiagnostics:
    def __init__(self, count, device, *, finger=None, press=None, end=None, duration_s=None):
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
        self.tick_shape = zeros(4)
        self.values.update({key: zeros(4) for key in ('raw_shape_reward', 'weighted_shape_reward')})
        # Last dimension: actual gate>0, full gate==1.
        self.run_steps = torch.zeros(count, 4, 2, dtype=torch.long, device=device)
        self.run_band_steps = torch.zeros_like(self.run_steps)
        self.run_total_steps = torch.zeros_like(self.run_steps)
        self.run_total_band_steps = torch.zeros_like(self.run_steps)
        self.closed_runs = torch.zeros_like(self.run_steps)
        self.closed_run_max = torch.zeros_like(self.run_steps)
        self.closed_long_s = zeros(4, 2, 3)
        self.closed_long_band_s = zeros(4, 2, 3)
        self.closed_long_count = torch.zeros(count, 4, 2, 3, dtype=torch.long, device=device)
        self.threshold_steps = torch.tensor([120, 240, 720], device=device)
        self.initial_reference = zeros(4)
        self.initial_reference_valid = torch.zeros(count, 4, dtype=torch.bool, device=device)
        self.values.update({key: zeros(4) for key in
            ('initial_quality_observed_s', 'initial_quality_declined_s')})
        self.initial_window_end = torch.zeros(4, dtype=torch.float64, device=device)
        self.initial_absent = torch.zeros(4, dtype=torch.bool, device=device)
        if finger is not None:
            for f in range(4):
                assigned = finger == f+1
                self.initial_absent[f] = not bool(assigned.any())
                self.initial_window_end[f] = ((press[assigned].amin()-2.).clamp(0., duration_s)
                    if bool(assigned.any()) else duration_s)
        self.recovery = (FingerRecoveryWindows(count, device, finger, press, end, duration_s)
                         if finger is not None else None)

    def reset(self, indices):
        for key, value in self.values.items():
            value[indices] = torch.inf if key.endswith('_min') else -torch.inf if key in ('idle_max', 'press_max') else 0.
        self.tick_standby[indices] = 0.
        self.tick_shape[indices] = 0.
        for value in (self.run_steps, self.run_band_steps, self.run_total_steps,
                      self.run_total_band_steps, self.closed_runs, self.closed_run_max,
                      self.closed_long_s, self.closed_long_band_s, self.closed_long_count):
            value[indices] = 0
        self.initial_reference[indices] = 0.
        self.initial_reference_valid[indices] = False
        if self.recovery is not None:
            self.recovery.reset(indices)

    def set_reset_posture(self, indices, posture):
        """Capture actual B quality once at selected episode resets, not H32."""
        quality = posture['quality'].double()
        valid = posture['valid'].all(-1) & torch.isfinite(quality)
        self.initial_reference[indices] = torch.where(valid, quality, 0.)[indices]
        self.initial_reference_valid[indices] = valid[indices]

    def physics(self, posture, pressing, wrist_delta, now=None):
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
        contribution = posture['per_finger_rate'].double()*dt
        self.values['raw_standby_reward'] += contribution
        self.tick_standby += contribution
        shape = posture['shape_per_finger_rate'].double()*dt
        self.values['raw_shape_reward'] += shape
        self.tick_shape += shape
        positive = torch.stack((gate > 0, gate == 1), -1)
        inside = posture['band_inside'][..., None] & positive
        self.run_total_steps += positive
        self.run_total_band_steps += inside
        closed = (~positive) & (self.run_steps > 0)
        length = torch.where(closed, self.run_steps, 0)
        self.closed_runs += closed
        self.closed_run_max.copy_(torch.maximum(self.closed_run_max, length))
        long = closed[..., None] & (length[..., None] >= self.threshold_steps)
        self.closed_long_count += long
        self.closed_long_s += long*length[..., None]/240.
        self.closed_long_band_s += long*self.run_band_steps[..., None]/240.
        self.run_steps = torch.where(positive, self.run_steps+1, 0)
        self.run_band_steps = torch.where(positive, self.run_band_steps+inside, 0)
        if self.recovery is not None:
            if now is None:
                raise ValueError('Score-window diagnostics require actual physics time')
            self.recovery.physics(now, posture['band_inside'], posture['valid'].all(-1))
            initial_window = ((now[:, None] > 0) &
                ((now[:, None] < self.initial_window_end) |
                 (self.initial_absent & (now[:, None] <= self.initial_window_end))))
            eligible = (initial_window & (gate == 1) & self.initial_reference_valid &
                        posture['valid'].all(-1) & torch.isfinite(quality))
            declined = eligible & (quality < self.initial_reference-1e-6)
            self.values['initial_quality_observed_s'] += eligible.double()*dt
            self.values['initial_quality_declined_s'] += declined.double()*dt
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
        self.values['weighted_shape_reward'] += self.tick_shape*approach_weight*(~failed[:, None])
        self.tick_shape.zero_()
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
        output['standby']['initial_quality_decline'] = dict(
            reference_quality=self.initial_reference[index],
            reference_valid=self.initial_reference_valid[index],
            planned_window_s=self.initial_window_end,
            observed_s=v['initial_quality_observed_s'],
            declined_s=v['initial_quality_declined_s'],
            declined_fraction=v['initial_quality_declined_s']/v['initial_quality_observed_s'].clamp_min(1e-30),
            evaluable=v['initial_quality_observed_s'] > 0, tolerance=1e-6)
        output['standby']['eligible_mean_quality'] = v['quality_integral']/v['gate_weighted_s'].clamp_min(1e-30)
        ongoing = self.run_steps[index]
        long = ongoing[..., None] >= self.threshold_steps
        for channel, key in enumerate(('actual_gate_runs', 'full_gate_runs')):
            long_s = (self.closed_long_s[index]+long*ongoing[..., None]/240.)[:, channel]
            long_band_s = (self.closed_long_band_s[index]+
                           long*self.run_band_steps[index][..., None]/240.)[:, channel]
            total_s = self.run_total_steps[index, :, channel]/240.
            output['standby'][key] = dict(
                count=(self.closed_runs[index]+(ongoing > 0))[:, channel],
                total_s=total_s,
                in_band_s=self.run_total_band_steps[index, :, channel]/240.,
                max_s=torch.maximum(self.closed_run_max[index], ongoing)[:, channel]/240.,
                long_threshold_s=[.5, 1., 3.],
                long_count=(self.closed_long_count[index]+long)[:, channel],
                long_total_s=long_s, long_in_band_s=long_band_s,
                long_in_band_fraction=long_band_s/long_s.clamp_min(1e-30))
        output['shape'] = {key: v[key] for key in ('raw_shape_reward', 'weighted_shape_reward')}
        if self.recovery is not None:
            output['recovery'] = self.recovery.episode(index)
        for condition in ('idle', 'press'):
            count = v[condition+'_seconds']
            output[condition+'_angles'] = dict(valid_weighted_s=count,
                mean_rad=v[condition+'_sum']/count.clamp_min(1e-30),
                min_rad=torch.where(count > 0, v[condition+'_min'], 0.),
                max_rad=torch.where(count > 0, v[condition+'_max'], 0.))
        def host(value):
            if isinstance(value, dict):
                return {k: host(x) for k, x in value.items()}
            if isinstance(value, (list, tuple)):
                return [host(x) for x in value]
            return value.cpu().tolist() if isinstance(value, torch.Tensor) else copy.deepcopy(value)
        return host(output)
