"""Verify retained input versions, actual runs and byte-exact media copies."""
import ast
import hashlib
import json
import re
from pathlib import Path

P=Path(__file__).resolve().parent;R=P.parents[4];A=R/'stability_adapter_2'
B=P.parent/'left_hand_off_current_v1';V=R/'docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1'
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
            for key,val in obj.items():
                if key in ('input_sha256','image_sha256') and isinstance(val,dict):
                    for path,h in val.items():verify(path,h)
                else:maps(val)
            if 'path' in obj:
                for key in ('sha256','sha256_before','sha256_after'):
                    if key in obj:verify(obj['path'],obj[key])
        elif isinstance(obj,list):
            for value in obj:maps(value)
    # Big physics/command arrays carry no input maps; their raw bytes are pinned by analyses.
    for f in sorted(P.rglob('*.json')):
        if f.name in ('physics_endpoint_contacts.json','trace.json','controls.json','final_state.json','initial_values.json') or f.name.endswith('_rows.json'):
            continue
        maps(read(f))
    rows=[r for f in sorted(P.glob('search_v*/search.json')) for r in read(f)['rows']]
    assert len(rows)==21 and sum(r['accepted_for_native'] for r in rows)==7
    analysis=read(P/'analysis_final_v2.json');timeline=read(P/'timelines_final_v1.json');summary=read(P/'selected_summary_v1.json')
    assert analysis['passed'] and timeline['passed'] and summary['passed']
    cases=analysis['cases'];assert len(cases)==9
    assert sum(r['physics_steps'] for r in cases.values())==2780 and sum(r['completed_control_steps'] for r in cases.values())==694
    assert sum(r['completed_5s'] for r in cases.values())==2
    png=0
    for label,row in cases.items():
        n=P/label;report=read(n/'report.json')
        assert report['inputs_unchanged'] and not report['forbidden_calls'] and not report['strap_enabled'] and not report['checkpoints_connected']
        assert report['training_updates']==0
        if row['physics_steps']:
            capture=read(n/'media/capture.json')
            assert capture['frames'][0]['physics_step']==0 and capture['frames'][-1]['physics_step']==row['physics_steps']
            assert all(f['render_preserves_states'] for f in capture['frames'])
            for frame in capture['frames']:
                for path,h in frame['image_sha256'].items():verify(path,h);png+=1
        if row['completed_5s']:
            assert row['left_free_5s'] and row['left_task_zero_on_applied_steps'] and row['actual_left_contact_steps']==0
            assert summary['movement_and_hand_contacts'][label]['right_wrist_hand_contact_steps']==0
    wave=timeline['comparisons']['native_upper50_v14_elbow5'];assert wave['initial_full_state_and_first2p5s_trace_exact']
    assert timeline['cases']['native_upper50_v14_elbow5']['elbow_actual_2p5_to_5s_range_deg']>9
    manifest=read(P/'artifacts_v1/provenance_v1.json')
    assert len(manifest['videos'])==16 and len(manifest['native_png_copies'])==12
    for row in manifest['videos']+manifest['native_png_copies']:
        assert row['byte_exact'] and row['source_sha256']==row['copy_sha256']
        verify(row['source_path'],row['source_sha256']);verify(row['copy_path'],row['copy_sha256'])
        if 'ffprobe_source' in row:assert row['ffprobe_source']['stream']==row['ffprobe_copy']['stream']
    docs=[P/'README.md',P/'CHANGED_FILES_v1.md',A/'USER_GUIDED_NO_LEFT_COMPLETION_V1.md',P/'artifacts_v1/README.md',V/'INDEX.md',P/'review_final_v1.md'];links=0
    for file in docs:
        for target in re.findall(r'\]\((/[^)]+)\)',file.read_text()):
            path=Path(re.sub(r':\d+$','',target));line=re.search(r':(\d+)$',target)
            assert path.exists(),(file,path)
            if line:assert 1<=int(line[1])<=len(path.read_text().splitlines())
            links+=1
    sources=list(A.glob('*user_guided_no_left*.py'))+[A/'left_wrist_tracking_off_v2.py',P/'artifacts_v1/build_artifacts_v1.py',Path(__file__)]
    for file in sources:
        if file.name=='search_user_guided_no_left_v9.py':
            try:ast.parse(file.read_text())
            except SyntaxError:pass
            else:raise AssertionError('historical failed V9 unexpectedly changed')
        else:ast.parse(file.read_text())
        verify(file,sha(file))
    save(P/'source_final_v1.json',{'preserved':preserved,'append_prefixes':updates,'scope':'prior preservation chain with documented historical artifact limitations; current before maps, native/analysis/artifact inputs and capture images; V12 missing before pins verified compositionally through parent V11 maps; V9 historical syntax failure retained; no retroactive before-pin claim'})
    files=sorted(f for f in P.rglob('*') if f.is_file())+sorted(f for f in V.rglob('*') if f.is_file())
    save(P/'artifact_inventory_v1.json',{'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in files]})
    save(P/'final_verification_v1.json',{'passed':True,'preserved_input_versions':len(preserved),'inventory_files':len(files),'source_candidates':21,'source_accepted':7,'source_rejected':14,'native_attempts':9,'physics_steps':2780,'completed_controls':694,'completed_5s_cases':2,'left_contact_and_task_zero_in_selected_5s':True,'selected_native_png_count':604,'all_native_png_count':png,'videos_copied':16,'png_copied':12,'links_checked':links,'historical_V9_syntax_failure_preserved':True,'scope':'short static and small-elbow tests under active human control; no passive equilibrium, fret/strike success, or training claim'})
    print('preservation and actual five-second evidence passed',len(preserved),'input versions',len(files),'files')


if __name__=='__main__':main()
