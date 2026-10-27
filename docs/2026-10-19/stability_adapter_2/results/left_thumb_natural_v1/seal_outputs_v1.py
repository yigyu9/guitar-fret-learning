"""Seal thumb-only initial changes and the retained six-joint strike demonstration."""
import ast
import hashlib
import json
import re
from pathlib import Path

P=Path(__file__).resolve().parent;R=P.parents[4];A=R/'stability_adapter_2';B=P.parent/'elbow_wrist_ready_pose_v1'
def read(p):return json.loads(Path(p).read_text())
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
        assert Path(row['path']).read_text().splitlines()[row['heading_line']-1].startswith('## ')
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
    raw=[r for v in (1,2) for r in read(P/('search_v%d/report.json'%v))['rows']]
    assert len(raw)==4 and sum(r['accepted_for_native'] for r in raw)==2
    assert read(P/'search_v2/back24mm_audit.json')['accepted_for_native']
    thumb=read(P/'thumb_audit_v1.json')
    assert thumb['passed'] and thumb['other76_initial_angles_exact'] and thumb['guitar_initial_raw_states_exact'] and thumb['PD_properties_exact']
    assert all(row['raw_pose_exact'] for row in thumb['nonthumb_initial_pose_comparison'])
    assert thumb['thumb5_targets_fixed_all300_controls'] and thumb['thumb_guitar_contact_records']==0
    analysis=read(P/'strike_analysis_v1.json');commands=read(P/'command_audit_v1.json')
    assert analysis['passed'] and commands['passed']
    selected=analysis['cases']['native_v1']
    assert selected['six_string_down_pass'] and selected['six_string_up_pass'] and len(selected['releases'])==12
    assert all(r['lane_core'] for r in selected['releases'])
    native_names=list(analysis['cases']);assert len(native_names)==1
    physics=controls=videos=0
    import xml.etree.ElementTree as ET
    mesh_counts={}
    for name in native_names:
        n=P/name;report=read(n/'report.json');initial=read(n/'initial_verification.json')
        assert report['completed'] and report['inputs_unchanged'] and not report['forbidden_calls'] and report['failure'] is None
        assert report['physics_steps']==1200 and report['control_steps']==300
        assert not report['strap_enabled'] and not report['checkpoints_connected'] and not report['training_updates']
        assert all(initial['invariants'].values()) and initial['FK_ok'] and initial['source_audit']['source_clear']
        case=analysis['cases'][name]
        assert case['left_contact_steps']==0 and case['right_wrist_hand_contact_steps']==0 and case['other75_targets_exact']
        assert commands['cases'][name]['initial_and_first_2s_exact'] and commands['cases'][name]['targets75_exact']
        physics+=report['physics_steps'];controls+=report['control_steps'];videos+=len(report['videos'])
        for movie in report['videos'].values():
            assert sha(movie['path'])==movie['sha256'] and movie['stream']['nb_read_frames']=='151'
        inputs=read(n/'attempt.json')['input_sha256'];geometry=read(A/'assets/om_body_geometry_v3/manifest.json')
        for label,asset in [('human',A/'assets/humanoid_fixed_lower.xml'),('guitar',Path(geometry['asset']))]:
            xml=ET.parse(asset).getroot();meshdir=(asset.parent/xml.find('compiler').get('meshdir')).resolve()
            declarations=[(meshdir/m.get('file')).resolve() for m in xml.findall('./asset/mesh')]
            assert str(asset) in inputs and all(str(p) in inputs for p in declarations)
            mesh_counts[label]=len(declarations)
    assert physics==1200 and controls==300 and videos==3
    sources=list(A.glob('*left_thumb_natural*.py'))+list(P.glob('artifacts_v*/*.py'))+[Path(__file__)]
    for file in sources:ast.parse(file.read_text());verify(file,sha(file))
    docs=[P/'README.md',P/'CHANGED_FILES_v1.md',A/'LEFT_THUMB_NATURAL_COMPLETION_V1.md',P/'review_final_v1.md']+list(P.glob('artifacts_v*/README*.md'))+list((P.parents[1]/'video/left_thumb_natural_v1').glob('INDEX*.md'));links=0
    for file in docs:
        for target in re.findall(r'\]\((/[^)]+)\)',file.read_text()):
            path=Path(re.sub(r':\d+$','',target));line=re.search(r':(\d+)$',target)
            assert path.exists(),(file,path)
            if line:assert 1<=int(line[1])<=len(path.read_text().splitlines())
            links+=1
    media=P.parents[1]/'video/left_thumb_natural_v1'
    for version in (1,):
        provenance=read(P/('artifacts_v%d/provenance_v%d.json'%(version,version)))
        assert provenance['producer_sha256_before']==provenance['producer_sha256_after']
        verify(provenance['producer'],provenance['producer_sha256_before'])
        assert provenance['inputs_before']==provenance['inputs_after']
        for row in provenance['outputs']:
            verify(row['source'],row['sha256']);verify(row['destination'],row['sha256'])
    save(P/'source_final_v1.json',{'preserved':preserved,'append_prefixes':updates,'scope':'prior immutable chain plus current source/native/command/media inputs; sourceV1 late-anchor limit retained and composed with prior SHA; V2 staged pre-pins; approved navigation appends; thumb-only initial changes and single virtual-pick cycle, not contact/learning/anatomical certification'})
    files=sorted([f for f in P.rglob('*') if f.is_file()]+[f for f in media.rglob('*') if f.is_file()])
    save(P/'artifact_inventory_v1.json',{'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in files]})
    save(P/'final_verification_v1.json',{'passed':True,'preserved_input_versions':len(preserved),'inventory_files':len(files),'source_candidates':4,'source_geometry_accepted':2,'source_rejected':2,'source_accepted_excluded_from_native':1,'new_native_runs':1,'physics_steps':physics,'control_steps':controls,'new_video_count':videos,'checkpoint_connections':0,'training_updates':0,'XML_mesh_declarations':mesh_counts,'links_checked':links,'six_string_down_pass':True,'six_string_up_pass':True,'selected_native':'native_v1','thumb5_only_initial_change':True,'nonthumb_initial_raw_poses_exact':True,'scope':'evidence integrity passes; thumb5 initial changes retain other76 angles/nonthumb poses and measured single-cycle strike; commandaudit first2 self-reference not previous-case dynamics equality; contact0, not learned fret/anatomical certification/passive equilibrium'})
    print('thumb-only evidence and preservation passed',len(preserved),'input versions',len(files),'files')



if __name__=='__main__':main()
