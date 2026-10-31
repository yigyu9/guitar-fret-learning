"""Bounded distributed trunk flexion with supported/withdrawn left-hand starts."""
import argparse
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import calibrated_upper_fk,state_from_fk,source_audit,capsule_witness,ROOT,ASSET
from .search_upper_arm_static_v1 import BASE
PRIOR=ROOT/'docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/search_v1/lean3_gap500_z-10/candidate.json'

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    from .environment_contract_v1 import EnvironmentContract,CONFIG
    c=EnvironmentContract();initial=read(BASE);state0=initial['actual'];bodies=initial['human_body_names'];q0=c.q_ref.copy();fk,parents=calibrated_upper_fk(c.names,bodies,state0,q0);original=fk(q0);gp,gr=pose(state0['guitar_body_states'][0])
    normal=gr.apply([-1.,0,0]);forward=original['Pelvis'][1].apply([0,-1.,0]);forward[2]=0;forward/=np.linalg.norm(forward);axis=np.cross([0,0,1],forward);axis/=np.linalg.norm(axis)
    left=np.array([i for i,n in enumerate(c.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]);right=np.array([i for i,n in enumerate(c.names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]);body=c.body
    closure={**c.inputs,str(BASE):sha(BASE),str(PRIOR):sha(PRIOR),str(ASSET):sha(ASSET),str(Path(__file__)):sha(__file__)}
    lp,lr=original['LH:palm'];withdraw=lp+.08*np.array([0.,0,1.])-.03*forward;selected=[];audits=[]
    baseline_witness=gr.inv().apply(capsule_witness(original,normal)-gp);target_y=float(np.clip(baseline_witness[1],-.55,-.25));goal=gp+gr.apply([-.1505,target_y,-.010])
    for lean,absent in ((3,True),(9,False),(9,True),(12,True)):
        q=np.array(read(PRIOR)['joint_angles_rad']) if lean==3 else q0.copy();body_errors={}
        if lean!=3:
            targets={n:Rotation.from_rotvec(axis*np.deg2rad(lean*f))*original[n][1] for n,f in zip(('Torso','Spine','Chest'),(.25,.625,1.))}
            lo=np.maximum(c.lower[body],q0[body]-np.deg2rad(5));hi=np.minimum(c.upper[body],q0[body]+np.deg2rad(5))
            def body_res(v):
                trial=q.copy();trial[body]=v;poses=fk(trial)
                return np.r_[np.concatenate([100*(targets[n].inv()*poses[n][1]).as_rotvec() for n in targets]),.01*(v-q0[body])]
            fit=least_squares(body_res,np.clip(q[body],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=100);q[body]=fit.x
            body_errors={n:float(np.rad2deg((targets[n].inv()*fk(q)[n][1]).magnitude())) for n in targets}
            lo=np.maximum(c.lower[right],q0[right]-.3);hi=np.minimum(c.upper[right],q0[right]+.3);wrgoal=original['R_Wrist'][0]+.03*normal
            def right_res(v):
                trial=q.copy();trial[right]=v;poses=fk(trial)
                return np.r_[1000*(capsule_witness(poses,normal)-goal),10*(poses['R_Wrist'][0]-wrgoal),.1*(v-q0[right])]
            fit=least_squares(right_res,np.clip(q[right],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=150);q[right]=fit.x
        target=withdraw if absent else lp;lo=np.maximum(c.lower[left],q0[left]-.6);hi=np.minimum(c.upper[left],q0[left]+.6)
        def left_res(v):
            trial=q.copy();trial[left]=v;pp,rr=fk(trial)['LH:palm']
            return np.r_[1000*(pp-target),10*(lr.inv()*rr).as_rotvec(),.01*(v-q0[left])]
        fit=least_squares(left_res,np.clip(q[left],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=180);q[left]=fit.x;q=q.astype(np.float32).astype(float)
        poses=fk(q);pp,rr=poses['LH:palm'];lhpos=float(np.linalg.norm(pp-target));lhrot=float(np.rad2deg((lr.inv()*rr).magnitude()));witness=capsule_witness(poses,normal);gap=float(normal@(witness-(gp+gr.apply([-.15,-.4,-.0217]))));fitgap=float(np.linalg.norm(witness-goal));audit=source_audit(state_from_fk(state0,bodies,q,fk),bodies,parents)
        label=f'rounded{lean}_'+('left_away' if absent else 'left_support');row={'label':label,'requested_lean_deg':lean,'left_absent_initial_goal':absent,'left_palm_target_W_m':target.tolist(),'left_palm_position_error_m':lhpos,'left_palm_orientation_error_deg':lhrot,'body_orientation_errors_deg':body_errors,'support_top_plane_signed_gap_m':gap,'support_fit_error_m':fitgap,'source_audit':audit,'segment_world_delta_deg':{n:float(np.rad2deg(np.dot((poses[n][1]*original[n][1].inv()).as_rotvec(),axis))) for n in ('Torso','Spine','Chest')},'max_body_scalar_delta_deg':float(np.rad2deg(abs(q[body]-q0[body])).max()),'max_left_arm_scalar_delta_rad':float(abs(q[left]-q0[left]).max()),'max_right_arm_scalar_delta_rad':float(abs(q[right]-q0[right]).max())}
        valid=audit['source_clear'] and lhpos<.002 and lhrot<1 and all(v<.05 for v in body_errors.values()) and np.all(q>=c.lower) and np.all(q<=c.upper) and gap>=0 and (lean==3 or fitgap<.002)
        row['accepted_for_native']=bool(valid);audits.append(row);save(a.out/(label+'_audit.json'),row)
        if valid:
            folder=a.out/label;folder.mkdir();candidate={'joint_names':c.names,'joint_angles_rad':q.tolist(),'position_W_m':c.candidate['position_W_m'],'quaternion_xyzw':c.candidate['quaternion_xyzw'],'predicted_human_poses':{n:{'p':bp.tolist(),'q':br.as_quat().tolist()} for n,(bp,br) in poses.items()},'rounded_spine_proposal':row};save(folder/'candidate.json',candidate)
            cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'),prep_seconds=2,diagnostic_seconds=5,reset_randomization=False);save(folder/'config.json',cfg);selected.append({'label':label,'config_path':str(folder/'config.json'),'requested_lean_deg':lean,'left_absent_initial_goal':absent,'source_row':row})
        print(label,'accepted',valid,'source_clear',audit['source_clear'],'left_error_mm',lhpos*1000,'support_error_mm',fitgap*1000,flush=True)
    save(a.out/'selected.json',{'input_sha256':closure,'selected':selected,'audits':audits,'native_initializations':0,'scope':'source FK; initial left-away test, not runtime release or native clearance certification'})
    if any(sha(p)!=h for p,h in closure.items()):raise AssertionError('search inputs changed')

if __name__=='__main__':main()
