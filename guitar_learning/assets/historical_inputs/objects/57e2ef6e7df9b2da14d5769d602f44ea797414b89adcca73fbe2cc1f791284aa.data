"""Finalize provenance without changing any consumed trial source or data."""
from pathlib import Path
import hashlib
import json
import shutil
import ast

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())


def main():
    before = read(PHASE/'native_v2/inputs_before.json')['sha256']
    allowed = [str(ROOT/'stability_adapter_2'/n) for n in ('PLAN.md','README.md')]
    changed = [p for p,h in before.items() if sha(p) != h]
    assert sorted(changed) == sorted(allowed)
    assert all(sha(PHASE/'main_before'/Path(p).name)==before[p] for p in allowed)
    after = read(PHASE/'native_v2/inputs_after.json')
    summary = read(PHASE/'analysis/summary.json')
    assert after['inputs_unchanged'] and summary['policy_prefix_exact_reproduction']
    assert summary['next_observation_history_max_error'] == 0
    assert summary['completed_5s_physics_recording'] and all(summary['checks'].values())
    assert all(sha(p)==h for p,h in summary['input_sha256'].items())
    manifest = read(PHASE/'figures/policy_timeline_v3/manifest.json')
    assert all(sha(p)==h for p,h in manifest['inputs_sha256'].items())
    assert all(sha(p)==h for p,h in manifest['outputs_sha256'].items())
    assert sha(manifest['producer']) == manifest['producer_sha256']
    final = PHASE/'source_final'; final.mkdir(exist_ok=False)
    sources = [ROOT/'stability_adapter_2'/n for n in (
        'STRIKE_LIVE_GUITAR_PROBE_PLAN.md','STRIKE_TRANSFER_RECORDING_CONTINUATION.md',
        'strike_native_view.py','run_strike_live_probe.py','run_strike_live_probe_v2.py',
        'strike_probe_preserved_run.py','analyze_strike_live_probe.py','seal_strike_live_probe.py', 'README.md','PLAN.md')]
    syntax = {}
    for source in sources:
        shutil.copy2(source,final/source.name)
        assert sha(source)==sha(final/source.name)
        if source.suffix=='.py': ast.parse(source.read_text(),feature_version=(3,8));syntax[str(source)]=True
    review = PHASE/'review.md'; assert review.is_file()
    producer_manifests = list((PHASE/'figures').rglob('*manifest*.json'))
    inventory = {str(p): {'sha256': sha(p), 'bytes': p.stat().st_size}
                 for p in sorted(PHASE.rglob('*')) if p.is_file()}
    (PHASE/'artifact_inventory.json').write_text(json.dumps({'files':inventory,
        'excludes': ['artifact_inventory.json','final_verification.json'], 'review_sha256':sha(review)},indent=2)+'\n')
    verification = {'native_initializations_completed': 3, 'physical_rollouts': 2,
        'probe_only_physics_steps': 0, 'first_policy_physics_steps': 196,
        'final_physics_steps': 1200, 'final_policy_steps': 49, 'policy_end_time_s':196/240,
        'recording_5s_complete':True, 'policy_playing_success':False,'learning_updates':0,
        'source_and_data_preservation': {'inputs_before':len(before),'during_run_changed':after['changed'],
            'after_run_changed_only_authorized_main_documents':changed,'main_before_verified':True},
        'review_sha256':sha(review),'python38_syntax':syntax,
        'final_sources':{str(p):sha(p) for p in sources},
        'inventory_sha256':sha(PHASE/'artifact_inventory.json'),
        'limitations':['passive continuation is not playing evaluation',
            'no terminal196 native pq sample in final trace',
            'passive checks exclude continuous source geometry safety and upper-body-pose finite checks',
            'changed actuator/initial pose; checkpoint generalized transfer not certified'],
        'artifact_files':len(inventory), 'producer_manifests':[str(p) for p in producer_manifests]}
    (PHASE/'final_verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    assert all(sha(p)==d['sha256'] for p,d in inventory.items())
    print(json.dumps({'artifact_files':len(inventory),'review_sha256':sha(review),'preservation_pass':True}))


if __name__ == '__main__': main()
