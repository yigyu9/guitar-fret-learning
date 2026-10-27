"""원 유한 제어를 유지하고 발바닥 IK에 골반 정면 yaw 잔차를 더한다."""
import numpy as np
from scipy.optimize import least_squares
from ..initial_pose_noise_v1 import pose
from ..grounded_guitar_support_v1.runtime_v18 import Controller as PreviousController
from ..seated_foot_support_v1.runtime_v6 import Scene


HEADING_BODIES = ('L_Ankle', 'L_Toe', 'R_Ankle', 'R_Toe', 'Torso', 'Spine', 'Chest', 'Head')


def horizontal_forward(rotation):
    front = rotation.apply([0., -1., 0.])
    front[2] = 0.
    length = np.linalg.norm(front)
    assert length > 1e-10
    return front / length


def heading_error_rad(rotation, reference):
    front = horizontal_forward(rotation)
    return float(np.arctan2(np.cross(reference, front)[2], reference @ front))


class Controller(PreviousController):
    def __init__(self, scene):
        super().__init__(scene)
        assert scene.cfg['validation_protocol'] == 'front_facing_prepare5_hold5_v1'
        state = scene.native()
        poses = {n: pose(b) for n, b in zip(scene.human_bodies, state['human_body_states'])}
        self.front_reference_W = horizontal_forward(poses['Pelvis'][1])
        self.front_initial_heading = {n: float(np.rad2deg(heading_error_rad(poses[n][1], self.front_reference_W)))
                                      for n in HEADING_BODIES}
        target = self.fk(self.base_target)
        self.front_base_heading = {n: float(np.rad2deg(heading_error_rad(target[n][1], self.front_reference_W)))
                                   for n in HEADING_BODIES}
        assert all(abs(v) <= 2. for v in self.front_initial_heading.values()), self.front_initial_heading
        assert all(abs(v) <= 2. for v in self.front_base_heading.values()), self.front_base_heading
        assert scene.foot_target_logic is self and scene.native() == state

    def apply(self, named):
        s = self.s
        q = np.array([r['pos'] for r in s.native()['human_dof_states']])
        ix = self.leg
        u = np.clip((s.steps/240)/.5, 0., 1.)
        ramp = u*u*(3-2*u)
        goal = .0005-.00075*ramp
        lo = np.maximum(s.lower[ix]+1e-7, s.q_ref[ix]-.6)
        hi = np.minimum(s.upper[ix]-1e-7, s.q_ref[ix]+.6)
        request = dict(named)
        legacy_hip = float(request['R_Hip_x'])
        request['R_Hip_x'] = float(s.q_ref[s.names.index('R_Hip_x')]+s.cfg['right_hip_final_bias_rad'])
        hips = [j for j in s.lower_indices if '_Hip_' in s.names[j]]

        def prediction(x):
            trial = q.copy()
            for j in hips:
                trial[j] = request[s.names[j]]
            trial[ix] = x
            return self.fk(trial)

        def residual(x):
            poses = prediction(x)
            rows = []
            for name, local in self.locals.items():
                p, r = poses[name]
                bottom = p+r.apply(local)
                rows.extend([2000*(bottom[:, 2]-goal), 2*(p[:2]-self.reference[name][0][:2])])
                rows.append(np.array([80.*heading_error_rad(r, self.front_reference_W)]))
            rows.append(.02*(x-s.q_ref[ix]))
            return np.concatenate(rows)

        fit = least_squares(residual, np.clip(s.target[ix], lo+1e-8, hi-1e-8),
                            bounds=(lo, hi), max_nfev=150, ftol=1e-9, xtol=1e-9, gtol=1e-9)
        poses = prediction(fit.x)
        feet, headings = {}, {}
        for name, local in self.locals.items():
            p, r = poses[name]
            bottom = p+r.apply(local)
            feet[name] = dict(min_bottom_z_m=float(bottom[:, 2].min()),
                              max_bottom_z_m=float(bottom[:, 2].max()),
                              bottom_span_m=float(np.ptp(bottom[:, 2])))
            headings[name] = float(np.rad2deg(heading_error_rad(r, self.front_reference_W)))
        assert np.isfinite(fit.x).all()
        assert all(abs(v['min_bottom_z_m']-goal) < .0005 and v['bottom_span_m'] < .001 for v in feet.values()), feet
        assert all(abs(v) <= 2. for v in headings.values()), headings
        for side in ('L', 'R'):
            ankle = np.array([fit.x[list(ix).index(s.names.index(side+'_Ankle_'+axis))] for axis in 'xyz'])
            assert np.linalg.norm(ankle) < np.deg2rad(160)
        for j, value in zip(ix, fit.x):
            request[s.names[j]] = float(value)
        return request, dict(desired_source_bottom_z_m=float(goal), ramp_fraction=float(ramp), predicted_feet=feet,
            legacy_R_Hip_x_request_rad=legacy_hip, final_R_Hip_x_request_rad=request['R_Hip_x'],
            prediction_hip_targets_rad={s.names[j]: request[s.names[j]] for j in hips},
            actual_hip_q_rad={s.names[j]: float(q[j]) for j in hips},
            heading_reference_W=self.front_reference_W.tolist(), heading_weight_rad=80., heading_gate_deg=2.,
            predicted_heading_error_deg=headings, initial_heading_error_deg=self.front_initial_heading,
            base_target_heading_error_deg=self.front_base_heading,
            scope='원10축 유한 발 IK와 최종 Hip 요청을 유지하고 고정 Pelvis local−Y 정면 잔차만 추가. 예측 바닥/heading은 실제 상태가 아니며 native 접촉·자세는 별도 판정. 원 gain/cap/rate와 영범위8축 보존.')
