"""부모동작 후 LH fixed-e16 유지와 엄지 절대 보정; 실제 안정성 미검증."""
import copy
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from ..initial_pose_noise_v1 import pose
from guitar_learning.native.paths import read, save, sha
from ..grounded_guitar_release_v1.motion_v1 import smoothstep
from .motion_v1 import Motion as ParentMotion,solve_left

HAND_MODE='finite_gripped_actual16_fixed_error_thumb3_minus0p1_v1'
THUMB_DELTA=-.1
HAND_RAMP=[16.,16.5]
SELECTION_SHA='6391cceecac7e0476ce5e132ed7c8238981f4fb5a3f77a4d8a5838a9bac704b7'
REQUEST_SCOPE='postMotion_preFoot_preRate'


def failure_json(value):
    if isinstance(value,np.ndarray):return failure_json(value.tolist())
    if isinstance(value,np.generic):return failure_json(value.item())
    if isinstance(value,dict):return {k:failure_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [failure_json(v) for v in value]
    if isinstance(value,float) and not np.isfinite(value):return repr(value)
    return value


def arm_checks(values,scene,indices):
    return dict(finite=bool(np.isfinite(values).all()),
        native_bounds=bool(np.all(values>=scene.lower[indices]) and np.all(values<=scene.upper[indices])),
        qref0p8=bool(np.all(abs(values-scene.q_ref[indices])<=.8)),
        principal160=bool(np.all(np.linalg.norm(values.reshape(4,3),axis=1)<np.deg2rad(160))))


def fit_error(fk,q,indices,values,goal,rotation):
    trial=q.copy();trial[indices]=values;p,r=fk(trial)['L_Wrist']
    return dict(position_error_m=float(np.linalg.norm(p-goal)),
        rotation_error_rad=float((rotation.inv()*r).magnitude()))


class Motion(ParentMotion):
    def __init__(self,scene,fk):
        cfg=scene.cfg
        assert cfg['ready_hand_maintenance_mode']==HAND_MODE
        assert cfg['ready_hand_maintenance_thumb_delta_rad']==THUMB_DELTA
        assert cfg['ready_hand_maintenance_ramp_s']==HAND_RAMP
        selected=Path(cfg['ready_hand_maintenance_selection']).resolve()
        assert cfg['ready_hand_maintenance_selection_sha256']==SELECTION_SHA and sha(selected)==SELECTION_SHA
        result=read(selected)
        assert result['selected_delta_rad']==THUMB_DELTA and result['inputs_unchanged'] is True
        rows=[r for r in result['samples'] if r['requested_delta_rad']==THUMB_DELTA]
        assert len(rows)==8 and {(r['step'],r['route']) for r in rows}=={
            (k,n) for k in (3840,5532,6644,6720) for n in ('B_increment_float64','B_increment_armF32')}
        assert all(r['conditional_feasible'] is True and all(v is True for v in r['checks'].values()) for r in rows)
        assert result['actual_dynamic_tracking_validated'] is False and result['final_adoption_eligible'] is False
        super().__init__(scene,fk)
        self.thumb=scene.names.index('LH:thumb3');assert self.thumb==55 and self.thumb in self.fingers
        self.thumb_slot=self.fingers.tolist().index(self.thumb)
        for key,value in (('stiffness',20.),('damping',5.),('effort',4.)):
            assert float(scene.pd_properties[key][self.thumb])==value
        assert self.thumb in scene.position_indices and self.thumb not in scene.zero_indices
        self.fixed_left=np.array([i for i,n in enumerate(scene.names) if n.startswith('LH:') and i not in self.fingers])
        self.right_fingers=np.array([i for i,n in enumerate(scene.names) if n.startswith('RH:')])
        assert len(self.fixed_left)==7 and len(self.right_fingers)==21
        self.reference16=None;self.reference16_path=Path(cfg['attempt_out'])/'hand_maintenance_reference16.json'

    def fail(self,reason,parent,request,details):
        path=Path(self.s.cfg['attempt_out'])/('hand_maintenance_failure_step'+str(self.s.steps)+'.json')
        evidence=dict(reason=reason,physics_step_before=int(self.s.steps),time_s=self.s.steps/240,
            state=self.s.native(),reference16=self.reference16,parent_requested105_rad=parent.tolist(),
            requested105_rad=request.tolist(),request_scope=REQUEST_SCOPE,details=details)
        save(path,failure_json(evidence))
        raise RuntimeError('finite hand maintenance: '+reason)

    def latch16(self,state,held):
        assert self.s.steps==3840 and self.reference16 is None
        q=np.array([v['pos'] for v in state['human_dof_states']])
        gp,gr=pose(state['guitar_body_states'][0])
        wp,wr=pose(state['human_body_states'][self.s.human_bodies.index('L_Wrist')])
        self.reference16=dict(step=3840,time_s=16.,state=copy.deepcopy(state),actual105_rad=q.tolist(),
            last_submitted105_rad=held.tolist(),arm_indices105=self.arm.tolist(),
            actual_wrist_G_m=gr.inv().apply(wp-gp).tolist(),actual_wrist_G_xyzw=(gr.inv()*wr).as_quat().tolist(),
            e16_12_rad=(q[self.arm]-held[self.arm]).tolist(),
            scope='Separate actual16 reference; original actual10/spec/FK calibration unchanged. Fixed native scalar joint error, not world Euler.')
        assert np.isfinite(np.r_[q,held,self.reference16['e16_12_rad']]).all()
        save(self.reference16_path,self.reference16)

    def apply(self,named):
        original=np.array([named[n] for n in self.s.names])
        parent_named=super().apply(named)
        s=self.s;time=s.steps/240
        if s.steps<3840:return parent_named
        parent=np.array([parent_named[n] for n in s.names]);held=s.target.astype(float).copy();state=s.native()
        if s.steps==3840:
            self.latch16(state,held)
            return parent_named
        request=parent.copy();parent_info=copy.deepcopy(self.info)
        if self.reference16 is None:self.fail('missed actual16 reference',parent,request,{})
        q=np.array([v['pos'] for v in state['human_dof_states']])
        phase=parent_info['phase'];boundary=bool(parent_info['LH']['phase_boundary_hold'])
        assert boundary==(s.steps==self.phase_start_step)
        a=float(smoothstep(time,*HAND_RAMP));desired=desired_fit=command_fit=None
        raw_command=None;command_checks={};arm_control='parent_inherited';goal=goal_r=None
        if phase=='gripped' and not boundary:
            gp,gr=pose(state['guitar_body_states'][0])
            goal=gp+gr.apply(self.reference16['actual_wrist_G_m'])
            goal_r=gr*Rotation.from_quat(self.reference16['actual_wrist_G_xyzw'])
            try:
                desired,desired_fit=solve_left(self.fk,q,self.arm,s.lower,s.upper,s.q_ref,goal,goal_r,held[self.arm])
            except (AssertionError,ValueError,RuntimeError,FloatingPointError) as exc:
                self.fail('desired actual IK exception',parent,request,dict(error=repr(exc)))
            strict=arm_checks(desired,s,self.arm)
            strict.update(fit_finite=bool(np.isfinite([desired_fit['position_error_m'],desired_fit['rotation_error_rad']]).all()),
                position10um=bool(desired_fit['position_error_m']<1e-5),
                rotation0p01deg=bool(desired_fit['rotation_error_rad']<np.deg2rad(.01)),
                original_strict_commands=desired_fit['strict_commands'] is True)
            raw_command=desired-np.array(self.reference16['e16_12_rad'])
            command=raw_command.astype(np.float32).astype(float)
            command_checks=dict(desired_actual=strict,raw_command=arm_checks(raw_command,s,self.arm),
                F32_command=arm_checks(command,s,self.arm),
                F32_exact=bool(np.array_equal(command,command.astype(np.float32).astype(float))))
            request[self.arm]=command
            if not all(strict.values()) or not all(command_checks['raw_command'].values()) or not all(command_checks['F32_command'].values()):
                self.fail('strict desired fit or final command bounds',parent,request,
                    dict(desired_actual12_rad=desired.tolist(),desired_fit=desired_fit,
                        raw_command12_rad=raw_command.tolist(),command_checks=command_checks))
            command_fit=fit_error(self.fk,q,self.arm,command,goal,goal_r)
            arm_control='actual16_fixed_error'
        opening=float(parent_info['LH']['opening_fraction']);close=float(parent_info['LH']['close_fraction'])
        parent_thumb=float(parent[self.thumb]);nominal=parent_thumb;factor=0.
        if phase in ('gripped','regrasp_hold'):nominal=float(self.closed[self.thumb_slot]);factor=1.
        elif phase=='open':
            nominal=float(self.closed[self.thumb_slot]+(self.open[self.thumb_slot]-self.closed[self.thumb_slot])*opening)
            factor=1.-opening
        elif phase=='close':factor=close
        elif phase in ('withdraw','released_hold','approach'):nominal=float(self.open[self.thumb_slot])
        else:self.fail('unknown parent phase',parent,request,dict(phase=phase))
        raw_thumb=float(held[self.thumb] if boundary else nominal+THUMB_DELTA*a*factor)
        thumb=float(np.float32(raw_thumb))
        request[self.thumb]=thumb
        if arm_control=='parent_inherited':
            command_checks=dict(inherited_command=arm_checks(request[self.arm],s,self.arm),
                F32_exact=bool(np.array_equal(request[self.arm],request[self.arm].astype(np.float32).astype(float))))
        changed=np.r_[self.arm,self.thumb];other=np.setdiff1d(np.arange(105),changed)
        other_fingers=self.fingers[self.fingers!=self.thumb]
        invariants=dict(other92_exact=bool(np.array_equal(request[other],parent[other])),
            LH_other13_exact=bool(np.array_equal(request[other_fingers],parent[other_fingers])),
            fixed7_exact=bool(np.array_equal(request[self.fixed_left],parent[self.fixed_left])),
            RH_parent_exact=bool(np.array_equal(request[np.r_[self.distal,self.proximal,self.right_fingers]],parent[np.r_[self.distal,self.proximal,self.right_fingers]])),
            inherited_arm_exact=bool(phase=='gripped' and not boundary or np.array_equal(request[self.arm],parent[self.arm])),
            boundary_held26_exact=bool(not boundary or np.array_equal(request[self.left],held[self.left])),
            thumb_finite=bool(np.isfinite([raw_thumb,thumb]).all()),
            thumb_bounds=bool(s.lower[self.thumb]<=raw_thumb<=s.upper[self.thumb] and s.lower[self.thumb]<=thumb<=s.upper[self.thumb]),
            thumb_qref0p8=bool(abs(raw_thumb-s.q_ref[self.thumb])<=.8 and abs(thumb-s.q_ref[self.thumb])<=.8),
            thumb_principal160=bool(abs(raw_thumb)<np.deg2rad(160) and abs(thumb)<np.deg2rad(160)),
            state_preserved=s.native()==state)
        if arm_control=='parent_inherited':invariants['inherited_command_valid']=all(command_checks['inherited_command'].values()) and command_checks['F32_exact']
        if not all(invariants.values()):self.fail('ownership/thumb command/state invariant',parent,request,dict(invariants=invariants))
        lh=copy.deepcopy(parent_info['LH'])
        lh.update(arm_requested12_rad=request[self.arm].tolist(),finger_requested14_rad=request[self.fingers].tolist(),
            phase_ownership_exact=True,hand_maintenance_arm_control=arm_control)
        if arm_control=='actual16_fixed_error':
            lh.update(goal_wrist_W_m=goal.tolist(),goal_wrist_xyzw=goal_r.as_quat().tolist(),
                goal_role='desired_actual16_G_reference',IK=desired_fit,
                source_IK_position_error_m=desired_fit['position_error_m'],source_IK_rotation_error_rad=desired_fit['rotation_error_rad'])
        maintenance=dict(mode=HAND_MODE,physics_step_before=int(s.steps),time_s=time,phase=phase,boundary=boundary,
            reference16=dict(file=str(self.reference16_path),step=3840,
                actual_wrist_G_m=self.reference16['actual_wrist_G_m'],actual_wrist_G_xyzw=self.reference16['actual_wrist_G_xyzw'],
                last_submitted_arm12_rad=np.array(self.reference16['last_submitted105_rad'])[self.arm].tolist()),
            e16_12_rad=self.reference16['e16_12_rad'],parent_requested105_rad=parent.tolist(),requested105_rad=request.tolist(),
            request_scope=REQUEST_SCOPE,arm_control=arm_control,
            arm_indices105=self.arm.tolist(),finger_indices105=self.fingers.tolist(),
            other_LH13_indices105=other_fingers.tolist(),fixed_LH7_indices105=self.fixed_left.tolist(),RHfinger21_indices105=self.right_fingers.tolist(),
            desired_actual12_rad=None if desired is None else desired.tolist(),desired_fit=desired_fit,
            raw_command12_rad=None if raw_command is None else raw_command.tolist(),command12_rad=request[self.arm].tolist(),
            command_fit=command_fit,command_fit_role='FK of biased submitted-arm request; diagnostic, not desired-actual fit',command_checks=command_checks,
            thumb=dict(index105=self.thumb,parent_requested_rad=parent_thumb,nominal_reference_rad=nominal,
                raw_rad=raw_thumb,F32_rad=thumb,delta_rad=THUMB_DELTA,ramp_fraction=a,phase_factor=factor,
                absolute_offset_rad=0. if boundary else THUMB_DELTA*a*factor,boundary_held_exact=bool(not boundary or thumb==held[self.thumb])),
            invariants=invariants,other92_comparison_scope='Parent postMotion output vs child postMotion output outside arm12+thumb55',
            new_IK_called=arm_control=='actual16_fixed_error',parent_arm_IK_scope='inherited except gripped',
            actual_dynamic_tracking_validated=False,final_adoption_eligible=False)
        allowed=np.r_[self.left,self.distal];other_base=np.setdiff1d(np.arange(105),allowed)
        self.info=copy.deepcopy(parent_info)
        self.info.update(LH=lh,changed_indices105=np.flatnonzero(request!=original).tolist(),
            LH_phase_ownership_exact=all(invariants.values()),other_base_request_channels_exact=bool(np.array_equal(request[other_base],original[other_base])),
            parent_intermediate=dict(requested105_rad=parent.tolist(),ready=parent_info,request_scope=REQUEST_SCOPE),hand_maintenance=maintenance)
        return dict(zip(s.names,request.tolist()))

    def record_final(self,row):
        super().record_final(row)
        if self.s.steps<=3840:return
        ready=row['ready'];maintenance=ready['hand_maintenance']
        request=np.array(row['requested105_rad']);final=np.array(row['final105_rad'])
        expected=np.array(maintenance['requested105_rad'])
        assert np.array_equal(request[self.left],expected[self.left])
        assert np.array_equal(request[self.distal],expected[self.distal])
        maintenance.update(final_submitted_LH26_rad=final[self.left].tolist(),
            final_submitted_thumb_rad=float(final[self.thumb]),
            postFoot_requested_LH26_rad=request[self.left].tolist(),final_scope='Scene final after original foot/rate/F32 pipeline')
