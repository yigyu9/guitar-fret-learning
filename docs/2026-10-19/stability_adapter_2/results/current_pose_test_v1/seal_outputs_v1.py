"""Seal standalone current-pose playback and native lifecycle checks."""
import ast
import hashlib
import json
import re
from pathlib import Path

P=Path(__file__).resolve().parent;R=P.parents[4];A=R/'stability_adapter_2';B=P.parent/'left_neck_three_face_v1'
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
    assert 'Critical: 0' in (P/'review_v1.md').read_text()
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
    lab=A/'current_pose_test_v1'
    reference=read(B/'native_off_v1/initial_values.json')
    cases=sorted(P.glob('sessions/*/trial_*/report.json'))+[P/'recreation_check_v1'/('trial_%03d'%i)/'report.json' for i in range(2)]
    assert len(cases)==3
    physics=0
    for reportfile in cases:
        n=reportfile.parent;r=read(reportfile)
        assert r['completed'] and r['failure'] is None and r['inputs_unchanged'] and not r['forbidden_calls']
        assert r['physics_steps']==48 and r['control_steps']==12 and not r['strap_enabled'] and not r['checkpoints_connected']
        assert read(n/'initial_values.json')==reference
        for file in ('physics_endpoint_contacts.json','six_joint_target_rows.json','pick_feedback_effort_rows.json'):
            rows=read(n/'media'/file)['rows'];old=read(B/'native_off_v1/media'/file)['rows']
            assert rows==old[:len(rows)]
        for movie in r['videos'].values():assert sha(movie['path'])==movie['sha256']
        physics+=r['physics_steps']
    assert read(P/'recreation_check_v1/verification.json')['passed'] and physics==144
    provenance=read(P/'artifacts_v1/provenance_v1.json')
    assert provenance['inputs_before']==provenance['inputs_after']
    assert provenance['producer_sha256_before']==provenance['producer_sha256_after']
    for row in provenance['outputs']:assert sha(row['source'])==sha(row['destination'])==row['sha256']
    for f in list(lab.glob('*.py'))+list(P.glob('artifacts_v1/*.py'))+list(P.glob('*.py')):ast.parse(f.read_text())
    docs=[lab/'README.md',lab/'COMPLETION.md',P/'README.md',P/'CHANGED_FILES_v2.md',P/'review_v1.md']+list(P.glob('artifacts_v1/*.md'))
    links=0
    for f in docs:
        for target in re.findall(r'\]\((/[^)]+)\)',f.read_text()):
            path=Path(re.sub(r':\d+$','',target));line=re.search(r':(\d+)$',target)
            assert path.exists(),(f,path)
            if line:
                assert path.suffix not in ('.png','.mp4')
                assert 1<=int(line[1])<=len(path.read_text().splitlines())
            links+=1
    for file in [*lab.iterdir(),*docs,Path(__file__)]:
        if file.is_file():verify(file,sha(file))
    save(P/'source_final_v1.json',{'preserved':preserved,'append_prefixes':updates,'scope':'prior evidence chain plus standalone playback inputs and native short checks; failed V1 remains; DISPLAY GUI integration unverified'})
    files=sorted(f for f in P.rglob('*') if f.is_file())
    save(P/'artifact_inventory_v1.json',{'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in files]})
    save(P/'final_verification_v1.json',{'passed':True,'preserved_input_versions':len(preserved),'inventory_files':len(files),'default_GUI_horizon_s':5,'successful_headless_checks':3,'headless_physics_seconds_each':.2,'total_headless_physics_steps':144,'same_prefix_exact':True,'fresh_simulator_recreation_count':2,'GUI_display_verified':False,'setup_failure_preserved':True,'links_checked':links,'critical_review_count':0,'scope':'initial/config/controller/native prefix and fresh scene lifecycle verified; desktop viewer/key dispatch not verified; short checks are not 5s gameplay or learning'})
    print('test-space preservation and native checks passed',len(preserved),'input versions',len(files),'files',flush=True)

if __name__=='__main__':main()
