"""Explicit deadline pilot: real native physics, frozen pair, 81 target owner.

This is not reward-v4 certification. Native imports are deferred until reset;
Isaac must load before Torch. Source done flags remain diagnostics only.
"""
import hashlib
import json
from collections import deque
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT/'data/song_bundles/02_Jazz1-200-B_solo'
FCP = ROOT/'fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt'
SCP = ROOT/'strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt'
HORIZON_SECONDS = 2 + 861/60 + 1/60
PROFILE = {
    'name': 'deadline_pilot_v1', 'production_reward_v4_certified': False,
    'continuous_per_second': {'position_loss': -2., 'rotation_upper_loss': -1.,
        'sounding_match': .6, 'fret_approach': .15, 'pick_approach': .15,
        'body_loss': -.1, 'target_rate_loss': -.01},
    'per_actual_crossing': {'accepted': 1., 'wrong_in_play': -.25},
    'per_fixed_event_deadline': {'joint_success': 1., 'miss_or_error': -.5},
    'position_huber_scale_m': .05, 'rotation_huber_scale_rad': .15,
    'approach_exponential_scale_m': .04,
    'unimplemented_production_terms': ['gaze', 'continuous_hold_dropout_ledger',
        'distal_press_pad_certification', 'fatal_scheduled_tail',
        'certified_exact_SO3_outside_distance', 'collision_force_reward'],
    'termination': 'fixed_song_horizon_only; measurement_or_safety_error_aborts_transition',
    'physical_safety': 'finite states, fixed lower exact, abs(qdot)<=50rad/s, no forbidden APIs',
}


def _save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def anchored_target(action, anchor, lower, upper):
    """Zero follows current baseline; endpoints retain full effective authority."""
    action, anchor, lower, upper = [np.asarray(v, dtype=float) for v in (action, anchor, lower, upper)]
    if any(v.shape != (81,) or not np.isfinite(v).all() for v in (action, anchor, lower, upper)):
        raise ValueError('finite 81-channel codec inputs required')
    if np.any(np.abs(action)>1) or np.any(anchor<lower) or np.any(anchor>upper) or np.any(lower>=upper):
        raise ValueError('codec bounds violated')
    return anchor + np.where(action>=0, upper-anchor, anchor-lower)*action


def pilot_reward(position_outside, rotation_upper, sounding_match, fret_approach,
                 pick_approach, body_excess, target_rate, accepted, wrong, success, miss,
                 music_active):
    """Measured continuous rates integrate at 60Hz; event pulses pay once."""
    values = np.r_[position_outside, rotation_upper, sounding_match, fret_approach,
                   pick_approach, body_excess, target_rate, accepted, wrong, success, miss]
    if not np.isfinite(values).all():
        raise ValueError('reward measurement invalid')
    def huber(v):
        v=np.abs(np.asarray(v)); return np.where(v<=1., .5*v*v, v-.5)
    ledger = {
        'position': -2.*float(huber(np.asarray(position_outside)/.05).sum())/60,
        'rotation_upper_proxy': -float(huber(rotation_upper/.15))/60,
        'body': -.1*float(huber(np.asarray(body_excess)/np.deg2rad(5)).mean())/60,
        'target_rate': -.01*float(np.mean(np.square(target_rate)))/60,
        'sounding': .6*float(sounding_match)/60 if music_active else 0.,
        'fret_approach': .15*float(fret_approach)/60 if music_active else 0.,
        'pick_approach': .15*float(pick_approach)/60 if music_active else 0.,
        'actual_crossings': float(accepted)-.25*float(wrong),
        'fixed_event_deadlines': float(success)-.5*float(miss),
    }
    return float(sum(ledger.values())), ledger


def _scene_class(recording):
    from .dual_music_scene_v1 import DualMusicScene
    from .self_collision_environment import SelfCollisionEnvironment
    if recording:
        return DualMusicScene
    class HeadlessDeadlineScene(DualMusicScene):
        def _create_scene(self):
            candidate=self.contract.candidate
            self.goal_position=np.array(candidate['position_W_m'])
            x,y,z,w=candidate['quaternion_xyzw']
            self.pose['params']['guitar_quat_wxyz_computed']=[w,x,y,z]
            SelfCollisionEnvironment._create_scene(self)
            self.initial_q=self.contract.q_ref.astype(np.float32)
            props=self.gym.get_actor_dof_properties(self.env,self.human)
            props['stiffness'][self.torso_indices]*=self.contract.config['body_kp_scale']
            props['damping'][self.torso_indices]*=self.contract.config['body_kd_scale']
            if not self.gym.set_actor_dof_properties(self.env,self.human,props):
                raise RuntimeError('POSITION properties rejected')
    return HeadlessDeadlineScene


