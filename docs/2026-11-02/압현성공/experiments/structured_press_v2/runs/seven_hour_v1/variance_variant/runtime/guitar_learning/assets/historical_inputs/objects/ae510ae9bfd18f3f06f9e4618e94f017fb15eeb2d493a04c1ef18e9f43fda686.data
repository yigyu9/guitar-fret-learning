"""Close this diagnostic's inputs, native media, copies and append-only navigation."""
from pathlib import Path
import json
import hashlib

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1'
V=ROOT/'docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
    assert not Path(p).exists();Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def main():
    checks=[];inputs={};prefixes=read(P/'documentation_append_v1.json')
    for path,row in prefixes.items():
        before=Path(row['before_copy']).read_bytes();after=Path(path).read_bytes()
        checks.append(after.startswith(before) and sha(row['before_copy'])==row['before_sha256'])
    for version in (1,2):
        n=P/f'native_v{version}';report=read(n/'report.json');checks.append(report['completed'] and report['physics_steps']==3840 and not report['forbidden_calls'])
        checks.append(report['strap_enabled'] is False and report['right_strike_enabled'] is False and not report['checkpoints_connected'])
        for path,h in read(n/'attempt.json')['input_sha256'].items():
            exact=sha(path)==h;preserved=exact
            if not exact and path in prefixes:
                b=Path(prefixes[path]['before_copy']).read_bytes();preserved=hashlib.sha256(b).hexdigest()==h and Path(path).read_bytes().startswith(b)
            checks.append(preserved);inputs.setdefault(path,[]).append({'version':version,'before_sha256':h,'exact_current':exact,'preserved_exact_or_append_prefix':preserved})
        capture=read(n/'media/capture.json');checks.append([f['physics_step'] for f in capture['frames']]==list(range(0,3841,8)))
        for f in capture['frames']:
            checks.append(f['render_preserves_states']);checks.extend(sha(path)==h for path,h in f['image_sha256'].items())
        for row in report['videos'].values():checks.append(sha(row['path'])==row['sha256'] and int(row['stream']['nb_read_frames'])==481)
        analysis=read(P/f'analysis_v{version}.json');checks.extend(analysis['invariants'].values());checks.extend(sha(path)==h for path,h in analysis['input_sha256'].items())
        manifest=read(P/'artifacts_v1'/f'copy_manifest_v{version}.json')
        for row in manifest['entries']:checks.append(sha(row['source'])==sha(row['copy'])==row['sha256'])
    comparison=read(P/'repeat_comparison_v1.json');checks.append(comparison['same_initial_state'] and comparison['guitar_trace_exact'])
    checks.extend(sha(path)==h for path,h in comparison['input_sha256'].items())
    checks.extend(sha(path)==h for path,h in read(P/'v1_evidence_scope_correction.json')['source_sha256'].items())
    checks.extend(sha(row['path'])==row['sha256'] for row in read(P/'artifacts_v1/artifact_before_v2.json')['inputs'])
    checks.extend(sha(row['path'])==row['sha256'] for row in read(P/'artifacts_v1/documentation_before_v3.json')['inputs'])
    own_sources=[Path(__file__).resolve()]+[p for p in (ROOT/'stability_adapter_2').glob('*left_grip_release_cycle_v*.py')]+[ROOT/'stability_adapter_2'/f'LEFT_GRIP_RELEASE_CYCLE_PLAN_V{x}.md' for x in (1,2)]
    save(P/'source_final_v1.json',{'scope':'this phase current input versions; main PLAN changes verified as appended exact execution prefix, historical external README prepend not retrospectively certified','inputs':inputs,'own_sources':{str(p):sha(p) for p in own_sources},'navigation_prefixes':prefixes})
    files=sorted(p for base in (P,V) for p in base.rglob('*') if p.is_file() and p.name not in ('artifact_inventory_v1.json','final_verification_v1.json'))
    save(P/'artifact_inventory_v1.json',{'files':{str(p):sha(p) for p in files}})
    save(P/'final_verification_v1.json',{'passed':all(checks),'checks':len(checks),'unique_native_input_files':len(inputs),'inventory_files':len(files),'failures':sum(not x for x in checks),'physical_runs':2,'seconds_each':16,'before_input_limitation_v1':'A/config.json not pinned in V1; V2 includes before/after hash, no retrospective V1 certification'})
    assert all(checks);print('PASS',len(checks),'checks;',len(files),'preserved files')

if __name__=='__main__':main()
