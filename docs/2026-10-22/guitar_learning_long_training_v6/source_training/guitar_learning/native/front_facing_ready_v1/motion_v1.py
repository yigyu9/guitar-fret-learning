"""실제step을 유지하는 왼손 해제·재접근과 오른말단 반복 타현 스케줄러."""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from ..initial_pose_noise_v1 import pose
from ..lower_body_release_v1.common import read, save
from ..grounded_guitar_release_v1.motion_v1 import WEIGHTS, smoothstep, solve_wrist
from ..front_facing_strike_v1.motion_v1 import pick_goal, command_gate
from ..front_facing_strike_v1.motion_v2 import solve_pick_oriented
from .protocol_v1 import schedule, TASK_CHAIN


def stage_at(plan, time):
    release = plan['release']
    if release is None or time < release[0]:
        return 'gripped'
    if time < release[0]+1.:
        return 'open'
    if time < release[1]:
        return 'withdraw'
    if plan['approach'] is None or time < plan['approach'][0]:
        return 'released_hold'
    if time < plan['approach'][1]:
        return 'approach'
    if time < plan['close'][1]:
        return 'close'
    return 'regrasp_hold'


def chain_errors(fk, q, state, bodies):
    predicted = fk(q)
    rows = {n:dict(position_m=float(np.linalg.norm(predicted[n][0]-pose(state['human_body_states'][bodies.index(n)])[0])),
                   rotation_deg=float(np.degrees((predicted[n][1]*pose(state['human_body_states'][bodies.index(n)])[1].inv()).magnitude()))) for n in TASK_CHAIN}
    return dict(max_position_m=max(r['position_m'] for r in rows.values()),max_rotation_deg=max(r['rotation_deg'] for r in rows.values()),bodies=rows)


def solve_left(fk, q, indices, lower, upper, qref, goal, rotation, seed):
    values, error64, rotation64, nfev = solve_wrist(fk,q,indices,lower,upper,qref,goal,rotation,seed)
    values = values.astype(np.float32).astype(float)
    trial = q.copy(); trial[indices] = values
    p,r = fk(trial)['L_Wrist']
    error = float(np.linalg.norm(p-goal)); angle = float((rotation.inv()*r).magnitude())
    valid = bool(np.isfinite(values).all() and np.isfinite([error,angle]).all()
        and np.all(values>=lower[indices]) and np.all(values<=upper[indices])
        and np.all(abs(values-qref[indices])<=.8)
        and np.all(np.linalg.norm(values.reshape(4,3),axis=1)<np.deg2rad(160)))
    return values,dict(position_error_m=error,rotation_error_rad=angle,float64_position_error_m=error64,
                       float64_rotation_error_rad=rotation64,nfev=int(nfev),strict_commands=valid)