class NativeDeadlineEnvironment:
    obs_dim, action_dim = 820, 81

    def __init__(self, recording=False, output=None, seed=42, baseline_device='cpu'):
        if baseline_device != 'cpu':
            raise ValueError('copied baseline views use CPU; joint policy device is independent')
        if recording and output is None:
            raise ValueError('recording requires fresh output path')
        self.recording, self.output, self.seed = bool(recording), Path(output) if output else None, int(seed)
        self.scene=None; self.recorder=None; self.last_report=None; self.metadata={}
        self.episode_reports=[]; self.last_info=None
        self.episode=0; self._finished=False; self._ready=False

    def reset(self):
        self.close()
        Scene=_scene_class(self.recording)  # Isaac is imported before Torch.
        from .dual_music_clock_v1 import JointMusicClock
        from .joint_learning_observation_v1 import JointMusicMeasurement
        from .dual_music_scene_v1 import preload_targets
        from .deadline_rotation_v3 import RotationEnvelope
        from .run_joint_hold import native_state
        from .build_fixed_lower_asset import LOWER_BODIES
        from tab2body.learning.fret_v2_model import FretV2ActorCritic
        from tab2body.learning.strike_v2_model import StrikeV2ActorCritic
        from tab2body.tools.fret_rollout_contract import verify_rollout_model
        import torch
        music=JointMusicClock()
        dense=json.loads((BUNDLE/'training/fret_training.json').read_text())
        self.horizon=2+max(len(dense['frames'])/60,music.events[-1].traversal_end_time_s+.05)+1/60
        self.horizon_ticks=int(round(self.horizon*60))
        self.scene=Scene(self.horizon)
        self._finished=False; self._ready=False; self.tick=0; self.episode+=1
        self.rows=[]; self.trace=[]; self.return_total=0.; self.source_done_counts={'Fret':0,'Strike':0}
        self.initial=native_state(self.scene)
        if self.initial!=self.scene.contract.reference['native_initial_state']:
            raise AssertionError('initial native state differs from reference')
        self.fixed=[self.scene.human_bodies.index(n) for n in ('Pelvis',)+LOWER_BODIES]
        self.preload,self.preload_record=preload_targets(self.scene.contract,1.)
        self.measurement=JointMusicMeasurement(self.scene)
        if not self.recording: self.measurement.samples=deque(maxlen=1)
        self.fret,self.strike=self.measurement.fret,self.measurement.strike
        fc=torch.load(FCP,map_location='cpu',weights_only=True)
        sc=torch.load(SCP,map_location='cpu',weights_only=True)
        fp=fc['checkpoint_contract']['payload']; sp=sc['checkpoint_contract']['payload']
        self.baseline_contract_sha=[fc['checkpoint_contract']['sha256'],sc['checkpoint_contract']['sha256']]
        self.fm=FretV2ActorCritic(420,30,value_dim=6,init_std=fp['model']['policy_init_std'])
        verify_rollout_model(self.fret,self.fm,fp)
        self.sm=StrikeV2ActorCritic(303,30,value_dim=1,init_std=sp['model']['policy_init_std'])
        self.fm.load_state_dict(fc['model'],strict=True); self.sm.load_state_dict(sc['model'],strict=True)
        for model in (self.fm,self.sm): model.eval(); model.requires_grad_(False)
        self.frozen=[{k:v.clone() for k,v in m.state_dict().items()} for m in (self.fm,self.sm)]
        self.fidx,self.sidx=self.fret.ctrl_idx.numpy(),self.strike.ctrl_idx.numpy()
        if len(self.fidx)!=30 or len(self.sidx)!=30 or set(self.fidx)&set(self.sidx):
            raise AssertionError('baseline ownership invalid')
        self.rotation=RotationEnvelope(); self.cross_count=0; self.event_count=0
        self.actor_calls={'Fret':0,'Strike':0}; self.started=False
        self.nominal=self._nominal()
        observation=self._observe(self.scene.observe())
        self.metadata={'profile':PROFILE,'observation':self.observation_manifest,
            'inputs':self.measurement.inputs,'horizon_s':self.horizon,
            'baseline_qualification':'diagnostic_unqualified_registered_pair',
            'root_lower_fixed':True,'strap_enabled':False,'physical_backend':'CPU PhysX',
            'source_velocity_scope':'baseline ABI copied COM; physical observation corrects body origin',
            'initial_state_exact_reference':True}
        self._ready=True
        if self.output:
            self.run_output=self.output/('episode_%04d'%self.episode)
            self.run_output.mkdir(parents=True,exist_ok=False)
            _save(self.run_output/'initial_values.json',{'native_initial_state':self.initial,
                'joint_names':self.scene.names,'q_ref_rad':self.scene.contract.q_ref.tolist(),
                'preload':self.preload_record,'PD_properties':{k:self.scene.pd_properties[k].tolist()
                    for k in self.scene.pd_properties.dtype.names},'metadata':self.metadata})
        if self.recording:
            from .gym_trial_recording import GymTrialRecording
            self.recorder=GymTrialRecording(self.scene,self.run_output/'media')
            self.recorder.capture()
        self._sample()
        return observation

    def abi(self):
        if not self._ready: raise RuntimeError('reset required for actual ABI')
        c=self.scene.contract
        return {'version':'deadline_native820_v1','profile':PROFILE,'observation':self.observation_manifest,
            'names':c.names,'groups':c.groups,'lower':c.effective_lower.tolist(),
            'upper':c.effective_upper.tolist(),'rates':c.rates.tolist(),
            'action_codec':'dynamic_absolute_anchor_zero=baseline; +/-1=effective endpoints; single rate owner',
            'inputs':dict(c.inputs,**self.measurement.inputs),'horizon_s':self.horizon,
            'control_hz':60,'physics_hz':240,'baseline_contract_sha256':self.baseline_contract_sha}

    def require_training_ready(self):
        if not self._ready or self.metadata.get('profile',{}).get('name')!='deadline_pilot_v1':
            raise RuntimeError('explicit measured pilot reset required; production gate remains closed')

    def _nominal(self):
        import torch
        from .strike_preparation_handoff import seed_source_history
        self.measurement.refresh()
        desired=self.preload.copy()
        if self.tick<120:
            self.fret.preparation_remaining.fill_(120-self.tick)
            self.strike.song_time_s.fill_(self.tick/60-2)
            self.action_phase=None
            return desired
        frame=self.tick-120
        if not self.started:
            self.fret.preparation_remaining.zero_(); self.fret.progress_buf.zero_()
            self.strike.progress_buf.zero_(); seed_source_history(self.strike,self.scene.target)
            self.started=True
        self.fret.goals.frame_idx.fill_(min(frame,self.fret.goals.n_frames-1))
        self.strike.song_time_s.fill_(frame/60)
        fo,so=self.fret.strict_observation(),self.strike.strict_observation()
        if fo.shape!=(1,420) or so.shape!=(1,303): raise AssertionError('baseline observation changed')
        with torch.no_grad():
            fa=self.fm.act(fo,deterministic=True)[0]
            sa=self.sm.act(so,deterministic=True)[0]
        if not torch.isfinite(fa).all() or not torch.isfinite(sa).all():
            raise ValueError('nonfinite baseline action')
        self.fret.cache_policy_actions(fa); self.strike.apply_actions(sa)
        for view,idx in ((self.fret,self.fidx),(self.strike,self.sidx)):
            c=self.scene.contract
            lo=np.maximum(c.effective_lower[idx],view.ctrl_lo.numpy()[0])
            hi=np.minimum(c.effective_upper[idx],view.ctrl_hi.numpy()[0])
            if np.any(lo>hi): raise ValueError('empty source/native intersection')
            desired[idx]=np.clip(view.pd_target.numpy()[idx],lo,hi)
        self.action_phase=self.strike.motor_phase.clone()
        for key in self.actor_calls: self.actor_calls[key]+=1
        self.last_source_actions={'Fret':fa[0].tolist(),'Strike':sa[0].tolist()}
        return desired

    def _observe(self, physical):
        observation,manifest=self.measurement.observe(physical)
        nominal=self.scene.contract.normalized_native(self.nominal).astype(np.float32)
        observation=np.r_[observation,nominal].astype(np.float32)
        if observation.shape!=(820,) or not np.isfinite(observation).all():
            raise ValueError('finite measured 820 observation required')
        self.observation_manifest={'version':'deadline_native820_v1','dimension':820,
            'blocks':manifest['blocks']+[{'name':'current_nominal_target','offset':739,'length':81,
                'scale':'native normalized','future_actual_outcome_inputs':False}],
            'physical_manifest':manifest['physical_manifest'],'teacher_action_inputs':True}
        return observation

    def _sample(self):
        from .run_joint_hold import native_state
        state=native_state(self.scene)
        if any(state['human_body_states'][i]!=self.initial['human_body_states'][i] for i in self.fixed):
            raise AssertionError('fixed root/lower body changed')
        q=np.array([r['pos'] for r in state['human_dof_states']])
        qdot=np.array([r['vel'] for r in state['human_dof_states']])
        p=state['guitar_body_states'][0]['pose']['p']; r=state['guitar_body_states'][0]['pose']['r']
        p=np.array([p[k] for k in 'xyz']); quat=np.array([r[k] for k in 'xyzw'])
        if not np.isfinite(np.r_[q,qdot,p,quat]).all() or np.max(np.abs(qdot))>50:
            raise ValueError('unsafe/nonfinite native state: transition excluded')
        if self.scene.forbidden_calls: raise AssertionError('forbidden native API')
        row={'physics_step':self.scene.steps,'position_W_m':p.tolist(),
            'quaternion_xyzw':quat.tolist(),'q_rad':q.tolist(),'qdot_rad_s':qdot.tolist()}
        if self.recording: self.trace.append(row)
        return q,p,quat

    def _approach(self):
        import torch
        fret=self.fret; rf=fret.reward_fn; goal=fret.goals.current()
        p0,p1,direction,lo,hi,approaches,outward=rf._string_and_fret_geometry()
        points=rf._finger_points()
        starts,ends=points[:,:,:-1],points[:,:,1:]
        samples=starts[:,:,:,None]+rf._sample_alpha*(ends-starts)[:,:,:,None]
        fret_idx=goal['fret'].long().clamp(1,22)-1
        target=torch.gather(approaches,2,fret_idx[...,None,None].expand(-1,-1,1,3)).squeeze(2)
        distance=rf._approach_distance(samples,target,outward,
            goal['finger'].long().clamp(1,4)-1,goal['barre'])
        active=(goal['fret']>0)[0]
        fq=float(torch.exp(-distance[0,active]/.04).mean()) if bool(active.any()) else 0.
        _,_,_,ready,entry,exit_point,_=self.strike._current_target_geometry()
        from tab2body.env.tasks.task_strike import PHASE_APPROACH,PHASE_RELEASE_RECOVER
        phase=int(self.strike.motor_phase[0])
        target=ready if phase==PHASE_APPROACH else exit_point if phase==PHASE_RELEASE_RECOVER else entry
        tip=self.strike.to_guitar_frame(self.strike.hbody_pos('RH:pick')[:,None])[:,0]
        distance=float(torch.linalg.vector_norm(tip-target,dim=-1)[0])
        return fq,float(np.exp(-distance/.04)),distance

    def step(self, action):
        self.require_training_ready()
        if self.tick>=self.horizon_ticks: raise RuntimeError('episode finished; reset required')
        import torch
        c=self.scene.contract
        nominal=self.nominal.copy(); old_target=self.scene.target.copy()
        desired=anchored_target(action,nominal,c.effective_lower,c.effective_upper)
        owner_action=np.clip((desired-c.mid)/c.half,-1.,1.)
        physical,info=self.scene.step(owner_action)
        self.measurement.refresh()
        history={}
        for label,view,idx in (('Fret',self.fret,self.fidx),('Strike',self.strike,self.sidx)):
            view.pd_target.copy_(torch.tensor(self.scene.target.copy()))
            view.prev_action.copy_(view.actions_for_pd_targets(view.pd_target[idx][None]))
            reconstructed=(view.ctrl_mid+view.action_scale*view.prev_action*view.ctrl_half).clamp(view.ctrl_lo,view.ctrl_hi)
            history[label]=float((reconstructed[0]-view.pd_target[idx]).abs().max())
        source_done={'Fret':False,'Strike':False}
        if self.tick>=120:
            self.fret.progress_buf+=1; self.strike.progress_buf+=1
            _,_,fd,_=self.fret.evaluate_after_physics()
            _,_,sd,_=self.strike.evaluate_after_physics(self.action_phase)
            source_done={'Fret':bool(fd[0]),'Strike':bool(sd[0])}
            for key in source_done: self.source_done_counts[key]+=int(source_done[key])
        q,p,quat=self._sample()
        low=np.array([-.50,-.15,.65]); high=np.array([-.15,.15,self.scene.z_chest])
        outside=np.maximum(low-p,0)+np.maximum(p-high,0)
        rotation=self.rotation.distance(quat)
        music=self.measurement.music; target=music.targets(); mask=target>=0
        match=float(np.mean(self.measurement.sounding[mask]==target[mask])) if mask.any() else 0.
        fq,kq,kdist=self._approach()
        crossings=music.crossings[self.cross_count:]; events=music.results[self.event_count:]
        accepted=sum(bool(r['accepted']) for r in crossings)
        wrong=sum(not r['accepted'] and r['score_time_s']>=0 for r in crossings)
        success=sum(bool(r['joint_success']) for r in events); miss=len(events)-success
        self.cross_count=len(music.crossings); self.event_count=len(music.results)
        body_excess=np.maximum(np.abs(q[c.body]-c.q_ref[c.body])-np.deg2rad(2),0)
        rate=(self.scene.target-old_target)/(c.rates*c.dt)
        reward,ledger=pilot_reward(outside,rotation['upper_rad'],match,fq,kq,body_excess,
            rate,accepted,wrong,success,miss,self.tick>=120)
        self.return_total+=reward
        row={'control_tick':self.tick,'physics_step':self.scene.steps,'reward':reward,
            'ledger':ledger,'position_outside_m':outside.tolist(),'rotation':rotation,
            'sounding_match':match,'fret_approach_quality':fq,'pick_approach_quality':kq,
            'pick_target_distance_G_m':kdist,'source_done_diagnostic':source_done,
            'source_history_max_reconstruction_error_rad':history,
            'nominal81_rad':nominal.tolist(),'policy_action81':np.asarray(action).tolist(),
            'requested81_rad':desired.tolist(),'final81_rad':self.scene.target.tolist()}
        if self.recording: self.rows.append(row)
        self.last_step=row; self.tick+=1
        terminated=self.tick>=self.horizon_ticks
        self.nominal=self._nominal() if not terminated else self.nominal
        observation=self._observe(physical)
        info.update(pilot_ledger=ledger,source_done_diagnostic=source_done,training_ready=True,
            pilot_profile=PROFILE['name'],actual_crossings=accepted,settled_events=len(events))
        self.last_info=info
        if self.recorder and self.scene.steps%8==0: self.recorder.capture()
        if terminated: self._finish('planned_full_song_horizon')
        return observation,reward,terminated,False,info

    def _finish(self, reason):
        if self._finished or self.scene is None: return
        self._finished=True
        frozen=all(torch_equal(v,self.frozen[i][k]) for i,m in enumerate((self.fm,self.sm))
            for k,v in m.state_dict().items())
        if not frozen: raise AssertionError('baseline weights changed')
        videos={}
        if self.recorder:
            if not self.recorder.frames or self.recorder.frames[-1]['physics_step']!=self.scene.steps:
                self.recorder.capture()
            videos=self.recorder.encode()
        music=self.measurement.music
        self.last_report={'stop_reason':reason,'full_horizon_completed':self.tick==self.horizon_ticks,
            'physics_steps':self.scene.steps,'control_steps':self.tick,'physics_seconds':self.scene.steps/240,
            'return':self.return_total,'baseline_actor_calls':self.actor_calls,
            'baseline_weights_unchanged':frozen,'source_done_diagnostic_counts':self.source_done_counts,
            'settled_events':len(music.results),'joint_success_events':sum(r['joint_success'] for r in music.results),
            'accepted_crossings':sum(r['accepted'] for r in music.crossings),'videos':videos,
            'profile':PROFILE,'production_training_certified':False,
            'forbidden_calls':list(self.scene.forbidden_calls)}
        self.episode_reports.append(self.last_report)
        if self.output:
            _save(self.run_output/'report.json',self.last_report)
            if self.recording:
                _save(self.run_output/'controls.json',self.rows); _save(self.run_output/'trace.json',self.trace)
                _save(self.run_output/'joint_crossings.json',music.crossings)
                _save(self.run_output/'joint_events.json',music.results)
                _save(self.run_output/'music_physics_samples.json',self.measurement.samples)

    def close(self):
        if self.scene is not None:
            try:
                if self._ready: self._finish('closed_partial_episode')
            finally:
                self.scene.close(); self.scene=None; self.recorder=None; self._ready=False


def torch_equal(first, second):
    import torch
    return torch.equal(first,second)
