"""Make persistent lifecycle evidence part of the new entry point's outcome."""
import copy
import json
from pathlib import Path
from .recording import write,digest


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
