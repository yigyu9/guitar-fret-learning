"""Freeze a compact source search or the inherited direct-gated native trial."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2'
B=R/'docs/2026-10-12/stability_adapter_2/results';P=B/'source_hand_wrist_clearance_v1'
OLD=B/'fixed_strap_source_hand_initial_v1'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['search','native']);stage=parser.parse_args().stage
    assert not (P/(stage+'_execution.json')).exists()
    module='search_wrist_clearance' if stage=='search' else 'run_wrist_clearance_candidate'
    paths={Path(__file__).resolve(),A/(module+'.py'),A/'SOURCE_HAND_WRIST_CLEARANCE_PLAN.md',
        OLD/'native/initial_values.json',OLD/'artifact_inventory.json',OLD/'proposal.json',
        B/'coupled_support_source_v1/model.json', A/'run_source_hand_initial.py',
        B/'fixed_strap_source_compatibility_v1/joint_ranges.jsonl',
        B/'torso_hold_native_collision_v1/initial_collision/shape_properties.json',
        B/'palm_neck_side_v1/initial_audit_v2/audit.json'}
    paths.update(A/n for n in ['config.json','coupled_support_source.py','build_fixed_lower_asset.py','search_multi_face_grip.py',
        'environment.py','control.py','strap.py','trial_settings.py','physics_presets.py','initial_overlap.py',
        'palm_side_source_checks.py','face_referenced_geometry.py','plot_neck_palm.py','source_patch_interval.py','warmstart_targets.py'])
    config=read(A/'config.json')
    paths.update(R/config[n] for n in ['humanoid_asset','guitar_asset','pose_source','gain_source'])
    paths.add(A/'assets/humanoid_fixed_lower.xml')
    paths.update(p for p in (R/'tab2body/assets/mesh').iterdir() if p.is_file())
    paths.add(Path(read(OLD/'proposal.json')['rows'][0]['trial_path']))
    direct=set(paths)
    if stage=='native':
        data=read(P/'proposal.json');assert read(P/'search.json')['selected'] is not None
        paths.update(Path(p) for p in data['input_sha256'])
        new_inputs={P/'proposal.json',P/'search.json',P/'search_execution.json',P/'source_prediction.json',A/'search_wrist_clearance.py',Path(data['rows'][0]['trial_path'])}
        paths.update(new_inputs);direct.update(new_inputs)
        paths.update(A/n for n in ['run_small_wrist_recorded_diagnostic.py','near_contact_initial_audit.py','run_joint_hold.py',
            'capture_isaac_gym_initial.py','gym_trial_recording.py','strap_trial_recording.py','SMALL_WRIST_MOTION_PLAN.md',
            'TORSO_HOLD_EXECUTION.md','TORSO_HOLD_AND_NATIVE_COLLISION_PLAN.md','STRAP_VIDEO_VISUALIZATION_PLAN.md'])
        paths.add(Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    before={str(p):sha(p) for p in sorted(paths,key=str)}
    if stage=='native':
        assert all(before[p]==h for p,h in data['input_sha256'].items())
        assert sha(A/'run_source_hand_initial.py')=='a318a62b47f93dce1d3c526a64297d419341cc4983784e0aa4e2443b4f11a8b7'
        assert sha(A/'run_small_wrist_recorded_diagnostic.py')=='34d50c9f95a1b100efce621470a099d0aa259df7bbf307e5c7e44c6927598ef6'
    manifest={}
    for p in paths:
        if p in direct or p.parent==A or p.suffix=='.ttf':
            relative=p.relative_to(R) if str(p).startswith(str(R)+'/') else Path('external')/Path(*p.parts[1:])
            dest=P/(stage+'_source')/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
            assert sha(dest)==before[str(p)];manifest[str(p)]=dict(snapshot=str(dest),sha256=before[str(p)])
    (P/(stage+'_source_manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    command=[sys.executable,'-m','stability_adapter_2.'+module]
    if stage=='native':command+=['--trial',data['rows'][0]['trial_path'],'--proposal',str(P/'proposal.json'),'--out',str(P/'native')]
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',
        MPLCONFIGDIR='/tmp/stability2_wrist_clearance',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
    start=time.monotonic()
    with(P/(stage+'.log')).open('xb') as log:result=subprocess.run(command,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
    after={p:sha(p) for p in before};terminal='completed' if result.returncode==0 else 'error'
    if stage=='native' and result.returncode!=0 and (P/'native/report.json').exists():
        report=read(P/'native/report.json')
        if report['physics_steps']==0 and report['checks'].get('direct_native_source_gate') is False:terminal='initial_geometry_rejected_zero_steps'
    (P/(stage+'_execution.json')).write_text(json.dumps(dict(command=command,
        environment={k:env[k] for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MUJOCO_GL','MPLBACKEND','MPLCONFIGDIR','PYTHONPATH','LD_LIBRARY_PATH']},
        exit_code=result.returncode,terminal_state=terminal,wall_seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after=after,
        log_sha256=sha(P/(stage+'.log'))),indent=2)+'\n')
    print((P/(stage+'.log')).read_text()[-8000:]);assert before==after and terminal!='error'


if __name__=='__main__':main()
