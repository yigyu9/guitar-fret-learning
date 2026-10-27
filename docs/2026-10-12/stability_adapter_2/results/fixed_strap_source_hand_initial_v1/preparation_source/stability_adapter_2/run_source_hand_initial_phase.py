"""Archive and execute numeric preparation or one direct-gated physical trial."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]
A = R / 'stability_adapter_2'
B = R / 'docs/2026-10-12/stability_adapter_2/results'
P = B / 'fixed_strap_source_hand_initial_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage',choices=['preparation','native'])
    stage = parser.parse_args().stage
    assert not (P / (stage + '_execution.json')).exists()
    module = 'prepare_source_hand_initial' if stage == 'preparation' else 'run_source_hand_initial'
    proposal = B / 'initial_middle3_alignment_v1/proposal.json' if stage == 'preparation' else P / 'proposal.json'
    data = read(proposal)
    paths = set(Path(p) for p in data['input_sha256'])
    paths.update([Path(__file__).resolve(), A / (module+'.py'), proposal,
        A / 'SOURCE_HAND_INITIAL_EXECUTION.md', A / 'FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md',
        B / 'initial_middle3_alignment_v1/native/initial_values.json',
        B / 'fixed_strap_source_compatibility_v1/artifact_inventory.json',
        B / 'fixed_strap_source_compatibility_v1/joint_ranges.jsonl', Path(data['rows'][0]['trial_path'])])
    paths.update(A / n for n in ['warmstart_targets.py','environment.py','strap.py','initial_overlap.py',
        'palm_side_source_checks.py','build_fixed_lower_asset.py','capture_isaac_gym_initial.py',
        'run_small_wrist_recorded_diagnostic.py','near_contact_initial_audit.py','run_joint_hold.py',
        'gym_trial_recording.py','strap_trial_recording.py','SMALL_WRIST_MOTION_PLAN.md',
        'TORSO_HOLD_EXECUTION.md','TORSO_HOLD_AND_NATIVE_COLLISION_PLAN.md','STRAP_VIDEO_VISUALIZATION_PLAN.md'])
    paths.add(Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    before = {str(p):sha(p) for p in sorted(paths,key=str)}
    assert all(before[p] == h for p,h in data['input_sha256'].items())
    assert sha(A / 'run_small_wrist_recorded_diagnostic.py') == '34d50c9f95a1b100efce621470a099d0aa259df7bbf307e5c7e44c6927598ef6'
    snapshot = {}
    for p in paths:
        if p.parent == A or p.suffix == '.ttf' or p in [proposal, Path(data['rows'][0]['trial_path']), B / 'initial_middle3_alignment_v1/native/initial_values.json', B / 'fixed_strap_source_compatibility_v1/joint_ranges.jsonl']:
            relative = p.relative_to(R) if str(p).startswith(str(R)+'/') else Path('external') / Path(*p.parts[1:])
            dest = P / (stage+'_source') / relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest)
            assert sha(dest) == before[str(p)]
            snapshot[str(p)] = dict(snapshot=str(dest),sha256=before[str(p)])
    (P / (stage+'_source_manifest.json')).write_text(json.dumps(snapshot,indent=2)+'\n')
    command = [sys.executable,'-m','stability_adapter_2.'+module]
    if stage == 'native': command += ['--trial',data['rows'][0]['trial_path'],'--proposal',str(proposal),'--out',str(P/'native')]
    env = dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',
        MPLCONFIGDIR='/tmp/stability2_source_hand',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
    start = time.monotonic()
    with (P / (stage+'.log')).open('xb') as log:
        result = subprocess.run(command,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
    after = {p:sha(p) for p in before}
    terminal = 'completed' if result.returncode == 0 else 'error'
    if stage == 'native' and result.returncode != 0 and (P/'native/report.json').exists():
        report = read(P/'native/report.json')
        if report['physics_steps'] == 0 and report['checks'].get('direct_native_source_gate') is False:
            terminal = 'initial_geometry_rejected_zero_steps'
    (P / (stage+'_execution.json')).write_text(json.dumps(dict(command=command,
        environment={k:env[k] for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MUJOCO_GL','MPLBACKEND','MPLCONFIGDIR','PYTHONPATH','LD_LIBRARY_PATH']},
        exit_code=result.returncode,terminal_state=terminal,wall_seconds=time.monotonic()-start,
        input_sha256_before=before,input_sha256_after=after,log_sha256=sha(P/(stage+'.log'))),indent=2)+'\n')
    print((P / (stage+'.log')).read_text()[-6000:])
    assert before == after and terminal != 'error'


if __name__ == '__main__': main()
