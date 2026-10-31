"""Compare native target pulse responses; coupling prevents a direct axis-swap verdict."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--phase',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True); args=parser.parse_args()
    phase=args.phase.resolve(); out=args.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    paths=[Path(__file__).resolve()]
    for axis in ('off','x','y','z'):
        paths += [phase/axis/'data'/n for n in ('states.json','commands.json','initial_values.json','report.json','mass_matrix_initial.json','initial_audit.json')]
        paths += [phase/axis/n for n in ('inputs_before.json','inputs_after.json')]
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    hashes={str(p):digest(p) for p in paths}
    write=lambda n,d:(out/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    write('inputs_before.json',{'sha256':hashes})
    read=lambda p:json.loads(p.read_text())
    initial=[read(phase/a/'data/initial_values.json') for a in ('off','x','y','z')]
    assert all(v['native_initial_state']==initial[0]['native_initial_state'] and v['PD_properties']==initial[0]['PD_properties'] for v in initial)
    names=initial[0]['joint_names']; shoulder=[names.index('R_Shoulder_'+a) for a in ('x','y','z')]
    states={a:{r['physics_step']:r for r in read(phase/a/'data/states.json')} for a in ('off','x','y','z')}
    bodies=list(read(phase/'off/data/initial_audit.json')['body_errors'])
    assert len(bodies)==len(initial[0]['native_initial_state']['human_body_states'])
    def relative(state):
        rotations=[]
        for name in ('R_Thorax','R_Shoulder'):
            quat=state['human_body_states'][bodies.index(name)]['pose']['r']
            rotations.append(Rotation.from_quat([quat[k] for k in ('x','y','z','w')]))
        return rotations[0].inv()*rotations[1]
    basis=np.eye(3)[:,[0,2,1]]
    q0=np.array([r['pos'] for r in initial[0]['native_initial_state']['human_dof_states']])[shoulder]
    rest=Rotation.from_rotvec(basis@q0).inv()*relative(initial[0]['native_initial_state'])
    rows=[]; reports={}
    for a in ('off','x','y','z'):
        report=read(phase/a/'data/report.json'); closure=read(phase/a/'inputs_after.json')
        assert report['completed_5s'] and report['physics_steps']==1200 and report['frame_count']==151 and all(report['checks'].values())
        assert closure['inputs_unchanged'] and closure['task_error'] is None
        assert all(digest(Path(v['path']))==v['sha256'] for v in report['videos'].values())
        reports[a]={'physics_steps':1200,'frame_count':151,'native_checks':report['checks'],'closure':closure,'videos':report['videos']}
        commands=read(phase/a/'data/commands.json'); assert len(commands)==2 and [c['before_physics_step'] for c in commands]==[0,4]
        assert all(c['native_targets_rad']==c['requested_targets_rad'] for c in commands)
        assert commands[1]['requested_targets_rad']==initial[0]['base_targets_rad']
        delta=np.array(commands[0]['requested_targets_rad'])-np.array(initial[0]['base_targets_rad'])
        assert np.count_nonzero(delta)==(0 if a=='off' else 1)
        if a!='off': assert abs(delta[names.index('R_Shoulder_'+a)]-.02)<1e-7
        for step in range(1,5):
            r=states[a][step]; base=states['off'][step]
            q=lambda x:np.array([s['pos'] for s in x['native_state']['human_dof_states']])
            vel=lambda x:np.array([s['vel'] for s in x['native_state']['human_dof_states']])
            force=np.array(r['total_native_dof_force_Nm']); force0=np.array(base['total_native_dof_force_Nm'])
            assert force.shape==force0.shape==(81,) and np.isfinite(force).all()
            native_relative=relative(r['native_state']); baseline_relative=relative(base['native_state'])
            predicted_relative=Rotation.from_rotvec(basis@q(r)[shoulder])*rest
            rows.append({'shoulder_relative_rotation_delta_from_OFF_rad':(native_relative*baseline_relative.inv()).as_rotvec().tolist(),
                'shoulder_state_FK_error_deg':float(np.degrees((predicted_relative*native_relative.inv()).magnitude())),
                'axis':a,'physics_step':step,'joint_names':names,'q_delta_rad':(q(r)-q(base)).tolist(),
                'qdot_delta_rad_s':(vel(r)-vel(base)).tolist(),'total_force_delta_Nm':(force-force0).tolist(),
                'shoulder_q_delta_rad':(q(r)-q(base))[shoulder].tolist(),
                'shoulder_qdot_delta_rad_s':(vel(r)-vel(base))[shoulder].tolist(),
                'native_contact_rows':len(r['contacts']),'baseline_contact_rows':len(base['contacts'])})
    summary={'initial_states_PD_exact':True,'reports':reports,
        'shoulder_names':[names[i] for i in shoulder],
        'shoulder_relative_rotation_FK_max_error_deg':max(r['shoulder_state_FK_error_deg'] for r in rows),
        'step4_shoulder_response_columns_x_y_z_rad':np.array([next(r['shoulder_q_delta_rad'] for r in rows if r['axis']==a and r['physics_step']==4) for a in ('x','y','z')]).T.tolist(),
        'scope':'native target readback and observed pulse responses; total force is not isolated drive torque; coupled dynamics do not certify target-coordinate permutation; no music or learning'}
    write('rows.json',rows); write('summary.json',summary)
    unchanged=all(digest(Path(p))==h for p,h in hashes.items()); write('inputs_after.json',{'unchanged':unchanged,'input_count':len(hashes)})
    assert unchanged
    print(json.dumps(summary['step4_shoulder_response_columns_x_y_z_rad']))


if __name__=='__main__':main()
