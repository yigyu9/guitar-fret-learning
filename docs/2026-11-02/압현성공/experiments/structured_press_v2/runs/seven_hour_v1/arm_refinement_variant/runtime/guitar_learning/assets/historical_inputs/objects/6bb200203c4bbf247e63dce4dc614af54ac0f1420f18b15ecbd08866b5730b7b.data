"""Contact-point residual added to one PD target; no simulator writes."""
import numpy as np
from .underneck_initial_search import calibrated_fk, pose, read, FACETS


class PalmThumbSupport:
    def __init__(self, env, state):
        self.indices = np.array([i for i,n in enumerate(env.names) if
            n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:thumb'))])
        self.cap = np.array([.15 if env.names[i].startswith('LH:') else .3 for i in self.indices])
        self.initial = env.initial_q[self.indices].astype(float)
        self.lower = env.lower[self.indices]; self.upper = env.upper[self.indices]
        actual = np.array([r['pos'] for r in state['human_dof_states']])
        self.fk,_ = calibrated_fk(env.names,env.human_bodies,state,actual)
        self.chest_index = env.human_bodies.index('Chest')
        self.chest_p,self.chest_r = pose(state['human_body_states'][self.chest_index])
        self.facets = read(FACETS)['facets']; self.points = {}
        self.body_indices = {n:env.human_bodies.index(n) for n in ('LH:palm','LH:thumb3')}
        gp,gr = pose(state['guitar_body_states'][0])
        # Closest source surface witnesses define physical patch candidates, not attachments.
        from .underneck_pose_trial_v5 import initial_audit
        audit = initial_audit(env,env.candidate)
        for digit,n in (('palm','LH:palm'),('thumb','LH:thumb3')):
            entries = audit['surface_gaps'][digit]['member_distances']
            witness = entries[n]
            bp,br = pose(state['human_body_states'][self.body_indices[n]])
            local = br.inv().apply(np.asarray(witness['palm_witness_world_m'])-bp)
            target = gr.inv().apply(np.asarray(witness['target_witness_world_m'])-gp)
            outward = np.array([1.,.01631590413943356,0.]) if digit=='palm' else np.array([0.,0.,-1.])
            outward /= np.linalg.norm(outward)
            # Sub-millimetre hand target preload, never a guitar force or state write.
            self.points[n] = (local,target-.0003*outward)
        self.delta = np.zeros(len(self.indices))

    def update(self, state, base, previous, dt):
        actual = np.array([r['pos'] for r in state['human_dof_states']])
        cp,cr = pose(state['human_body_states'][self.chest_index]); chest_delta = cr*self.chest_r.inv()
        gp,gr = pose(state['guitar_body_states'][0])
        def points(q):
            poses = self.fk(q); rows = []
            for n,(local,_) in self.points.items():
                p,r = poses[n]; point = p+r.apply(local)
                rows.append(cp+chest_delta.apply(point-self.chest_p))
            return np.asarray(rows)
        predicted = points(actual); measured = []
        for n,(local,_) in self.points.items():
            p,r = pose(state['human_body_states'][self.body_indices[n]])
            measured.append(p+r.apply(local))
        measured = np.asarray(measured); fk_error = float(np.max(np.linalg.norm(predicted-measured,axis=1)))
        if fk_error>.002: raise ValueError('support FK/native mismatch '+str(fk_error))
        target = np.array([gp+gr.apply(goal) for _,goal in self.points.values()])
        error = (target-measured).ravel(); jacobian = np.empty((6,len(self.indices)))
        for j,i in enumerate(self.indices):
            q = actual.copy(); q[i] += 1e-5
            jacobian[:,j] = ((points(q)-predicted)/1e-5).ravel()
        # Damped task correction integrates into target offset to compensate loaded PD deflection.
        velocity = 2*jacobian.T@np.linalg.solve(jacobian@jacobian.T+.01**2*np.eye(6),error)
        requested_delta = np.clip(self.delta+np.clip(velocity,-.3,.3)*dt,-self.cap,self.cap)
        low = np.maximum(self.lower,self.initial-self.cap)
        high = np.minimum(self.upper,self.initial+self.cap)
        raw = base[self.indices]+requested_delta
        desired = np.clip(raw,low,high)
        final = np.clip(desired,previous[self.indices]-.3*dt,previous[self.indices]+.3*dt)
        final = np.clip(final,low,high)
        # Stop integration where the total target or its rate blocks the requested direction.
        blocked = velocity*(raw-final)>1e-12
        self.delta = np.where(blocked,self.delta,requested_delta)
        desired = np.clip(base[self.indices]+self.delta,low,high)
        final = np.clip(desired,previous[self.indices]-.3*dt,previous[self.indices]+.3*dt)
        final = np.clip(final,low,high)
        palm_r = pose(state['human_body_states'][self.body_indices['LH:palm']])[1]
        return final,dict(contact_point_targets_W_m=target.tolist(),actual_contact_points_W_m=measured.tolist(),
            point_errors_m=np.linalg.norm(target-measured,axis=1).tolist(),fk_position_error_m=fk_error,
            palm_normal_up=float(palm_r.apply(self.facets['LH:palm']['normal_local'])[2]),
            integrated_residual_rad=self.delta.tolist(),integral_blocked=blocked.tolist(),
            delivered_residual_rad=(final-base[self.indices]).tolist(),final_left17_targets_rad=final.tolist(),
            target_cap_rad=self.cap.tolist(),target_rate_rad_s=.3)
