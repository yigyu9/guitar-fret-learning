"""Spawned independent scenes, barrier IPC, and one batched parent policy.

No tensor/native packages are imported until inside the appropriate process.
"""
import copy
import json
import math
import multiprocessing as mp
from multiprocessing.connection import wait
from pathlib import Path
import random
import time
import traceback
from guitar_learning.training.training_log_io import write, digest

FIELDS=('state','events','mask','priority_events','priority_mask')


def _native_environment(spec,worker_id):
    import isaacgym  # Must precede numpy/torch and native dependency imports.
    import numpy as np
    import torch
    from guitar_learning.core.task_sampling import build_environment
    seed=int(spec.get('seed',7))+worker_id
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    kwargs=dict(spec.get('env_kwargs',{}))
    if spec.get('headless',True):
        from guitar_learning.runtime.headless_session import HeadlessPreparedSession
        kwargs['session_factory']=HeadlessPreparedSession
    return build_environment(spec['config'],Path(spec['out'])/'environment',bundle=spec['bundle'],stage=spec['stage'],
        start_event_index=spec.get('start_event_index',0),phrase_events=spec.get('phrase_events',8),
        tempo_scale=spec.get('tempo_scale',1.),seed=int(spec.get('seed',7)),worker_id=worker_id,music=spec.get('music'),**kwargs)


def _resource():
    import resource
    import sys
    torch=sys.modules.get('torch')
    allocated=torch.cuda.memory_allocated() if torch is not None and torch.cuda.is_initialized() else 0
    return dict(pid=__import__('os').getpid(),rss_peak_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                torch_cuda_allocated_bytes=allocated)


def _compact(env,info,action):
    import numpy as np
    result={key:info[key] for key in ('cost','reward_terms','music','termination_reason','failure_reasons','task_time_s','episode',
                                    'episode_task','pick_guide') if key in info}
    if hasattr(env,'last_safety'):
        safety=env.last_safety
        result['stability']={key:safety[key] for key in ('flags','loss_s','guitar_delta_m','guitar_rotation_vector_rad',
                              'foot_delta_m','max_joint_speed_rad_s','failure_reasons')}
        result['goal_distance_m']={key:float(np.linalg.norm(row['delta'])) for key,row in env.last_measured['geometry'].items()}
        result['fret_candidates']={key:bool(row['candidate']) for key,row in env.last_measured['targets'].items()}
        scene=env.control.session.scene
        actual=np.array([row['pos'] for row in env.last_sample['native']['human_dof_states']])
        def bounds(value):
            value=np.asarray(value)
            return dict(min=float(value.min()),max=float(value.max()))
        result['debug']=dict(action=action,action_range=bounds(action),target_range=bounds(scene.target),
                            reference_range=bounds(env.control.reference105),actual_q_range=bounds(actual))
    result['resource']=_resource()
    if hasattr(env,'last_safety') and info.get('physics_measurements'):
        from guitar_learning.training.training_metrics import safety_tick_summary, quality_tick_summary
        result['safety240']=safety_tick_summary(info['physics_measurements'])
        targets=getattr(getattr(env,'task',None),'targets',())
        if (len(targets)==1 and
                info['physics_measurements'][0]['music']['targets'][targets[0].target_id].get('fretting_quality') is not None):
            result['quality240']=quality_tick_summary(info['physics_measurements'],targets[0])
    return result



def _final_audit(env,spec,worker_id,failure):
    import os
    import sys
    import threading
    from guitar_learning.training.training_log_io import project_source_paths, write
    session=getattr(getattr(env,'control',None),'session',None)
    scene=getattr(session,'scene',None)
    torch=sys.modules.get('torch')
    audit=dict(worker_id=worker_id,failure=failure,resource=_resource(),
        actual_imported_sources=sorted(project_source_paths(list(sys.modules.items()))),
        forbidden_calls=copy.deepcopy(getattr(scene,'forbidden_calls',[])),
        headless_description=copy.deepcopy(getattr(session,'headless_description',None)),
        human_root_fixed=getattr(scene,'human_root_fixed',None),
        guitar_root_fixed=getattr(scene,'guitar_root_fixed',None),
        guitar_gravity_disabled=getattr(scene,'guitar_gravity_disabled',None),
        native_current_step=getattr(scene,'steps',None),
        runtime=dict(executable=sys.executable,version=sys.version,platform=sys.platform,
            active_python_threads=threading.active_count(),
            torch_num_threads=torch.get_num_threads() if torch is not None else None,
            torch_num_interop_threads=torch.get_num_interop_threads() if torch is not None else None,
            thread_environment={key:os.environ.get(key) for key in
                ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}))
    write(Path(spec['out'])/'worker_final_audit.json',audit)


