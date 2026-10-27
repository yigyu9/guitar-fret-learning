"""Run current launch, shared GPU reward/control and legacy regression checks."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import time

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent.parent
baseline = root/'docs/2026-10-26/guitar_learning_reward_simplification_v25/support/cpu_modules.json'
modules = sorted(set(json.loads(baseline.read_text()) + ['test_main_tools', 'test_simple_start', 'test_simplified_wrong_press']))
env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
def check(module):
    start = time.monotonic()
    proc = subprocess.run(['/home/ajou/miniconda3/envs/rl38/bin/python', '-B', '-m', 'unittest', '-q', 'guitar_learning.tests.'+module], cwd=root, env=env, text=True, capture_output=True)
    return dict(module=module, returncode=proc.returncode, elapsed_s=time.monotonic()-start, output=proc.stdout+proc.stderr)
rows = []
with ThreadPoolExecutor(max_workers=3) as executor:
    for future in as_completed([executor.submit(check, module) for module in modules]):
        row = future.result()
        rows.append(row)
        (out/'cpu_checks.json').write_text(json.dumps(sorted(rows, key=lambda row:row['module']), indent=2)+'\n')
        print(row['module'], row['returncode'], flush=True)
raise SystemExit(any(row['returncode'] for row in rows))
