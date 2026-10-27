"""Seal preserved baseline archive and small-right-shift preparation evidence."""
import ast
import hashlib
import json
import re
from pathlib import Path

P=Path(__file__).resolve().parent;R=P.parents[4];A=R/'stability_adapter_2';B=P.parent/'current_pose_test_v1'
def read(p):
    path=Path(p);raw=path.read_text()
    if path.resolve()==(P/'artifacts_v1/archive_pd_correction_provenance_v2.json').resolve():
        assert sha(path)=='ad9574b803518877f68bbfb5e989cb1bb6ee88492daf28b009c97f7dc89e57c6' and raw.endswith('\\n')
        return json.loads(raw[:-2])
    return json.loads(raw)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def save(p,obj):
    with p.open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)


def main():
    assert read(B/'final_verification_v1.json')['passed']
    assert 'Critical: 0' in (P/'review_final_v1.md').read_text()
    prior=read(B/'source_final_v1.json')['preserved'];snapshots={}
    for row in prior:
        if row.get('snapshot'):snapshots[row['path'],row['expected_sha256']]=row['snapshot']
    updates=read(P/'navigation_update_v1.json')
    for row in updates:
        assert sha(row['before_snapshot'])==row['before_sha256'] and sha(row['path'])==row['after_sha256']
        assert Path(row['path']).read_bytes().startswith(Path(row['before_snapshot']).read_bytes())
        snapshots[row['path'],row['before_sha256']]=row['before_snapshot']
    preserved=[];seen=set();cache={}
    def verify(path,h):
        path=str(path);key=path,h
        if key in seen:return
        seen.add(key)
        if path not in cache:cache[path]=sha(path)
        if cache[path]==h:
            preserved.append({'path':path,'expected_sha256':h,'resolution':'current exact'});return
        snap=snapshots.get(key);assert snap,(path,'unexpected change')
        assert sha(snap)==h and Path(path).read_bytes().startswith(Path(snap).read_bytes())
        preserved.append({'path':path,'expected_sha256':h,'resolution':'exact prefix snapshot of authorized append','snapshot':snap})
    for row in prior:verify(row['path'],row['expected_sha256'])
    for row in read(B/'artifact_inventory_v1.json')['files']:verify(row['path'],row['sha256'])
    for name in ('source_final_v1.json','artifact_inventory_v1.json','final_verification_v1.json'):verify(B/name,sha(B/name))
    def maps(obj):
        if isinstance(obj,dict):
            if obj and all(isinstance(k,str) and k.startswith('/') and isinstance(v,str) and len(v)==64 for k,v in obj.items()):
                for path,h in obj.items():verify(path,h)
            if 'path' in obj:
                for key in ('sha256','sha256_before','sha256_after'):
                    if key in obj:verify(obj['path'],obj[key])
            for value in obj.values():maps(value)
        elif isinstance(obj,list):
            for value in obj:maps(value)
    for f in sorted(P.rglob('*.json')):maps(read(f))
    initial_dir=R/'docs/2026-10-19/initial'
    for f in sorted(initial_dir.rglob('*.json')):maps(read(f))
    baseline=P.parent/'left_neck_three_face_v1/native_off_v1'
    n=P/'native_right10_v1';report=read(n/'report.json');initial=read(n/'initial_verification.json')
    assert report['completed'] and report['inputs_unchanged'] and not report['forbidden_calls'] and report['failure'] is None
    assert report['physics_steps']==1200 and report['control_steps']==300 and not report['strap_enabled'] and not report['checkpoints_connected']
    assert all(initial['invariants'].values()) and initial['FK_ok'] and initial['source_audit']['source_clear']
    faces=read(P/'face_audit_v1.json');strike=read(P/'strike_analysis_v1.json');commands=read(P/'command_audit_v1.json');comparison=read(P/'comparison_v1.json')
    assert faces['passed'] and faces['initial_three_faces_pass'] and faces['completed_5s'] and faces['after2s_all6_pass_fraction']==0
    assert faces['maximum_readonly_reconstruction_error']<1e-10
    case=strike['cases'][n.name];assert case['six_string_down_pass'] and case['six_string_up_pass'] and case['other75_targets_exact'] and case['right_wrist_hand_contact_steps']==0
    assert commands['passed'] and commands['cases'][n.name]['targets75_exact'] and comparison['passed']
    result=comparison['results'][n.name]
    assert result['maximum_body_change_from2s_mm']<1 and result['maximum_SO3_change_from2s_deg']<1
    assert result['support_contact_steps']['right_upper_arm_body_contacts']>1000 and result['support_contact_steps']['right_hip_body_contacts']>1000
    raw=read(n/'initial_values.json');reference=read(baseline/'initial_values.json');names=raw['joint_names']
    frozen=[i for i,name in enumerate(names) if not name.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]
    assert len(frozen)==57 and all(raw['native_initial_state']['human_dof_states'][i]==reference['native_initial_state']['human_dof_states'][i] for i in frozen)
    assert raw['PD_properties']==reference['PD_properties']
    assert read(P/'config_v1/report.json')['canonical_angles_guitar_human_poses_exact_to_source']
    assert len(read(P/'search_v1/search.json')['rows'])==2 and len(read(P/'search_v2/search.json')['selected'])==1
    short=next((P/'interactive/sessions').glob('*/trial_000'))
    assert read(short/'report.json')['completed'] and read(short/'report.json')['physics_steps']==48
    for file in ('physics_endpoint_contacts.json','six_joint_target_rows.json','pick_feedback_effort_rows.json'):
        rows=read(short/'media'/file)['rows'];full=read(n/'media'/file)['rows'];assert rows==full[:len(rows)]
    for file in [initial_dir/'current_neck_support_v1/artifacts_v1/provenance_v1.json',P/'artifacts_v1/provenance_v2.json']:
        data=read(file);assert data['inputs_before']==data['inputs_after'] and data['producer_sha256_before']==data['producer_sha256_after']
        verify(data['producer'],data['producer_sha256_before'])
        for row in data['outputs']:assert sha(row['source'])==sha(row['destination'])==row['source_sha256']==row['output_sha256']
    for file in P.glob('artifacts_v1/*provenance*.json'):
        data=read(file)
        if 'inputs_after' in data:assert data['inputs_before']==data['inputs_after']
        if 'producer_sha256_after' in data:assert data['producer_sha256_before']==data['producer_sha256_after']
    for movie in report['videos'].values():assert sha(movie['path'])==movie['sha256'] and movie['stream']['nb_read_frames']=='151'
    own=list(A.glob('*right_shift*.py'))+list((A/'right_shift_pose_test_v1').glob('*.py'))+list(P.glob('artifacts_v1/*.py'))+[Path(__file__)]
    for file in own:ast.parse(file.read_text());verify(file,sha(file))
    docs=[P/'README.md',P/'CHANGED_FILES_v1.md',P/'review_final_v1.md',A/'RIGHT_SHIFT_INITIAL_COMPLETION_V1.md',A/'right_shift_pose_test_v1/README.md',initial_dir/'README.md',initial_dir/'current_neck_support_v1/README_v3.md',initial_dir/'right_shift10_comparison_v1/README_v3.md',P/'artifacts_v1/README_v4.md',P.parents[1]/'video/right_shift_initial_v1/INDEX_v4.md']
    links=0
    for file in docs:
        assert not re.search(r'\{(?:AR|A|P|V)\}',file.read_text())
        for target in re.findall(r'\]\(([^)]+)\)',file.read_text()):
            assert target.startswith('/'),(file,target)
            path=Path(re.sub(r':\d+$','',target));line=re.search(r':(\d+)$',target);assert path.exists(),(file,path)
            if line:
                assert path.suffix not in ('.png','.mp4') and 1<=int(line[1])<=len(path.read_text().splitlines())
            links+=1
        verify(file,sha(file))
    save(P/'source_final_v2.json',{'preserved':preserved,'append_prefixes':updates,'scope':'prior immutable chain plus current source/native/analyses and baseline/candidate archive copies; only documented main navigation appends; partial packaging retained, latest corrected docs identify successful delivery; not passive equilibrium/full grip/checkpoint learning'})
    video_dir=P.parents[1]/'video/right_shift_initial_v1'
    files=sorted(f for base in (P,initial_dir,video_dir) for f in base.rglob('*') if f.is_file())
    save(P/'artifact_inventory_v2.json',{'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in files]})
    save(P/'final_verification_v2.json',{'passed':True,'preserved_input_versions':len(preserved),'inventory_files':len(files),'unique_source_angle_candidates':2,'source_audit_versions':2,'selected_source':'right10mm','full_native_runs':1,'full_native_physics_steps':1200,'viewer_short_checks':1,'viewer_check_physics_steps':48,'successful_baseline_archive_copy_count':22,'successful_candidate_archive_media_copy_count':31,'six_string_down_pass':True,'six_string_up_pass':True,'initial57_DOF_exact':True,'after2s_all6_face_gate_pass_fraction':0,'headless_preset_exact_prefix':True,'desktop_GUI_verified':False,'links_checked':links,'scope':'baseline preserved and right-shift support/virtual-pick comparison; larger startup22.91mm/5.01deg settling retained; not left-hand-release/full-grip/learned-song/passive-equilibrium robustness'})
    print('baseline and right-shift preservation passed',len(preserved),'input versions',len(files),'files',flush=True)

if __name__=='__main__':main()
