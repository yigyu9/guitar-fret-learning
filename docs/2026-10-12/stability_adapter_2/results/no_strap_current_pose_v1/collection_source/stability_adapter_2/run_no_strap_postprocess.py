"""Archive one saved-data analysis or video-collection execution."""
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
D = R / 'docs/2026-10-12/stability_adapter_2'
P = D / 'results/no_strap_current_pose_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['analysis', 'collection'])
    stage = parser.parse_args().stage
    module = 'analyze_no_strap_video' if stage == 'analysis' else 'collect_no_strap_videos'
    assert not (P / (stage + '_execution.json')).exists()
    paths = [Path(__file__).resolve(), A / (module + '.py'), A / 'NO_STRAP_VIDEO_PLAN.md']
    if stage == 'analysis':
        paths += [A / n for n in ['analyze_natural_envelope.py', 'build_fixed_lower_asset.py']]
        paths += [P / 'execution.json', P / 'native/no_strap_mode.json', P / 'native/videos.json', P / 'native/attempt.json']
        for f in [P / 'native', D / 'results/initial_middle3_alignment_v1/native']:
            paths += [f / n for n in ['initial_values.json', 'states.jsonl', 'trace.jsonl', 'controls.jsonl', 'report.json', 'capture.json', 'initial_grip_audit.json']]
        capture = json.loads((P / 'native/capture.json').read_text())
        paths += [Path(p) for frame in capture['frames'] for p in frame['image_sha256']]
        paths += [Path(v['path']) for v in json.loads((P / 'native/videos.json').read_text()).values()]
    else:
        paths += [P / 'analysis.json', P / 'native/videos.json', D / 'VIDEO_INDEX_v10.md']
        paths += list((D / 'videos').glob('*.mp4'))
        paths += [Path(v['path']) for v in json.loads((P / 'native/videos.json').read_text()).values()]
    before = {str(p):sha(p) for p in paths}
    manifest = {}
    for p in paths:
        if p.parent == A or p.suffix == '.json':
            dest = P / (stage + '_source') / p.relative_to(R)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            assert sha(dest) == before[str(p)]
            manifest[str(p)] = dict(snapshot=str(dest), sha256=before[str(p)])
    (P / (stage + '_source_manifest.json')).write_text(json.dumps(manifest, indent=2) + '\n')
    command = [sys.executable, '-m', 'stability_adapter_2.' + module]
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    start = time.monotonic()
    with (P / (stage + '.log')).open('xb') as log:
        result = subprocess.run(command, cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = {p:sha(p) for p in before}
    record = dict(command=command, environment={k:env[k] for k in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS']}, exit_code=result.returncode, wall_seconds=time.monotonic()-start, input_sha256_before=before, input_sha256_after=after, log_sha256=sha(P / (stage + '.log')))
    (P / (stage + '_execution.json')).write_text(json.dumps(record, indent=2) + '\n')
    print((P / (stage + '.log')).read_text()[-6000:])
    assert result.returncode == 0 and before == after


if __name__ == '__main__': main()
