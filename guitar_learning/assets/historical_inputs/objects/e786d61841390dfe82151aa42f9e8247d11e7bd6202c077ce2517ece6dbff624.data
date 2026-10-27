"""Compare stored native elbow/palm motion using a fixed initial guitar-front direction."""
import argparse
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--case',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    inputs={str(Path(__file__).resolve()):sha(__file__),str(Path(__file__).with_name('initial_pose_noise_v1.py')):sha(Path(__file__).with_name('initial_pose_noise_v1.py'))}
    def load(path):
        path=Path(path).resolve();inputs[str(path)]=sha(path);return read(path)
    initial0=load(args.baseline/'initial_values.json');initial1=load(args.case/'initial_values.json')
    report0=load(args.baseline/'report.json');report1=load(args.case/'report.json')
    cfg=load(report1['config']);candidate=load(cfg['initial_candidate'])
    names=initial0['joint_names'];bodies=initial0['human_body_names'];assert initial1['joint_names']==names and initial1['human_body_names']==bodies
    source=candidate['right_thigh_waist']['arm_forward']
    allowed=source.get('elbow3_scalar_delta_rad',source.get('arm6_scalar_delta_rad'))
    assert allowed and all(n.startswith(('R_Shoulder_','R_Elbow_')) for n in allowed)
    changed=[names.index(n) for n in allowed]
    frozen=[i for i in range(81) if i not in changed]
    assert np.array_equal(np.array(initial0['q_ref_rad'])[frozen],np.array(initial1['q_ref_rad'])[frozen])
    guitar_exact=initial0['native_initial_state']['guitar_body_states']==initial1['native_initial_state']['guitar_body_states']
    assert guitar_exact
    _,gr=pose(initial0['native_initial_state']['guitar_body_states'][0]);forward=gr.apply([0,0,1]);forward[2]=0;forward/=np.linalg.norm(forward)
    q0=np.array(initial0['q_ref_rad']);q1=np.array(initial1['q_ref_rad']);rows={}
    for name in ('R_Elbow','R_Wrist','RH:palm'):
        i=bodies.index(name);p0,r0=pose(initial0['native_initial_state']['human_body_states'][i]);p1,r1=pose(initial1['native_initial_state']['human_body_states'][i]);delta=p1-p0
        rows[name]={'initial_delta_W_mm':(delta*1000).tolist(),'initial_forward_mm':float(delta@forward*1000),
            'initial_orthogonal_displacement_mm':float(np.linalg.norm(delta-forward*(delta@forward))*1000),
            'initial_world_rotation_difference_deg':float(np.rad2deg((r0.inv()*r1).magnitude()))}
    assert rows['RH:palm']['initial_forward_mm']>0
    support_fixed=None;references_exact=None
    if 'elbow3_scalar_delta_rad' in source:
        support_fixed=all(initial0['native_initial_state']['human_body_states'][bodies.index(n)]==initial1['native_initial_state']['human_body_states'][bodies.index(n)] for n in ('R_Thorax','R_Shoulder'))
        assert support_fixed and np.linalg.norm(rows['R_Elbow']['initial_delta_W_mm'])<1e-5
        references_exact=load(args.baseline/'media/two_block_configuration.json')==load(args.case/'media/two_block_configuration.json')
        assert references_exact
    else:assert rows['R_Elbow']['initial_forward_mm']>0
    ep0=load(args.baseline/'media/physics_endpoint_contacts.json')['rows'];ep1=load(args.case/'media/physics_endpoint_contacts.json')['rows']
    assert len(ep0)==report0['physics_steps'] and len(ep1)==report1['physics_steps']
    count=min(len(ep0),len(ep1));forward_rows=[]
    for k in range(count):
        assert ep0[k]['physics_step']==ep1[k]['physics_step']==k+1
        entry={'physics_step':k+1,'time_s':(k+1)/240}
        for name in rows:
            p0,r0=pose(ep0[k]['human_body_states'][name]);p1,r1=pose(ep1[k]['human_body_states'][name]);delta=p1-p0
            entry[name+'_forward_delta_mm']=float(delta@forward*1000)
        forward_rows.append(entry)
    for name in rows:
        values=[r[name+'_forward_delta_mm'] for r in forward_rows]
        rows[name].update({'final_same_time_forward_delta_mm':values[-1],'minimum_same_time_forward_delta_mm':min(values),
                          'maximum_same_time_forward_delta_mm':max(values),'comparison_end_time_s':count/240})
    assert all(sha(p)==h for p,h in inputs.items())
    save(args.out,{'input_sha256':inputs,'baseline':str(args.baseline.resolve()),'case':str(args.case.resolve()),
        'forward_unit_W':forward.tolist(),'frozen_initial_q_count':len(frozen),'frozen_initial_q_exact':True,'support_bodies_initial_full_state_exact':support_fixed,'two_block_configuration_exact':references_exact,'guitar39_initial_full_state_exact':guitar_exact,
        'changed_scalar_delta_rad':{names[i]:float(q1[i]-q0[i]) for i in changed},'completed_5s':report1['completed'],
        'comparison_physics_steps':count,'source_requested':candidate['right_thigh_waist']['arm_forward'],
        'body_motion':rows,'forward_rows':forward_rows,'scope':'fixed initial guitar-front horizontal direction; world positions at identical native physics endpoints, not displacement relative to the moving guitar or measured force'})

if __name__=='__main__':main()
