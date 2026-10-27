"""Evaluate and capture the unchanged final R model; no further training."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path('/home/ajou/yigyu/3')
FOLDER = Path(__file__).resolve().parent
RESULT = FOLDER.parent
CHECKPOINT = RESULT/'training/R_evaluation/evaluated.pt'
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
manifest = json.loads((FOLDER/'source_manifest.json').read_text())
environment = dict(os.environ)
environment['PATH'] = '/home/ajou/miniconda3/envs/rl38/bin:'+environment.get('PATH', '')
environment['LD_LIBRARY_PATH'] = '/home/ajou/miniconda3/envs/rl38/lib:'+environment.get('LD_LIBRARY_PATH', '')
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    environment[key] = '1'
records = []


def execute(name, module, arguments):
    assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256'] for row in manifest)
    command = [PYTHON, '-u', '-B', '-m', module]+arguments
    print('START', name, flush=True)
    started = time.monotonic()
    with (FOLDER/(name+'.log')).open('x') as output:
        result = subprocess.run(command, cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT)
    records.append(dict(name=name, command=command, code=result.returncode, wall_s=time.monotonic()-started))
    (FOLDER/'result_pipeline.json').write_text(json.dumps(records, indent=2)+'\n')
    print('END', name, result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


execute('full_song_evaluation', 'guitar_learning.tool.evaluation.evaluate_finger_skill',
        [str(CHECKPOINT), '--out', str(RESULT/'full_song_evaluation'), '--scope', 'full_song', '--num-envs', '16'])
execute('video', 'guitar_learning.tool.demonstration.render_finger_skill',
        ['--checkpoint', str(CHECKPOINT), '--out', str(RESULT/'video'), '--scope', 'full_song', '--num-envs', '16'])
print('RESULTS_COMPLETE', flush=True)
