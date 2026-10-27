"""Close this phase after all writers and logs finish; no physics or policy."""
from pathlib import Path
import hashlib
import json
import shutil

P = Path(__file__).resolve().parent
ROOT = P.parents[4]
A = ROOT/'stability_adapter_2'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):
    return json.loads(path.read_text())
def save(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')

def main():
    assert not (P/'artifact_inventory.json').exists()
    closure=load(P/'native_v4/inputs_before.json')['sha256']
    allowed={str(A/'PLAN.md'),str(A/'README.md')}
    changed=[p for p,h in closure.items() if sha(Path(p))!=h]
    assert set(changed)<=allowed, changed
    for name in ('PLAN.md','README.md'):
        assert sha(P/'main_before'/name)==closure[str(A/name)]
        assert (A/name).read_bytes().startswith((P/'main_before'/name).read_bytes())
    visual=P.parents[1]/'VISUAL_REPORT.md'
    assert visual.read_bytes().startswith((P/'VISUAL_REPORT_before_append.md').read_bytes())
    trace_baseline_exact=(P/'native_v4/data/trace.json').read_bytes()==(P/'native_v1/data/trace.json').read_bytes()
    trace_PI_exact=(P/'native_v3/data/trace.json').read_bytes()==(P/'native_v2/data/trace.json').read_bytes()
    assert trace_baseline_exact and trace_PI_exact
    baseline=load(P/'native_v1/data/controls.json');final=load(P/'native_v4/data/controls.json')
    goals_baseline_exact=all(a['final_targets_rad']==b['final_targets_rad'] for a,b in zip(baseline,final))
    assert len(baseline)==len(final)==300 and goals_baseline_exact
    analysis_inputs=load(P/'analysis/inputs_before.json')
    assert all(sha(Path(p))==h for p,h in analysis_inputs.items())
    assert load(P/'analysis/inputs_after.json')['unchanged']
    for version in ('v4_readiness','v4_readiness_v2'):
        folder=P/'figures'/version
        manifest,execution=load(folder/'manifest.json'),load(folder/'artifact_execution.json')
        assert manifest['input_closure_unchanged'] and execution['exit_code']==0
        assert manifest['producer_sha256']==execution['producer_sha256']==sha(Path(manifest['producer']))
        for key in ('inputs_sha256','outputs_sha256'):
            assert manifest[key]==execution[key]
            assert all(sha(Path(p))==h for p,h in manifest[key].items())
    previous=P.parent/'strike_live_guitar_probe_v1/artifact_inventory_v2.json'
    old_files=load(previous)['files']
    old_changed=[p for p,r in old_files.items() if sha(Path(p))!=r['sha256']]
    assert not old_changed, old_changed
    source=P/'source_final';source.mkdir()
    new_names=('GUITAR_RELATIVE_READY_PLAN.md','GUITAR_READY_TRACKING_REVISION.md',
        'STRIKE_PREPARATION_HANDOFF_REVISION.md','GUITAR_READY_BASELINE_SELECTION.md',
        'guitar_relative_readiness.py','guitar_relative_readiness_v2.py','preparation_joint_tracking.py',
        'strike_preparation_handoff.py','search_strike_ready_pose.py',
        'run_guitar_relative_ready.py','run_guitar_relative_ready_v2.py','run_guitar_relative_ready_v3.py',
        'run_guitar_relative_ready_v4.py','preparation_preserved_run.py','preparation_preserved_run_v2.py',
        'preparation_preserved_run_v3.py','preparation_preserved_run_v4.py','README.md','PLAN.md',
        'tests/test_guitar_relative_readiness.py','tests/test_guitar_relative_readiness_v2.py',
        'tests/test_preparation_joint_tracking.py','tests/test_strike_preparation_handoff.py')
    for name in new_names:
        target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(A/name,target)
    save(P/'source_final_manifest.json',{str(A/name):sha(A/name) for name in new_names})
    excludes={'artifact_inventory.json','final_verification.json'}
    files={str(f):{'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(P.rglob('*'))
        if f.is_file() and f.name not in excludes}
    save(P/'artifact_inventory.json',{'files':files,'excludes':sorted(excludes),
        'review_sha256':sha(P/'review.md'),'note':'All trial/test/analysis logs closed before hashing; no phase-local live seal log.'})
    mismatch=[p for p,r in files.items() if sha(Path(p))!=r['sha256']]
    assert not mismatch
    trials={v:load(P/v/'data/report.json') for v in ('native_v1','native_v2','native_v3','native_v4')}
    assert all(r['completed_5s'] and all(r['checks'].values()) and r['actor_steps']==0 for r in trials.values())
    assert all(load(P/v/'inputs_after.json')['inputs_unchanged'] for v in ('search_v1',*trials))
    save(P/'final_verification.json',{'artifact_files':len(files),'inventory_mismatches':mismatch,
        'source_closure_only_authorized_main_appends':changed,'previous_phase_files_checked':len(old_files),
        'previous_phase_changed':old_changed,'trial_count':len(trials),'physics_steps_total':sum(r['physics_steps'] for r in trials.values()),
        'all_trials_completed_5s':True,'actor_steps':0,'actual_PLAY_handoff_tested':False,
        'v4_trace_and_final_goals_exact_v1':trace_baseline_exact and goals_baseline_exact,
        'v3_trace_exact_v2':trace_PI_exact,'main_and_visual_report_prefixes_preserved':True,
        'analysis_and_figure_metadata_hashes_verified':True,
        'learning_updates':0,'final_entry':str(A/'preparation_preserved_run_v4.py'),
        'review_sha256':sha(P/'review.md'),'inventory_sha256':sha(P/'artifact_inventory.json')})
    print('phase sealed:',len(files),'artifacts, 4 x 5s; policy handoff not executed')

if __name__=='__main__':main()
