"""Short GPU integration checks; these are not a learning-performance study."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

root = Path('/home/ajou/yigyu/3')
folder = Path(__file__).resolve().parent
result_root = folder.parent
manifest = json.loads((folder/'source_manifest.json').read_text())
python = '/home/ajou/miniconda3/envs/rl38/bin/python'
environment = dict(os.environ)
environment['PATH'] = '/home/ajou/miniconda3/envs/rl38/bin:'+environment.get('PATH', '')
environment['LD_LIBRARY_PATH'] = '/home/ajou/miniconda3/envs/rl38/lib:'+environment.get('LD_LIBRARY_PATH', '')
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    environment[key] = '1'
records = []

def execute(name, arguments):
    assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256'] for row in manifest)
    start = time.monotonic()
    command = [python, '-B']+arguments
    print('START', name, flush=True)
    with (folder/(name+'.log')).open('x') as stream:
        result = subprocess.run(command, cwd=root, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    records.append(dict(name=name, code=result.returncode, wall_s=time.monotonic()-start, command=command))
    (folder/'native_checks.json').write_text(json.dumps(records, indent=2)+'\n')
    print('END', name, result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


def train(name, phase, updates, envs=128, extra=()):
    return ['-m', 'guitar_learning.train', '--hand', 'left', '--physics', 'gpu', '--size', 'large',
        '--num-envs', str(envs), '--horizon', '32', '--seed', '7', '--updates', str(updates),
        '--learning-family', 'finger-skill-v24', '--skill-phase', phase,
        '--out', str(result_root/name)]+list(extra)

execute('resume1024', train('resume1024', 'F', 1, 1024, ['--resume', str(result_root/'smoke1024_v2/F/final.pt')]))
execute('correlated_F3', train('correlated_F3', 'F', 12, extra=['--skill-exploration', 'correlated', '--skill-hold-ticks', '3']))
execute('support_R', train('support_R', 'R', 2))
execute('joint_J', train('joint_J', 'J', 2))
execute('phase_transfer', [str(folder/'check_phase_transfer.py')])
execute('evaluate_F3', ['-m', 'guitar_learning.tool.evaluation.evaluate_finger_skill',
    str(result_root/'correlated_F3/F/final.pt'), '--out', str(result_root/'evaluate_F3'), '--scope', 'full_song', '--num-envs', '16'])
execute('render_F3', ['-m', 'guitar_learning.tool.demonstration.render_finger_skill',
    '--checkpoint', str(result_root/'correlated_F3/F/final.pt'), '--out', str(result_root/'render_F3'), '--scope', 'full_song', '--num-envs', '16'])
assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256'] for row in manifest)
print('ALL_SHORT_NATIVE_CHECKS_COMPLETE', flush=True)
