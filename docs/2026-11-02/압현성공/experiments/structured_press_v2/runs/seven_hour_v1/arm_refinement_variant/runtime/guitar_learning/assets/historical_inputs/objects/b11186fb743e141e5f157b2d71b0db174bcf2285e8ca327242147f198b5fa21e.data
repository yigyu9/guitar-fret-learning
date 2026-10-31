"""Bounded, flushed host/process monitoring without native or tensor imports."""
import json
import os
from pathlib import Path
import sys
import threading
import time
from datetime import datetime, timezone


class LowMemoryError(RuntimeError):
    pass


def available_memory_bytes():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])*1024
    raise RuntimeError('MemAvailable not reported')


def process_memory(pid):
    """Current RSS/PSS and lifetime RSS peak have distinct fields, in bytes."""
    result=dict(pid=pid,rss_current_bytes=None,pss_current_bytes=None,rss_peak_bytes=None)
    try:
        for line in Path('/proc/%s/status'%pid).read_text().splitlines():
            key=line.split(':',1)[0]
            if key in ('VmRSS','VmHWM'):
                result['rss_current_bytes' if key=='VmRSS' else 'rss_peak_bytes']=int(line.split()[1])*1024
        try:
            for line in Path('/proc/%s/smaps_rollup'%pid).read_text().splitlines():
                if line.startswith('Pss:'):
                    result['pss_current_bytes']=int(line.split()[1])*1024
                    break
        except (OSError,ValueError):
            pass
    except (OSError,ValueError):
        pass
    return result


def stopped_reason(error):
    if isinstance(error,LowMemoryError):return 'memory_guard'
    if isinstance(error,KeyboardInterrupt):return 'interrupted'
    if isinstance(error,TimeoutError):return 'worker_timeout'
    if 'worker' in str(error).lower() and any(word in str(error).lower() for word in ('failure','failed','exited','died')):
        return 'worker_failed'
    return 'error'


def save_failure_checkpoint(trainer,out,metadata,eligible=True,ineligible_reason='resume_not_validated'):
    """Never replace an existing checkpoint, or mask the original exception."""
    if trainer is None:return dict(path=None,error=None,reason='trainer_not_created')
    if not eligible:return dict(path=None,error=None,reason=ineligible_reason)
    path=Path(out)/'failure_last_valid.pt'
    try:
        trainer.save(path,metadata=metadata)
        return dict(path=str(path),error=None,reason='current_valid_PPO_optimizer_state')
    except BaseException as error:
        return dict(path=None,error=dict(type=type(error).__name__,message=str(error)),attempted_path=str(path))


class Monitor:
    def __init__(self,out,min_available_memory_gib=4.,heartbeat_seconds=10.,resource_interval_seconds=5.,
                 memory_probe=available_memory_bytes,process_probe=process_memory,console=None):
        self.out=Path(out)
        self.threshold=int(min_available_memory_gib*1024**3)
        self.heartbeat_seconds=heartbeat_seconds
        self.resource_interval_seconds=resource_interval_seconds
        self.memory_probe,self.process_probe=memory_probe,process_probe
        self.console=console if console is not None else sys.stdout
        self.lock=threading.RLock()
        self.stop_event=threading.Event()
        self.thread=None
        self.started=time.monotonic()
        self.last_sample=-float('inf')
        self.last_heartbeat=-float('inf')
        self.context=dict(phase='initializing',operation=None,pending_workers=[],worker_status=[],update_index=None,ticks=0,horizon=None)
        self.minimum_available=None
        self.low_memory=None
        self.probe_error=None
        self.status={}
        self.streams={name:(self.out/(name+'.jsonl')).open('x') for name in ('resources','events')}

    def _write(self,name,value):
        self.streams[name].write(json.dumps(value,allow_nan=False)+'\n')
        self.streams[name].flush()

    def _base(self):
        return dict(wall_time_utc=datetime.now(timezone.utc).isoformat(),elapsed_s=time.monotonic()-self.started,
                    parent_pid=os.getpid(),**self.context)

    def _status(self,value):
        temporary=self.out/'status.json.tmp'
        with temporary.open('w') as stream:
            json.dump(value,stream,indent=2,allow_nan=False)
            stream.write('\n')
        os.replace(str(temporary),str(self.out/'status.json'))
        self.status=value

    def event(self,kind,**fields):
        with self.lock:
            self._write('events',dict(self._base(),event=kind,**fields))

    def set_phase(self,phase,**fields):
        with self.lock:
            self.context.update(phase=phase,operation=None,pending_workers=[],**fields)
            self.event('phase')
            self.sample(force=True)
        self.check()

    def sample(self,force=False):
        with self.lock:
            now=time.monotonic()
            due=force or now-self.last_sample>=self.resource_interval_seconds
            if due:
                try:
                    available=self.memory_probe()
                    self.minimum_available=available if self.minimum_available is None else min(self.minimum_available,available)
                    workers=[dict(row,memory=self.process_probe(row['pid'])) for row in self.context['worker_status'] if row.get('pid')]
                    sample=dict(self._base(),available_memory_bytes=available,min_available_memory_bytes=self.minimum_available,
                                memory_floor_bytes=self.threshold,parent_memory=self.process_probe(os.getpid()),workers=workers)
                    if available<self.threshold and self.low_memory is None:
                        self.low_memory=dict(available_memory_bytes=available,memory_floor_bytes=self.threshold)
                        self._write('events',dict(self._base(),event='low_memory',**self.low_memory))
                    sample['low_memory']=self.low_memory
                    self._write('resources',sample)
                    self._status(sample)
                    self.last_sample=now
                except Exception as error:
                    self.probe_error=dict(type=type(error).__name__,message=str(error))
                    # A monitoring failure cannot silently disable the guard.
            if force or now-self.last_heartbeat>=self.heartbeat_seconds:
                available=self.status.get('available_memory_bytes')
                memory='unknown' if available is None else '%.2f GiB'%(available/1024**3)
                message='[training] phase=%s update=%s tick=%s/%s free=%s waiting=%s'%(
                    self.context['phase'],self.context['update_index'],self.context['ticks'],self.context['horizon'],
                    memory,self.context['pending_workers'])
                print(message,file=self.console,flush=True)
                self.last_heartbeat=now

    def check(self):
        if self.probe_error is not None:raise RuntimeError('resource monitor failed: '+str(self.probe_error))
        if self.low_memory is not None:
            raise LowMemoryError('MemAvailable %.3f GiB below %.3f GiB guard'%(
                self.low_memory['available_memory_bytes']/1024**3,self.threshold/1024**3))

    def wait(self,context):
        with self.lock:
            self.context.update({key:context[key] for key in ('operation','pending_workers','worker_status') if key in context})
            self.sample()
        self.check()

    def progress(self,context):
        with self.lock:
            self.context.update({key:context[key] for key in ('ticks','horizon') if key in context})
            self.sample()
        self.check()

    def start(self):
        self.sample(force=True)
        self.check()
        def run():
            interval=min(self.heartbeat_seconds,self.resource_interval_seconds,.5)
            while not self.stop_event.wait(interval):self.sample()
        self.thread=threading.Thread(target=run,name='training-resource-monitor',daemon=True)
        self.thread.start()

    def close(self,stopped):
        self.stop_event.set()
        if self.thread is not None:self.thread.join(timeout=2.)
        with self.lock:
            self.context.update(phase='stopped',stopped=stopped,pending_workers=[])
            self.sample(force=True)
            self.event('stopped',reason=stopped)
            for stream in self.streams.values():stream.close()
