"""Seal reviewed transfer results and their actual before-import source snapshots."""
import hashlib
import json
from pathlib import Path
import shutil


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    phase=Path(__file__).resolve().parent;root=phase.parents[4]
    expected_review='7e964c6b4acc45c52af45a739f16918d0918c0ce072599aeea443de7bdafe792'
    assert digest(phase/'review.md')==expected_review
    current_core=[];snapshot_counts={}
    for name in ('native',):
        run=phase/name;before=json.loads((run/'inputs_before.json').read_text())['sha256']
        after=json.loads((run/'inputs_after.json').read_text());report=json.loads((run/'data/report.json').read_text())
        assert after['inputs_unchanged'] and after['task_error'] is None
        assert report['completed_5s'] and report['physics_steps']==1200 and all(report['checks'].values())
        count=0
        for p,h in before.items():
            archived=run/'source_before'/Path(p).relative_to(root) if root in Path(p).parents else run/'no_archived_external_input'
            if archived.exists():assert digest(archived)==h;count+=1
            elif Path(p).is_file():assert digest(Path(p))==h
            else:raise AssertionError('missing input '+p)
        snapshot_counts[name]=count
        for rel in ('stability_adapter_2/run_strike_lateral_staging.py','stability_adapter_2/strike_lateral_staging_preserved_run.py','stability_adapter_2/STRIKE_LATERAL_STAGING_PLAN.md'):
            assert digest(root/rel)==before[str(root/rel)]
        for video in report['videos'].values():assert digest(Path(video['path']))==video['sha256']
    analysis=phase/'analysis';manifest=json.loads((analysis/'inputs_before.json').read_text())['sha256']
    assert json.loads((analysis/'inputs_after.json').read_text())['unchanged']
    assert all(digest(Path(p))==h for p,h in manifest.items())
    audit=json.loads((phase/'lateral_staging_audit.json').read_text())
    assert audit['inputs_unchanged'] and all(digest(Path(p))==h for p,h in audit['input_SHA256_before_parsing'].items())
    copies=phase/'source_final';copies.mkdir(exist_ok=False)
    for name in ('run_strike_lateral_staging.py','strike_lateral_staging_preserved_run.py','analyze_strike_transfer_trials_v2.py','STRIKE_LATERAL_STAGING_PLAN.md','PLAN.md','README.md'):
        src=root/'stability_adapter_2'/name;shutil.copy2(src,copies/name);current_core.append({'source':str(src),'copy':str(copies/name),'sha256':digest(src)})
    (copies/'manifest.json').write_text(json.dumps(current_core,indent=2)+'\n')
    inventory={str(p.relative_to(phase)):digest(p) for p in sorted(phase.rglob('*')) if p.is_file() and p.name not in ('artifact_inventory.json','final_verification.json')}
    (phase/'artifact_inventory.json').write_text(json.dumps({'sha256':inventory},indent=2)+'\n')
    (phase/'final_verification.json').write_text(json.dumps({'review_sha256':expected_review,'clean_trials':['native'],'completed_physics_steps':1200,'archived_source_counts':snapshot_counts,'current_trial_implementation_exact':True,'analysis_input_hashes_exact':True,'video_hashes_exact':True,'artifact_count':len(inventory),'inventory_sha256':digest(phase/'artifact_inventory.json'),'music_success':False,'scope':'Reviewed source-time-preserving lateral READY xy4mm staging before original measured ENTRY6mm.202common controls/102native prefix exact before firststage3.366667;251 source geometries/phase gates/formulas,125native anchors,300ratebounds exact.4timely hits/5physical last612ms premature,5scheduledREC,wrong2/miss6,PLAY through5s with no HOLD or actual terminal PD restore.1200physics151camera151trace27checks1109unchanged closure,Gmax7.095455/end4.355244. Not fullsong success, all30 policy actuation equivalence, or rigid-contact/cause certification.'},indent=2)+'\n')
    print('sealed lateral-staging',len(inventory),'artifacts')


if __name__=='__main__':main()
