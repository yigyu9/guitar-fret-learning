"""Seal reviewed transfer results and their actual before-import source snapshots."""
import hashlib
import json
from pathlib import Path
import shutil


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    phase=Path(__file__).resolve().parent;root=phase.parents[4]
    expected_review='e7397bb100d4abb30ff51d3981743ab4718d0f633ad4fbcd59cc00869e732308'
    assert digest(phase/'review.md')==expected_review
    current_core=[];snapshot_counts={}
    for name in ('base_v2','rate','gain_v2'):
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
        for rel in ('stability_adapter_2/run_strike_transfer_iteration.py','stability_adapter_2/strike_transfer_preserved_run.py','stability_adapter_2/STRIKE_TRANSFER_ITERATION_PLAN.md'):
            assert digest(root/rel)==before[str(root/rel)]
        for video in report['videos'].values():assert digest(Path(video['path']))==video['sha256']
    analysis=phase/'analysis_final';manifest=json.loads((analysis/'inputs_before.json').read_text())['sha256']
    assert json.loads((analysis/'inputs_after.json').read_text())['unchanged']
    assert all(digest(Path(p))==h for p,h in manifest.items())
    copies=phase/'source_final';copies.mkdir(exist_ok=False)
    for name in ('run_strike_transfer_iteration.py','strike_transfer_preserved_run.py','analyze_strike_transfer_trials.py','STRIKE_TRANSFER_ITERATION_PLAN.md','PLAN.md','README.md'):
        src=root/'stability_adapter_2'/name;shutil.copy2(src,copies/name);current_core.append({'source':str(src),'copy':str(copies/name),'sha256':digest(src)})
    (copies/'manifest.json').write_text(json.dumps(current_core,indent=2)+'\n')
    inventory={str(p.relative_to(phase)):digest(p) for p in sorted(phase.rglob('*')) if p.is_file() and p.name not in ('artifact_inventory.json','final_verification.json')}
    (phase/'artifact_inventory.json').write_text(json.dumps({'sha256':inventory},indent=2)+'\n')
    (phase/'final_verification.json').write_text(json.dumps({'review_sha256':expected_review,'clean_trials':['base_v2','rate','gain_v2'],'completed_physics_steps':3600,'archived_source_counts':snapshot_counts,'current_trial_implementation_exact':True,'analysis_input_hashes_exact':True,'video_hashes_exact':True,'artifact_count':len(inventory),'inventory_sha256':digest(phase/'artifact_inventory.json'),'music_success':False,'scope':'Reviewed 3-condition diagnostic; previous input source versions are retained in each source_before. Current main copies include subsequent progress append.'},indent=2)+'\n')
    print('sealed transfer comparison',len(inventory),'artifacts')


if __name__=='__main__':main()
