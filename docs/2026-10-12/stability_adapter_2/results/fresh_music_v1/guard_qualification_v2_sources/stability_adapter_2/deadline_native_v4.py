"""825D stability-priority pilot with unchanged passive strap and physical control.

The frozen 820D parent remains unchanged. Only original route cable forces are
allowed, with exact per-call arguments during the physics owner's force window.
"""
import copy
from pathlib import Path
from unittest.mock import patch

import numpy as np

from . import deadline_native_v1 as old
from .strap import cable_forces
from .deadline_stability_reward_v1 import priority_reward
from . import deadline_native_v3 as previous

REST_LENGTH = 1.1018469719600776
STIFFNESS, DAMPING, MAX_TENSION = 6000., 120., 300.
GAMMA = 2**(-1/(60*10))
REWARD_FLOOR, REWARD_SCALE, FATAL_EXTRA = -8., .1, -1.
PROFILE = copy.deepcopy(old.PROFILE)
PROFILE.update(name='stability_priority_pilot_v1', reward_floor_per_control=REWARD_FLOOR,
    reward_scale=REWARD_SCALE, gamma=GAMMA, fatal_extra=FATAL_EXTRA,
    termination='fixed_horizon or finite abs(qdot)>50; invalid/API/fixed-body failure aborts',
    fatal_tail='current floor plus discounted remaining horizon floors plus extra -1')
PROFILE['continuous_per_second'].update(position_loss=-8., rotation_upper_loss=-4.)
PROFILE['stability_multiplier'] = 4.
PROFILE['velocity_safety_measurement_scope']='native actual state at 60Hz control endpoints; not all 240Hz subframes certified'


def settlement(raw_reward, remaining_ticks=0, finite_velocity_fatal=False):
    if not np.isfinite(raw_reward) or type(remaining_ticks) is not int or remaining_ticks<0:
        raise ValueError('finite reward/nonnegative integer remaining horizon required')
    if finite_velocity_fatal:
        tail=REWARD_FLOOR*GAMMA*(-np.expm1(remaining_ticks*np.log(GAMMA)))/(1-GAMMA)
        raw=REWARD_FLOOR+float(tail)+FATAL_EXTRA
        ledger={'current_floor':REWARD_FLOOR,'discounted_remaining_floor':float(tail),
                'fatal_extra':FATAL_EXTRA,'remaining_ticks':remaining_ticks,
                'replaced_raw_reward':float(raw_reward)}
    else:
        raw=max(REWARD_FLOOR,float(raw_reward))
        ledger={'unfloored_raw_reward':float(raw_reward),'floor_adjustment':raw-float(raw_reward)}
    return raw*REWARD_SCALE,raw,ledger


def route_law(points, velocities):
    points,velocities=np.asarray(points),np.asarray(velocities)
    if points.shape!=(13,3) or velocities.shape!=(13,3) or not np.isfinite(np.r_[points.ravel(),velocities.ravel()]).all():
        raise ValueError('13 finite actual route points and velocities required')
    forces,tension,length,rate=cable_forces(points,velocities,REST_LENGTH,STIFFNESS,DAMPING,MAX_TENSION)
    if not np.isfinite(forces).all() or not np.allclose(forces.sum(0),0.,atol=2e-10,rtol=0):
        raise AssertionError('strap reaction forces invalid')
    if not np.allclose(np.cross(points,forces).sum(0),0.,atol=2e-10,rtol=0):
        raise AssertionError('strap route net torque invalid')
    return forces,float(tension),float(length),float(rate)


def _xyz(value):
    return tuple(float(getattr(value,k)) for k in 'xyz')


