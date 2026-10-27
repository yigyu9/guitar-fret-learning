"""Archive and execute preparation or the single recorded middle3 relaxation trial."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time

R = Path(__file__).resolve().parents[1]
A = R / 'stability_adapter_2'
P = R / 'docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['preparation', 'native'])
    stage = parser.parse_args().stage
    assert not (P / (stage + '_execution.json')).exists() and not (P / (stage + '.log')).exists()
    module = 'prepare_fixed_strap_middle_relax_v2' if stage == 'preparation' else 'run_palm_witness_initial_diagnostic'
    paths = [Path(__file__).resolve(), A / (module + '.py'), A / 'FIXED_STRAP_MIDDLE_RELAX_V2_PLAN.md', A / 'warmstart_targets.py']
    command = ['/home/ajou/miniconda3/envs/rl38/bin/python', '-u', '-m', 'stability_adapter_2.' + module]
    if stage == 'native':
        trial = A / 'trials/fixed_strap_middle_relax_v2/middle3_minus015.json'
        proposal = P / 'proposal.json'
        data = json.loads(proposal.read_text())
        assert not (P / 'native').exists() and all(data['checks'].values()) and sha(trial) == data['rows'][0]['trial_sha256']
        paths += [trial, proposal] + [Path(p) for p in data['input_sha256']] + [A / n for n in ['run_small_wrist_recorded_diagnostic.py', 'near_contact_initial_audit.py', 'strap_trial_recording.py']]
        assert sha(A / 'run_palm_witness_initial_diagnostic.py') == '2f6565f3e5bf79b682a5704fcbbaf5978ff925c53fd6a130a92f46e145bdd380'
        assert sha(A / 'run_small_wrist_recorded_diagnostic.py') == '34d50c9f95a1b100efce621470a099d0aa259df7bbf307e5c7e44c6927598ef6'
        command += ['--trial', str(trial), '--proposal', str(proposal), '--out', str(P / 'native')]
    else:
        old = P.parent / 'joint_only_fixed_strap_v1'
        paths += [old / 'proposal.json', old / 'native/initial_values.json']
        data = json.loads((old / 'proposal.json').read_text())
        paths += [Path(p) for p in data['input_sha256']] + [Path(data['rows'][0]['trial_path'])]
        previous = P.parent / 'fixed_strap_middle_relax_v1'
        paths += [previous / 'artifact_inventory.json', previous / 'final_verification.json', A / 'FIXED_STRAP_MIDDLE_RELAX_DECISION.md']
        paths += [Path(p) for p in json.loads((previous / 'artifact_inventory.json').read_text())]
    paths = list(dict.fromkeys(paths))
    before = {str(p): sha(p) for p in paths}
    snapshot = P / (stage + '_source')
    snapshot.mkdir(exist_ok=False)
    manifest = {}
    for p in paths:
        if p.suffix == '.py' or p.name in ['FIXED_STRAP_MIDDLE_RELAX_V2_PLAN.md', 'FIXED_STRAP_MIDDLE_RELAX_DECISION.md']:
            dest = snapshot / p.relative_to(R)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            assert sha(dest) == before[str(p)]
            manifest[str(p)] = dict(snapshot=str(dest), sha256=before[str(p)])
    (P / (stage + '_source_manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MUJOCO_GL='disable', MPLBACKEND='Agg', MPLCONFIGDIR='/tmp/stability2_small_wrist', PYTHONPATH=str(R / 'isaacgym/python') + ':' + str(R), LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
    start = time.monotonic()
    with (P / (stage + '.log')).open('xb') as log:
        result = subprocess.run(command, cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = {str(p): sha(p) for p in paths}
    (P / (stage + '_execution.json')).write_text(json.dumps(dict(command=command, environment={k:env[k] for k in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MUJOCO_GL', 'MPLBACKEND', 'MPLCONFIGDIR', 'PYTHONPATH', 'LD_LIBRARY_PATH']}, exit_code=result.returncode, wall_seconds=time.monotonic() - start, input_sha256_before=before, input_sha256_after=after, log_sha256=sha(P / (stage + '.log'))), indent=2) + '\n')
    print((P / (stage + '.log')).read_text()[-4500:])
    assert result.returncode == 0 and before == after


if __name__ == '__main__':
    main()
