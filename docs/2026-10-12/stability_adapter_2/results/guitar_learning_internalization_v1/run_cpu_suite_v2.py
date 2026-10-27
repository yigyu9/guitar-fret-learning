"""Run the full current regression suite in three independent module groups."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent / 'cpu_final_v2'
OUT.mkdir(exist_ok=False)
modules = ['.'.join(path.relative_to(ROOT).with_suffix('').parts)
           for path in sorted((ROOT/'guitar_learning/tests').glob('test_*.py'))]
partitions = [modules[index::3] for index in range(3)]
(OUT/'modules.json').write_text(json.dumps(partitions, indent=2)+'\n')

def run(item):
    index, group = item
    log = OUT/('group_%d.log' % index)
    environment = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    with log.open('x') as stream:
        result = subprocess.run([sys.executable, '-m', 'unittest', *group, '-v'],
            cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    return dict(group=index, modules=len(group), returncode=result.returncode, log=str(log))

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(run, enumerate(partitions)))
(OUT/'result.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results), flush=True)
sys.exit(any(row['returncode'] for row in results))
