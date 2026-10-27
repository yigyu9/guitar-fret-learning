"""Bounded left-arm PD target solve; no simulation writes."""
import numpy as np
from scipy.optimize import least_squares
from .underneck_initial_search import calibrated_fk, pose


class CurrentGuitarArm:
    def __init__(self, env, state, prepared):
        self.indices = np.array([i for i, n in enumerate(env.names)
            if n.startswith(('L_Shoulder', 'L_Elbow', 'L_Wrist'))])
        self.wrist_index = env.human_bodies.index('L_Wrist')
        self.chest_index = env.human_bodies.index('Chest')
        self.reference = np.asarray(prepared, dtype=float).copy()
        self.low = np.maximum(env.lower[self.indices], env.initial_q[self.indices]-.3)
        self.high = np.minimum(env.upper[self.indices], env.initial_q[self.indices]+.3)
        actual = np.array([r['pos'] for r in state['human_dof_states']])
        self.fk, _ = calibrated_fk(env.names, env.human_bodies, state, actual)
        self.chest_position, self.chest_rotation = pose(state['human_body_states'][self.chest_index])
        _, guitar_rotation = pose(state['guitar_body_states'][0])
        _, wrist_rotation = pose(state['human_body_states'][self.wrist_index])
        self.relative_rotation = guitar_rotation.inv()*wrist_rotation

    def solve(self, state, wrist_G, previous, dt):
        actual = np.array([r['pos'] for r in state['human_dof_states']])
        gp, gr = pose(state['guitar_body_states'][0])
        cp, cr = pose(state['human_body_states'][self.chest_index])
        wp, wr = pose(state['human_body_states'][self.wrist_index])
        delta = cr*self.chest_rotation.inv()
        target = gp+gr.apply(wrist_G)
        target_rotation = gr*self.relative_rotation
        def predict(v):
            q = actual.copy(); q[self.indices] = v
            p, r = self.fk(q)['L_Wrist']
            return cp+delta.apply(p-self.chest_position), delta*r
        p0, r0 = predict(actual[self.indices])
        fk_error = float(np.linalg.norm(p0-wp))
        fk_rotation_error = float((r0.inv()*wr).magnitude())
        if fk_error > .002 or fk_rotation_error > .01:
            raise ValueError('FK/native mismatch: '+str((fk_error, fk_rotation_error)))
        def residual(v):
            p, r = predict(v)
            return np.r_[p-target, .04*(target_rotation.inv()*r).as_rotvec(),
                         .02*(v-self.reference)]
        low = np.maximum(self.low, previous-.8*dt)
        high = np.minimum(self.high, previous+.8*dt)
        # Rate bounds are included in the solve, so the fitted command is executable.
        fit = least_squares(residual, np.clip(previous, low+1e-9, high-1e-9),
                            bounds=(low, high), max_nfev=20)
        if not np.isfinite(fit.x).all(): raise ValueError('nonfinite arm fit')
        p, r = predict(fit.x)
        return fit.x, dict(wrist_target_G_m=np.asarray(wrist_G).tolist(),
            wrist_target_W_m=target.tolist(), actual_wrist_W_m=wp.tolist(),
            wrist_error_m=float(np.linalg.norm(wp-target)),
            predicted_error_m=float(np.linalg.norm(p-target)),
            orientation_error_rad=float((target_rotation.inv()*wr).magnitude()),
            predicted_orientation_error_rad=float((target_rotation.inv()*r).magnitude()),
            fk_position_error_m=fk_error, fk_rotation_error_rad=fk_rotation_error,
            fit_success=bool(fit.success), fit_cost=float(fit.cost),
            final_left9_targets_rad=fit.x.tolist())
