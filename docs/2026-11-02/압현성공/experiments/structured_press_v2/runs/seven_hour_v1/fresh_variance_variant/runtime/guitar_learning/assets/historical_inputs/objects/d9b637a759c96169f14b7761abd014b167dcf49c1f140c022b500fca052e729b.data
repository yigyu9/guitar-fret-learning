"""Existing independent collector with validated coupled-noise native resets."""
import contextlib
import functools
from pathlib import Path
import traceback
from unittest.mock import patch
from . import parallel_cpu_env_v1 as old


def worker(connection,seed,log_path,bank_path):
    with Path(log_path).open('x',buffering=1) as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        env=None
        try:
            from .dual_music_scene_v1 import DualMusicScene
            from .deadline_initial_noise_v1 import NativeInitialNoiseEnvironment
            import torch
            torch.set_num_threads(1);torch.manual_seed(seed)
            env=NativeInitialNoiseEnvironment(bank_path,recording=False,strap_enabled=True,seed=seed)
            while True:
                command,value=connection.recv()
                if command=='close':break
                if command=='reset':
                    obs=env.reset();env.require_training_ready()
                    result={'observation':obs,'abi':env.abi(),'metadata':env.metadata}
                elif command=='step':
                    obs,reward,terminated,truncated,info=env.step(value)
                    result={'observation':obs,'reward':reward,'terminated':terminated,'truncated':truncated,'info':info,'report':env.last_report if terminated or truncated else None}
                elif command=='snapshot':
                    from .run_joint_hold import native_state
                    result={'native_state':native_state(env.scene),'physics_steps':env.scene.steps,'forbidden_calls':list(env.scene.forbidden_calls),'strap_force_calls':env.scene.gym.allowed_calls,'initial_pose_noise':env.noise_selection}
                else:raise ValueError('unknown command')
                connection.send({'ok':True,'result':result})
        except EOFError:pass
        except BaseException as error:
            failure={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()};print(failure['traceback'],flush=True)
            try:connection.send({'ok':False,'failure':failure})
            except (BrokenPipeError,EOFError,OSError):pass
        finally:
            if env is not None:env.close()
            connection.close()

class ParallelInitialNoiseEnvironment(old.ParallelCPUEnvironment):
    def __init__(self,num_envs,output,bank_path,seed=103):
        self.reset_records=[]
        with patch.object(old,'worker',functools.partial(worker,bank_path=str(Path(bank_path).resolve()))):
            super().__init__(num_envs,output,seed)
    def _receive(self,index):
        result=super()._receive(index)
        if 'metadata' in result:self.reset_records.append({'worker':index,**result['metadata']['initial_pose_noise']})
        return result
    def reset(self):
        obs=super().reset();self.metadata['parallel_collection']['reset_randomization']=True
        self.metadata['parallel_collection']['reset_sampling']='uniform discrete validated coupled poses with replacement'
        return obs
