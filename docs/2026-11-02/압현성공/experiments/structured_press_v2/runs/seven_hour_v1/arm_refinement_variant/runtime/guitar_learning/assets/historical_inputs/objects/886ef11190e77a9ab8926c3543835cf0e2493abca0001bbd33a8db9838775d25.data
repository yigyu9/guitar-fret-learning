"""Preload comparisons and coupled frozen Fret/Strike on one free-guitar scene."""
import argparse
import hashlib
import json
from pathlib import Path
import traceback
import copy
from unittest.mock import patch


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p,v):
    with Path(p).open('x') as f: json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def plain(x):
    import torch
    if isinstance(x,torch.Tensor):return x.detach().cpu().tolist()
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [plain(v) for v in x]
    return x


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--mode',choices=('preload','pair'),required=True)
    parser.add_argument('--factor',type=float,choices=(0.,.5,1.),required=True)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(exist_ok=False,parents=True)
    from .dual_music_scene_v1 import DualMusicScene,preload_targets,BASE
    from .dual_music_clock_v1 import JointMusicClock,BUNDLE
    from .dual_music_observation_v1 import compose_observation
    from .environment import ROOT,np
    from .environment_contract_v1 import EnvironmentContract,MARKERS
    from .run_joint_hold import native_state
    from .gym_trial_recording import GymTrialRecording
    from .build_fixed_lower_asset import LOWER_BODIES
    # Native imports above must precede Torch.
    import torch
    scene=recorder=None;failure=None;records=[];trace=[];music=None;views=None;videos={};stop=None;started=False
    paths=set(str(p) for p in (ROOT/'stability_adapter_2').rglob('*') if p.is_file() and p.suffix in ('.py','.json','.xml','.md'))
    paths.update(str(p) for p in (ROOT/'tab2body').rglob('*') if p.is_file() and p.suffix in ('.py','.json','.xml'))
    paths.update(str(p) for p in BUNDLE.rglob('*.json'));paths.add(str(BASE))
    paths.update(EnvironmentContract().inputs)
    if args.mode=='pair':
        # Constants are resolved without importing native task/extension modules before the guarded run.
        FCP=ROOT/'fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt'
        FG=BUNDLE/'training/fret_training.json';HAND_TARGETS=BUNDLE/'training/hand_position_targets.json'
        SCP=ROOT/'strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt'
        SG=BUNDLE/'training/strike_plan.json';GRIP=ROOT/'strike/02_physical_control/pick-grip-reference.json'
        paths.update(map(str,[FCP,SCP,FG,HAND_TARGETS,SG,GRIP]))
    hashes={p:sha(p) for p in sorted(paths)}
    save(out/'attempt.json',{'mode':args.mode,'factor':args.factor,'input_sha256':hashes})
    try:
        horizon=5.
        if args.mode=='pair':
            music=JointMusicClock()
            dense=json.loads((BUNDLE/'training/fret_training.json').read_text())
            horizon=2+max(len(dense['frames'])/60,music.events[-1].traversal_end_time_s+.05)+1/60
        scene=DualMusicScene(horizon)
        preload,preload_record=preload_targets(scene.contract,args.factor)
        state0=native_state(scene)
        if state0 != scene.contract.reference['native_initial_state']:raise AssertionError('initial state changed')
        fixed=[scene.human_bodies.index(n) for n in ('Pelvis',)+LOWER_BODIES]
        save(out/'initial_values.json',{'native_initial_state':state0,'native_initial_exact_reference':True,
            'human_body_names':scene.human_bodies,'guitar_body_names':scene.guitar_bodies,
            'joint_names':scene.names,'preload':preload_record,'horizon_s':horizon,
            'PD_properties':{k:scene.pd_properties[k].tolist() for k in scene.pd_properties.dtype.names},
            'q_ref_rad':scene.contract.q_ref.tolist(),'observation_manifest':scene.observation_manifest,'marker_order':MARKERS,
            'root_lower_fixed':True,'strap_enabled':False,'preparation_s':2,'source_clocks_projected_to_common_zero':args.mode=='pair'})
        recorder=GymTrialRecording(scene,out/'media')
        source_meta=None
        if args.mode=='pair':
            from .fret_native_view_v2 import create_fret_view
            from . import strike_native_view
            from .strike_native_view import refresh_native
            from .dual_strike_evaluator_v1 import DualStrikeView
            from .dual_strike_contract_guard_v1 import verify_strike_inputs,verify_strike_view
            from tab2body.learning.fret_v2_model import FretV2ActorCritic
            from tab2body.learning.strike_v2_model import StrikeV2ActorCritic
            from tab2body.tools.fret_rollout_contract import verify_rollout_model
            from .strike_preparation_handoff import seed_source_history
            from tab2body.full.readiness import evaluate_sounding_fret_readiness
            before=native_state(scene)
            fc=torch.load(FCP,map_location='cpu',weights_only=True);sc=torch.load(SCP,map_location='cpu',weights_only=True)
            sp=verify_strike_inputs(sc,SG,GRIP)
            fret,fp=create_fret_view(scene,fc,FG,HAND_TARGETS)
            with patch.object(strike_native_view,'NativeStrikeView',DualStrikeView):
                strike=strike_native_view.create_view(scene,sc,SG,GRIP)
            verify_strike_view(sp,strike)
            if native_state(scene)!=before:raise AssertionError('view creation changed physics')
            fm=FretV2ActorCritic(420,30,value_dim=6,init_std=fp['model']['policy_init_std'])
            verify_rollout_model(fret,fm,fp)
            sm=StrikeV2ActorCritic(303,30,value_dim=1,init_std=sc['checkpoint_contract']['payload']['model']['policy_init_std'])
            fm.load_state_dict(fc['model'],strict=True);sm.load_state_dict(sc['model'],strict=True)
            for m in (fm,sm):m.eval();m.requires_grad_(False)
            frozen=[{k:v.clone() for k,v in m.state_dict().items()} for m in (fm,sm)]
            fidx,sidx=fret.ctrl_idx.numpy(),strike.ctrl_idx.numpy()
            if set(fidx)&set(sidx) or len(fidx)!=30 or len(sidx)!=30:raise AssertionError('source channel ownership conflict')
            for view,indices in ((fret,fidx),(strike,sidx)):
                low=np.maximum(scene.contract.effective_lower[indices],view.ctrl_lo.numpy()[0])
                high=np.minimum(scene.contract.effective_upper[indices],view.ctrl_hi.numpy()[0])
                if np.any(low>high):raise ValueError('source/native range intersection empty')
            music.dwell_s=fret.reward_fn.press_hold_min_frames/60
            diagnostic_detector=copy.deepcopy(strike.detector)
            diagnostic_detector.rearm_min_frames*=4
            previous_tip=None;substeps=[]
            views=(fret,strike)
            def refresh_views():
                before=native_state(scene)
                for view in views:refresh_native(view,scene)
                if native_state(scene)!=before or not torch.equal(fret.body_state,strike.body_state):
                    raise AssertionError('view snapshot timestamps diverged')
            def measure(owner):
                nonlocal previous_tip
                refresh_views()
                cells=fret.reward_fn.refresh_press_state()
                ready=evaluate_sounding_fret_readiness(cells,torch.tensor(music.targets())[None])
                tip=strike.to_guitar_frame(strike.hbody_pos('RH:pick')[:,None])[:,0].clone()
                start,end=strike.string_segments_g()
                detection=diagnostic_detector.step(previous_tip if previous_tip is not None else tip,tip,start,end,dt=1/240)
                releases=[]
                for string in range(6):
                    if bool(detection['release'][0,string]):
                        releases.append((string,float(detection['subframe_t'][0,string]),int(detection['direction'][0,string]),bool(detection['zone_allowed'][0,string])))
                previous_tip=tip
                music.update(owner.steps,ready.effective_sounding_fret[0].numpy(),releases)
                substeps.append({'physics_step':owner.steps,'sounding_fret':ready.effective_sounding_fret[0].tolist(),
                    'press_cells':torch.nonzero(cells[0]).tolist(),'raw_release':detection['release'][0].tolist(),
                    'zone_allowed':detection['zone_allowed'][0].tolist(),
                    'subframe_t':detection['subframe_t'][0].tolist(),'direction':detection['direction'][0].tolist(),
                    'detector_state':diagnostic_detector.state[0].tolist(),'music':music.observation().tolist()})
            scene.after_physics=measure
            source_meta={'Fret_checkpoint':str(FCP),'Fret_sha256':sha(FCP),'Strike_checkpoint':str(SCP),'Strike_sha256':sha(SCP),
                         'Fret_names':[scene.names[i] for i in fidx],'Strike_names':[scene.names[i] for i in sidx],
                         'Strike_checkpoint_input_and_view_contract_checked':True,
                         'source_post_physics_strike_sha256':strike.source_sha256,'dwell_s':music.dwell_s,
                         'canonical_sha256':music.timeline.content_sha256,'events':len(music.events),
                         'detector_rearm_physics_frames':diagnostic_detector.rearm_min_frames,
                         'source_zone_gate_active':bool(strike.zone_gate_active),
                         'source_velocity_scope':'inherited source ABI uses copied native COM linear velocity; physical548 converts to body origin',
                         'history_scope':'source inverse helper may clip; reconstructed targets compared with actual final each control',
                         'joint_zone_gate':'actual detector zone_allowed required, independent of source stage gates',
                         'joint_snapshot_scope':'conservative240Hz endpoint bracket, not exact subframe PhysX measurement'}
            save(out/'source_contract.json',source_meta)
        def sample():
            s=native_state(scene)
            if any(s['human_body_states'][i]!=state0['human_body_states'][i] for i in fixed):raise AssertionError('fixed body changed')
            values=[v for row in s['human_dof_states'] for v in (row['pos'],row['vel'])]
            if not np.isfinite(values).all() or max(abs(row['vel']) for row in s['human_dof_states'])>50:raise ValueError('unsafe native joint state')
            p=s['guitar_body_states'][0]['pose']['p'];q=s['guitar_body_states'][0]['pose']['r']
            trace.append({'physics_step':scene.steps,'position_W_m':[p[k] for k in 'xyz'],'quaternion_xyzw':[q[k] for k in 'xyzw'],
                          'q_rad':[r['pos'] for r in s['human_dof_states']]})
        sample();recorder.capture()
        started=False
        for tick in range(int(round(horizon*60))):
            desired=preload.copy();phase='PREP' if tick<120 else 'PLAY'
            row={'physics_step_before':scene.steps,'phase':phase,'actor_used':args.mode=='pair' and tick>=120}
            if args.mode=='pair':
                refresh_views()
                if tick<120:
                    fret.preparation_remaining.fill_(120-tick)
                    strike.song_time_s.fill_(tick/60-2)
                if tick>=120:
                    frame=tick-120
                    if not started:
                        fret.preparation_remaining.zero_();fret.progress_buf.zero_();strike.progress_buf.zero_()
                        strike.song_time_s.zero_();seed_source_history(strike,scene.target)
                        started=True
                    if int(fret.goals.frame_idx[0])!=min(frame,fret.goals.n_frames-1) or abs(float(strike.song_time_s[0])-frame/60) > 1/240:
                        raise AssertionError('source clocks diverged from owner')
                    row['Strike_clock_before_projection_s']=float(strike.song_time_s[0])
                    strike.song_time_s.fill_(frame/60)
                    fo,so=fret.strict_observation(),strike.strict_observation()
                    if fo.shape!=(1,420) or so.shape!=(1,303):raise AssertionError('checkpoint observation dimension changed')
                    with torch.no_grad():fa=fm.act(fo,deterministic=True)[0];sa=sm.act(so,deterministic=True)[0]
                    if not torch.isfinite(fa).all() or not torch.isfinite(sa).all():raise ValueError('nonfinite actor action')
                    fret.cache_policy_actions(fa);strike.apply_actions(sa)
                    desired[fidx]=fret.pd_target.numpy()[fidx];desired[sidx]=strike.pd_target.numpy()[sidx]
                    for view,indices in ((fret,fidx),(strike,sidx)):
                        low=np.maximum(scene.contract.effective_lower[indices],view.ctrl_lo.numpy()[0])
                        high=np.minimum(scene.contract.effective_upper[indices],view.ctrl_hi.numpy()[0])
                        desired[indices]=np.clip(desired[indices],low,high)
                    row.update(score_frame=frame,Fret_observation=fo[0].tolist(),Strike_observation=so[0].tolist(),
                               Fret_action=fa[0].tolist(),Strike_action=sa[0].tolist())
                    action_phase=strike.motor_phase.clone()
            action=np.clip((desired-scene.contract.mid)/scene.contract.half,-1.,1.)
            observation,info=scene.step(action)
            row.update(info,action81=action.tolist(),requested81_rad=desired.tolist(),physics_observation=observation.tolist())
            if args.mode=='pair':
                refresh_views()
                for label,view,indices in (('Fret',fret,fidx),('Strike',strike,sidx)):
                    view.pd_target.copy_(torch.tensor(scene.target.copy()))
                    view.prev_action.copy_(view.actions_for_pd_targets(view.pd_target[indices][None]))
                    reconstructed=(view.ctrl_mid+view.action_scale*view.prev_action*view.ctrl_half).clamp(view.ctrl_lo,view.ctrl_hi)
                    error=reconstructed[0]-view.pd_target[indices]
                    row[label+'_history_reconstruction_error_rad']=error.tolist()
                    row[label+'_history_clipped_channels']=int((error.abs()>2e-7).sum())
                if tick>=120:
                    fret.progress_buf+=1;strike.progress_buf+=1
                    _,fr,fd,fi=fret.evaluate_after_physics()
                    _,sr,sd,si=strike.evaluate_after_physics(action_phase)
                    row.update(Fret_reward=fr.tolist(),Strike_reward=sr.tolist(),Fret_done=fd.tolist(),Strike_done=sd.tolist(),
                               Fret_info=plain(fi),Strike_info=plain(si))
                    if bool(fd[0]) or bool(sd[0]):stop='first_source_terminal'
                if tick<120:
                    fret.preparation_remaining.fill_(max(0,119-tick))
                    strike.song_time_s.fill_((tick+1)/60-2)
                combined,manifest=compose_observation(observation,fret.strict_observation()[0].numpy(),
                    strike.strict_observation()[0].numpy(),music.observation())
                row['combined_observation']=combined.tolist()
                row['joint_diagnostic']=music.observation().tolist()
                row['joint_event_results']=len(music.results)
            records.append(row);sample()
            if scene.steps%8==0:recorder.capture()
            if stop:break
            if scene.steps%240==0:print('recorded',scene.steps/240,'seconds',flush=True)
        if stop is None:stop='planned_horizon' if args.mode=='pair' else 'five_second_observation'
        if args.mode=='pair':
            if not all(torch.equal(v,frozen[i][k]) for i,m in enumerate((fm,sm)) for k,v in m.state_dict().items()):raise AssertionError('frozen weights changed')
            save(out/'observation_manifest.json',{'dimension':1299,'blocks':manifest,'scope':'candidate physical+original source blocks+experimental joint diagnostic, not final training ABI'})
            save(out/'music_physics_samples.json',substeps)
            save(out/'joint_crossings.json',music.crossings);save(out/'joint_events.json',music.results)
    except BaseException as e:
        failure={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()};print(failure['traceback'],flush=True)
    finally:
        if scene and recorder and trace and (not recorder.frames or recorder.frames[-1]['physics_step']!=scene.steps):
            try:recorder.capture()
            except BaseException:pass
        steps=scene.steps if scene else 0;forbidden=list(scene.forbidden_calls) if scene else []
        if scene:scene.close()
        if recorder:
            try:videos=recorder.encode()
            except BaseException as e:
                if failure is None:failure={'type':type(e).__name__,'message':str(e)}
        save(out/'controls.json',records);save(out/'trace.json',trace)
        unchanged=all(sha(p)==h for p,h in hashes.items())
        save(out/'report.json',{'completed':failure is None and unchanged and not forbidden,'failure':failure,'stop_reason':stop,
            'physics_steps':steps,'control_steps':len(records),'physics_seconds':steps/240,'inputs_unchanged':unchanged,
            'forbidden_calls':forbidden,'videos':videos,'dual_checkpoints_connected':args.mode=='pair' and started,
            'music_detection_scope':'experimental conservative bracket, not training-ready detector certification',
            'training_ready':False,'training_updates':0})
    if failure or not unchanged or forbidden:raise RuntimeError(failure or 'source/ownership changed')


if __name__=='__main__':main()
