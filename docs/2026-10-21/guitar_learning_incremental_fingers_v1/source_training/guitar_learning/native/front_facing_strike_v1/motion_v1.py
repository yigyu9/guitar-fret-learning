"""오른팔꿈치·손목6축만 새로 요청하는 유한 타현 모션."""
from pathlib import Path
import numpy as np
from ..initial_pose_noise_v1 import pose
from ..lower_body_release_v1.common import read, save
from ..elbow_wrist_strike_source_v1 import solve_pick
from ..grounded_guitar_play_v1.motion_v1 import interpolate

TIMES = [10., 10.8, 11.1, 11.5, 12.1, 12.3, 12.9, 13.1, 13.5]


def pick_goal(time, initial, points):
    return interpolate(time, TIMES, np.vstack([initial, points[0], points[1], points[1],
                                               points[2], points[2], points[3], points[3], points[4]]))


def command_gate(values, lower, upper, qref):
    return bool(np.isfinite(values).all() and np.all(values >= lower) and np.all(values <= upper)
                and np.all(values >= qref-1.) and np.all(values <= qref+1.)
                and np.all(np.linalg.norm(values.reshape(2, 3), axis=1) < np.deg2rad(160)))


class Motion:
    def __init__(self, scene, fk):
        self.s = scene
        self.fk = fk
        self.spec = read(scene.cfg['play_spec'])
        self.case = scene.cfg['play_case']
        assert self.case in ('baseline', 'strike')
        self.distal = np.array([scene.names.index(n+'_'+a) for n in ('R_Elbow', 'R_Wrist') for a in 'xyz'])
        self.proximal = np.array([scene.names.index(n+'_'+a) for n in ('R_Thorax', 'R_Shoulder') for a in 'xyz'])
        assert self.spec['joint_indices105'] == self.distal.tolist()
        assert self.spec['proximal_latch']['indices105'] == self.proximal.tolist()
        self.started = False
        self.stage = 'settle'
        self.info = {}

    def apply(self, named):
        s = self.s
        time = s.steps/240
        if time < 10:
            return named
        state = s.native()
        q = np.array([r['pos'] for r in state['human_dof_states']])
        gp, gr = pose(state['guitar_body_states'][0])
        if not self.started:
            assert s.steps == 2400
            self.initial_pick = gr.inv().apply(pose(state['human_body_states'][s.human_bodies.index('RH:pick')])[0]-gp)
            assert np.array_equal(self.initial_pick, self.spec['initial_pick_G_m'])
            save(Path(s.cfg['attempt_out'])/'play_reference.json', dict(time_s=time, state=state,
                initial_pick_G_m=self.initial_pick.tolist(), spec=self.spec))
            self.started = True
        original = np.array([named[n] for n in s.names])
        request = original.copy()
        self.stage = 'baseline_hold' if self.case == 'baseline' else ('playing' if time < 13.5 else 'observe')
        self.info = dict(case=self.case, press_enabled=False, strike_enabled=self.case == 'strike',
                         changed_joint_indices105=self.distal.tolist() if self.case == 'strike' else [],
                         right_world_palm_IK_active=False)
        if self.case == 'strike':
            goal = pick_goal(time, self.initial_pick, np.array(self.spec['strike']['waypoints_G_m']))
            fitted, error64, nfev = solve_pick(self.fk, q, self.distal, s.lower, s.upper, s.q_ref,
                                             gp+gr.apply(goal), s.target[self.distal].astype(float))
            values = fitted[self.distal].astype(np.float32).astype(float)
            trial = q.copy()
            trial[self.distal] = values
            error = float(np.linalg.norm(self.fk(trial)['RH:pick'][0]-(gp+gr.apply(goal))))
            if not command_gate(values, s.lower[self.distal], s.upper[self.distal], s.q_ref[self.distal]) or not np.isfinite(error) or error > .002:
                raise RuntimeError('새 distal6 float32 strict bounds/qref/principal/reach2mm gate')
            request[self.distal] = values
            self.info.update(pick_goal_G_m=goal.tolist(), pick_IK_error_m=error,
                             pick_IK_float64_error_m=error64, pick_IK_nfev=int(nfev),
                             requested_distal6_rad=values.tolist())
        unchanged = np.setdiff1d(np.arange(105), self.distal if self.case == 'strike' else [])
        assert np.array_equal(request[unchanged], original[unchanged]) and s.native() == state
        assert np.array_equal(request[self.proximal], self.spec['proximal_latch']['final6_rad'])
        self.info['other_base_request_channels_exact'] = True
        return dict(zip(s.names, request.tolist()))

    def record_final(self, row):
        if not self.started:
            return
        requested, final = (np.array(row[k]) for k in ('requested105_rad', 'final105_rad'))
        expected = np.array(self.spec['proximal_latch']['final6_rad'])
        assert np.array_equal(requested[self.proximal], expected)
        assert np.array_equal(final[self.proximal], expected)
        self.info.update(proximal_requested_latch_exact=True, proximal_submitted_latch_exact=True,
                         final_distal6_rad=final[self.distal].tolist(),
                         final_minus_requested_distal6_rad=(final[self.distal]-requested[self.distal]).tolist())
        row['play'] = self.info.copy()
