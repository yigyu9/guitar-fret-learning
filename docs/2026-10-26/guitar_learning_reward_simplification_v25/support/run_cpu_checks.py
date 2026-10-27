"""Run the relevant existing and new CPU suites against frozen active sources."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import os
import subprocess
import time

folder = Path(__file__).resolve().parent
manifest = json.loads((folder/'source_manifest.json').read_text())
assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256'] for row in manifest)
modules = json.loads((folder/'cpu_modules.json').read_text())
environment = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')

def run(module):
    begin = time.monotonic()
    result = subprocess.run(['/home/ajou/miniconda3/envs/rl38/bin/python', '-B', '-m', 'unittest', '-q', 'guitar_learning.tests.'+module], capture_output=True, text=True, env=environment)
    return dict(module=module, code=result.returncode, wall_s=time.monotonic()-begin, output=result.stdout+result.stderr)

rows = []
with ThreadPoolExecutor(max_workers=3) as executor:
    for result in as_completed([executor.submit(run, module) for module in modules]):
        row = result.result()
        rows.append(row)
        (folder/'cpu_checks.json').write_text(json.dumps(sorted(rows, key=lambda x:x['module']), indent=2)+'\n')
        print(row['module'], row['code'], flush=True)
assert all(hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256'] for row in manifest)
raise SystemExit(any(row['code'] for row in rows))
