"""Replay the two changed GPU CPU-test modules after production freeze."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path('/home/ajou/yigyu/3')
OUT = Path(__file__).resolve().parent
base = json.loads((OUT/'report.json').read_text())
environment = dict(os.environ, **base['environment'])
records=[]
for name in ('guitar_learning.tests.test_gpu_training', 'guitar_learning.tests.test_gpu_environment'):
    command=[base['python'], '-B', '-m', 'unittest', name, '-v']
    source=ROOT/(name.replace('.', '/')+'.py')
    started=time.monotonic()
    result=subprocess.run(command,cwd=str(ROOT),env=environment,stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,text=True,timeout=300)
    log=OUT/'final_replays'/(name+'.log')
    log.parent.mkdir(parents=True,exist_ok=True)
    log.write_text(result.stdout)
    matches=re.findall(r'Ran (\d+) tests? in ([\d.]+)s',result.stdout)
    record=dict(name=name,command=command,returncode=result.returncode,
                elapsed_s=time.monotonic()-started,log=str(log.relative_to(ROOT)),
                tests_reported=int(matches[-1][0]) if matches else 0,
                unittest_elapsed_s=float(matches[-1][1]) if matches else None,
                test_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    records.append(record)
    print(json.dumps(record),flush=True)
current_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (ROOT/'guitar_learning/gpu/environment.py',ROOT/'guitar_learning/gpu/control.py',
              ROOT/'guitar_learning/gpu/scene.py',ROOT/'guitar_learning/training/gpu_pool.py')}
(OUT/'final_replays.json').write_text(json.dumps(dict(environment=base['environment'],
    cwd=str(ROOT),production_sha256=current_hashes,modules=records),indent=2)+'\n')
