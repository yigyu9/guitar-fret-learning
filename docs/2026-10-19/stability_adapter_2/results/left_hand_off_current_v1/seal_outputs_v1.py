"""Close current evidence while retaining all prior source/asset/output versions."""
import ast
import hashlib
import json
import re
from pathlib import Path

P=Path(__file__).resolve().parent;R=P.parents[4];A=R/'stability_adapter_2'
B=P.parent/'right_arm_wrap_forward_v1';V=R/'docs/2026-10-19/stability_adapter_2/video/left_hand_off_current_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
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
        actual=cache[path]
        if actual==h:preserved.append({'path':path,'expected_sha256':h,'resolution':'current exact'});return
        snap=snapshots.get(key);assert snap,(path,'unexpected change')
        assert sha(snap)==h and Path(path).read_bytes().startswith(Path(snap).read_bytes())
        preserved.append({'path':path,'expected_sha256':h,'resolution':'exact prefix snapshot of authorized append','snapshot':snap})
    for row in prior:verify(row['path'],row['expected_sha256'])
    for row in read(B/'artifact_inventory_v1.json')['files']:verify(row['path'],row['sha256'])
    for name in ('source_final_v1.json','artifact_inventory_v1.json','final_verification_v1.json'):verify(B/name,sha(B/name))
    # All explicit before maps and composed source/native/analysis maps remain preserved.
    def maps(obj):
        if isinstance(obj,dict):
            for key,val in obj.items():
                if key in ('input_sha256','image_sha256') and isinstance(val,dict):
                    for path,h in val.items():verify(path,h)
                else:maps(val)
        elif isinstance(obj,list):
            for value in obj:maps(value)
    for f in sorted(P.rglob('*.json')):
        obj=read(f);maps(obj)
        if isinstance(obj,dict) and obj and all(isinstance(k,str) and k.startswith('/') and isinstance(v,str) and len(v)==64 for k,v in obj.items()):
            for path,h in obj.items():verify(path,h)
    rows=[r for f in sorted(P.glob('search_v*/search.json')) for r in read(f)['rows']]
    assert len(rows)==6 and sum(r['accepted_for_native'] for r in rows)==2
    n=P/'native_back100_static';report=read(n/'report.json');capture=read(n/'media/capture.json')
    assert not report['completed'] and report['physics_steps']==224 and report['control_steps']==56
    assert report['failure']['message']=='guitar safety displacement' and report['inputs_unchanged']
    assert not report['forbidden_calls'] and not report['strap_enabled'] and not report['checkpoints_connected']
    assert capture['frames'][0]['physics_step']==0 and capture['frames'][-1]['physics_step']==224
    assert len(capture['frames'])==29 and all(r['render_preserves_states'] for r in capture['frames'])
    off=read(P/'left_off_analysis_v1.json');assert off['passed'] and not off['maintained_for_5s']
    assert off['left_contact_presence_steps']==off['left_tracking_enabled_steps']==0 and off['left_virtual_force_and_task_exact_zero']
    manifest=read(P/'artifacts_v1/provenance_v3.json')
    # Each artifact input/producer/output is recorded explicitly by its owner; verify every absolute path/hash record.
    def records(obj):
        if isinstance(obj,dict):
            if 'path' in obj:
                for key in ('sha256','sha256_before','sha256_after'):
                    if key in obj:verify(obj['path'],obj[key])
            for value in obj.values():records(value)
        elif isinstance(obj,list):
            for value in obj:records(value)
    records(manifest)
    for f in P.rglob('*.json'):records(read(f))
    for camera,row in report['videos'].items():
        source=Path(row['path']);copy=V/('left_off_back100_static_'+camera+'_v2.mp4');assert sha(source)==sha(copy)==row['sha256']
        verify(source,row['sha256']);verify(copy,row['sha256'])
        assert int(row['stream']['nb_read_frames'])==29 and abs(float(row['stream']['duration'])-29/30)<1e-6
    docs=[P/'README.md',P/'CHANGED_FILES_v1.md',A/'LEFT_HAND_OFF_CURRENT_COMPLETION_V1.md',P/'artifacts_v1/README_V3.md',V/'INDEX_V3.md',P/'artifacts_v1/ARTIFACT_HISTORY_LIMITATION_V1.md'];links=0
    for file in docs:
        for target in re.findall(r'\]\((/[^)]+)\)',file.read_text()):
            path=Path(re.sub(r':\d+$','',target));line=re.search(r':(\d+)$',target)
            assert path.exists(),(file,path)
            if line:assert 1<=int(line[1])<=len(path.read_text().splitlines())
            links+=1
    sources=list(A.glob('*left_hand_off_current*.py'))+[A/'left_wrist_tracking_off_v1.py']+list((P/'artifacts_v1').glob('*.py'))+[Path(__file__)]
    for file in sources:ast.parse(file.read_text())
    save(P/'source_final_v1.json',{'preserved':preserved,'append_prefixes':updates,'scope':'prior forward preservation chain (including documented historic artifact producer limitations); current source6/native1 partial/analysis/native frames/artifact before maps; V1 artifact provenance original bytes overwritten then regenerated (not historical before evidence); V3 artifacts closed; analysis helper pins resolved compositionally through current timeline/native maps'})
    files=sorted(f for f in P.rglob('*') if f.is_file())+sorted(f for f in V.rglob('*') if f.is_file())
    save(P/'artifact_inventory_v1.json',{'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in files]})
    save(P/'final_verification_v1.json',{'passed':True,'preserved_input_versions':len(preserved),'inventory_files':len(files),'source_candidates':6,'source_accepted':2,'native_runs':1,'physics_steps':224,'completed_5s':False,'left_contact_and_task_zero':True,'native_png':58,'links_checked':links,'scope':'evidence integrity passes; guitar maintenance fails; no five-second stability claim'})
    print('verification passed; physical maintenance failed')

if __name__=='__main__':main()