class StrapForceGuard:
    """Forward all other APIs through the existing restrictive guard."""
    def __init__(self, guarded, owner):
        self.guarded,self.owner=guarded,owner
        self.pending=[]; self.window=False; self.allowed_calls=0

    def arm(self, expected):
        if self.window or not self.owner.integrating_control or not self.owner.strap_enabled:
            raise RuntimeError('strap force window outside owned physics')
        self.pending=list(expected); self.window=True

    def disarm(self):
        incomplete=bool(self.pending); self.window=False; self.pending=[]
        if incomplete: raise AssertionError('strap force submissions incomplete')

    def __getattr__(self,name):
        if name!='apply_body_force_at_pos': return getattr(self.guarded,name)
        def strap_only(*args,**kwargs):
            expected=self.pending[0] if self.pending else None
            actual=(args[0],args[1],_xyz(args[2]),_xyz(args[3]),args[4]) if len(args)==5 else None
            if kwargs or not self.window or not self.owner.integrating_control or actual!=expected:
                self.owner.forbidden_calls.append(name)
                raise RuntimeError('force call differs from actual original strap route')
            # Bypass only the old blanket force rejection; all other methods
            # continue to go through InitializationGuard.
            result=getattr(self.guarded.gym,name)(*args)
            if result is False: raise RuntimeError('native strap force rejected')
            self.pending.pop(0); self.allowed_calls+=1
            return result
        return strap_only


def _strap_scene_class(recording, enabled):
    Parent=old._scene_class(recording)
    class StrapDeadlineScene(Parent):
        def __init__(self,horizon):
            super().__init__(horizon)
            self.strap_enabled=bool(enabled)
            strap=self.config['strap']
            actual=(strap['stiffness_n_per_m'],strap['damping_n_s_per_m'],strap['max_tension_n'])
            if actual!=(STIFFNESS,DAMPING,MAX_TENSION): raise ValueError('original strap law changed')
            from .environment_guard_v2 import InitializationGuard
            from .capture_isaac_gym_initial import GraphicsGym
            if not isinstance(self.gym,GraphicsGym) or not isinstance(self.gym.gym,InitializationGuard):
                raise TypeError('expected GraphicsGym(InitializationGuard(native)) wrapper chain')
            self.gym.gym=StrapForceGuard(self.gym.gym,self)
            self.rest_length=REST_LENGTH
            if self.tension!=0.: raise AssertionError('initial applied cable tension must be zero')
            self.last_applied_at_physics_step=None
            self.last_applied_points=None; self.last_applied_forces=None
            self.last_applied_phase=None
            self.strap_latest=self.strap_state()
            if len(self.route_handles)!=13 or len(self.guide_indices)!=11:
                raise AssertionError('original strap native body mapping changed')
            self.strap_initial={'route_points_W_m':self.strap_latest['points'],
                'route_velocities_W_m_s':self.strap_latest['velocities'],
                'length_m':self.strap_latest['length_m'],'rest_length_m':REST_LENGTH,
                'slack_m':REST_LENGTH-self.strap_latest['length_m'],
                'calculated_tension_n':self.strap_latest['calculated_tension_n'],
                'last_applied_tension_n':self.tension,'last_applied_at_physics_step':None,
                'last_applied_phase':None,
                'enabled':self.strap_enabled,'guides':strap['guides'],
                'guide_indices':self.guide_indices,'route_handles':list(self.route_handles),
                'guide_body_names':[self.human_bodies[i] for i in self.guide_indices],
                'route_COM_local_m':[c.tolist() for c in self.route_com],
                'k_n_m':STIFFNESS,'c_n_s_m':DAMPING,'cap_n':MAX_TENSION}

        def strap_state(self):
            points,velocities=self.route()
            forces,tension,length,rate=route_law(points,velocities)
            return {'points':points.tolist(),'velocities':velocities.tolist(),'forces':forces.tolist(),
                'length_m':length,'length_rate_m_s':rate,'calculated_tension_n':tension,
                'current_enabled_calculated_tension_n':tension if self.strap_enabled else 0.,
                'last_applied_tension_n':self.tension,
                'last_applied_at_physics_step':self.last_applied_at_physics_step,
                'last_applied_points_W_m':self.last_applied_points,
                'last_applied_forces_W_n':self.last_applied_forces,
                'last_applied_phase':self.last_applied_phase,
                'last_applied_time_scope':'before integration of step k to k+1; value is calculated commanded cable tension, not sensor force'}

        def step_physics(self):
            if not self.integrating_control: raise RuntimeError('strap physics requires target owner')
            from .environment import gymapi
            self.strap_latest=self.strap_state()
            self.tension=self.strap_latest['current_enabled_calculated_tension_n']
            if self.strap_enabled:
                calls=[(self.env,handle,gymapi.Vec3(*force),gymapi.Vec3(*point),gymapi.ENV_SPACE)
                    for handle,force,point in zip(self.route_handles,self.strap_latest['forces'],self.strap_latest['points'])]
                expected=[(env,handle,_xyz(force),_xyz(point),space) for env,handle,force,point,space in calls]
                self.gym.arm(expected)
                try:
                    for call in calls: self.gym.apply_body_force_at_pos(*call)
                finally: self.gym.disarm()
                self.last_applied_points=copy.deepcopy(self.strap_latest['points'])
                self.last_applied_forces=copy.deepcopy(self.strap_latest['forces'])
            else:
                self.last_applied_points=None; self.last_applied_forces=None
            self.last_applied_at_physics_step=self.steps
            self.last_applied_phase='ON_passive_route' if self.strap_enabled else 'OFF_no_force'
            # Do not invoke LearningScene.step_physics: it unconditionally
            # clears tension and intentionally bypasses the legacy cable law.
            self.gym.simulate(self.sim); self.gym.fetch_results(self.sim,True)
            self.steps+=1
            if self.after_physics is not None: self.after_physics(self)
    return StrapDeadlineScene


