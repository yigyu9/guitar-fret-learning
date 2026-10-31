"""Verify preserved inputs, recorded contact coverage and native media copies."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1'
V=ROOT/'docs/2026-10-19/stability_adapter_2/video/chest_contact_cycle_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    n=P/'native_v1';analysis=read(P/'analysis_v2.json');pins=read(n/'attempt.json')['input_sha256'];checks=list(analysis['checks'].values());nav=read(P/'documentation_append_v1.json')
    excluded=set(analysis['scoped_audit_exact_exclusions'])
    for path,h in pins.items():
        if path in excluded:continue
        exact=sha(path)==h
        proof=analysis['native_main_PLAN_prefix_proof']
        if not exact and path==proof['source']:
            b=Path(proof['before_copy']).read_bytes();exact=hashlib.sha256(b).hexdigest()==h and Path(path).read_bytes().startswith(b)
        if not exact and path in nav:
            b=Path(nav[path]['before_copy']).read_bytes();exact=hashlib.sha256(b).hexdigest()==h and Path(path).read_bytes().startswith(b)
        checks.append(exact)
    for path,h in analysis['input_sha256'].items():
        same=sha(path)==h
        if not same and path==analysis['native_main_PLAN_prefix_proof']['source']:
            b=Path(analysis['analysis_PLAN_before_copy']).read_bytes();same=hashlib.sha256(b).hexdigest()==h and Path(path).read_bytes().startswith(b)
        checks.append(same)
    for path,row in nav.items():checks.append(sha(row['before_copy'])==row['before_sha256'] and Path(path).read_bytes().startswith(Path(row['before_copy']).read_bytes()))
    capture=read(n/'media/capture.json');checks.append([r['physics_step'] for r in capture['frames']]==list(range(0,3841,8)))
    for frame in capture['frames']:
        checks.append(frame['render_preserves_states']);checks.extend(sha(p)==h for p,h in frame['image_sha256'].items())
    for row in read(n/'report.json')['videos'].values():checks.append(sha(row['path'])==row['sha256'] and int(row['stream']['nb_read_frames'])==481)
    for row in read(P/'artifacts_v1/copy_manifest_v1.json')['entries']:checks.append(sha(row['source'])==sha(row['copy'])==row['sha256'])
    for name in ('artifact_before_v1.json','artifact_before_v2.json'):
        for row in read(P/'artifacts_v1'/name)['inputs']:checks.append(sha(row['path'])==row['sha256'])
    checks.extend(v['total_steps']==3840 and 0<=v['positive_lambda_steps']<=v['contact_steps']<=3840 for v in analysis['actual_native_contacts'].values())
    save(P/'source_final_v1.json',{'native_before_inputs':pins,'navigation_prefixes':nav,'scoped_exclusions':analysis['scoped_audit_exact_exclusions'],'global_native_inputs_unchanged':analysis['global_native_inputs_unchanged'],'global_input_mismatches':analysis['global_input_mismatches'],'own_sources':{str(ROOT/'stability_adapter_2'/f):sha(ROOT/'stability_adapter_2'/f) for f in ('run_chest_contact_cycle_v1.py','analyze_chest_contact_cycle_v1.py','analyze_chest_contact_cycle_v2.py','verify_chest_contact_cycle_v1.py','CHEST_CONTACT_CYCLE_PLAN_V1.md')}})
    files=sorted(f for b in (P,V) for f in b.rglob('*') if f.is_file() and f.name not in ('artifact_inventory_v1.json','final_verification_v1.json'))
    save(P/'artifact_inventory_v1.json',{'files':{str(p):sha(p) for p in files}})
    save(P/'final_verification_v1.json',{'passed':all(checks),'checks':len(checks),'failures':sum(not x for x in checks),'physical_runs':1,'physics_steps':3840,'files':len(files),'audit_scope':'actual/shared inputs excluding exactly4 independently edited fresh_music files; global native guard remains failed and original report is preserved','global_native_report_completed':analysis['global_native_report_completed']})
    assert all(checks);print('PASS',len(checks),'checks',len(files),'files')
if __name__=='__main__':main()
