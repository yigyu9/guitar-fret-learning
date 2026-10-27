"""Sequential short native checks, strict resume, evaluation and capture."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/home/ajou/yigyu/3')
FOLDER = Path(__file__).resolve().parent
RESULT = FOLDER.parent
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
manifest = json.loads((FOLDER/'source_manifest.json').read_text())
environment = dict(os.environ)
environment['PATH'] = '/home/ajou/miniconda3/envs/rl38/bin:'+environment.get('PATH', '')
environment['LD_LIBRARY_PATH'] = '/home/ajou/miniconda3/envs/rl38/lib:'+environment.get('LD_LIBRARY_PATH', '')
environment['PYTHONPATH'] = str(ROOT/'isaacgym/python')+':'+str(ROOT)+':'+environment.get('PYTHONPATH', '')
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    environment[key] = '1'
records = []


def execute(name, command):
    assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256'] for row in manifest)
    print('START', name, flush=True)
    started = time.monotonic()
    with (FOLDER/(name+'.log')).open('x') as output:
        result = subprocess.run([PYTHON, '-u', '-B']+command, cwd=ROOT, env=environment,
                                stdout=output, stderr=subprocess.STDOUT)
    records.append(dict(name=name, command=[PYTHON, '-u', '-B']+command,
                        code=result.returncode, wall_s=time.monotonic()-started))
    (FOLDER/'native_pipeline.json').write_text(json.dumps(records, indent=2)+'\n')
    print('END', name, result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


execute('shadow', [str(FOLDER/'shadow_wrist.py')])
common = ['-m', 'guitar_learning.train', '--hand', 'left', '--physics', 'gpu',
          '--learning-family', 'finger-skill', '--size', 'large', '--horizon', '32', '--seed', '7']
execute('large1024', common+['--num-envs', '1024', '--updates', '8', '--out', str(RESULT/'large1024')])
execute('resume1024', common+['--num-envs', '1024', '--updates', '1', '--out', str(RESULT/'resume1024'),
                            '--resume', str(RESULT/'large1024/J/final.pt')])
execute('large128', common+['--num-envs', '128', '--updates', '64', '--out', str(RESULT/'large128')])
checkpoint = str(RESULT/'large128/J/final.pt')
execute('full_song_evaluation', ['-m', 'guitar_learning.tool.evaluation.evaluate_finger_skill',
    checkpoint, '--out', str(RESULT/'full_song_evaluation'), '--scope', 'full_song', '--num-envs', '16'])
execute('video', ['-m', 'guitar_learning.tool.demonstration.render_finger_skill', '--checkpoint', checkpoint,
    '--out', str(RESULT/'video'), '--scope', 'full_song', '--num-envs', '16'])
assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256'] for row in manifest)
print('NATIVE_CHECKS_COMPLETE', flush=True)
