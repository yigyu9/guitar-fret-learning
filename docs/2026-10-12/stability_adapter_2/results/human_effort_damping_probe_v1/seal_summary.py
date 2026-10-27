"""Seal reviewed transfer results and their actual before-import source snapshots."""
import hashlib
import json
from pathlib import Path
import shutil


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    phase=Path(__file__).resolve().parent;root=phase.parents[4]
    expected_review='71fb74b056cefa02a00f56e72cc8af10ead497a3407d11e861ebec51d0e48b6f'
    assert digest(phase/'review.md')==expected_review
    current_core=[];snapshot_counts={}
    for name in ('d0_off','d0_on','d1_off','d1_on'):
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
        for rel in ('stability_adapter_2/run_human_effort_damping_probe.py','stability_adapter_2/human_effort_damping_preserved_run.py','stability_adapter_2/HUMAN_EFFORT_DAMPING_PROBE_PLAN.md'):
            assert digest(root/rel)==before[str(root/rel)]
        for video in report['videos'].values():assert digest(Path(video['path']))==video['sha256']
    analysis=phase/'analysis';manifest=json.loads((analysis/'inputs_before.json').read_text())['sha256']
    assert json.loads((analysis/'inputs_after.json').read_text())['unchanged']
    assert all(digest(Path(p))==h for p,h in manifest.items())
    copies=phase/'source_final';copies.mkdir(exist_ok=False)
    for name in ('run_human_effort_damping_probe.py','human_effort_damping_preserved_run.py','analyze_human_effort_damping_probe.py','HUMAN_EFFORT_DAMPING_PROBE_PLAN.md','PLAN.md','README.md'):
        src=root/'stability_adapter_2'/name;shutil.copy2(src,copies/name);current_core.append({'source':str(src),'copy':str(copies/name),'sha256':digest(src)})
    (copies/'manifest.json').write_text(json.dumps(current_core,indent=2)+'\n')
    inventory={str(p.relative_to(phase)):digest(p) for p in sorted(phase.rglob('*')) if p.is_file() and p.name not in ('artifact_inventory.json','final_verification.json')}
    (phase/'artifact_inventory.json').write_text(json.dumps({'sha256':inventory},indent=2)+'\n')
    (phase/'final_verification.json').write_text(json.dumps({'review_sha256':expected_review,'clean_trials':['d0_off','d0_on','d1_off','d1_on'],'completed_physics_steps':4800,'archived_source_counts':snapshot_counts,'current_trial_implementation_exact':True,'analysis_input_hashes_exact':True,'video_hashes_exact':True,'artifact_count':len(inventory),'inventory_sha256':digest(phase/'artifact_inventory.json'),'music_success':False,'scope':'Reviewed four fresh human R12 EFFORT stiffness0 damping0/original conditions, single RShoulder_z OFF0/ONnominal10Nm request first4steps and others80zero; originalPOSITION plus .05target restored afterstep4, not initialtarget; 4800physics/8videos/9checks each; newd0 full152sample states match previous activationv2 exactly; measured scalar response retaineddamping changesbehavior, no isolated force sensor torque measurement or fullStrike equivalence certification; archived input versions preserved.'},indent=2)+'\n')
    print('sealed EFFORT damping pulse',len(inventory),'artifacts')


if __name__=='__main__':main()
