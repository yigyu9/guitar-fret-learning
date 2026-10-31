"""Measure small constant PD-target perturbations for 0.1s in native Gym."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1'
CALIBRATION=PHASE.parent/'palm_normal_control_v1/cap_0p3/calibration.json'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--mode',choices=('bias','tracking'),default='bias')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    hashes={str(CALIBRATION):digest(CALIBRATION)}
    calibration=json.loads(CALIBRATION.read_text())
    if not all(calibration['checks'].values()):raise AssertionError('source calibration failed')
    paths=[Path(p) for p in calibration['input_sha256']]+[Path(__file__).resolve(),args.candidate.resolve()]
    paths += [ROOT/'stability_adapter_2/palm_normal_task.py']
    hashes.update({str(p):digest(p) for p in paths})
    if any(hashes[p]!=h for p,h in calibration['input_sha256'].items()):raise AssertionError('source inputs changed')
    # All project helper/data inputs above are sealed before these imports and reads.
    from .palm_side_feedback import context,SETTINGS,SideFeedback,np
    from .palm_normal_task import prepare,error_from_state
    from .self_collision_environment import SelfCollisionEnvironment
    from .run_joint_hold import native_state,snapshot
    from .native_contacts import body_names,read_contacts
    from .build_fixed_lower_asset import read,LOWER_BODIES,pose
    from scipy.spatial.transform import Rotation
    candidate=read(args.candidate);bias=np.asarray(candidate['bias_rad'],dtype=float)
    ctx=prepare(context());arm=ctx['indices'];q0=ctx['q0'][arm]
    low=np.array(calibration['lower_rad']);high=np.array(calibration['upper_rad'])
    if bias.shape!=(12,) or not np.isfinite(bias).all() or not ((q0+bias>=low)&(q0+bias<=high)).all():
        raise ValueError('candidate must be finite and within existing target box')
    controller=SideFeedback(calibration['fk']['matrix'],q0,bias,low,high) if args.mode=='tracking' else None
    env=SelfCollisionEnvironment(read(SETTINGS),ctx['shift'])
    other=np.setdiff1d(np.arange(len(env.names)),arm);props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
    names=body_names(env.gym,env.env)
    proxy=np.array(read(PHASE.parent/'palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local'])
    states=[];trace=[];tasks=[];contacts=[];controls=[];up=[];checks={}
    def record_state():
        state=native_state(env);states.append(state);trace.append(snapshot(env));tasks.append(error_from_state(state,ctx).tolist())
        up.append(float(Rotation.from_quat(pose(state['human_body_states'][ctx['palm_index']])[1]).apply(proxy)[2]))
        if up[-1]<=0:raise AssertionError('source palm-up proxy outside upper hemisphere')
    def save(failure=None):
        report={'mode':args.mode,'candidate_path':str(args.candidate.resolve()),'source_sha256':hashes,
            'native_initializations':1,'physics_steps':env.steps,'checks':checks,'failure':failure,
            'human_body_names':env.human_bodies,'human_joint_names':env.names,'arm_indices':arm.tolist(),
            'bias_rad':bias.tolist(),'lower_rad':low.tolist(),'upper_rad':high.tolist(),
            'minimum_source_palm_up_proxy_z':min(up,default=None),'initial_settings':env.initial_settings,
            'pd_kp':props['stiffness'].astype(float).tolist(),'pd_kd':props['damping'].astype(float).tolist(),
            'rest_length_m':env.rest_length,'stability_success':False,
            'scope':'target-only perturbation at identical initial state; finite 0.1s response is not a feedback Jacobian; parallelism is soft'}
        for name,value in [('report',report),('states',states),('trace',trace),('tasks',tasks),('controls',controls),('contacts',contacts)]:
            (args.out/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    try:
        record_state();checks={'initial_state_exact':states[0]==ctx['seed'],'commands_preserve_states':True,
            'other_targets_exact':True,'target_bounds':True,'residual_cap_and_rate':True,'queries_preserve_states':True}
        if not checks['initial_state_exact']:raise AssertionError('initial state changed')
        previous=np.zeros(12);record={};interval=env.config['physics_hz']//env.config['control_hz']
        if interval!=4:raise AssertionError('expected 240Hz physics / 60Hz control')
        for step in range(24):
            updated=step%interval==0
            if updated:
                before=native_state(env);target=q0+bias;record={'task_error_m_scaled_rad':tasks[-1]}
                if controller is not None:
                    target,record=controller.update(error_from_state(before,ctx),1/env.config['control_hz'])
                    checks['residual_cap_and_rate'] &= bool((np.abs(controller.delta)<=.15+1e-12).all() and
                        (np.abs(controller.delta-previous)<=1/env.config['control_hz']+1e-12).all())
                    previous=controller.delta.copy()
                offsets=np.zeros(66,dtype=np.float32)
                for i,d in zip(arm,target-q0):offsets[list(env.main_indices).index(i)]=d
                env.set_main_offsets(offsets);checks['commands_preserve_states'] &= native_state(env)==before
            checks['other_targets_exact'] &= bool(np.array_equal(env.target[other],env.initial_q[other]))
            checks['target_bounds'] &= bool(((env.target[arm]>=low-2e-7)&(env.target[arm]<=high+2e-7)).all())
            controls.append(dict(record,updated_before_step=updated,physics_step=step+1,final_target_rad=env.target[arm].astype(float).tolist()))
            env.step_physics();record_state()
            contacts.append({'physics_step':env.steps,'contacts':read_contacts(env.gym,env.env,names)})
            checks['queries_preserve_states'] &= native_state(env)==states[-1]
        checks.update(root_lower_exact=all(s['human_body_states'][env.human_bodies.index(n)]==states[0]['human_body_states'][env.human_bodies.index(n)]
                for s in states for n in ('Pelvis',)+LOWER_BODIES),
            pd_unchanged=bool(np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human))),
            fixed_absolute_length=all(t['strap_rest_length_m']==env.rest_length for t in trace),
            finite_trace=all(t['finite'] for t in trace),palm_up_proxy_upper_hemisphere=min(up)>0,
            inputs_unchanged=all(digest(p)==h for p,h in hashes.items()))
        save()
        if not all(checks.values()):raise AssertionError(checks)
        print(json.dumps({'mode':args.mode,'checks':checks,'point_end_mm':float(np.linalg.norm(tasks[-1][:3])*1000)}),flush=True)
    except Exception as error:
        save({'type':type(error).__name__,'message':str(error)});raise
    finally:env.close()


if __name__=='__main__':main()
