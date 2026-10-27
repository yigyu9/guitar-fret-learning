"""Separate initial native FK derivatives from one-step PD target responses."""
import argparse
import copy
import json
from pathlib import Path
from .palm_side_feedback import PHASE,SETTINGS,context,observation,task_error,input_paths
from .self_collision_environment import SelfCollisionEnvironment
from .environment import np
from .build_fixed_lower_asset import read,sha,LOWER_BODIES
from .run_joint_hold import native_state,snapshot
from .native_contacts import body_names,read_contacts
from scipy.spatial.transform import Rotation
from scipy.optimize import lsq_linear


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',choices=('fk','response'),required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();ctx=context()
    args.out.mkdir(parents=True,exist_ok=False)
    files=input_paths()+[Path(__file__).resolve()]
    files += [Path(p) for p in read(input_paths()[6])['input_sha256']]
    files += [Path(__file__).with_name(n) for n in ('self_collision_environment.py','native_contacts.py')]
    hashes={str(p):sha(p) for p in files}
    baseline_state=read(input_paths()[5]);baseline_after=baseline_state['states'][1]
    rows=[];native_count=0;step_count=0
    arm=ctx['indices'];q0=ctx['q0'];names=ctx['reference']['human_joint_names']
    from .build_fixed_lower_asset import pose
    pp,pq=pose(ctx['seed']['human_body_states'][ctx['reference']['human_body_names'].index('LH:palm')])
    initial_rotation=Rotation.from_quat(pq);initial_point=pp+initial_rotation.apply(ctx['local_point'])
    def write_partial():
        (args.out/'columns.json').write_text(json.dumps({'rows':rows,'native_initializations':native_count,
            'physics_steps':step_count,'input_sha256':hashes},indent=2,allow_nan=False)+'\n')
    def sample(delta,label):
        nonlocal native_count,step_count
        settings=copy.deepcopy(read(SETTINGS))
        if args.kind=='fk':settings['joint_angles_rad'].update({names[i]:float(q0[i]+d) for i,d in zip(arm,delta) if d})
        env=SelfCollisionEnvironment(settings,ctx['shift']);native_count+=1
        before=None
        try:
            before=native_state(env);props=env.gym.get_actor_dof_properties(env.env,env.human)
            actual_q=np.array([d['pos'] for d in before['human_dof_states']])
            checks={'guitar_initial_exact':before['guitar_body_states']==ctx['seed']['guitar_body_states'],
                'root_lower_initial_exact':all(before['human_body_states'][env.human_bodies.index(n)]==ctx['seed']['human_body_states'][env.human_bodies.index(n)] for n in ('Pelvis',)+LOWER_BODIES),
                'other_initial_q_exact':bool(np.array_equal(actual_q[np.setdiff1d(np.arange(len(q0)),arm)],q0[np.setdiff1d(np.arange(len(q0)),arm)])),
                'absolute_length_exact':env.rest_length==read(SETTINGS)['strap_rest_length_m'],
                'pd_exact':all(props[k].astype(float).tolist()==ctx['reference'][r] for k,r in
                    (('stiffness','native_pd_kp'),('damping','native_pd_kd'),('effort','native_effort_caps_nm'),('driveMode','native_drive_modes')))}
            if args.kind=='response':
                checks['initial_state_exact']=before==ctx['seed']
                offsets=np.zeros(66,dtype=np.float32)
                for i,d in zip(arm,delta):offsets[list(env.main_indices).index(i)]=d
                env.set_main_offsets(offsets)
                actual_delta=env.target[arm].astype(float)-q0[arm]
                checks['commands_preserve_states']=before==native_state(env)
                checks['target_bounds']=bool(((env.target[arm]>=ctx['lower']-2e-7)&(env.target[arm]<=ctx['upper']+2e-7)).all())
                if not all(checks.values()):raise AssertionError(checks)
                env.step_physics();step_count+=1
            else:actual_delta=actual_q[arm]-q0[arm]
            after=native_state(env);point,rotation=observation(env,ctx);error=task_error(env,ctx)
            checks.update(queries_preserve_states=after==native_state(env),
                actual_initial_probes_in_box=bool(((actual_q[arm]>=np.array(ctx['reference']['diagnostic_lower_rad'][:12])-2e-7)&
                    (actual_q[arm]<=np.array(ctx['reference']['diagnostic_upper_rad'][:12])+2e-7)).all()),
                root_lower_after_exact=all(after['human_body_states'][env.human_bodies.index(n)]==before['human_body_states'][env.human_bodies.index(n)] for n in ('Pelvis',)+LOWER_BODIES))
            row={'label':label,'actual_delta_rad':actual_delta.tolist(),'initial_state':before,'after_state':after,
                'point_W_m':point.tolist(),'rotation_xyzw':rotation.as_quat().tolist(),'task_error_m_scaled_rad':error.tolist(),
                'snapshot':snapshot(env),'checks':checks,'physics_steps':env.steps,
                'contacts':read_contacts(env.gym,env.env,body_names(env.gym,env.env)) if env.steps else []}
            rows.append(row);write_partial()
            if not all(checks.values()):raise AssertionError(checks)
            return row
        except Exception as error:
            write_partial()
            (args.out/'failure.json').write_text(json.dumps({'type':type(error).__name__,'message':str(error),
                'label':label,'initial_state':before,'native_initializations':native_count,'physics_steps':step_count},indent=2)+'\n')
            raise
        finally:env.close()
    baseline=sample(np.zeros(12),'baseline')
    if args.kind=='fk' and baseline['after_state']!=ctx['seed']:raise AssertionError('fresh FK baseline mismatch')
    if args.kind=='response' and baseline['after_state']!=baseline_after:raise AssertionError('first-step baseline mismatch')
    columns=[]
    for j,i in enumerate(arm):
        h=.001 if args.kind=='fk' else .03
        low,high=(np.array(ctx['reference']['diagnostic_lower_rad'][:12]),np.array(ctx['reference']['diagnostic_upper_rad'][:12])) if args.kind=='fk' else (ctx['lower'],ctx['upper'])
        sign=1 if high[j]-q0[i]>=q0[i]-low[j] else -1
        h=sign*min(h,high[j]-q0[i] if sign>0 else q0[i]-low[j])
        if abs(h)<1e-6:raise ValueError('no representable probe interval')
        delta=np.zeros(12);delta[j]=h;row=sample(delta,names[i]);actual_h=row['actual_delta_rad'][j]
        if args.kind=='fk':
            col=np.r_[(np.array(row['point_W_m'])-initial_point)/actual_h,
                .08*(Rotation.from_quat(row['rotation_xyzw'])*initial_rotation.inv()).as_rotvec()/actual_h]
        else:col=(np.array(baseline['task_error_m_scaled_rad'])-row['task_error_m_scaled_rad'])/actual_h
        columns.append(col)
        print(json.dumps({'kind':args.kind,'joint':names[i],'actual_h':actual_h,'norm':float(np.linalg.norm(col))}),flush=True)
    matrix=np.array(columns).T
    checks={'all_probe_contracts':all(all(r['checks'].values()) for r in rows),'finite_matrix':bool(np.isfinite(matrix).all()),
        'baseline_exact':baseline['after_state']==(ctx['seed'] if args.kind=='fk' else baseline_after)}
    result={'matrix':matrix.tolist(),'arm_names':[names[i] for i in arm],'settings_sha256':sha(SETTINGS),
        'native_initializations':native_count,'physics_steps':step_count,'checks':checks,
        'singular_values':np.linalg.svd(matrix,compute_uv=False).tolist(),'input_sha256':hashes,
        'orientation_scale_m_per_rad':.08,'scope':'initial native point FK' if args.kind=='fk' else 'one-step native PD target response, not stationary actuator model'}
    if args.kind=='fk':
        delta=np.array([.0005 if np.array(ctx['reference']['diagnostic_upper_rad'])[j]-q0[i]>.001 else -.0005 for j,i in enumerate(arm)])
        held=sample(delta,'combined_holdout');delta=np.array(held['actual_delta_rad'])
        predicted=matrix@delta
        actual=np.r_[np.array(held['point_W_m'])-initial_point,.08*(Rotation.from_quat(held['rotation_xyzw'])*initial_rotation.inv()).as_rotvec()]
        result['heldout_error_m_scaled_rad']=(actual-predicted).tolist()
        checks['heldout_position_error_below_2um']=bool(np.linalg.norm((actual-predicted)[:3])<2e-6)
        checks['heldout_rotation_error_below_20urad']=bool(np.linalg.norm((actual-predicted)[3:])/.08<2e-5)
        checks['all_probe_contracts']=all(all(r['checks'].values()) for r in rows)
    else:
        fit=lsq_linear(np.vstack((matrix,1e-5*np.eye(12))),np.r_[baseline['task_error_m_scaled_rad'],np.zeros(12)],
            bounds=(ctx['lower']-q0[arm],ctx['upper']-q0[arm]),tol=1e-12,max_iter=500)
        if not fit.success:raise AssertionError(fit.message)
        result.update(bias_rad=fit.x.tolist(),baseline_error_m_scaled_rad=baseline['task_error_m_scaled_rad'],
            predicted_error_m_scaled_rad=(np.array(baseline['task_error_m_scaled_rad'])-matrix@fit.x).tolist())
        bias=sample(fit.x,'bias_validation')
        result['validation_error_m_scaled_rad']=bias['task_error_m_scaled_rad']
        checks['bias_within_bounds']=bool(((q0[arm]+fit.x>=ctx['lower'])&(q0[arm]+fit.x<=ctx['upper'])).all())
        checks['all_probe_contracts']=all(all(r['checks'].values()) for r in rows)
    result['native_initializations']=native_count;result['physics_steps']=step_count
    checks['inputs_unchanged']=all(sha(Path(p))==h for p,h in hashes.items())
    (args.out/'calibration.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if not all(checks.values()):raise AssertionError(checks)
    print(json.dumps({'checks':checks,'initializations':native_count,'steps':step_count}),flush=True)


if __name__=='__main__':main()
