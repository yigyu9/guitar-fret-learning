"""Audit consumed source versions and bounded native evidence, without rewriting it."""
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path('/home/ajou/yigyu/3')
PHASE=Path(__file__).resolve().parent
RUNS=('interrupt_native_v1','resume_native_v1','fake_memory_native_v1','dense_8env_native_v1','dense_8env_native_v2','pool_native_v1','pool_native_v2')
def load(path):return json.loads(path.read_text())
def digest(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()

if __name__=='__main__':
    preserved=defaultdict(list);preserved_count=0
    manifests=[ROOT/'guitar_learning/archive/20261018_before_reliability_music/archive_manifest.json',
        ROOT/'guitar_learning/archive/20261018_before_right_guide_scale_v2/archive_manifest.json',ROOT/'guitar_learning/archive/20261018_before_pool_normalization_v2/archive_manifest.json',
        PHASE/'source_run_v1/manifest.json',PHASE/'source_run_v2/manifest.json',PHASE/'source_run_v3/manifest.json',
        PHASE/'pool_before_tick_accounting/manifest.json',PHASE/'runner_before_resume_eligibility/manifest.json',PHASE/'main_before/manifest.json']
    for manifest in manifests:
        payload=load(manifest);rows=payload['files'] if isinstance(payload,dict) else payload
        for row in rows:
            source=row.get('original_path',row.get('path',row.get('source')))
            saved=row.get('archived_path',row.get('snapshot_path',row.get('archived',row.get('archive'))))
            assert digest(saved)==row['sha256'],saved
            preserved[(source,row['sha256'])].append(saved);preserved_count+=1
    variants=defaultdict(lambda:defaultdict(list));run_checks={};raw_ticks=raw_physics=resets=0
    keys=('changed_inputs','missing_import_pins','original_source_parity_errors','missing_worker_audits','worker_audit_read_errors','guard_violations','worker_failures','physical_flags_errors','cleanup_errors')
    for name in RUNS:
        folder=PHASE/name;report=load(folder/'report.json');assert all(not report[k] for k in keys),name
        expected='interrupted' if name=='interrupt_native_v1' else 'memory_guard' if name=='fake_memory_native_v1' else 'error' if name=='pool_native_v1' else 'updates_complete'
        assert report['stopped']==expected,name
        assert report['completed']==(expected=='updates_complete'),name
        pins=load(folder/'inputs_before.json')
        for path,sha in pins.items():variants[path][sha].append(name)
        audits=list(folder.glob('worker_*/audit_episode_*/initial_values.json'));resets+=len(audits)
        raw=list(folder.glob('worker_*/audit_episode_*/transition_*.json.gz'));raw_ticks+=len(raw)
        for path in raw:
            with gzip.open(path,'rt') as stream:row=json.load(stream)
            samples=row['info']['native_control']['physics_samples240'];measurements=row['info']['physics_measurements']
            assert len(samples)==len(measurements)==4,path
            for sample,measured in zip(samples,measurements):
                assert sample['native']['physics_step']==sample['geometry']['physics_step']==measured['physics_step']==measured['music']['physics_step'],path
            raw_physics+=4
        run_checks[name]=dict(stopped=report['stopped'],completed=report['completed'],source_and_guard_checks_clear=True,input_files=len(pins),reset_audits=len(audits),raw_ticks=len(raw))
    union={};versioned=[]
    for path,versions in sorted(variants.items()):
        current=digest(path);union[path]=[]
        if len(versions)>1:versioned.append(path)
        for sha,names in sorted(versions.items()):
            copies=preserved.get((path,sha),[])
            assert current==sha or copies,(path,sha)
            union[path].append(dict(sha256=sha,runs=names,current_file_matches=current==sha,preserved_copies=copies))
    assert set(versioned)=={str(ROOT/'guitar_learning'/p) for p in ('dense_environment.py','task_sampling.py','tests/test_task_sampling.py')},versioned
    model_paths=[p for p in union if Path(p).suffix.lower() in ('.xml','.obj','.stl','.ply','.dae')]
    with (PHASE/'inputs_union_v1.json').open('x') as stream:json.dump(union,stream,indent=2);stream.write('\n')
    result=dict(completed=True,scope='before/after native audits plus preserved source variants; planned interrupt/fake guard plus preserved first pool mismatch; only corrected retry is a passing pool validation',runs=run_checks,unique_input_paths=len(union),input_path_sha_versions=sum(len(v) for v in union.values()),versioned_consumed_paths=versioned,all_versions_preserved_or_current_match=True,verified_preserved_copies=preserved_count,model_input_count=len(model_paths),model_input_paths=model_paths,reset_audits=resets,raw_control_ticks=raw_ticks,raw_physics_samples=raw_physics)
    with (PHASE/'preservation_check_v1.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print({k:result[k] for k in ('completed','unique_input_paths','input_path_sha_versions','verified_preserved_copies','model_input_count','reset_audits','raw_control_ticks','raw_physics_samples')})
