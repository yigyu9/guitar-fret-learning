"""Verify actual resized guitar properties, coordinates, recordings and scope."""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1';inputs={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    p=Path(p);inputs[str(p)]=sha(p);return json.loads(p.read_text())
def main():
    inputs[str(Path(__file__))]=sha(__file__);manifest=read(R/'stability_adapter_2/assets/realistic_guitar_v1/manifest.json');center_audit=read(P/'body_center_audit_v1.json');checks={'source_geometry_and_ABI':all(manifest['checks'].values()) and all(sha(p)==h for p,h in manifest['input_sha256'].items()),'new_asset_and_meshes_pinned':sha(manifest['asset'])==manifest['asset_sha256'] and all(sha(e['path'])==e['sha256'] for e in manifest['meshes'])};summaries=[];initials={};props={}
    for label,folder in (('original','native_baseline_v2'),('realistic','native_realistic_v2')):
        out=P/folder;d=read(out/'report.json');initial=read(out/'initial_values.json');initials[label]=initial;mass=read(out/'native_properties.json');props[label]=mass;cap=read(out/'media/capture.json');attempt=read(out/'attempt.json');contact=read(out/'contacts.json');rows=d['rows'];qref=np.array(initial['q_ref_rad'])
        checks[label+'_completed_five_seconds']=d['completed'] and d['physics_steps']==1200 and d['controls']==300 and len(rows)==301 and rows[-1]['time_s']==5
        checks[label+'_constant_qref_no_music_policy_CP']=all(np.array_equal(np.array(e['submitted_target_rad']),qref) for e in rows) and d['music_actors']==d['policy_calls']==d['checkpoint_loads']==0 and not attempt['initial_noise']
        checks[label+'_guard_reset_and_strap']=not d['forbidden_calls'] and d['initial_state_write_calls']==['set_actor_rigid_body_states','set_actor_dof_states'] and d['strap_force_calls']==15600 and d['property_setter_calls']==int(label=='realistic') and d['property_setter_rejections']==0
        checks[label+'_property_readback']=all(abs(e['mass_kg']-t['mass_kg'])<1e-6 and np.allclose(e['COM_body_m'],t['COM_body_m'],atol=1e-7,rtol=1e-6) and np.allclose(e['inertia_COM_kg_m2'],t['inertia_COM_kg_m2'],atol=1e-9,rtol=1e-5) and np.linalg.eigvalsh(np.array(e['inertia_COM_kg_m2'])).min()>0 for e,t in zip(mass['applied'],mass['requested']))
        checks[label+'_property_caches']=all(read(out/'property_cache_checks.json').values()) and all(d['property_cache_checks'].values())
        checks[label+'_actual_source_clear_and_FK']=initial['source_audit']['source_clear'] and max(e['position_error_m'] for e in initial['native_FK_error'].values())<1e-5 and max(e['orientation_error_deg'] for e in initial['native_FK_error'].values())<.01
        checks[label+'_native_inputs_unchanged']=read(out/'inputs_verified.json')['unchanged'] and all(sha(p)==h for p,h in attempt['input_sha256'].items())
        checks[label+'_151_frames_full_videos']=len(cap['frames'])==151 and cap['frames'][0]['time_s']==0 and cap['frames'][-1]['time_s']==5 and all(e['render_preserves_states'] for e in cap['frames']) and all(sha(e['path'])==e['sha256'] and int(e['stream']['nb_read_frames'])==151 and abs(float(e['stream']['duration'])-151/30)<.002 for e in d['videos'].values())
        for v in d['videos'].values():inputs[v['path']]=v['sha256']
        inputs[str(out/'initial_collision.png')]=sha(out/'initial_collision.png');checks[label+'_300_contact_queries']=len(contact)==300;counts={}
        for frame in contact:
            seen=set()
            for c in frame['contacts']:
                a,b=c['body0_name'],c['body1_name'];human=b if a.startswith('guitar/') else a if b.startswith('guitar/') else ''
                if human:seen.add(human.rsplit('/',1)[-1])
            for name in seen:counts[name]=counts.get(name,0)+1
        p2=np.array(rows[120]['position_W_m']);r2=Rotation.from_quat(rows[120]['quaternion_xyzw']);last=rows[-1];r5=Rotation.from_quat(last['quaternion_xyzw']);center=np.array(center_audit['actual_envelope_center_G_m']) if label=='realistic' else np.array([0,-.4,-.0217]);initial_center=np.array(rows[0]['position_W_m'])+Rotation.from_quat(rows[0]['quaternion_xyzw']).apply(center);final_center=np.array(last['position_W_m'])+r5.apply(center)
        summaries.append({'label':label,'completed':True,'final_actor_root_change_mm':last['position_change_m']*1000,'maximum_actor_root_change_mm':max(e['position_change_m'] for e in rows)*1000,'final_SO3_change_deg':last['rotation_change_deg'],'late_net_actor_root_change_mm':float(np.linalg.norm(np.array(last['position_W_m'])-p2)*1000),'late_net_SO3_change_deg':float(np.rad2deg((r2.inv()*r5).magnitude())),'geometric_envelope_center_initial_W_m':initial_center.tolist(),'geometric_envelope_center_final_W_m':final_center.tolist(),'geometric_envelope_center_change_mm':float(np.linalg.norm(final_center-initial_center)*1000),'contact_sample_counts_of_300':counts,'native_videos':d['videos'],'mass_total_kg':mass['total_mass_kg'],'G_body_applied_properties':next(e for e in mass['applied'] if e['name']=='G:body'),'strap_initial':initial['strap_initial'],'scope':'each case own initial motion; geometry, startup placement and strap button route all differ; no isolated causal stability comparison'})
    checks['same_body_names_and_masses']= [e['name'] for e in props['original']['applied']]==[e['name'] for e in props['realistic']['applied']] and all(abs(a['mass_kg']-b['mass_kg'])<1e-6 for a,b in zip(props['original']['applied'],props['realistic']['applied']))
    checks['same_humanoid_PD_and_nonarm_initial_targets']=initials['original']['PD_properties']==initials['realistic']['PD_properties'] and all(a==b for n,a,b in zip(initials['original']['joint_names'],initials['original']['q_ref_rad'],initials['realistic']['q_ref_rad']) if not n.startswith(('L_','R_')))
    checks['sources_and_assets_current_exact']=all(all(sha(p)==h for p,h in read(P/name).items()) for name in ('source_before_native_v2.json','assets_before_native_v1.json','source_before_search_v1.json'))
    checks['body_center_companion_exact']=center_audit['passed'] and all(sha(p)==h for p,h in center_audit['input_sha256'].items())
    checks['all_direct_analysis_inputs_exact']=all(sha(p)==h for p,h in inputs.items())
    result={'passed':all(checks.values()),'checks':checks,'input_sha256':inputs,'geometry_summary':{k:manifest[k] for k in ('humanoid','reference','dimension_scale_ratio','new_body_length_m','new_body_max_width_m','new_body_depth_range_m','total_length_m','legacy_body_reference_G_m','body_envelope_center_G_m','strap_buttons_G_m')},'body_center_correction':center_audit,'summaries':summaries,'limits':'source neutral human height not measured person height; concert outline approximate, not exact Yamaha scan; no real hollow wood mass certification; no checkpoint/learning or music performance tested; contact60Hz queries not all240Hz substeps; no Newton force conversion'}
    with (P/'verification_v2.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'summaries':[{k:e[k] for k in ('label','final_actor_root_change_mm','final_SO3_change_deg','geometric_envelope_center_change_mm','mass_total_kg')} for e in summaries]},ensure_ascii=False,indent=2));assert result['passed'],checks
if __name__=='__main__':main()
