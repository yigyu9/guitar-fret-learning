"""Frozen-source position/incremental comparison, no reward/PPO changes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

R = Path('/home/ajou/yigyu/3')
P = Path(__file__).resolve().parents[1]
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
manifest = json.loads((P/'support/source_manifest.json').read_text())
records = []


def execute(label, arguments):
    assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256']
               for row in manifest), 'Active source changed after freeze'
    print('START', label, flush=True)
    start = time.monotonic()
    command = [PYTHON, '-B']+arguments
    with (P/'support'/(label+'.log')).open('x') as stream:
        result = subprocess.run(command, cwd=R, env=os.environ,
            stdout=stream, stderr=subprocess.STDOUT)
    records.append(dict(stage=label, code=result.returncode,
        wall_s=time.monotonic()-start, command=command))
    (P/'support/progress.json').write_text(json.dumps(records, indent=2)+'\n')
    print('END', label, result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


def train(name, mode, updates, envs=128, resume=None):
    arguments = ['-m', 'guitar_learning.train', '--hand', 'left', '--physics', 'gpu',
        '--size', 'large', '--num-envs', str(envs), '--horizon', '32', '--seed', '7',
        '--updates', str(updates), '--finger-action-mode', mode, '--out', str(P/name)]
    if resume:
        arguments += ['--resume', str(P/resume/'final.pt')]
    return arguments


execute('smoke1024', train('smoke1024', 'position', 2, 1024))
execute('resume1024', train('resume1024', 'position', 1, 1024, 'smoke1024'))
for mode in ('incremental', 'position'):
    execute('train_'+mode, train('train_'+mode, mode, 100))
    execute('inspect_'+mode, ['-m', 'guitar_learning.tool.inspect_gpu_training_log',
        '--run', str(P/('train_'+mode))])
    arguments = ['-m', 'guitar_learning.tool.validation.evaluate_hand_contact',
        '--run', str(P/('train_'+mode)), '--out', str(P/('eval_'+mode))]
    if mode == 'position':
        arguments.append('--video')
    execute('eval_'+mode, arguments)
print('ALL_COMPARISON_STAGES_COMPLETE', flush=True)