class Motion:
    def __init__(self, scene, fk):
        self.s=scene; self.fk=fk; self.spec=read(scene.cfg['ready_spec'])
        self.plan=schedule(scene.cfg['ready_case']); assert self.plan==scene.cfg['ready_schedule']
        self.arm=np.array([scene.names.index(n+'_'+a) for n in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist') for a in 'xyz'])
        self.fingers=np.array([scene.names.index(n) for n in WEIGHTS])
        self.left=np.r_[self.arm,self.fingers]
        self.distal=np.array([scene.names.index(n+'_'+a) for n in ('R_Elbow','R_Wrist') for a in 'xyz'])
        self.proximal=np.array([scene.names.index(n+'_'+a) for n in ('R_Thorax','R_Shoulder') for a in 'xyz'])
        assert self.spec['left']['arm_indices105']==self.arm.tolist() and self.spec['left']['finger_indices105']==self.fingers.tolist()
        self.closed=np.array(self.spec['left']['finger_closed_reference14_rad'])
        self.open=np.array(self.spec['left']['finger_open_goal14_rad'])
        self.started=False; self.phase=None; self.cycle=None; self.info={}; self.stage='prepared'
        self.right_spec=self.spec['right_strike_spec']
        self.final_palm=Rotation.from_rotvec([0.,np.deg2rad(-15.),0.])*Rotation.from_quat(self.right_spec['clearance_solver_v2']['palm_G_reference_xyzw'])
        self.orientation_start=None; self.first_strike=None

    def command_pose(self, q, indices, target, name):
        trial=q.copy(); trial[indices]=target
        return self.fk(trial)[name]

    def apply(self, named):
        s=self.s; time=s.steps/240
        if time<10:return named
        state=s.native(); q=np.array([v['pos'] for v in state['human_dof_states']]); gp,gr=pose(state['guitar_body_states'][0])
        proof=chain_errors(self.fk,q,state,s.human_bodies)
        if proof['max_position_m']>=1e-5 or proof['max_rotation_deg']>=.01:
            save(Path(s.cfg['attempt_out'])/('task_chain_failure_step'+str(s.steps)+'.json'),dict(step=s.steps,state=state,proof=proof))
            raise RuntimeError('original-initial task-chain FK10um/.01deg gate')
        original=np.array([named[n] for n in s.names]); request=original.copy()
        held=s.target.astype(float).copy()
        if not self.started:
            assert s.steps==2400
            self.initial_left=held[self.left].copy()
            assert np.array_equal(held[self.fingers],self.closed)
            self.grasp_G=np.array(self.spec['left']['actual10_wrist_G_m'])
            self.grasp_rotation_G=Rotation.from_quat(self.spec['left']['actual10_wrist_G_xyzw'])
            save(Path(s.cfg['attempt_out'])/'ready_reference.json',dict(step=s.steps,time_s=time,state=state,
                last_submitted105_rad=held.tolist(),spec=self.spec))
            self.started=True
        phase=stage_at(self.plan,time)
        if phase!=self.phase:
            self.phase=phase; self.phase_start_step=s.steps; self.phase_start26=held[self.left].copy()
            self.phase_start_p,self.phase_start_r=self.command_pose(q,self.arm,held[self.arm],'L_Wrist')
            if phase=='open':
                self.release_actual_origin,self.release_actual_rotation=pose(state['human_body_states'][s.human_bodies.index('L_Wrist')])
                self.release_delta=gr.apply([.08,0.,0.]); self.release_start_step=s.steps;self.release_start_actual26=q[self.left].copy()
            if phase=='withdraw':
                self.withdraw_origin=self.phase_start_p.copy(); self.withdraw_rotation=self.phase_start_r
            if phase=='close':
                self.close_start_actual14=q[self.fingers].copy()
            if phase=='approach':
                self.approach_origin=self.phase_start_p.copy(); self.approach_rotation=self.phase_start_r
        request[self.left]=held[self.left]
        opening=withdraw=approach=close=0.; goal=None; goal_r=None; fit=None
        if self.plan['release'] is not None and time>=self.plan['release'][0]:
            release=self.plan['release']; opening=smoothstep(time,release[0],release[0]+1.)
            withdraw=smoothstep(time,release[0]+1.,release[1])
            request[self.fingers]=self.closed+(self.open-self.closed)*opening
            if phase in ('withdraw','released_hold'):
                goal=self.withdraw_origin+self.release_delta*withdraw; goal_r=self.withdraw_rotation
            elif phase in ('approach','close','regrasp_hold'):
                current_grasp=gp+gr.apply(self.grasp_G); current_rotation=gr*self.grasp_rotation_G
                if phase=='approach':
                    approach=smoothstep(time,*self.plan['approach'])
                    goal=self.approach_origin+(current_grasp-self.approach_origin)*approach
                    goal_r=Rotation.from_rotvec((current_rotation*self.approach_rotation.inv()).as_rotvec()*approach)*self.approach_rotation
                else:
                    approach=1.; goal=current_grasp; goal_r=current_rotation
                    close=smoothstep(time,*self.plan['close'])
                    start=self.phase_start26[12:] if phase=='close' else self.open
                    request[self.fingers]=start+(self.closed-start)*close
            if goal is not None:
                if s.steps==self.phase_start_step:
                    values=held[self.arm].copy(); trial=q.copy();trial[self.arm]=values;p,r=self.fk(trial)['L_Wrist']
                    fit=dict(position_error_m=float(np.linalg.norm(p-goal)),rotation_error_rad=float((goal_r.inv()*r).magnitude()),float64_position_error_m=None,float64_rotation_error_rad=None,nfev=0,strict_commands=True)
                else:
                    values,fit=solve_left(self.fk,q,self.arm,s.lower,s.upper,s.q_ref,goal,goal_r,held[self.arm])
                if not fit['strict_commands'] or fit['position_error_m']>.01 or fit['rotation_error_rad']>.05:
                    raise RuntimeError('유한 LH wrist IK/bounds/qref/principal hard gate')
                request[self.arm]=values
        boundary=s.steps==self.phase_start_step
        if boundary:request[self.left]=held[self.left]
        if boundary or phase=='gripped':
            assert np.array_equal(request[self.left],held[self.left])
        elif phase=='open':
            assert np.array_equal(request[self.arm],held[self.arm])
        elif phase in ('withdraw','released_hold','approach'):
            assert np.array_equal(request[self.fingers],self.open)
        elif phase=='regrasp_hold':
            assert np.array_equal(request[self.fingers],self.closed)
        lh=dict(stage=phase,phase_boundary_hold=boundary,boundary_hold=boundary,phase_ownership_exact=True,arm_indices105=self.arm.tolist(),finger_indices105=self.fingers.tolist(),
            phase_start_step=self.phase_start_step,phase_start_submitted26_rad=self.phase_start26.tolist(),
            phase_start_command_wrist_W_m=self.phase_start_p.tolist(),phase_start_command_wrist_xyzw=self.phase_start_r.as_quat().tolist(),
            opening_fraction=float(opening),withdraw_fraction=float(withdraw),approach_fraction=float(approach),close_fraction=float(close),
            finger_open_goal14_rad=self.open.tolist(),finger_closed_reference14_rad=self.closed.tolist(),
            actual10_wrist_G_m=self.grasp_G.tolist(),actual10_wrist_G_xyzw=self.grasp_rotation_G.as_quat().tolist(),
            goal_wrist_W_m=None if goal is None else goal.tolist(),goal_wrist_xyzw=None if goal_r is None else goal_r.as_quat().tolist(),
            source_IK_position_error_m=None if fit is None else fit['position_error_m'],source_IK_rotation_error_rad=None if fit is None else fit['rotation_error_rad'],IK=fit,
            release_start_step=getattr(self,'release_start_step',None),release_start_actual26_rad=None if not hasattr(self,'release_start_actual26') else self.release_start_actual26.tolist(),release_actual_origin_W_m=getattr(self,'release_actual_origin',np.zeros(3)).tolist(),
            release_actual_rotation_xyzw=getattr(self,'release_actual_rotation',Rotation.identity()).as_quat().tolist(),
            release_delta_W_m=getattr(self,'release_delta',np.zeros(3)).tolist(),
            withdraw_command_origin_W_m=getattr(self,'withdraw_origin',np.zeros(3)).tolist(),
            withdraw_command_rotation_xyzw=getattr(self,'withdraw_rotation',Rotation.identity()).as_quat().tolist(),
            current_G_grasp_W_m=(gp+gr.apply(self.grasp_G)).tolist(),current_G_grasp_xyzw=(gr*self.grasp_rotation_G).as_quat().tolist())
        active=next(((i,start) for i,start in enumerate(self.plan['strike_starts']) if start<=time<start+4.),None)
        request[self.distal]=held[self.distal]
        rh=dict(active=active is not None,stage='hold',cycle=None,start_s=None,local_time_s=None,pick_IK_error_m=None)
        if active is not None:
            cycle,start=active; local=10.+time-start
            if cycle!=self.cycle:
                self.cycle=cycle; self.cycle_start_step=s.steps; self.cycle_start6=held[self.distal].copy()
                pickW,_=self.command_pose(q,self.distal,held[self.distal],'RH:pick')
                self.cycle_initial_pick=gr.inv().apply(pickW-gp)
                if self.first_strike is None:
                    self.first_strike=start
                    _,pr=self.command_pose(q,self.distal,held[self.distal],'RH:palm');self.orientation_start=gr.inv()*pr
            fraction=smoothstep(time,self.first_strike,self.first_strike+.8)
            palm=Rotation.from_rotvec((self.final_palm*self.orientation_start.inv()).as_rotvec()*fraction)*self.orientation_start
            pick=pick_goal(local,self.cycle_initial_pick,np.array(self.right_spec['strike']['waypoints_G_m']))
            if s.steps==self.cycle_start_step:
                values=held[self.distal].copy();error64=0.;nfev=0
            else:
                fitted,error64,nfev=solve_pick_oriented(self.fk,q,self.distal,s.lower,s.upper,s.q_ref,gp+gr.apply(pick),gr*palm,held[self.distal]);values=fitted[self.distal].astype(np.float32).astype(float)
            trial=q.copy();trial[self.distal]=values;predicted=self.fk(trial);error=float(np.linalg.norm(predicted['RH:pick'][0]-(gp+gr.apply(pick))))
            if not command_gate(values,s.lower[self.distal],s.upper[self.distal],s.q_ref[self.distal]) or not np.isfinite(error) or error>.002:
                raise RuntimeError('유한 RH distal6 strict IK2mm gate')
            request[self.distal]=values
            rh=dict(active=True,stage='strike',cycle=cycle,start_s=float(start),local_time_s=float(local),
                cycle_start_step=self.cycle_start_step,cycle_start_submitted6_rad=self.cycle_start6.tolist(),cycle_initial_pick_G_m=self.cycle_initial_pick.tolist(),cycle_initial_pick_minus_reference10_G_m=(self.cycle_initial_pick-np.array(self.right_spec['initial_pick_G_m'])).tolist(),
                pick_goal_G_m=pick.tolist(),pick_IK_error_m=error,pick_IK_float64_error_m=error64,pick_IK_nfev=int(nfev),
                palm_goal_G_xyzw=palm.as_quat().tolist(),first_strike_s=self.first_strike,
                orientation_start_palm_G_xyzw=self.orientation_start.as_quat().tolist(),orientation_ramp_fraction=fraction,
                palm_soft_orientation_error_rad=float(((gr*palm).inv()*predicted['RH:palm'][1]).magnitude()))
        if active is None:assert np.array_equal(request[self.distal],held[self.distal])
        assert np.isfinite(request[self.arm]).all() and np.all(request[self.arm]>=s.lower[self.arm]) and np.all(request[self.arm]<=s.upper[self.arm])
        assert np.all(abs(request[self.arm]-s.q_ref[self.arm])<=.8) and np.all(np.linalg.norm(request[self.arm].reshape(4,3),axis=1)<np.deg2rad(160))
        lh['close_start_actual14_rad']=None if not hasattr(self,'close_start_actual14') else self.close_start_actual14.tolist()
        assert np.array_equal(request[self.proximal],self.right_spec['proximal_latch']['final6_rad'])
        allowed=set(self.left)|set(self.distal); other=[j for j in range(105) if j not in allowed]
        assert np.array_equal(request[other],original[other]) and np.all(request[self.fingers]>=s.lower[self.fingers]) and np.all(request[self.fingers]<=s.upper[self.fingers])
        assert s.native()==state
        lh.update(arm_requested12_rad=request[self.arm].tolist(),finger_requested14_rad=request[self.fingers].tolist())
        changed=np.flatnonzero(request!=original).tolist();self.stage=phase+('_strike' if active else '')
        self.info=dict(case=self.plan['case'],phase=phase,time_s=time,cycle=rh['cycle'],strike_start_s=rh['start_s'],local_strike_time_s=rh['local_time_s'],
            changed_indices105=changed,LH=lh,RH=rh,LH_phase_ownership_exact=True,RH_phase_ownership_exact=True,task_chain_FK=proof,other_base_request_channels_exact=True)
        return dict(zip(s.names,request.tolist()))

    def record_final(self,row):
        if not self.started:return
        request=np.array(row['requested105_rad']);final=np.array(row['final105_rad'])
        expected=np.array(self.right_spec['proximal_latch']['final6_rad'])
        assert np.array_equal(request[self.proximal],expected) and np.array_equal(final[self.proximal],expected)
        self.info.update(proximal_requested_latch_exact=True,proximal_submitted_latch_exact=True,
            final_LH26_rad=final[self.left].tolist(),final_RH6_rad=final[self.distal].tolist())
        row['ready']=self.info.copy()
