"""CPU audit of immutable actual native snapshots against original target cells."""
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.spatial.transform import Rotation

ROOT=Path('/home/ajou/yigyu/3')
PARENT=ROOT/'docs/2026-10-27/guitar_learning_failure_diagnosis_v1'
BASE=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())+'\n')


def main():
    import torch
    from guitar_learning.gpu.simplified_finger_environment import SimplifiedFingerEnvironment
    from guitar_learning.gpu.environment import CONTACT_CONTRACT
    from guitar_learning.training.recording import project_source_paths
    sys.path.insert(0,str(PARENT/'02_contact_reward/support'))
    from current_contact_replay import sample_masks
    torch.set_num_threads(1)
    started=time.monotonic()
    metadata_path=PARENT/'02_contact_reward/teacher_fixed_B_export/metadata.json'
    settings_path=PARENT/'baseline/trace_initial/settings.json'
    metadata=json.loads(metadata_path.read_text());settings=json.loads(settings_path.read_text())
    old_pins=json.loads((PARENT/'baseline/trace_initial/inputs_before.json').read_text())
    measurement_source_matches={name:old_pins.get(str(ROOT/name))==sha(ROOT/name) for name in ('guitar_learning/gpu/environment.py','guitar_learning/gpu/simplified_finger_environment.py','guitar_learning/gpu/wrong_press.py','guitar_learning/gpu/fingertip_pad.py','guitar_learning/gpu/press_surface.py','guitar_learning/gpu/geometry.py')}
    assert all(measurement_source_matches.values()),measurement_source_matches
    static_sources=sorted((PARENT/'02_contact_reward').glob('static_*'))+sorted((PARENT/'02_contact_reward').glob('teacher_*'))
    inputs=[BASE/'precommit.json',Path(__file__),metadata_path,settings_path,PARENT/'02_contact_reward/review_partial.json']
    for label in ('trace_initial','trace_final'):inputs += [PARENT/'baseline'/label/'trace_env0000.npz']
    for folder in static_sources:
        inputs += [p for p in (folder/'trace240.npz',folder/'report.json',folder/'settings.json',folder/'static_scope.json') if p.is_file()]
    ledger=PARENT/'02_contact_reward/ledger_fixed_B_fast_normal_guard'
    inputs += [ledger/'report.json',ledger/'scope.json',ledger/'control60.npz',ledger/'trace240.npz']
    pins={str(p.resolve()):sha(p) for p in inputs}
    n=67;indices=torch.arange(n);static_time=None
    class StaticOriginal(SimplifiedFingerEnvironment):
        def _score_time(self):return static_time
        def _reset_scope(self,ids):
            super()._reset_scope(ids)
            self.focus_mask[ids]=False;self.focus_mask[ids,indices[ids]]=True
            self.recovery_mask[ids]=self.focus_mask[ids]
            self.finger_weights[ids]=self.focus_mask[ids].float()
    env=StaticOriginal(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],skill=settings['finger_skill'],device='cpu')
    assert env.M==67
    for item in env.task.provenance['provenance']:
        source=Path(item['path']).resolve()
        assert sha(source)==item['sha256'] and old_pins.get(str(source))==item['sha256']
        pins[str(source)]=item['sha256']
    static_time=(env.onset+env.end)/2
    goals=[dict(string=t.string,fret=t.fret,finger=t.finger) for t in env.task.targets]
    targets=[dict(index=i,target_id=t.target_id,string=t.string,fret=t.fret,finger=t.finger,onset_s=t.onset_s,end_s=t.end_s,press_s=t.press_s) for i,t in enumerate(env.task.targets)]
    pins.update({p:sha(p) for p in project_source_paths(list(sys.modules.items()))})
    write(BASE/'inputs_before.json',pins)
    cases={};counts={};errors=dict(native_reconstruction_point_max_m=0.,positive_mismatches=0,wrong_mismatches=0,wrong_flag_mismatches=0,candidate_mismatches=0,helper_same_sample_mismatches=0)
    raw_cases={};frames_audited=[]

    def independent(raw):
        body=raw['body_state'];force=raw['contact_force'];g=body[env.guitar_index]
        gr=Rotation.from_quat(g[3:7]);gp=g[:3]
        def material(body_ids,local,normals=None):
            points=[];ns=[]
            for k,idx in enumerate(body_ids):
                r=Rotation.from_quat(body[idx,3:7]);points.append(gr.inv().apply(body[idx,:3]+r.apply(local[k])-gp))
                if normals is not None:ns.append(gr.inv().apply(r.apply(normals[k])))
            return np.array(points),np.array(ns)
        pad,normals=material(env.pad_indices.tolist(),env.pad_local.numpy(),env.pad_normals.numpy())
        virtual,_=material(env.finger_indices.tolist(),env.surface_local.numpy())
        virtual=virtual.reshape(-1,3)
        starts=env.starts[0].numpy();ends=env.ends[0].numpy();frety=env.frets[0,:,1].numpy();plane=env.press_plane.numpy();unit=plane[:3]/np.linalg.norm(plane[:3])
        press_starts=starts.copy();press_ends=ends.copy()
        for points in (press_starts,press_ends):points[:,2]=-(points[:,:2]@plane[:2]+plane[3])/plane[2]
        loaded=np.linalg.norm(force,axis=-1)>=CONTACT_CONTRACT['force_threshold_n']
        body_load=loaded[env.pad_indices.numpy()]
        valid=env.pad_valid.numpy();height=pad@unit+plane[3]/np.linalg.norm(plane[:3]);cosine=-(normals@unit)
        low=np.minimum(frety[:-1],frety[1:]);high=np.maximum(frety[:-1],frety[1:])
        # Independent current pad-contact-cell classification from actual raw poses.
        on_plane=pad-height[...,None]*unit;line=press_ends-press_starts
        delta=on_plane[...,None,:]-press_starts
        fraction=(delta*line).sum(-1)/(line*line).sum(-1)
        distance2=((delta-fraction[...,None]*line)**2).sum(-1)
        nearest=distance2.argmin(-1);best=np.take_along_axis(distance2,nearest[...,None],axis=-1)[...,0]
        unique=(distance2<=best[...,None]+1e-12).sum(-1)==1
        selected_fraction=np.take_along_axis(fraction,nearest[...,None],axis=-1)[...,0]
        interiors=(pad[...,1,None]>low+.002)&(pad[...,1,None]<high-.002)
        assigned=np.where(interiors.any(-1),interiors.argmax(-1)+1,0)
        pad_cells=(valid&body_load[:,None]&unique&(best<=.003**2)&(selected_fraction>=0)&(selected_fraction<=1)&(height>=-.001)&(height<=.003)&(cosine>=.1)&(assigned>0))
        # Independent original full10-body virtual sources for other_higher.
        vline=ends-starts;frac=(virtual[:,None,1]-starts[None,:,1])/vline[None,:,1]
        projected=starts+frac[...,None]*vline;lateral=np.abs(projected[...,0]-virtual[:,None,0]);vn=lateral.argmin(-1);vb=np.take_along_axis(lateral,vn[:,None],-1)[:,0]
        vfrac=np.take_along_axis(frac,vn[:,None],-1)[:,0];vh=np.take_along_axis(virtual[:,None,2]-projected[...,2],vn[:,None],-1)[:,0]
        vint=(virtual[:,1,None]>low+.002)&(virtual[:,1,None]<high-.002);vf=np.where(vint.any(-1),vint.argmax(-1)+1,0)
        vloaded=np.repeat(loaded[env.finger_indices.numpy()],env.surface_count)
        qualifies=(env.surface_valid.numpy()&vloaded&((lateral<=vb[:,None]+1e-12).sum(-1)==1)&(vfrac>=0)&(vfrac<=1)&(vb<=.003)&(np.abs(vh)<=.003))
        positives=[];flags=[];positions=[];facings=[];other_same=[];witnesses=[]
        for t in targets:
            f,s,fr=t['finger']-1,t['string'],t['fret'];p=pad[f];start=press_starts[s];line=press_ends[s]-start
            projection=((p-start)*line).sum(-1)/(line*line).sum();lat2=((p-height[f,:,None]*unit-start-projection[:,None]*line)**2).sum(-1)
            position=valid[f]&(p[:,1]>=low[fr-1]+.002)&(p[:,1]<=high[fr-1]-.002)&(lat2<=.003**2)&(height[f]>=-.001)&(height[f]<=.003)
            facing=position&(cosine[f]>=.1);positive=bool(facing.any() and body_load[f]);fl=np.zeros((10,3),bool)
            higher=qualifies&(vn==s)&(vf>fr)&(env.pad_fingers.numpy()!=f+1)
            fl[:,0]=higher.reshape(10,env.surface_count).any(-1)
            unauthorized=pad_cells[f]&~((nearest[f]==s)&(assigned[f]==fr))&~positive
            fl[2*(f+1)+1,1]=bool((unauthorized&(nearest[f]==s)&(assigned[f]!=fr)).any())
            fl[2*(f+1)+1,2]=bool((unauthorized&(nearest[f]!=s)).any())
            other=pad_cells.copy();other[f]=False;other_match=other&(nearest==s)&(assigned==fr)
            positives.append(positive);flags.append(fl);positions.append(position);facings.append(facing);other_same.append(bool(other_match.any()))
            samples=np.flatnonzero(position)
            af=(low[fr-1]+.002-start[1])/line[1];bf=(high[fr-1]-.002-start[1])/line[1]
            closest=start+np.clip(projection,max(min(af,bf),0),min(max(af,bf),1))[:,None]*line
            cell_distance=np.linalg.norm(closest-p,axis=-1);cell_distance[~valid[f]]=np.inf
            j=int(samples[0]) if len(samples) else int(np.argmin(cell_distance))
            own_errors=[]
            for cause,selection in (('own_wrong_fret',unauthorized&(nearest[f]==s)&(assigned[f]!=fr)),('own_wrong_string',unauthorized&(nearest[f]!=s))):
                found=np.flatnonzero(selection)
                if len(found):
                    k=int(found[0]);own_errors.append(dict(cause=cause,sample=k,point_G_m=p[k].tolist(),normal_G=normals[f,k].tolist(),signed_height_m=float(height[f,k]),normal_cos=float(cosine[f,k]),actual_physical_string=int(nearest[f,k])+1,actual_fret=int(assigned[f,k])))
            higher_witness=None
            if higher.any():
                k=int(np.flatnonzero(higher)[0]);bi=k//env.surface_count;higher_witness=dict(body=metadata['body_names'][int(env.finger_indices[bi])],sample=k%env.surface_count,point_G_m=virtual[k].tolist(),physical_string=int(vn[k])+1,fret=int(vf[k]),body_resultant_n=float(np.linalg.norm(force[env.finger_indices[bi]])))
            other_witness=None
            if other_match.any():
                of,k=np.argwhere(other_match)[0];other_witness=dict(body=metadata['body_names'][int(env.pad_indices[of])],finger=int(of)+1,sample=int(k),point_G_m=pad[of,k].tolist(),physical_string=int(nearest[of,k])+1,fret=int(assigned[of,k]),normal_cos=float(cosine[of,k]),body_resultant_n=float(np.linalg.norm(force[env.pad_indices[of]])))
            witnesses.append(dict(pad_distance_to_target_cell_m=float(cell_distance.min()),own_error_witnesses=own_errors,other_higher_witness=higher_witness,other_same_cell_witness=other_witness,sample=j,point_G_m=p[j].tolist(),normal_G=normals[f,j].tolist(),signed_height_m=float(height[f,j]),normal_cos=float(cosine[f,j]),lateral_m=float(np.sqrt(lat2[j])),position_samples=int(position.sum()),facing_samples=int(facing.sum()),native_body=metadata['body_names'][int(env.pad_indices[f])],body_resultant_n=float(np.linalg.norm(force[env.pad_indices[f]])),other_same_cell_distal=bool(other_match.any()),other_higher_source_bodies=[metadata['body_names'][int(env.finger_indices[i])] for i in np.flatnonzero(fl[:,0])]))
        return dict(positive=np.array(positives),flags=np.array(flags),position=np.array([x.any() for x in positions]),facing=np.array([x.any() for x in facings]),loaded=body_load[env.finger.numpy()-1],other_same=np.array(other_same),witnesses=witnesses,pad=pad)

    for label in ('trace_initial','trace_final'):
        file=PARENT/'baseline'/label/'trace_env0000.npz';a=np.load(file)
        choose=set(np.linspace(0,len(a['physics_step'])-1,16,dtype=int).tolist())
        for finger in range(1,5):
            ix=np.flatnonzero(a['candidate'][:,env.finger.numpy()==finger].any(-1))
            if len(ix):choose.add(int(ix[0]))
        ix=np.flatnonzero(a['wrong'].any(-1))
        if len(ix):choose.add(int(ix[0]))
        for frame in sorted(choose)[:24]:
            raw={key:a[key][frame].copy() for key in ('q','qd','target','body_state','contact_force')}
            snapshot={key:torch.tensor(value).unsqueeze(0).repeat((n,)+(1,)*value.ndim) for key,value in raw.items()}
            snapshot['physics_step']=torch.full((n,),int(a['physics_step'][frame]),dtype=torch.long)
            if not env.initialized:env.reset(indices,snapshot)
            else:env._snapshot(snapshot)
            helper=sample_masks(env,goals,indices)
            independent_result=independent(raw)
            rebuilt=np.stack([independent_result['pad'][t['finger']-1] for t in targets])
            errors['native_reconstruction_point_max_m']=max(errors['native_reconstruction_point_max_m'],float(np.abs(rebuilt-helper['points_G'].numpy()).max()))
            positive=independent_result['positive'];flags=independent_result['flags'];wrong=flags.any((1,2));candidate=positive&~wrong
            ep=env.contact_loaded_target[indices,indices].numpy();ew=env.wrong[indices,indices].numpy();ec=env.candidate[indices,indices].numpy();ef=env.wrong_source_flags[indices,indices].numpy()
            errors['positive_mismatches']+=int((positive!=ep).sum());errors['wrong_mismatches']+=int((wrong!=ew).sum());errors['wrong_flag_mismatches']+=int((flags!=ef).sum());errors['candidate_mismatches']+=int((candidate!=ec).sum())
            errors['helper_same_sample_mismatches']+=int((helper['facing_mask'].any(-1).numpy()!=independent_result['facing']).sum())
            # Each target row sees identical native state, original target, changed scope/time only.
            actual_ids=np.flatnonzero(a['candidate'][frame]);source=dict(file=str(file),sha256=pins[str(file.resolve())],environment=0,frame=frame,physics_step=int(a['physics_step'][frame]),actual_time_s=float(a['physics_step'][frame]/240),actual_score_time_s=float(a['score_time_s'][frame]),original_candidate_target_ids=[targets[i]['target_id'] for i in actual_ids])
            frames_audited.append(dict(source=source,targets=67))
            for t in targets:
                i=t['index'];predicates=dict(far=bool(env.surface_distance[i,i]>=.02 and not candidate[i]),own_wrong_string=bool(flags[i,:,2].any() and not positive[i] and not candidate[i]),own_wrong_fret=bool(flags[i,:,1].any() and not positive[i] and not candidate[i]),other_finger_only=bool(not positive[i] and independent_result['other_same'][i] and not candidate[i]),other_higher=bool(flags[i,:,0].any()),other_higher_with_assigned_positive=bool(positive[i] and flags[i,:,0].any()),back_facing=bool(independent_result['loaded'][i] and independent_result['position'][i] and not independent_result['facing'][i]),near_unloaded=bool(independent_result['facing'][i] and not independent_result['loaded'][i] and not candidate[i]))
                for name,matched in predicates.items():
                    counts[name]=counts.get(name,0)+int(matched)
                    if matched and name not in cases:
                        cases[name]=dict(status='available_static_counterfactual',source=source,diagnostic_target=t,diagnostic_score_time_s=float(static_time[i]),scope='one original target only at its original audible midpoint; raw q/body/force unchanged; no musical ledger',positive=bool(positive[i]),wrong=bool(wrong[i]),candidate=bool(candidate[i]),wrong_flags=flags[i].tolist(),wrong_causes_present=[name for k,name in enumerate(('other_higher','own_wrong_fret','own_wrong_string')) if flags[i,:,k].any()],witness=independent_result['witnesses'][i])
                        for key,value in raw.items():raw_cases[name+'_'+key]=value
        print(label,'native_frames',len(choose),flush=True)

    static_checks=[];short_static=None
    for folder in static_sources:
        file=folder/'trace240.npz'
        if not file.exists():continue
        a=np.load(file)
        if not all(k in a for k in ('positive_mask','wrong_source_flags','signed_height_m','normal_cos')):continue
        positive=a['positive_mask'].any(-1);wrong=a['wrong_source_flags'].any((-1,-2));candidate=positive&~wrong&a['valid']
        check=dict(folder=str(folder),samples=int(a['candidate'].size),positive_mismatch=int((positive!=a['positive_before_wrong']).sum()),wrong_mismatch=int((wrong!=a['wrong']).sum()),candidate_mismatch=int((candidate!=a['candidate']).sum()))
        static_checks.append(check)
        protocol=json.loads((folder/'settings.json').read_text());report=json.loads((folder/'report.json').read_text());trace_rows=protocol['trace_rows'];scope=json.loads((folder/'static_scope.json').read_text())
        for slot,row in enumerate(trace_rows):
            if short_static is None:
                on=a['candidate'][:,slot]&a['valid'][:,slot]
                edges=np.diff(np.r_[False,on,False].astype(int));begins=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)-1
                for start,stop in zip(begins,ends):
                    duration=float((a['physics_step'][stop]-a['physics_step'][start])/240)
                    target=targets[scope['source_note_indices'][row]];tau=min(.05,target['end_s']-target['press_s'])
                    if 0<duration<tau:
                        short_static=dict(status='available_actual_static_segment_only',source=dict(file=str(file),sha256=pins[str(file.resolve())],row=row,trace_slot=slot,first_physics_step=int(a['physics_step'][start]),last_physics_step=int(a['physics_step'][stop])),target=target,scope='actual native240Hz brief candidate segment at static note midpoint; no musical payment',segment_streak_s=duration,contact_tau_s=tau,full_contact_tau_met_in_segment=False,segment_progress=duration/tau,partial_progress_reward_allowed=True,actual_reward_payment_verified=False,full_trajectory_later_or_other_streak_meets_tau=report['goals'][row]['best_static_contact_streak_s']>=tau,achievement='unavailable: static clock and no original musical ledger')
                        break
            # Release denotes loss of positive geometry, not inferred pair detachment.
            release=(a['phase']==3)&a['valid'][:,slot]&~positive[:,slot]&~a['candidate'][:,slot]
            release[0]=False;release[1:] &= a['candidate'][:-1,slot]
            found=np.flatnonzero(release)
            if len(found) and 'release' not in cases:
                k=int(found[0]);target=targets[scope['source_note_indices'][row]]
                cases['release']=dict(status='available_actual_static_trajectory',source=dict(file=str(file),sha256=pins[str(file.resolve())],row=row,trace_slot=slot,physics_step=int(a['physics_step'][k]),time_s=float(a['physics_step'][k]/240)),target=target,scope='actual native240Hz release phase; fixed original-note midpoint; no music payment',previous_candidate=True,candidate=False,positive_before_wrong=False,wrong=bool(wrong[k,slot]),wrist_shadow_already_failed=report['goals'][row]['wrist_shadow_failure_time_s'] is not None and a['physics_step'][k]/240>=report['goals'][row]['wrist_shadow_failure_time_s'])
            if 'assigned_distal_body_force_n' in a and 'back_facing' not in cases:
                eligible=a['valid'][:,slot]&a['position_mask'][:,slot].any(-1)&~a['facing_mask'][:,slot].any(-1)&(a['assigned_distal_body_force_n'][:,slot]>=.01)
                found=np.flatnonzero(eligible)
                if len(found):
                    k=int(found[0]);j=int(np.flatnonzero(a['position_mask'][k,slot])[0])
                    cases['back_facing']=dict(status='available_actual_static_trajectory',source=dict(file=str(file),sha256=pins[str(file.resolve())],row=row,trace_slot=slot,physics_step=int(a['physics_step'][k]),time_s=float(a['physics_step'][k]/240)),target=targets[scope['source_note_indices'][row]],scope='actual native240Hz snapshot at static original-note midpoint; registered palmar pad faces away; no artificial dorsal samples',candidate=bool(a['candidate'][k,slot]),body_resultant_n=float(a['assigned_distal_body_force_n'][k,slot]),sample=j,point_G_m=a['points_G'][k,slot,j].tolist(),normal_G=a['normals_G'][k,slot,j].tolist(),normal_cos=float(a['normal_cos'][k,slot,j]),signed_height_m=float(a['signed_height_m'][k,slot,j]),all_position_samples_fail_facing=True)
    control=np.load(ledger/'control60.npz');ls=json.loads((ledger/'scope.json').read_text());lr=json.loads((ledger/'report.json').read_text())
    for row in range(24):
        last=np.flatnonzero(control['valid'][:,row])[-1];progress=float(control['contact_progress'][last,row]);achieved=bool(control['achieved'][last,row])
        if 0<progress<1 and not achieved and 'short_contact' not in cases:
            cases['short_contact']=dict(status='available_actual_clock_ledger',source=dict(file=str(ledger/'control60.npz'),sha256=pins[str((ledger/'control60.npz').resolve())],row=row,last_control_index=int(last)),target=targets[ls['indices'][row]],scope='old fixed guitar fullDLS press-local3 one-note actual ledger; not current fixed-wrist teacher condition',contact_progress=progress,contact_tau_s=min(.05,ls['original_end_s'][row]-ls['original_press_s'][row]),full_contact_tau_met=False,achieved=False,required_s=ls['original_required_s'][row],best_clean_streak_s=float(control['note_best_streak_s'][last,row]),paid_first_contact_reward=float(control['reward_song_left_contact'][last,row]),expected_partial_contact_reward=.25*progress,episode_reason=lr['episodes'][row]['reason'])
    if 'short_contact' not in cases and short_static is not None:cases['short_contact']=short_static
    for name in ('far','own_wrong_string','own_wrong_fret','other_finger_only','other_higher','other_higher_with_assigned_positive','back_facing','near_unloaded','short_contact','release'):
        cases.setdefault(name,dict(status='unavailable_in_declared_saved_scope',reason='No qualifying actual native case found; no synthesized state/contact or relaxed criterion'))
    changed=[path for path,value in pins.items() if not Path(path).is_file() or sha(path)!=value]
    result=dict(schema='negative_native_snapshot_audit.v1',completed=not changed,changed_inputs=changed,gpu_used=False,
        measurement='current pad positive/wrongv2 recomputed on original native snapshot; source time/scope counterfactuals explicit',
        measurement_sources_match_original_baseline=measurement_source_matches,counterfactual_frames=frames_audited,counterfactual_counts=counts,independent_recalculation=errors,static_shared_mask_checks=static_checks,
        cases=cases,limitations=['distal/resultant load cannot identify contact partner or calibrated pressure','static original-target counterfactual is not performed song success','middle reference3/4 positive has episode summaries only; successful env1/2/3 native snapshots were not saved','no pilot logs used','missing cases remain unavailable; stage2 full negative matrix is not automatically complete'],wall_s=time.monotonic()-started)
    write(BASE/'results.json',result);write(BASE/'inputs_after.json',dict(verified=not changed,changed_paths=changed,input_pins=pins))
    if raw_cases:np.savez_compressed(BASE/'representative_actual_native_snapshots.npz',**raw_cases)
    if changed:raise RuntimeError('Read-only audit inputs changed')
    if any(errors[k] for k in errors if k.endswith('mismatches')):raise RuntimeError('Independent raw recheck mismatch; see results.json')
    print(json.dumps(dict(completed=True,errors=errors,cases={k:v['status'] for k,v in cases.items()},wall_s=result['wall_s']),indent=2))


if __name__=='__main__':main()