def _worker(connection,spec,worker_id,factory):
    env=None
    failure=None
    try:
        Path(spec['out']).mkdir(parents=True,exist_ok=True)
        # A supplied CPU factory must be module-level/picklable and imports no Isaac.
        env=(factory or _native_environment)(spec,worker_id)
        connection.send(('ready',_resource()))
        episode=0
        transition=0
        previous_classification=None
        while True:
            command,value=connection.recv()
            if command=='close':
                connection.send(('ok',None))
                break
            if command=='reset':
                observation,info=env.reset()
                contract=copy.deepcopy(env.contract)
                reset_info=dict(info,training_contract=contract,resource=_resource(),worker_id=worker_id)
                if hasattr(env,'control'):
                    from guitar_learning.training.training_log_io import write
                    scene=env.control.session.scene
                    folder=Path(spec['out'])/('audit_episode_%06d'%episode)
                    folder.mkdir(parents=True,exist_ok=False)
                    initial=dict(native=env.last_sample,joint_names=scene.names,human_body_names=scene.human_bodies,
                        guitar_body_names=scene.guitar_bodies,human_properties=scene.human_properties,
                        guitar_properties=scene.guitar_properties,loaded_assets=scene.loaded_assets,
                        collision_policy=scene.collision_policy,actual_shape_properties=scene.shape_properties,
                        zero_range_indices=scene.zero_indices,position_indices=scene.position_indices,
                        effort_indices=scene.effort_indices,
                        native_PD_properties={k:scene.pd_properties[k].tolist() for k in scene.pd_properties.dtype.names},
                        control_K105=scene.control_kp,control_D105=scene.control_kd,
                        human_root_fixed=scene.human_root_fixed,guitar_root_fixed=scene.guitar_root_fixed,
                        guitar_gravity_disabled=scene.guitar_gravity_disabled,target105_rad=scene.target,
                        resource=_resource())
                    write(folder/'initial_values.json',initial)
                    write(folder/'contract.json',contract)
                    if 'episode_task' in info: write(folder/'episode_task.json',info['episode_task'])
                    reset_info['initial_values_path']=str(folder/'initial_values.json')
                episode+=1
                transition=0
                previous_classification=None
                connection.send(('ok',(observation,reset_info)))
            elif command=='curriculum':
                observation=env.set_curriculum(value)
                connection.send(('ok',observation))
            elif command=='step':
                observation,reward,terminated,truncated,info=env.step(value)
                compact=_compact(env,info,value)
                from guitar_learning.training.training_log_io import classification_signature, format_info
                signature=classification_signature(compact)
                changed=previous_classification is not None and signature!=previous_classification
                if hasattr(env,'control') and (transition==0 or changed or info.get('failure_reasons') or spec.get('raw_samples',False)):
                    from guitar_learning.training.training_log_io import write
                    path=folder/('transition_%08d.json.gz'%transition)
                    write(path,dict(action=value,observation=observation,reward=reward,terminated=terminated,
                                    truncated=truncated,info=info),compressed=True)
                    compact['raw_sample_path']=str(path)
                previous_classification=signature
                compact=format_info(compact,value,detail=spec.get('log_detail','diagnostic'))
                compact.update(worker_id=worker_id,episode_index=episode-1,control_tick=transition)
                transition+=1
                connection.send(('ok',(observation,reward,terminated,truncated,compact)))
            else:
                raise ValueError('unknown worker command')
    except BaseException as error:
        failure=dict(worker_id=worker_id,type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        try: connection.send(('error',failure))
        except (BrokenPipeError,EOFError,OSError): pass
    finally:
        try:
            _final_audit(env,spec,worker_id,failure)
        except BaseException as audit_error:
            import json
            import sys
            detail=dict(worker_id=worker_id,type=type(audit_error).__name__,message=str(audit_error),original_failure=failure)
            print('worker audit error: '+json.dumps(detail),file=sys.stderr,flush=True)
            try:
                with (Path(spec['out'])/'worker_audit_error.json').open('x') as stream:
                    json.dump(detail,stream)
            except BaseException: pass
        if env is not None:
            try: env.close()
            except BaseException: pass
        connection.close()


class Pool:
    def __init__(self,specs,timeout_s=120.,worker_factory=None,wait_callback=None):
        if len(specs) not in (1,2,4,8,16) or not math.isfinite(timeout_s) or timeout_s<=0:
            raise ValueError('1/2/4/8/16 worker specs and positive finite timeout required')
        paths=[str(Path(spec['out']).resolve()) for spec in specs]
        if len(set(paths))!=len(paths): raise ValueError('independent worker output paths required')
        self.num_envs=len(specs)
        self.timeout_s=timeout_s
        self.wait_callback=wait_callback
        self._last_wait_callback=0.
        self.close_diagnostics=[]
        self.processes=[]
        self.connections=[]
        self.valid=True
        self.closed=False
        self.contract=None
        self.observations=[None]*self.num_envs
        context=mp.get_context('spawn')
        try:
            for worker_id,spec in enumerate(specs):
                parent,child=context.Pipe()
                process=context.Process(target=_worker,args=(child,copy.deepcopy(spec),worker_id,worker_factory))
                process.start()
                child.close()
                self.connections.append(parent)
                self.processes.append(process)
            self.resources=self._receive(list(range(self.num_envs)),expected='ready',operation='startup')
        except BaseException as error:
            self.valid=False
            self.close()
            error.pool_close_diagnostics=self.close_diagnostics
            raise

    def worker_status(self):
        return [dict(worker_id=index,pid=process.pid,alive=process.is_alive(),exitcode=process.exitcode)
                for index,process in enumerate(self.processes)]

    def _worker_error(self,index,reason):
        process=self.processes[index]
        # A closed pipe can become ready just before the sentinel is signalled.
        process.join(timeout=.05)
        return RuntimeError('%s: worker=%s pid=%s exitcode=%s'%(reason,index,process.pid,process.exitcode))

    def _receive(self,indices,expected='ok',operation='receive'):
        started=time.monotonic()
        deadline=started+self.timeout_s
        pending=set(indices)
        values={}
        while pending:
            now=time.monotonic()
            if self.wait_callback is not None and now-self._last_wait_callback>=.5:
                self._last_wait_callback=now
                self.wait_callback(dict(operation=operation,pending_workers=sorted(pending),elapsed_s=now-started,
                                        worker_status=self.worker_status()))
            handles={self.connections[index]:index for index in pending}
            sentinels={process.sentinel:index for index,process in enumerate(self.processes)}
            ready=wait(list(handles)+list(sentinels),timeout=min(.5,max(0.,deadline-now)))
            # Consume every ready response before inspecting deaths, preserving caller order on return.
            for connection in ready:
                if connection not in handles: continue
                index=handles[connection]
                try: status,value=connection.recv()
                except (EOFError,OSError) as error: raise self._worker_error(index,'worker connection closed') from error
                if status!=expected: raise self._worker_error(index,'worker failure '+str(value))
                values[index]=value
                pending.remove(index)
            for index,process in enumerate(self.processes):
                if not process.is_alive(): raise self._worker_error(index,'worker exited')
            if pending and time.monotonic()>=deadline:
                raise TimeoutError('worker IPC timeout: operation=%s pending=%s status=%s'%
                                   (operation,sorted(pending),self.worker_status()))
        return [values[index] for index in indices]

    def _request(self,command,indices,values):
        if self.closed or not self.valid: raise RuntimeError('pool is closed or invalid')
        try:
            for index,value in zip(indices,values):
                if not self.processes[index].is_alive(): raise self._worker_error(index,'worker exited before '+command)
                try: self.connections[index].send((command,value))
                except (BrokenPipeError,EOFError,OSError) as error:
                    raise self._worker_error(index,'worker send failed during '+command) from error
            return self._receive(indices,operation=command)
        except BaseException:
            self.valid=False
            self.close()
            raise

    def _stack(self):
        import numpy as np
        if any(obs is None for obs in self.observations): raise RuntimeError('all workers require initial reset')
        return {key:np.stack([obs[key] for obs in self.observations]) for key in FIELDS}

    def set_curriculum(self,progress):
        indices=list(range(self.num_envs))
        rows=self._request('curriculum',indices,[progress]*self.num_envs)
        self.observations=list(rows)
        return self._stack()

    def reset(self,indices=None):
        indices=list(range(self.num_envs)) if indices is None else list(indices)
        if len(set(indices))!=len(indices) or any(isinstance(i,bool) or not isinstance(i,int) or not 0<=i<self.num_envs for i in indices):
            raise ValueError('unique valid reset indices required')
        rows=self._request('reset',indices,[None]*len(indices))
        infos=[None]*self.num_envs
        try:
            for index,(observation,info) in zip(indices,rows):
                contract=info['training_contract']
                if self.contract is None: self.contract=copy.deepcopy(contract)
                elif self.contract!=contract: raise ValueError('worker environment contract mismatch')
                self.observations[index]=observation
                infos[index]=info
            return self._stack(),infos
        except BaseException:
            self.valid=False
            self.close()
            raise

    def step(self,actions):
        import numpy as np
        actions=np.asarray(actions)
        if actions.shape!=(self.num_envs,39) or not np.isfinite(actions).all() or np.any(np.abs(actions)>1):
            raise ValueError('finite bounded actions[N,39] required')
        rows=self._request('step',list(range(self.num_envs)),list(actions))
        try:
            for index,row in enumerate(rows): self.observations[index]=row[0]
            reward=np.array([row[1] for row in rows],dtype=np.float32)
            terminated=np.array([row[2] for row in rows])
            truncated=np.array([row[3] for row in rows])
            if not np.isfinite(reward).all() or terminated.dtype!=np.bool_ or truncated.dtype!=np.bool_:
                raise ValueError('finite rewards and boolean termination flags required')
            return self._stack(),reward,terminated,truncated,[row[4] for row in rows]
        except BaseException:
            self.valid=False
            self.close()
            raise

    def close(self):
        if self.closed: return
        self.closed=True
        self.close_diagnostics=[dict(row,close_sent=False,terminate_sent=False,kill_sent=False)
                                for row in self.worker_status()]
        for index,connection in enumerate(self.connections):
            try: connection.send(('close',None))
            except (BrokenPipeError,EOFError,OSError) as error:
                self.close_diagnostics[index]['close_error']=str(error)
            else: self.close_diagnostics[index]['close_sent']=True
        for escalation in (None,'terminate','kill'):
            for index,process in enumerate(self.processes):
                if escalation is not None and process.is_alive():
                    getattr(process,escalation)()
                    self.close_diagnostics[index][escalation+'_sent']=True
            deadline=time.monotonic()+2.
            for process in self.processes:
                process.join(timeout=max(0.,deadline-time.monotonic()))
        for index,row in enumerate(self.worker_status()):
            self.close_diagnostics[index].update(final_alive=row['alive'],final_exitcode=row['exitcode'])
        for connection in self.connections: connection.close()

    def __enter__(self): return self
    def __exit__(self,*args): self.close()


class Collector:
    def __init__(self,policy,pool,device='cpu'):
        import numpy as np
        self.policy,self.pool,self.device=policy,pool,device
        self.observation=None
        self.dataset_valid=True
        self.episode_cost=np.zeros(pool.num_envs)
        self.episode_reward=np.zeros(pool.num_envs)
        self.episode_steps=np.zeros(pool.num_envs,dtype=int)

    def _inputs(self,observation):
        import numpy as np
        import torch
        if any(key not in observation for key in FIELDS): raise ValueError('complete observation required')
        for key in FIELDS:
            if observation[key].dtype!=(np.bool_ if 'mask' in key else np.float32):
                raise ValueError('observation dtype mismatch: '+key)
        values=[torch.as_tensor(observation[key].copy(),device=self.device) for key in FIELDS]
        self.policy._validate(*values)
        return values

    def collect(self,horizon,progress_callback=None):
        import numpy as np
        import torch
        if isinstance(horizon,bool) or not isinstance(horizon,int) or horizon<1: raise ValueError('positive horizon required')
        if not self.dataset_valid: raise RuntimeError('collector invalid after failure')
        rows,completed=[],[]
        started=time.monotonic()
        try:
            if self.observation is None: self.observation,_=self.pool.reset()
            for tick in range(horizon):
                inputs=self._inputs(self.observation)
                with torch.no_grad(): result=self.policy.act(*inputs)
                observation,reward,terminated,truncated,infos=self.pool.step(result['action'].cpu().numpy())
                cost=np.array([info['cost'] for info in infos],dtype=np.float32)
                if not np.isfinite(cost).all() or np.any(cost<0): raise ValueError('finite nonnegative costs required')
                with torch.no_grad(): nxt=self.policy(*self._inputs(observation))
                row=dict(zip(FIELDS,inputs))
                row.update(latent=result['latent'],logp=result['logp'],old_mean=result['mean'],old_log_std=result['log_std'],
                           reward_value=result['reward_value'],cost_value=result['cost_value'])
                for key,value in dict(reward=reward,cost=cost,terminated=terminated,truncated=truncated).items():
                    row[key]=torch.as_tensor(value,device=self.device)
                active=~row['terminated']
                row.update(next_reward_value=nxt['reward_value']*active,next_cost_value=nxt['cost_value']*active)
                rows.append({key:value.detach().clone() for key,value in row.items()})
                self.episode_cost+=cost
                self.episode_reward+=reward
                self.episode_steps+=1
                done=np.flatnonzero(terminated|truncated).tolist()
                for index in done:
                    episode=infos[index].get('episode')
                    if episode is not None and (not isinstance(episode,dict) or episode.get('valid') is not True):
                        raise ValueError('invalid completed worker episode')
                    reason=infos[index].get('termination_reason') or ('terminal' if terminated[index] else 'truncated')
                    completed.append(dict(worker_id=index,valid=True,reason=reason,cost=float(self.episode_cost[index]),
                                          reward=float(self.episode_reward[index]),steps=int(self.episode_steps[index])))
                    if episode is not None and 'left_curriculum' in episode:
                        completed[-1]['left_curriculum']=copy.deepcopy(episode['left_curriculum'])
                    self.episode_cost[index]=self.episode_reward[index]=self.episode_steps[index]=0
                if progress_callback is not None:
                    progress_callback(dict(ticks=tick+1,horizon=horizon,num_envs=self.pool.num_envs,
                                           transitions=(tick+1)*self.pool.num_envs,elapsed_s=time.monotonic()-started,
                                           episodes_completed=len(completed),phase='step_complete',
                                           pending_reset_workers=done))
                self.observation=self.pool.reset(done)[0] if done else observation
            return {key:torch.stack([row[key] for row in rows]) for key in rows[0]},completed
        except BaseException:
            self.dataset_valid=False
            self.pool.valid=False
            self.pool.close()
            raise


def persistent_native_environment(spec,worker_id):
    import isaacgym  # Must precede numpy/torch in each spawned native worker.
    import numpy as np
    import torch
    from guitar_learning.runtime.persistent_environment import build_persistent_environment
    if not spec.get('headless',True):
        raise ValueError('persistent training currently requires headless sessions')
    seed=int(spec.get('seed',7))+worker_id
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    torch.set_num_threads(1)
    return build_persistent_environment(spec['config'],Path(spec['out'])/'environment',
        bundle=spec['bundle'],stage=spec['stage'],
        start_event_index=spec.get('start_event_index',0),phrase_events=spec.get('phrase_events',8),
        tempo_scale=spec.get('tempo_scale',1.),seed=int(spec.get('seed',7)),worker_id=worker_id,
        music=spec.get('music'),**dict(spec.get('env_kwargs',{})))


class PersistentPool(Pool):
    def __init__(self,specs,timeout_s=120.,worker_factory=None,wait_callback=None):
        super().__init__(specs,timeout_s=timeout_s,
            worker_factory=worker_factory or persistent_native_environment,wait_callback=wait_callback)


def finalize_persistent_run(out):
    out=Path(out)
    report_path=out/'report.json'
    if not report_path.is_file():
        return None
    core=json.loads(report_path.read_text())
    errors=[];workers=[]
    for index in range(core['settings']['num_envs']):
        folder=out/('worker_%03d'%index)/'environment'
        lifecycle=folder/'persistent_lifecycle.json'
        row=dict(worker_id=index,path=str(lifecycle),resets=[])
        try:
            final=json.loads(lifecycle.read_text())
            counts=final['native_calls']
            if not final['closed'] or counts['create_sim']!=1 or counts['create_env']!=1 or counts['destroy_sim']!=1:
                raise ValueError('one native scene must be created once and destroyed once at final close')
            if counts['load_asset']<1:
                raise ValueError('native asset load evidence missing')
            if final['forbidden_calls_total']:
                raise ValueError('native guard violations remain')
            reset_paths=sorted(folder.glob('episode_*/persistent_reset.json'))
            if len(reset_paths)!=final['episode_index']+1:
                raise ValueError('persistent reset evidence count mismatch')
            previous=None
            for number,path in enumerate(reset_paths):
                reset=json.loads(path.read_text());d=reset['diagnostics'];readback=reset['readback']
                if d['episode_index']!=number or d['native_identities']!=final['native_identities']:
                    raise ValueError('episode/scene/controller identity changed')
                if any(d['native_calls'][key]!=counts[key] for key in ('create_sim','create_env','load_asset')) or d['native_calls']['destroy_sim']:
                    raise ValueError('scene/environment/assets reconstructed during reset')
                if d['episode_local_physics_steps'] or d['controller_target_history_length'] or d['forbidden_calls_total']:
                    raise ValueError('episode clock/history/guard not reset correctly')
                if not d['native_properties_unchanged']:
                    raise ValueError('native properties changed')
                if previous is not None and d['initial_state_calls_total']!=previous+2:
                    raise ValueError('only one human DOF and one guitar body state reset expected')
                previous=d['initial_state_calls_total']
                if readback['human_DOF_pos_vel_max_error']>1e-6 or readback['guitar_velocity_max_scalar_error']>1e-6:
                    raise ValueError('prepared state/velocity readback mismatch')
                guitar=readback['body_pose_readback']['guitar']
                if guitar['max_position_error_m']>1e-6 or guitar['max_rotation_error_rad']>1e-6:
                    raise ValueError('prepared guitar pose readback mismatch')
                row['resets'].append(dict(path=str(path),sha256=digest(path),episode_index=number))
            if final['initial_state_calls_total']!=previous:
                raise ValueError('state setter called after the final reset boundary')
            row['lifecycle']=final;row['sha256']=digest(lifecycle)
        except (OSError,ValueError,KeyError,TypeError) as error:
            errors.append(dict(worker_id=index,type=type(error).__name__,message=str(error)))
        workers.append(row)
    audit=dict(completed=not errors,errors=errors,workers=workers,
        scope='persistent scene/asset lifetime and episode reset evidence, not hidden solver cache restoration')
    write(out/'persistent_audit.json',audit)
    # Preserve the exact original runner report before publishing the combined outcome.
    core_path=out/'core_report.json'
    if core_path.exists():raise FileExistsError(str(core_path))
    report_path.rename(core_path)
    result=copy.deepcopy(core)
    result['persistent_audit']=dict(path=str(out/'persistent_audit.json'),completed=audit['completed'],errors=errors)
    result['core_report']=dict(path=str(core_path),sha256=digest(core_path))
    result['completed']=bool(core['completed'] and audit['completed'])
    if core['completed'] and not audit['completed']:
        result.update(stopped='error',failure=dict(type='PersistentLifecycleAuditError',message=str(errors)))
    write(report_path,result)
    return audit['completed']
