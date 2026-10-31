"""Initial upper-body lean and right upper-arm support proposals; source-only."""
import argparse
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import calibrated_upper_fk,state_from_fk,source_audit,capsule_witness,ROOT,ASSET
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/bank_build_v1/proposal_00/native_audit.json'

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    from .environment_contract_v1 import EnvironmentContract,CONFIG
    from .underneck_initial_search import FACETS
    c=EnvironmentContract();initial=read(BASE);state0=initial['actual'];bodies=initial['human_body_names'];q0=c.q_ref.copy();fk,parents=calibrated_upper_fk(c.names,bodies,state0,q0);poses0=fk(q0);gp,gr=pose(state0['guitar_body_states'][0])
    normal=gr.apply([-1.,0,0]);forward=poses0['Pelvis'][1].apply([0,-1.,0]);forward[2]=0;forward/=np.linalg.norm(forward);axis=np.cross([0,0,1],forward);axis/=np.linalg.norm(axis)
    body=c.body;left=np.array([i for i,n in enumerate(c.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]);right=np.array([i for i,n in enumerate(c.names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]);normal_local=read(FACETS)['facets']['LH:palm']['normal_local']
    inputs={**c.inputs,str(BASE):sha(BASE),str(ASSET):sha(ASSET),str(FACETS):sha(FACETS),str(Path(__file__)):sha(__file__)}
    candidates=[];rows=[]
    def keep(label,q,details):
        q=q.astype(np.float32).astype(float);state=state_from_fk(state0,bodies,q,fk);audit=source_audit(state,bodies,parents);poses=fk(q);up=float(poses['LH:palm'][1].apply(normal_local)[2]);lp,lr=poses['LH:palm'];tp,tr=poses0['LH:palm'];lherr=float(np.linalg.norm(lp-tp));lhrot=float(np.rad2deg((tr.inv()*lr).magnitude()))
        witness=capsule_witness(poses,normal);wG=gr.inv().apply(witness-gp);gap=float(normal@(witness-(gp+gr.apply([-.15,-.4,-.0217]))))
        actual_lean=float(np.rad2deg(np.dot((poses['Chest'][1]*poses0['Chest'][1].inv()).as_rotvec(),axis)))
        row=dict(details,label=label,source_audit=audit,palm_up_proxy_z=up,left_palm_error_m=lherr,left_palm_error_deg=lhrot,support_witness_G_m=wG.tolist(),support_top_plane_signed_gap_m=gap,actual_predicted_Chest_delta_deg=actual_lean)
        valid=audit['source_clear'] and up>=0 and lherr<.002 and lhrot<1 and np.all(q>=c.lower) and np.all(q<=c.upper)
        if label!='reference':valid=valid and abs(actual_lean-details['requested_lean_deg'])<.05 and abs(row['fit_witness_error_m'])<.002 and gap>=-1e-7
        row['accepted_for_native']=bool(valid);rows.append(row)
        if valid:
            cand={'joint_names':c.names,'joint_angles_rad':q.tolist(),'position_W_m':c.candidate['position_W_m'],'quaternion_xyzw':c.candidate['quaternion_xyzw'],'predicted_human_poses':{n:{'p':bp.tolist(),'q':br.as_quat().tolist()} for n,(bp,br) in poses.items()},'static_support_proposal':row}
            folder=a.out/label;folder.mkdir();save(folder/'candidate.json',cand);cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'),prep_seconds=5,diagnostic_seconds=5,reset_randomization=False);save(folder/'config.json',cfg);candidates.append({'label':label,'config_path':str(folder/'config.json'),'row':row})
        save(a.out/('audit_'+label+'.json'),row)
    keep('reference',q0,{'requested_lean_deg':0.,'support_requested':False})
    baseline_witness=gr.inv().apply(capsule_witness(poses0,normal)-gp);target_y=float(np.clip(baseline_witness[1],-.55,-.25))
    for lean in (0.,3.,5.):
        qbody=q0.copy();target=Rotation.from_rotvec(axis*np.deg2rad(lean))*poses0['Chest'][1];lo=np.maximum(c.lower[body],q0[body]-np.deg2rad(5));hi=np.minimum(c.upper[body],q0[body]+np.deg2rad(5))
        def body_res(v):
            q=q0.copy();q[body]=v
            return np.r_[100*(target.inv()*fk(q)['Chest'][1]).as_rotvec(),.01*(v-q0[body])]
        fit=least_squares(body_res,np.clip(q0[body],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=80);qbody[body]=fit.x
        lo=np.maximum(c.lower[left],q0[left]-.3);hi=np.minimum(c.upper[left],q0[left]+.3);lp,lr=poses0['LH:palm']
        def left_res(v):
            q=qbody.copy();q[left]=v;pp,rr=fk(q)['LH:palm'];return np.r_[1000*(pp-lp),10*(lr.inv()*rr).as_rotvec(),.01*(v-q0[left])]
        fit=least_squares(left_res,np.clip(q0[left],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=100);qbody[left]=fit.x
        lo=np.maximum(c.lower[right],q0[right]-.3);hi=np.minimum(c.upper[right],q0[right]+.3)
        for gap in (.0005,.0015):
            for z in (-.035,-.010):
                goal=gp+gr.apply([-.15-gap,target_y,z]);wrgoal=poses0['R_Wrist'][0]+.03*normal
                def right_res(v):
                    q=qbody.copy();q[right]=v;poses=fk(q)
                    return np.r_[1000*(capsule_witness(poses,normal)-goal),10*(poses['R_Wrist'][0]-wrgoal),.1*(v-q0[right])]
                fit=least_squares(right_res,np.clip(q0[right],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=120);q=qbody.copy();q[right]=fit.x
                label='lean%d_gap%d_z%d'%(int(lean),int(gap*1e6),int(z*1e3));keep(label,q,{'requested_lean_deg':lean,'support_requested':True,'requested_source_gap_m':gap,'support_goal_W_m':goal.tolist(),'fit_success':bool(fit.success),'fit_witness_error_m':float(np.linalg.norm(capsule_witness(fk(q),normal)-goal))})
    # Pick closest valid fit at each lean without changing the candidate files.
    selected=[e for e in candidates if e['label']=='reference']
    for lean in (0.,3.,5.):
        valid=[e for e in candidates if e['row']['support_requested'] and e['row']['requested_lean_deg']==lean]
        if valid:selected.append(min(valid,key=lambda e:e['row']['fit_witness_error_m']))
    save(a.out/'search.json',{'inputs':inputs,'rows':rows,'selected':selected,'front_W_unit':forward.tolist(),'Chest_lean_axis_W_unit':axis.tolist(),'source_only':True,'native_initializations':0,'scope':'calibrated upper FK and source hull proposals; actual cooked contact/support not certified'})
    print({'accepted':len(candidates),'selected':[e['label'] for e in selected]},flush=True)
    if not selected or selected[0]['label']!='reference':raise RuntimeError('reference failed source audit')
if __name__=='__main__':main()
