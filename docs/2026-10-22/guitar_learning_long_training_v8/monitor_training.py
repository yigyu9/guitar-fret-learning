"""Record durable progress and stop only for storage/stall failures, not score."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

PHASE=Path(__file__).resolve().parent
ROOT=PHASE.parents[2]
launch=json.loads((PHASE/'launch.json').read_text())
RUN=Path(launch['out'])
source=json.loads((PHASE/'training_source_manifest.json').read_text())['source']
started=time.monotonic();last_update=-1;last_progress=started;stopped=False;count=0

def read(path):
    try:return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return None

with (PHASE/'progress.jsonl').open('x') as log:
    while True:
        row=dict(run=str(RUN),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),unix_time=time.time(),elapsed_s=time.monotonic()-started)
        status=read(RUN/'status.json')
        if status:row.update(status=status,phase=status.get('phase'),pid=status.get('parent_pid'))
        problem=None
        try:
            disk=os.statvfs(RUN);row['disk_free_bytes']=disk.f_bavail*disk.f_frsize
            local=os.statvfs(ROOT);row['local_disk_free_bytes']=local.f_bavail*local.f_frsize
            if row['disk_free_bytes']<5*1024**3:problem='output storage below5GiB'
            paths=sorted(RUN.glob('update_*.json'))
            metric=read(paths[-1]) if paths else None
            if metric:
                update=metric['update_index'];row.update(last_committed_update=update,optimizer_updates=metric['optimizer_updates'],reward_mean=metric['mean_reward'],cost_mean=metric['mean_cost'],curriculum=metric.get('left_curriculum'))
                if update!=last_update:last_update=update;last_progress=time.monotonic()
            if count%12==0:
                changed=[p for p,sha in source.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha]
                row['changed_source']=changed
                if changed:problem='frozen training source changed'
            gpu=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.free','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
            row['gpu_memory_mib']=gpu.stdout.strip()
        except OSError as error:problem='storage error: '+str(error)
        if time.monotonic()-last_progress>600:problem='no committed update for600s'
        row['guard_problem']=problem
        if problem and not stopped and status:
            os.kill(status['parent_pid'],signal.SIGINT);stopped=True;row['guard_action']='SIGINT native Python once; preserve all output'
        row['launch_result']=read(PHASE/'launch_result.json')
        log.write(json.dumps(row,allow_nan=False)+'\n');log.flush();os.fsync(log.fileno())
        if row['launch_result'] is not None:break
        count+=1
        time.sleep(50)
(PHASE/'monitor_result.json').write_text(json.dumps(dict(completed=True,guard_stopped=stopped,last_committed_update=last_update,elapsed_s=time.monotonic()-started),indent=2)+'\n')
