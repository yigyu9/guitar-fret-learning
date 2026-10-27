"""Run the authorized v8 long budget in a detached, durable launcher."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path('/home/ajou/yigyu/3')
PHASE=Path(__file__).resolve().parent
BASE=Path('/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v8_long')
OUT=BASE/'train2000'
BASE.mkdir(parents=True,exist_ok=True)
assert not OUT.exists()
env=dict(os.environ)
env.update(PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/bin:/usr/bin:/bin',
 PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='0',
 PYTHONPATH=str(ROOT/'isaacgym/python')+':'+str(ROOT),
 LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',OMP_NUM_THREADS='1')
command=['gdb','-q','-batch','-x',str(ROOT/'docs/2026-10-22/guitar_learning_long_training_v6/native_trace.gdb'),
 '--args','/home/ajou/miniconda3/envs/rl38/bin/python','-B','-m','guitar_learning.train',
 '--hand','left','--song','05_BN2-131-B_solo','--device','cuda:0','--physics','gpu',
 '--size','large','--num-envs','1024','--horizon','32','--updates','2000',
 '--checkpoint-every','100','--seed','7','--out',str(OUT)]
started=time.monotonic()
metadata=dict(scope='Fresh v8, no previous training transitions inherited',out=str(OUT),command=command,
 started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),launcher_pid=os.getpid(),
 log=str(BASE/'train2000_gdb.log'))
with (BASE/'train2000_gdb.log').open('x') as log:
 process=subprocess.Popen(command,cwd=str(ROOT),env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
 metadata['child_pid']=process.pid
 (PHASE/'launch.json').write_text(json.dumps(metadata,indent=2)+'\n')
 result=process.wait()
 log.flush();os.fsync(log.fileno())
metadata.update(returncode=result,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),wall_s=time.monotonic()-started)
(PHASE/'launch_result.json').write_text(json.dumps(metadata,indent=2)+'\n')
