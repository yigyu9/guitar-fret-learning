"""Independent spawn scenes; CUDA policy ownership remains in the learner."""
import copy
import multiprocessing as mp
from pathlib import Path
import traceback
import numpy as np


def worker(connection, seed, log_path):
    import contextlib
    with Path(log_path).open('x',buffering=1) as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        env=None
        try:
            from stability_adapter_2.dual_music_scene_v1 import DualMusicScene
            from stability_adapter_2.deadline_native_v8 import NativeDeadlineEnvironment
            import torch
            torch.set_num_threads(1);torch.manual_seed(seed)
            env=NativeDeadlineEnvironment(recording=False,strap_enabled=True,seed=seed)
            while True:
                command,value=connection.recv()
                if command=='close':break
                if command=='reset':
                    obs=env.reset();env.require_training_ready()
                    result={'observation':obs,'abi':env.abi(),'metadata':env.metadata}
                elif command=='step':
                    obs,reward,terminated,truncated,info=env.step(value)
                    result={'observation':obs,'reward':reward,'terminated':terminated,'truncated':truncated,
                            'info':info,'report':env.last_report if terminated or truncated else None}
                elif command=='snapshot':
                    from stability_adapter_2.run_joint_hold import native_state
                    result={'native_state':native_state(env.scene),'physics_steps':env.scene.steps,
                            'forbidden_calls':list(env.scene.forbidden_calls),'strap_force_calls':env.scene.gym.allowed_calls}
                else:raise ValueError('unknown worker command')
                connection.send({'ok':True,'result':result})
        except EOFError:pass
        except BaseException as error:
            failure={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
            print(failure['traceback'],flush=True)
            try:connection.send({'ok':False,'failure':failure})
            except (BrokenPipeError,EOFError,OSError):pass
        finally:
            if env is not None:env.close()
            connection.close()


class ParallelCPUEnvironment:
    obs_dim,action_dim=825,81
    def __init__(self,num_envs,output,seed=103):
        if type(num_envs) is not int or num_envs<1:raise ValueError('positive worker count')
        self.num_envs=num_envs;self.output=Path(output);self.output.mkdir(parents=True,exist_ok=False)
        self.processes=[];self.connections=[];self.metadata={};self.episode_reports=[];self.last_info=[];self._ready=False
        context=mp.get_context('spawn')
        try:
            for i in range(num_envs):
                parent,child=context.Pipe()
                process=context.Process(target=worker,args=(child,seed+i,self.output/('worker_%02d.log'%i)))
                self.processes.append(process);self.connections.append(parent)
                try:process.start()
                finally:child.close()
        except BaseException:
            self.close()
            raise

    def _receive(self,index):
        conn=self.connections[index]
        if not conn.poll(60):raise TimeoutError('native worker timed out: '+str(index))
        try:message=conn.recv()
        except EOFError as error:raise RuntimeError('native worker EOF; partial rollout rejected: '+str(index)) from error
        if not message['ok']:raise RuntimeError('native worker failure: '+str(message['failure']))
        return message['result']

    def reset(self):
        for connection in self.connections:connection.send(('reset',None))
        results=[self._receive(i) for i in range(self.num_envs)]
        self._abi=copy.deepcopy(results[0]['abi'])
        if any(r['abi']!=self._abi for r in results):raise AssertionError('worker physical ABI differs')
        self.metadata=copy.deepcopy(results[0]['metadata'])
        self.metadata['parallel_collection']={'workers':self.num_envs,'processes':[p.pid for p in self.processes],
            'start_method':'spawn','physics_per_worker':'CPU PhysX','policy_owner':'single CUDA learner',
            'reset_randomization':False,'independent_episode_ledgers':True,
            'graphics_resource_policy_by_worker':[r['metadata']['graphics_resource_policy'] for r in results]}
        self._ready=True
        return np.stack([r['observation'] for r in results])

    def abi(self):return copy.deepcopy(self._abi)
    def require_training_ready(self):
        if not self._ready:raise RuntimeError('parallel reset required')

    def step(self,actions):
        actions=np.asarray(actions)
        if actions.shape!=(self.num_envs,81) or not np.isfinite(actions).all():raise ValueError('finite Nx81 actions required')
        for conn,action in zip(self.connections,actions):conn.send(('step',action))
        results=[self._receive(i) for i in range(self.num_envs)]
        self.last_info=[r['info'] for r in results]
        for i,r in enumerate(results):
            if r['report'] is not None:self.episode_reports.append(dict(r['report'],worker=i))
        return (np.stack([r['observation'] for r in results]),np.array([r['reward'] for r in results]),
                np.array([r['terminated'] for r in results],dtype=bool),np.array([r['truncated'] for r in results],dtype=bool),self.last_info)

    def reset_done(self,mask):
        indices=np.flatnonzero(mask)
        for i in indices:self.connections[i].send(('reset',None))
        return {int(i):self._receive(int(i))['observation'] for i in indices}

    def snapshots(self):
        for conn in self.connections:conn.send(('snapshot',None))
        return [self._receive(i) for i in range(self.num_envs)]

    def close(self):
        for conn,process in zip(self.connections,self.processes):
            if process.is_alive():
                try:conn.send(('close',None))
                except (BrokenPipeError,EOFError,OSError):pass
        for conn,process in zip(self.connections,self.processes):
            if process.pid is None:
                conn.close();continue
            process.join(timeout=5)
            if process.is_alive():process.terminate();process.join(timeout=5)
            if process.is_alive():process.kill();process.join(timeout=5)
            conn.close()
        self._ready=False
