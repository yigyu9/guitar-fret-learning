"""Preserve and run the saved OFF/ON analysis once; no native initialization."""
from pathlib import Path
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
P = B / 'quiet_wrist_yz_feedback_v1'
BASE = B / 'initial_middle3_alignment_v1/native'
Z = B / 'quiet_wrist_z_support_authority_v1'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, value): Path(p).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    assert not any((P / n).exists() for n in ['analysis.json', 'series.json', 'analysis.log',
        'analysis_source', 'analysis_invocation.json', 'analysis_execution.json', 'analysis_source_manifest.json'])
    paths = {Path(__file__).resolve(), A / 'analyze_quiet_wrist_yz_feedback.py',
             A / 'QUIET_WRIST_YZ_FEEDBACK_PLAN.md', A / 'QUIET_WRIST_YZ_FEEDBACK_EXECUTION.md',
             Z / 'comparison_v2.json', Z / 'artifact_inventory.json', P / 'preflight.json'}
    for folder in [BASE, P / 'native/off', P / 'native/on']:
        paths.update(folder / name for name in ['initial_values.json', 'states.jsonl', 'trace.jsonl',
            'controls.jsonl', 'contacts.jsonl', 'report.json', 'initial_grip_audit.json', 'capture.json', 'videos.json'])
        for frame in read(folder / 'capture.json')['frames']:
            paths.update(Path(p) for key in ['image_sha256', 'raw_image_sha256'] for p in frame[key])
        paths.update(Path(v['path']) for v in read(folder / 'videos.json').values())
    for condition in ['off', 'on']:
        for suffix in ['_execution.json', '_inputs.json', '_invocation.json', '_source_manifest.json', '.log']:
            paths.add(P / (condition + suffix))
        execution = read(P / (condition + '_execution.json'))
        assert execution['exit_code'] == 0 and execution['terminal_state'] == 'completed'
        paths.update(Path(p) for p in execution['input_sha256_before'])
    before = {str(p): sha(p) for p in sorted(paths, key=str)}
    copies = []
    # Native recordings stay at their original paths; snapshot code/plans and metadata only.
    selected = {Path(__file__).resolve(), A / 'analyze_quiet_wrist_yz_feedback.py',
                A / 'QUIET_WRIST_YZ_FEEDBACK_PLAN.md', A / 'QUIET_WRIST_YZ_FEEDBACK_EXECUTION.md',
                Z / 'comparison_v2.json', Z / 'artifact_inventory.json', P / 'preflight.json'}
    selected.update(P / (c + s) for c in ['off', 'on'] for s in ['_execution.json', '_source_manifest.json'])
    for path in sorted(selected, key=str):
        destination = P / 'analysis_source' / path.relative_to(R)
        destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, destination)
        assert sha(destination) == before[str(path)]
        copies.append(dict(original_path=str(path), copy_path=str(destination), sha256=sha(path)))
    save(P / 'analysis_source_manifest.json', dict(files=copies, scope='Selected snapshots; full direct input closure hashed, native originals retained'))
    command = [sys.executable, '-u', '-m', 'stability_adapter_2.analyze_quiet_wrist_yz_feedback']
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MPLBACKEND='Agg')
    keys = ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MPLBACKEND']
    save(P / 'analysis_invocation.json', dict(command=command, cwd=str(R), environment={k: env[k] for k in keys}, input_sha256_before=before))
    before[str(P / 'analysis_invocation.json')] = sha(P / 'analysis_invocation.json')
    start = time.monotonic()
    with (P / 'analysis.log').open('xb') as log:
        completed = subprocess.run(command, cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = {p: sha(p) for p in before}
    save(P / 'analysis_execution.json', dict(command=command, exit_code=completed.returncode,
        wall_seconds=time.monotonic() - start, input_sha256_before=before, input_sha256_after=after,
        log_sha256=sha(P / 'analysis.log'), selected_snapshot_count=len(copies)))
    print((P / 'analysis.log').read_text()[-6000:])
    assert completed.returncode == 0 and before == after


if __name__ == '__main__': main()
