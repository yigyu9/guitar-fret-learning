"""Retry the terminal crashed negative trial once in a preserved new path."""
from pathlib import Path
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2'
B=R/'docs/2026-10-12/stability_adapter_2/results'
P=B/'quiet_index_support_authority_v1';OLD=B/'initial_middle3_alignment_v1'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):Path(p).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    condition='minus_retry_v2'
    assert read(P/'minus_execution.json')['exit_code']==-11
    crash=read(P/'minus_native_crash.json')
    assert crash['terminal']=='native_process_crash_before_support_input'
    assert all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in crash['output_inventory'].items())
    P.mkdir(parents=True,exist_ok=True)
    assert not any((P/n).exists() for n in [condition+'.log',condition+'_inputs.json',condition+'_invocation.json',condition+'_execution.json','native/'+condition])
    baseline=read(OLD/'native/initial_values.json');inventory=read(OLD/'artifact_inventory.json')
    for name in ['initial_values.json','report.json']:
        p=OLD/'native'/name;assert sha(p)==inventory[str(p)]['sha256']
    trial=A/'trials/initial_middle3_alignment_v1/middle3_initial_at_goal.json'
    assert read(trial)==baseline['input_trial']
    paths={Path(__file__).resolve(),A/'run_quiet_index_support.py',A/'QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md',
        A/'QUIET_INDEX_SUPPORT_EXECUTION.md',A/'QUIET_INDEX_NATIVE_RETRY_V2.md',A/'run_quiet_index_support_phase.py',
        P/'minus_execution.json',P/'minus_native_crash.json',trial,OLD/'native/initial_values.json',OLD/'native/report.json',OLD/'artifact_inventory.json',
        A/'__init__.py',A/'plot_joint_hold.py',A/'config.json',A/'assets/humanoid_fixed_lower.xml',A/'assets/humanoid_fixed_lower.json',
        B/'palm_neck_side_v1/facet_distal_search/search.json',B/'palm_neck_side_v1/facet_native_short/probe.json',
        B/'palm_neck_side_v1/initial_audit_v2/audit.json',B/'finger_grip_hold_v1/short/baseline/report.json',
        B/'thigh_palm_support_v1/search_near_touch.json',B/'torso_hold_native_collision_v1/initial_collision/shape_properties.json',
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')}
    # Include every relative local import, including imports inside functions.
    pending=[A/'run_quiet_index_support.py'];scanned=set()
    while pending:
        p=pending.pop()
        if p in scanned:continue
        scanned.add(p);paths.add(p)
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node,ast.ImportFrom) and (node.level or (node.module or '').startswith('stability_adapter_2.')):
                if node.level:
                    assert node.level==1
                    modules=[node.module.split('.')[0]] if node.module else [v.name for v in node.names]
                else:modules=[node.module.split('.')[1]]
                for module in modules:
                    child=A/(module+'.py')
                    assert child.is_file(),child
                    pending.append(child)
    paths.update(Path(p) for p in read(A/'assets/humanoid_fixed_lower.json')['input_sha256'])
    reference=B/'left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125'
    paths.update([reference/'states.json',reference/'report.json'])
    config=read(A/'config.json');paths.update(R/config[n] for n in ['humanoid_asset','guitar_asset','pose_source','gain_source'])
    paths.update(p for p in (R/'tab2body/assets/mesh').iterdir() if p.is_file())
    before={str(p):sha(p) for p in sorted(paths,key=str)}
    assert all(before[p]==baseline['input_sha256'][p] for p in before if p in baseline['input_sha256'])
    input_file=P/(condition+'_inputs.json');save(input_file,before)
    before[str(input_file)]=sha(input_file);manifest={}
    for p,h in before.items():
        p=Path(p);relative=p.relative_to(R) if str(p).startswith(str(R)+'/') else Path('external')/Path(*p.parts[1:])
        dest=P/(condition+'_source')/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        assert sha(dest)==h;manifest[str(p)]=dict(snapshot=str(dest),sha256=h)
    save(P/(condition+'_source_manifest.json'),manifest)
    command=[sys.executable,'-u','-m','stability_adapter_2.run_quiet_index_support','--trial',str(trial),
        '--inputs',str(input_file),'--condition','minus','--out',str(P/'native'/condition)]
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',
        MPLCONFIGDIR='/tmp/stability2_index_support',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
    keys=['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MUJOCO_GL','MPLBACKEND','MPLCONFIGDIR','PYTHONPATH','LD_LIBRARY_PATH']
    save(P/(condition+'_invocation.json'),dict(command=command,environment={k:env[k] for k in keys},input_sha256=before))
    start=time.monotonic()
    with (P/(condition+'.log')).open('xb') as log:result=subprocess.run(command,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
    after={p:sha(p) for p in before};terminal='completed' if result.returncode==0 else 'error'
    report=P/'native'/condition/'report.json'
    if result.returncode!=0 and report.exists():
        data=read(report)
        if data['physics_steps']==0 and data['checks'].get('direct_native_source_gate') is False:terminal='initial_geometry_rejected_zero_steps'
    preserved=all(Path(p).stat().st_size==v['size'] and sha(p)==v['sha256'] for p,v in crash['output_inventory'].items())
    save(P/(condition+'_execution.json'),dict(command=command,environment={k:env[k] for k in keys},exit_code=result.returncode,
        terminal_state=terminal,wall_seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after=after,
        prior_partial_outputs_unchanged=preserved,log_sha256=sha(P/(condition+'.log'))))
    print((P/(condition+'.log')).read_text()[-4000:]);assert before==after and preserved and terminal!='error'


if __name__=='__main__':main()
