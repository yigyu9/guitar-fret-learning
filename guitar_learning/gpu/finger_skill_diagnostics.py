"""Bounded phrase diagnostics; never changes rewards, controls or termination."""
import torch

from guitar_learning.gpu.episode_diagnostics import FingerRecoveryWindows
from guitar_learning.gpu.finger_motion_attribution import decompose_pad_motion


PHASES = ('initial_preparation', 'preparation', 'press', 'hold', 'release', 'idle')
COMPONENTS = ('total', 'support', 'finger')


class SkillEpisodeDiagnostics:
    def __init__(self, task, count, device):
        self.count, self.device = count, device
        self.finger = torch.tensor([t.finger for t in task.targets], device=device)
        self.press = torch.tensor([t.press_s for t in task.targets], dtype=torch.float64, device=device)
        self.onset = torch.tensor([t.onset_s for t in task.targets], dtype=torch.float64, device=device)
        self.end = torch.tensor([t.end_s for t in task.targets], dtype=torch.float64, device=device)
        original = FingerRecoveryWindows(0, device, self.finger, self.press, self.end, task.duration_s)
        self.owner, self.source_start, self.source_end = original.owner, original.start, original.end

        def zeros(*shape):
            return torch.zeros(count, *shape, dtype=torch.float64, device=device)

        self.offset, self.duration = zeros(), zeros()
        self.focus = torch.zeros(count, len(task.targets), dtype=torch.bool, device=device)
        self.active = torch.zeros(count, dtype=torch.bool, device=device)
        self.window_start = zeros(len(self.owner))
        self.window_end = zeros(len(self.owner))
        self.window_seen = zeros(len(self.owner))
        self.window_valid = zeros(len(self.owner))
        self.window_band = zeros(len(self.owner))
        self.preparation = {key: zeros(4) for key in ('observed_s', 'valid_s', 'in_band_s',
                                                     'gate_weighted_s', 'quality_integral')}
        self.pressing_s = zeros(4)
        self.paths = zeros(len(PHASES), 4, len(COMPONENTS))
        self.motion_seconds = zeros(len(PHASES), 4)
        self.motion_valid_sample_seconds = zeros(len(PHASES), 4)
        self.vector_sum_max_error = zeros()
        self.last_physics, self.last_control = zeros(), zeros()
        self.previous_points = zeros(4, 128, 3)
        self.previous_palm, self.previous_guitar = zeros(7), zeros(7)
        self.previous_palm[:, 6] = 1.
        self.previous_guitar[:, 6] = 1.

    def reset(self, indices, score_offset_s, duration_ticks, points_world,
              palm_pose, guitar_pose, focus_mask):
        """Replace selected rows only; all inputs use the full environment batch."""
        self.offset[indices] = score_offset_s[indices].double()
        self.duration[indices] = duration_ticks[indices].double() / 60.
        self.focus[indices] = focus_mask[indices]
        self.active[indices] = True
        low = self.offset[indices, None] + 3.
        high = self.offset[indices, None] + self.duration[indices, None]
        start = torch.maximum(self.source_start[None], low)
        self.window_start[indices] = start
        self.window_end[indices] = torch.maximum(start, torch.minimum(self.source_end[None], high))
        for value in (self.window_seen, self.window_valid, self.window_band,
                      self.pressing_s, self.paths, self.motion_seconds, self.motion_valid_sample_seconds,
                      self.vector_sum_max_error, self.last_physics, self.last_control,
                      *self.preparation.values()):
            value[indices] = 0.
        self.previous_points[indices] = points_world[indices].double()
        self.previous_palm[indices] = palm_pose[indices].double()
        self.previous_guitar[indices] = guitar_pose[indices].double()

    def physics(self, local_now, score_now, posture, pressing):
        """Integrate completed physics intervals, using endpoint B measurements."""
        local_now, score_now = local_now.double(), score_now.double()
        dt = (local_now - self.last_physics).clamp(0., 1 / 240.) * self.active
        dt = torch.minimum(dt, (self.duration - (local_now - dt)).clamp_min(0.))
        valid = posture['valid'].all(-1) & torch.isfinite(posture['angles']).all(-1)
        valid &= torch.isfinite(posture['quality']) & torch.isfinite(posture['gate'])
        band = posture['band_inside'] & valid
        prep_dt = (torch.minimum(local_now, local_now.new_tensor(3.)) -
                   torch.maximum(local_now - dt, local_now.new_tensor(0.))).clamp_min(0.)
        self.preparation['observed_s'] += prep_dt[:, None]
        self.preparation['valid_s'] += prep_dt[:, None] * valid
        self.preparation['in_band_s'] += prep_dt[:, None] * band
        gate = torch.where(valid, posture['gate'].double(), 0.)
        quality = torch.where(valid, posture['quality'].double(), 0.)
        self.preparation['gate_weighted_s'] += prep_dt[:, None] * gate
        self.preparation['quality_integral'] += prep_dt[:, None] * gate * quality
        self.pressing_s += dt[:, None] * pressing
        window_dt = (torch.minimum(score_now[:, None], self.window_end) -
                     torch.maximum((score_now - dt)[:, None], self.window_start)).clamp_min(0.)
        self.window_seen += window_dt
        self.window_valid += window_dt * valid[:, self.owner]
        self.window_band += window_dt * band[:, self.owner]
        self.last_physics.copy_(local_now)

    def _phases(self, local_now, score_now):
        """Current control endpoint labels; selected notes only, half-open times."""
        now = score_now[:, None]
        labels = torch.full((self.count, 4), PHASES.index('idle'), device=self.device, dtype=torch.long)
        for finger in range(1, 5):
            own = self.focus & (self.finger == finger)[None]
            preparing = (own & (now >= self.press - 2.) & (now < self.press)).any(-1)
            releasing = (own & (now >= self.end) & (now < self.end + .15)).any(-1)
            pressing = (own & (now >= self.press) & (now < self.onset)).any(-1)
            holding = (own & (now >= self.onset) & (now < self.end)).any(-1)
            for name, mask in (('preparation', preparing), ('release', releasing),
                               ('press', pressing), ('hold', holding)):
                labels[:, finger - 1] = torch.where(mask, PHASES.index(name), labels[:, finger - 1])
        return torch.where(local_now[:, None] < 3., PHASES.index('initial_preparation'), labels)

    def control(self, local_now, score_now, points_world, palm_pose, guitar_pose):
        """Same 128 material points; classify each displacement at its endpoint."""
        local_now, score_now = local_now.double(), score_now.double()
        current = points_world.double()
        palm, guitar = palm_pose.double(), guitar_pose.double()
        dt = (local_now - self.last_control).clamp(0., 1 / 60.) * self.active
        dt = torch.minimum(dt, (self.duration - (local_now - dt)).clamp_min(0.))
        pose_valid = torch.ones(self.count, dtype=torch.bool, device=self.device)
        clean_poses = []
        for value in (self.previous_palm, palm, self.previous_guitar, guitar):
            finite = torch.isfinite(value).all(-1) & (value[:, 3:].square().sum(-1) > 0)
            pose_valid &= finite
            identity = torch.zeros_like(value)
            identity[:, 6] = 1.
            clean_poses.append(torch.where(finite[:, None], value, identity))
        sample_valid = (torch.isfinite(self.previous_points).all(-1) &
                        torch.isfinite(current).all(-1) & pose_valid[:, None, None])
        motion = decompose_pad_motion(torch.nan_to_num(self.previous_points, nan=0., posinf=0., neginf=0.),
                                      torch.nan_to_num(current, nan=0., posinf=0., neginf=0.),
                                      *clean_poses)
        values = torch.stack([getattr(motion, key) for key in COMPONENTS], -2)
        path = (torch.linalg.vector_norm(values, dim=-1) * sample_valid[..., None]).mean(-2)
        error = (motion.total - motion.support - motion.finger).abs()
        error = torch.where(sample_valid[..., None], error, 0.).flatten(1).amax(-1)
        self.vector_sum_max_error.copy_(torch.maximum(self.vector_sum_max_error,
                                                      torch.where(dt > 0, error, 0.)))
        labels = self._phases(local_now, score_now)
        for index in range(len(PHASES)):
            selected = (labels == index) & (dt > 0)[:, None]
            self.paths[:, index] += path * selected[..., None]
            self.motion_seconds[:, index] += dt[:, None] * selected
            self.motion_valid_sample_seconds[:, index] += (dt[:, None] * selected *
                                                            sample_valid.double().mean(-1))
        self.previous_points.copy_(current)
        self.previous_palm.copy_(palm)
        self.previous_guitar.copy_(guitar)
        self.last_control.copy_(local_now)

    def episode(self, index):
        nominal = self.window_end[index] - self.window_start[index]
        seen, valid, band = self.window_seen[index], self.window_valid[index], self.window_band[index]
        selected = nominal >= .5 - 1e-12
        complete = seen + 1e-8 >= nominal
        occupancy80 = selected & complete & (band / nominal.clamp_min(1e-30) >= .8 - 1e-12)
        by_finger = []
        for finger in range(4):
            own = selected & (self.owner == finger)
            planned, observed, inside = nominal[own].sum(), seen[own].sum(), band[own].sum()
            by_finger.append(dict(planned_windows=int(own.sum()), planned_s=float(planned),
                observed_s=float(observed), valid_s=float(valid[own].sum()), in_band_s=float(inside),
                occupancy80_windows=int(occupancy80[own].sum()), complete_windows=int(complete[own].sum()),
                incomplete_or_unobserved_windows=int((own & ~complete).sum()),
                credited_in_band_fraction=float(inside / planned.clamp_min(1e-30)),
                coverage_fraction=float(observed / planned.clamp_min(1e-30)), evaluable=bool(own.any())))
        windows = [dict(finger=int(self.owner[w]) + 1, source_start_s=float(self.source_start[w]),
                        source_end_s=float(self.source_end[w]), start_s=float(self.window_start[index, w]),
                        end_s=float(self.window_end[index, w]), planned_s=float(nominal[w]),
                        observed_s=float(seen[w]), valid_s=float(valid[w]), in_band_s=float(band[w]),
                        evaluable=bool(selected[w]), complete=bool(complete[w]), occupancy80_met=bool(occupancy80[w]))
                   for w in range(len(self.owner)) if nominal[w] > 0]
        return dict(schema='guitar_learning.finger_skill_episode_diagnostics.v1',
            initial_preparation=dict(duration_s=3., **{k: v[index].tolist() for k, v in self.preparation.items()}),
            source_recovery=dict(windows=windows, by_finger=by_finger, minimum_window_s=.5,
                occupancy_target=.8, scope='Original score windows intersected with actual phrase playback; '
                'initial preparation excluded. Unobserved time after failure remains in planned denominators.'),
            physics_pressing_s=self.pressing_s[index].tolist(),
            motion=dict(phases=list(PHASES), components=list(COMPONENTS),
                path_m=self.paths[index].tolist(), observed_s=self.motion_seconds[index].tolist(),
                valid_sample_s=self.motion_valid_sample_seconds[index].tolist(),
                vector_sum_max_error_m=float(self.vector_sum_max_error[index]), fixed_samples=128,
                scope='Current control endpoint phase; mean of same128 material-point vector norms, '
                'invalid samples contribute zero with fixed128 denominator. Paths are not additive '
                'and do not measure force shares or causal success percentages.'))
