"""Run the requested two hand jobs and record host resources; no learning edits."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path('/home/ajou/yigyu/3')
PYTHON='/home/ajou/miniconda3/envs/rl38/bin/python'


def stamp():return datetime.now(timezone.utc).isoformat()
def cpu_ticks():
    values=list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:9]))
    return sum(values),values[3]+values[4]
def sample(previous):
    total,idle=cpu_ticks();delta=total-previous[0]
    memory={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
            if line.startswith(('MemAvailable:','MemTotal:','SwapTotal:','SwapFree:'))}
    result=dict(time_utc=stamp(),cpu_busy_percent=100*(1-(idle-previous[1])/delta) if delta else None,**memory)
    try:
        gpu=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
            '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5,check=True)
        values=[int(v.strip()) for v in gpu.stdout.splitlines()[0].split(',')]
        result['gpu']=dict(zip(('busy_percent','used_mib','total_mib','temperature_c'),values))
    except (OSError,ValueError,subprocess.SubprocessError) as error:result['gpu_error']=str(error)
    return result,(total,idle)


def run(plan_path,out):
    plan=json.loads(Path(plan_path).read_text());out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    jobs=[];started=time.monotonic();interrupted=False
    environment=dict(os.environ,PATH='/home/ajou/miniconda3/envs/rl38/bin:'+os.environ.get('PATH',''),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',PYTHONUNBUFFERED='1')
    def state(final=False):
        value=dict(schema='guitar_learning.resource_supervisor.v1',supervisor_pid=os.getpid(),
            started_utc=began,time_utc=stamp(),elapsed_s=time.monotonic()-started,
            completed=final,interrupted=interrupted,plan=str(Path(plan_path).resolve()),
            jobs=[dict(role=j['spec']['role'],pid=j['process'].pid,returncode=j['process'].poll(),
                out=j['spec']['out'],log=j['spec']['log']) for j in jobs])
        temporary=out/'status.json.tmp';temporary.write_text(json.dumps(value,indent=2)+'\n')
        os.replace(str(temporary),str(out/'status.json'))
        return value
    def terminate(signum,frame):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,terminate)
    began=stamp();previous=cpu_ticks()
    try:
        for spec in plan['jobs']:
            stream=Path(spec['log']).open('x')
            command=[PYTHON,'-m','guitar_learning.train_musical_quality','--settings',spec['settings'],
                '--resume',spec['resume'],'--out',spec['out']]
            try:process=subprocess.Popen(command,cwd=str(ROOT),env=environment,stdout=stream,
                stderr=subprocess.STDOUT,start_new_session=True)
            except BaseException:stream.close();raise
            jobs.append(dict(spec=spec,process=process,stream=stream));state()
        with (out/'host_resources.jsonl').open('x') as resources:
            while any(j['process'].poll() is None for j in jobs):
                measurement,previous=sample(previous)
                resources.write(json.dumps(measurement)+'\n');resources.flush();state()
                time.sleep(5)
    except BaseException:
        interrupted=True
        for job in jobs:
            if job['process'].poll() is None:job['process'].send_signal(signal.SIGINT)
        # Trainer owns scene cleanup and failure checkpoint. Keep supervising it.
        while any(j['process'].poll() is None for j in jobs):state();time.sleep(1)
        raise
    finally:
        for job in jobs:job['stream'].close()
        result=state(final=True)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return 0 if all(j['process'].returncode==0 for j in jobs) else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();sys.exit(run(args.plan,args.out))
