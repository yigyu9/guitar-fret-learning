import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1')
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
name, *native = sys.argv[1:]
command = json.loads((BASE/'namespace_base_argv_v2.json').read_text()) + [PYTHON, '-u', *native]
environment = dict(os.environ)
environment.update(PATH='/home/ajou/miniconda3/envs/rl38/bin:'+environment['PATH'],
    LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib', PYTHONFAULTHANDLER='1',
    OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
log = BASE/(name+'.log')
metadata = BASE/(name+'_launch.json')
if log.exists() or metadata.exists():
    raise FileExistsError(name)
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with log.open('x') as stream:
    process = subprocess.Popen(command, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    metadata.write_text(json.dumps(dict(pid=process.pid, argv=command, native_argv=[PYTHON,'-u',*native],
        started_utc=started, launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        log=str(log)),indent=2)+'\n')
    print('started',name,'pid',process.pid,flush=True)
    returncode = process.wait()
finished = dict(pid=process.pid,returncode=returncode,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
(BASE/(name+'_exit.json')).write_text(json.dumps(finished,indent=2)+'\n')
print(json.dumps(finished),flush=True)
sys.exit(returncode)
