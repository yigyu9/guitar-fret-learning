"""Close source-only reach evidence and retain the prior free-guitar experiment chain."""
import ast
import hashlib
import json
import re
from pathlib import Path

P=Path(__file__).resolve().parent;R=P.parents[4];A=R/'stability_adapter_2';B=P.parent/'user_guided_no_left_v1'
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
    raw=read(P/'source_v1/report.json');analytic=read(P/'source_v2/report.json');radial=read(P/'radial_bound_v1.json');depth=read(P/'depth_bound_v1.json')
    assert len(raw['rows'])==4 and len(analytic['rows'])==3
    assert all(not r['reachable'] for r in raw['rows']) and all(not r['accepted_for_native'] for r in analytic['rows'])
    assert sum(len(r['samples']) for r in raw['rows']+analytic['rows'])==172
    assert all(r['other75_targets_exact'] for r in raw['rows']+analytic['rows'])
    assert radial['passed'] and depth['passed'] and len(radial['rows'])==81 and len(depth['rows'])==6
    assert abs(radial['maximum_fixed_elbow_pick_radius_m']-.3881251802900909)<1e-12
    assert abs(depth['lane_G_y_m']+.325)<1e-12
    assert all(min(row['minimum_possible_error_each_string_m'])>.006 for row in depth['rows'])
    assert not list(P.glob('native_*'))
    sources=list(A.glob('elbow_wrist_*.py'))+list(P.glob('artifacts_v*/*.py'))+[Path(__file__)]
    for file in sources:ast.parse(file.read_text());verify(file,sha(file))
    docs=[P/'README.md',P/'CHANGED_FILES_v1.md',A/'ELBOW_WRIST_STRIKE_COMPLETION_V1.md',P/'review_final_v1.md']+list(P.glob('artifacts_v*/README*.md'));links=0
    for file in docs:
        for target in re.findall(r'\]\((/[^)]+)\)',file.read_text()):
            path=Path(re.sub(r':\d+$','',target));line=re.search(r':(\d+)$',target)
            assert path.exists(),(file,path)
            if line:assert 1<=int(line[1])<=len(path.read_text().splitlines())
            links+=1
    save(P/'source_final_v1.json',{'preserved':preserved,'append_prefixes':updates,'scope':'prior completed free-guitar chain including documented historic limitations; source-only reach/geometry input maps and plot producers; depth helper imports composed with prior pinned tab2body sources; no native strike execution or clearance certificate'})
    files=sorted(f for f in P.rglob('*') if f.is_file())
    save(P/'artifact_inventory_v1.json',{'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in files]})
    save(P/'final_verification_v1.json',{'passed':True,'preserved_input_versions':len(preserved),'inventory_files':len(files),'source_paths':7,'source_samples':172,'source_accepted':0,'new_native_runs':0,'new_video_count':0,'checkpoint_connections':0,'training_updates':0,'radial_rows':81,'depth_optimized_rows':6,'links_checked':links,'scope':'evidence integrity passes; present fixed-proximal/held-finger default-lane reach is insufficient; no universal six-joint impossibility or actual strike success claim'})
    print('source-only reach evidence and preservation passed',len(preserved),'input versions',len(files),'files')


if __name__=='__main__':main()
