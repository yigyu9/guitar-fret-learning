"""Seal reviewed transfer results and their actual before-import source snapshots."""
import hashlib
import json
from pathlib import Path
import shutil


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    phase=Path(__file__).resolve().parent;root=phase.parents[4]
    expected_review='eda5b3a49e44ab0da0c551a2a6407deecc162cfebad9171086f9dfab0b4007f4'
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
        for rel in ('stability_adapter_2/run_strike_ready_incremental.py','stability_adapter_2/strike_ready_incremental_preserved_run.py','stability_adapter_2/STRIKE_READY_INCREMENTAL_PLAN.md'):
            assert digest(root/rel)==before[str(root/rel)]
        for video in report['videos'].values():assert digest(Path(video['path']))==video['sha256']
    analysis=phase/'analysis';manifest=json.loads((analysis/'inputs_before.json').read_text())['sha256']
    assert json.loads((analysis/'inputs_after.json').read_text())['unchanged']
    assert all(digest(Path(p))==h for p,h in manifest.items())
    audit=json.loads((phase/'goal_audit.json').read_text())
    assert audit['inputs_unchanged'] and all(digest(Path(p))==h for p,h in audit['input_sha256'].items())
    copies=phase/'source_final';copies.mkdir(exist_ok=False)
    for name in ('run_strike_ready_incremental.py','strike_ready_incremental_preserved_run.py','analyze_strike_transfer_trials_v2.py','STRIKE_READY_INCREMENTAL_PLAN.md','PLAN.md','README.md'):
        src=root/'stability_adapter_2'/name;shutil.copy2(src,copies/name);current_core.append({'source':str(src),'copy':str(copies/name),'sha256':digest(src)})
    (copies/'manifest.json').write_text(json.dumps(current_core,indent=2)+'\n')
    inventory={str(p.relative_to(phase)):digest(p) for p in sorted(phase.rglob('*')) if p.is_file() and p.name not in ('artifact_inventory.json','final_verification.json')}
    (phase/'artifact_inventory.json').write_text(json.dumps({'sha256':inventory},indent=2)+'\n')
    (phase/'final_verification.json').write_text(json.dumps({'review_sha256':expected_review,'clean_trials':['native'],'completed_physics_steps':1200,'archived_source_counts':snapshot_counts,'current_trial_implementation_exact':True,'analysis_input_hashes_exact':True,'video_hashes_exact':True,'artifact_count':len(inventory),'inventory_sha256':digest(phase/'artifact_inventory.json'),'music_success':False,'scope':'Reviewed native POSITION READY0/closed1 incremental previousgoal+2delta arm goals, same RECOVER and finger4+.2rad; no timely hit, physicalaccepted1 phase0 with timing minus382.09ms; Gmax7.095deg/PLAYregion148of162, NOTADOPTED as music success; PREP49controls/25sampled native states/firstactor inputoutput exact,162goalformulas and integral hold/rateclip verified;152trace vs151camera frames, terminal844 continues physics through1200; no force-duality or source-native equivalence or fullsong certification; archived closure inputs retained'},indent=2)+'\n')
    print('sealed READY-incremental',len(inventory),'artifacts')


if __name__=='__main__':main()
