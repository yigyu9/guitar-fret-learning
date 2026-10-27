"""Run relevant CPU suites in fresh processes, preserving all outputs."""
import json
import os
from pathlib import Path
import subprocess
import time

P = Path(__file__).resolve().parent
rows = []
for name in json.loads((P/'cpu_modules.json').read_text()):
    started = time.monotonic()
    result = subprocess.run(['/home/ajou/miniconda3/envs/rl38/bin/python', '-B',
        '-m', 'unittest', '-q', 'guitar_learning.tests.'+name],
        capture_output=True, text=True, env=os.environ)
    rows.append(dict(module=name, code=result.returncode,
        wall_s=time.monotonic()-started, output=result.stdout+result.stderr))
    (P/'cpu_checks.json').write_text(json.dumps(rows, indent=2)+'\n')
    print(name, result.returncode, flush=True)
if any(row['code'] for row in rows):
    raise SystemExit(1)
