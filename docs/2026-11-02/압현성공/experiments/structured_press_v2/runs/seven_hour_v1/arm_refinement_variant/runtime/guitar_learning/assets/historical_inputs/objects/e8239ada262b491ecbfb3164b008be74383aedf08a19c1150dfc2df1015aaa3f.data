"""Find source-clear starts for the private realistic-proportion guitar."""
import argparse
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import calibrated_upper_fk,state_from_fk,capsule_witness,ROOT
from .realistic_guitar_geometry_v1 import source_scene,source_audit,half_width
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/native_v2/rounded9_left_support/initial_values.json'
MANIFEST=ROOT/'stability_adapter_2/assets/realistic_guitar_v1/manifest.json'
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    from .environment_contract_v1 import EnvironmentContract,CONFIG
    from .underneck_initial_search import source_scene as transformed_scene
    c=EnvironmentContract();base=read(BASE);state0=base['native_initial_state'];names=base['joint_names'];bodies=base['human_body_names'];q0=np.array(base['q_ref_rad']);fk,parents=calibrated_upper_fk(names,bodies,state0,q0);poses0=fk(q0);gp0,gr=pose(state0['guitar_body_states'][0]);normal=gr.apply([-1.,0,0]);front=poses0['Pelvis'][1].apply([0,-1.,0]);front[2]=0;front/=np.linalg.norm(front);manifest=read(MANIFEST)
    arm={s:np.array([i for i,n in enumerate(names) if n.startswith(tuple(s+'_'+k for k in ('Thorax','Shoulder','Elbow','Wrist')))]) for s in ('L','R')};wG=gr.inv().apply(capsule_witness(poses0,normal)-gp0);target_y=float(np.clip(wG[1],-.55,-.25));upper=half_width(manifest,target_y);inputs={**c.inputs,str(BASE):sha(BASE),str(MANIFEST):sha(MANIFEST),str(Path(__file__)):sha(__file__),manifest['asset']:sha(manifest['asset'])}
    for e in manifest['meshes']:inputs[e['path']]=e['sha256']
    rows=[];selected=[]
    for dy,dz in ((.035,.04),(.055,.04),(.035,.06),(.055,.06),(.075,.06),(.035,.08),(.055,.08),(.075,.08)):
        delta=dy*front+dz*np.array([0.,0,1.]);gp=gp0+delta;q=q0.copy();goals={};errors={}
        for side in ('L','R'):
            idx=arm[side];lo=np.maximum(c.lower[idx],q0[idx]-.6);hi=np.minimum(c.upper[idx],q0[idx]+.6)
            if side=='L':tp,tr=poses0['LH:palm'];tp=tp+delta;goals['LH:palm']=tp.tolist()
            else:tp=gp+gr.apply([-upper-.0005,target_y,-.01]);goals['R_Shoulder_witness']=tp.tolist()
            def residual(v):
                trial=q.copy();trial[idx]=v;poses=fk(trial)
                if side=='L':pp,rr=poses['LH:palm'];return np.r_[1000*(pp-tp),10*(tr.inv()*rr).as_rotvec(),.01*(v-q0[idx])]
                return np.r_[1000*(capsule_witness(poses,normal)-tp),10*(poses['R_Wrist'][0]-(poses0['R_Wrist'][0]+delta)),.1*(v-q0[idx])]
            fit=least_squares(residual,np.clip(q[idx],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=150);q[idx]=fit.x;poses=fk(q)
            errors[side]={'position_error_m':float(np.linalg.norm((poses['LH:palm'][0] if side=='L' else capsule_witness(poses,normal))-tp)),'orientation_error_deg':float(np.rad2deg((tr.inv()*poses['LH:palm'][1]).magnitude())) if side=='L' else None}
        q=q.astype(np.float32).astype(float);state=state_from_fk(state0,bodies,q,fk);_,state=transformed_scene(state,{'human_body_names':bodies},gp,gr);scene=source_scene(state,bodies,manifest['asset']);audit=source_audit(scene,parents);poses=fk(q);strapcfg=read(ROOT/'stability_adapter_2/config.json')['strap'];buttons=manifest['strap_buttons_G_m'];route=[gp+gr.apply(buttons[0])]+[poses[n][0]+poses[n][1].apply(v) for n,v in strapcfg['guides']]+[gp+gr.apply(buttons[1])];length=float(np.linalg.norm(np.diff(route,axis=0),axis=1).sum());slack=1.1018469719600776-length
        label=f'front{int(dy*1000)}_up{int(dz*1000)}';row={'label':label,'guitar_delta_W_m':delta.tolist(),'arm_fit_errors':errors,'source_audit':audit,'initial_strap_route_length_m':length,'initial_strap_slack_m':slack,'max_arm_delta_rad':float(max(abs(q[arm[s]]-q0[arm[s]]).max() for s in ('L','R')))};valid=audit['source_clear'] and max(e['position_error_m'] for e in errors.values())<.002 and errors['L']['orientation_error_deg']<1 and slack>=0;row['accepted_for_native']=bool(valid);rows.append(row);save(a.out/(label+'_audit.json'),row);print(label,valid,'source_clear',audit['source_clear'],'slack_mm',slack*1000,flush=True)
        if valid:
            folder=a.out/label;folder.mkdir();poses=fk(q);candidate={'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':bp.tolist(),'q':br.as_quat().tolist()} for n,(bp,br) in poses.items()},'realistic_guitar_initial_proposal':row};save(folder/'candidate.json',candidate);cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'),prep_seconds=2,diagnostic_seconds=5,reset_randomization=False);save(folder/'config.json',cfg);selected.append({'label':label,'config_path':str(folder/'config.json'),'source_row':row})
            break
    save(a.out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'geometry_manifest':str(MANIFEST),'native_initializations':0,'scope':'first source-clear small-shift placement; no dynamic success certification'})
    assert all(sha(p)==h for p,h in inputs.items()),'input changed'
if __name__=='__main__':main()
