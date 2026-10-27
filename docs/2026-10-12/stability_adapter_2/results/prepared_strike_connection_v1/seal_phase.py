"""Seal the completed connection diagnostic after all phase writers finish."""
from pathlib import Path
import hashlib
import json
import shutil

P=Path(__file__).resolve().parent
A=P.parents[4]/'stability_adapter_2'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')

def main():
    assert not (P/'artifact_inventory.json').exists()
    closure=load(P/'native/inputs_before.json')['sha256']
    changes=[p for p,h in closure.items() if sha(Path(p))!=h]
    assert set(changes)<={str(A/'PLAN.md'),str(A/'README.md')}
    for name in ('PLAN.md','README.md'):
        assert sha(P/'main_before'/name)==closure[str(A/name)]
        assert (A/name).read_bytes().startswith((P/'main_before'/name).read_bytes())
    assert (P.parents[1]/'VISUAL_REPORT.md').read_bytes().startswith((P/'VISUAL_REPORT_before_append.md').read_bytes())
    previous=P.parent/'guitar_relative_ready_v1'
    old=load(previous/'artifact_inventory.json')['files']
    assert all(sha(Path(p))==r['sha256'] for p,r in old.items())
    assert sha(previous/'artifact_inventory.json')==load(previous/'final_verification.json')['inventory_sha256']
    assert load(P/'native/inputs_after.json')['inputs_unchanged']
    analysis=load(P/'analysis/summary.json')
    assert all(sha(Path(p))==h for p,h in load(P/'analysis/inputs_before.json').items())
    assert load(P/'analysis/inputs_after.json')['unchanged']
    assert all(sha(Path(p))==h for p,h in load(P/'event_analysis/inputs_before.json').items())
    assert load(P/'event_analysis/inputs_after.json')['unchanged']
    assert all(sha(Path(p))==h for p,h in load(P/'contact_analysis/inputs_before.json').items())
    assert load(P/'contact_analysis/inputs_after.json')['unchanged']
    report=load(P/'native/data/report.json')
    assert report['completed_5s'] and all(report['checks'].values()) and report['actor_steps']>0
    assert analysis['preparation_native_prefix_exact'] and analysis['history_inverse_max_error']==0
    for video in report['videos'].values():
        assert sha(Path(video['path']))==video['sha256']
        assert video['stream']['nb_read_frames']=='151' and video['stream']['avg_frame_rate']=='30/1'
    names=('PREPARED_STRIKE_CONNECTION_PLAN.md','prepared_strike_start.py',
        'tests/test_prepared_strike_start.py','run_prepared_strike_connection.py',
        'prepared_strike_preserved_run.py','PLAN.md','README.md')
    destination=P/'source_final';destination.mkdir()
    for name in names:
        output=destination/name;output.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(A/name,output)
    save(P/'source_final_manifest.json',{str(A/name):sha(A/name) for name in names})
    excludes={'artifact_inventory.json','final_verification.json'}
    files={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(P.rglob('*'))
        if p.is_file() and p.name not in excludes}
    save(P/'artifact_inventory.json',{'files':files,'excludes':sorted(excludes),
        'review_sha256':sha(P/'review.md'),'note':'Logs and artifact writers closed before hashing. Seal stdout is outside this phase.'})
    assert all(sha(Path(p))==r['sha256'] for p,r in files.items())
    save(P/'final_verification.json',{'artifact_files':len(files),'inventory_mismatches':[],
        'previous_phase_files_checked':len(old),'previous_phase_changed':[],
        'authorized_main_appends':changes,'native_inputs_unchanged':True,'analysis_inputs_unchanged':True,
        'physics_steps':report['physics_steps'],'actor_steps':report['actor_steps'],
        'play_start_time_s':report['play_start_time_s'],'diagnostic_only':True,
        'strict_preparation_certified':False,'learning_updates':0,
        'review_sha256':sha(P/'review.md'),'inventory_sha256':sha(P/'artifact_inventory.json')})
    print('sealed actual Strike connection:',report['actor_steps'],'policy controls;',len(files),'artifacts')

if __name__=='__main__':main()