def _recorder(scene, path):
    from .strap_trial_recording import StrapTrialRecording, draw_route, FONT
    from . import strap_trial_recording as module
    class StateLabelRecording(StrapTrialRecording):
        def capture(self):
            def labelled(raw,output,points,view,projection,depth,rest_length):
                from PIL import Image,ImageDraw,ImageFont
                if scene.strap_enabled:
                    counts=draw_route(raw,output,points,view,projection,depth,rest_length)
                else:
                    Image.open(raw).convert('RGB').save(output)
                    counts={'visible_samples':0,'occluded_samples':0}
                image=Image.open(output).convert('RGB'); draw=ImageDraw.Draw(image)
                draw.rectangle((12,80,680,120),fill=(15,15,15))
                draw.text((23,88),'STRAP ON: original passive cable' if scene.strap_enabled else
                    'STRAP OFF: route is measured, no cable forces applied',
                    font=ImageFont.truetype(str(FONT),18),fill='white')
                image.save(output)
                return counts
            with patch.object(module,'draw_route',labelled): super().capture()
    return StateLabelRecording(scene,path)


class NativeDeadlineEnvironment(old.NativeDeadlineEnvironment):
    obs_dim=825

    def __init__(self, strap_enabled=True, **kwargs):
        super().__init__(**kwargs)
        self.strap_enabled=bool(strap_enabled)
        self.safety_violation=None; self._in_parent_step=False; self.raw_return_total=0.

    def reset(self):
        self.close()
        recording,output=self.recording,self.output
        Scene=_strap_scene_class(recording,self.strap_enabled)
        self.safety_violation=None; self.raw_return_total=0.
        # Parent handles exact initial physics and frozen baselines; the new
        # recorder/initial metadata are installed only after that reset ends.
        self.recording=False; self.output=None
        try:
            with patch.object(old,'_scene_class',return_value=Scene): observation=super().reset()
        finally:
            self.recording=recording; self.output=output
        self.metadata.update(profile=PROFILE,strap_enabled=self.strap_enabled,
            strap_initial=self.scene.strap_initial,
            prefix820_scope='same frozen v1 meaning/order; extra5 current passive-route measurements')
        if recording:
            self.measurement.samples=list(self.measurement.samples)
            self.trace=[]; self._sample()
        if output:
            self.run_output=Path(output)/('episode_%04d'%self.episode)
            self.run_output.mkdir(parents=True,exist_ok=False)
            old._save(self.run_output/'initial_values.json',{'native_initial_state':self.initial,
                'joint_names':self.scene.names,'q_ref_rad':self.scene.contract.q_ref.tolist(),
                'preload':self.preload_record,'metadata':self.metadata,
                'PD_properties':{k:self.scene.pd_properties[k].tolist() for k in self.scene.pd_properties.dtype.names}})
        if recording:
            self.recorder=_recorder(self.scene,self.run_output/'media'); self.recorder.capture()
        return observation

    def _observe(self, physical):
        observation=super()._observe(physical)
        self.legacy_observation_manifest=copy.deepcopy(self.observation_manifest)
        state=self.scene.strap_state()
        extra=np.array([float(self.strap_enabled),state['length_m'],REST_LENGTH,
            state['length_rate_m_s'],state['current_enabled_calculated_tension_n']/MAX_TENSION],dtype=np.float32)
        self.observation_manifest={'version':'strap_fallback825_v3','dimension':825,
            'blocks':self.legacy_observation_manifest['blocks']+[{'name':'strap_actual_route_state',
                'offset':820,'length':5,'fields':['enabled','L_m','L0_m','Ldot_m_s','current_enabled_calculated_T_div_300N']}],
            'physical_manifest':self.legacy_observation_manifest['physical_manifest'],'teacher_action_inputs':True}
        return np.r_[observation,extra].astype(np.float32)

    def legacy_abi(self):
        abi=old.NativeDeadlineEnvironment.abi(self)
        abi['observation']=copy.deepcopy(self.legacy_observation_manifest)
        return abi

    old_input_abi=legacy_abi

    def abi(self):
        abi=self.legacy_abi()
        abi.update(version='stability_priority825_v1',profile=PROFILE,observation=self.observation_manifest,
            action_dimension=81,strap_enabled=self.strap_enabled,
            strap={'rest_length_m':REST_LENGTH,'stiffness_n_per_m':STIFFNESS,
                'damping_n_s_per_m':DAMPING,'max_tension_n':MAX_TENSION,
                'route_points':13,'law':'original tension-only route; exact-argument owner guard'})
        return abi

    def previous_reward_abi(self):
        abi=self.abi()
        abi.update(version='strap_fallback825_v3',profile=previous.PROFILE)
        return abi

    def require_training_ready(self):
        if self._finished: raise RuntimeError('physical episode terminated; reset required before another step')
        if not self._ready or self.metadata.get('profile',{}).get('name')!='stability_priority_pilot_v1':
            raise RuntimeError('explicit strap fallback measured pilot reset required')

    def _sample(self):
        from .run_joint_hold import native_state
        state=native_state(self.scene)
        if any(state['human_body_states'][i]!=self.initial['human_body_states'][i] for i in self.fixed):
            raise AssertionError('fixed root/lower body changed')
        q=np.array([r['pos'] for r in state['human_dof_states']])
        qdot=np.array([r['vel'] for r in state['human_dof_states']])
        pose=state['guitar_body_states'][0]['pose']
        p=np.array([pose['p'][k] for k in 'xyz']); quat=np.array([pose['r'][k] for k in 'xyzw'])
        if not np.isfinite(np.r_[q,qdot,p,quat]).all(): raise ValueError('nonfinite native state: transition excluded')
        bad=np.flatnonzero(np.abs(qdot)>50)
        if len(bad):
            self.safety_violation={'type':'finite_joint_velocity_limit','physics_step':self.scene.steps,
                'threshold_rad_s':50.,'joints':[{'index':int(i),'name':self.scene.names[i],
                    'q_rad':float(q[i]),'qdot_rad_s':float(qdot[i])} for i in bad]}
        if self.scene.forbidden_calls: raise AssertionError('forbidden native API')
        if self.recording:
            self.trace.append({'physics_step':self.scene.steps,'position_W_m':p.tolist(),
                'quaternion_xyzw':quat.tolist(),'q_rad':q.tolist(),'qdot_rad_s':qdot.tolist(),
                'strap':self.scene.strap_state(),'safety_violation':self.safety_violation})
        return q,p,quat

    def _nominal(self):
        if self.safety_violation is not None: return self.nominal
        return super()._nominal()

    def step(self,action):
        self._in_parent_step=True
        try:
            with patch.object(old,'pilot_reward',priority_reward):
                observation,raw_before,terminated,truncated,info=super().step(action)
        finally: self._in_parent_step=False
        fatal=self.safety_violation is not None
        scaled,raw,ledger=settlement(raw_before,max(0,self.horizon_ticks-self.tick),fatal)
        self.return_total+=scaled-raw_before; self.raw_return_total+=raw
        self.last_step.update(unfloored_raw_reward=raw_before,raw_reward=raw,scaled_reward=scaled,
            reward=scaled,reward_settlement=ledger,safety_violation=self.safety_violation,
            strap=self.scene.strap_state())
        self.last_step['raw_component_ledger']=self.last_step['ledger']
        info.update(pilot_profile=PROFILE['name'],reward_raw=raw,reward_scaled=scaled,
            reward_settlement=ledger,safety_violation=self.safety_violation)
        self.last_info=info
        if terminated or fatal: self._finish('finite_joint_velocity_safety' if fatal else 'planned_full_song_horizon')
        return observation,scaled,bool(terminated or fatal),False,info

    def _finish(self,reason):
        if self._in_parent_step or self._finished or self.scene is None: return
        self._finished=True
        frozen=all(old.torch_equal(v,self.frozen[i][k]) for i,m in enumerate((self.fm,self.sm))
            for k,v in m.state_dict().items())
        if not frozen: raise AssertionError('baseline weights changed')
        music=self.measurement.music
        report={'stop_reason':reason,'full_horizon_completed':self.tick==self.horizon_ticks and self.safety_violation is None,
            'physics_steps':self.scene.steps,'control_steps':self.tick,'physics_seconds':self.scene.steps/240,
            'return':self.return_total,'raw_return':self.raw_return_total,'reward_scale':REWARD_SCALE,
            'baseline_actor_calls':self.actor_calls,'baseline_weights_unchanged':frozen,
            'source_done_diagnostic_counts':self.source_done_counts,'settled_events':len(music.results),
            'joint_success_events':sum(r['joint_success'] for r in music.results),
            'accepted_crossings':sum(r['accepted'] for r in music.crossings),
            'profile':PROFILE,'production_training_certified':False,
            'forbidden_calls':list(self.scene.forbidden_calls),'strap_enabled':self.strap_enabled,
            'strap_initial':self.scene.strap_initial,'strap_final':self.scene.strap_state(),
            'strap_force_calls':self.scene.gym.allowed_calls,'safety_violation':self.safety_violation}
        # Preserve raw evidence before any final capture/encoder can fail.
        if self.output:
            old._save(self.run_output/'raw_report.json',report)
            if self.recording:
                for filename,value in (('controls.json',self.rows),('trace.json',self.trace),
                    ('joint_crossings.json',music.crossings),('joint_events.json',music.results),
                    ('music_physics_samples.json',self.measurement.samples)):
                    old._save(self.run_output/filename,value)
        media_error=None; videos={}
        try:
            if self.recorder:
                if not self.recorder.frames or self.recorder.frames[-1]['physics_step']!=self.scene.steps:
                    self.recorder.capture()
                videos=self.recorder.encode()
        except BaseException as error:
            media_error={'type':type(error).__name__,'message':str(error)}
        report=dict(report,videos=videos,media_error=media_error)
        self.last_report=report; self.episode_reports.append(report)
        if self.output: old._save(self.run_output/'report.json',report)
        if media_error: raise RuntimeError('raw native data preserved; media failed: '+str(media_error))

    def close(self):
        try: super().close()
        except BaseException as error:
            if self.output and hasattr(self,'run_output') and self.run_output.is_dir():
                path=self.run_output/'close_error.json'
                if not path.exists(): old._save(path,{'type':type(error).__name__,'message':str(error)})
            raise
