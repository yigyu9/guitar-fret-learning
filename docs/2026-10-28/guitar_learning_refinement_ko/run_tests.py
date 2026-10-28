import concurrent.futures
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

root = Path('/home/ajou/yigyu/3')
folder = Path('/tmp/guitar_refinement_ko_20261028')
label = sys.argv[1]
paths = (json.loads((folder/'focused.json').read_text()) if len(sys.argv) > 2
         else [str(p.relative_to(root)) for p in sorted((root/'guitar_learning/tests').glob('test_*.py'))])
snapshot = sys.argv[-1] == 'snapshot'
if snapshot:
    paths = [row['path'] for row in json.loads((folder/'full_after.json').read_text())['failures']]
env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
           PYTHONPATH=str(root/'isaacgym/python')+':'+str(root),
           LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib:'+os.environ.get('LD_LIBRARY_PATH', ''))
logs = folder/label
logs.mkdir(exist_ok=True)

def run(path):
    started = time.monotonic()
    module = path[:-3].replace('/', '.')
    try:
        command = (['/home/ajou/miniconda3/envs/rl38/bin/python', str(folder/'snapshot_unittest.py'), module]
                   if snapshot else ['/home/ajou/miniconda3/envs/rl38/bin/python', '-m', 'unittest', module])
        result = subprocess.run(command,
                                cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=180, text=True)
        output, code = result.stdout, result.returncode
    except subprocess.TimeoutExpired as error:
        output, code = str(error), 'timeout'
    log = logs/(Path(path).stem+'.log')
    log.write_text(output)
    count = re.search(r'Ran (\d+) tests?', output)
    return dict(path=path, code=code, tests=int(count[1]) if count else None,
                seconds=round(time.monotonic()-started, 2), log=str(log))

rows = []
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for row in pool.map(run, paths):
        rows.append(row)
        if row['code'] != 0:
            print(json.dumps(row), flush=True)
summary = dict(modules=len(rows), passed=sum(r['code'] == 0 for r in rows),
               tests=sum(r['tests'] or 0 for r in rows), failures=[r for r in rows if r['code'] != 0], rows=rows)
(folder/(label+'.json')).write_text(json.dumps(summary, indent=2))
print(json.dumps({key:value for key,value in summary.items() if key != 'rows'}), flush=True)
