"""Small anatomical-right guitar shift, fixed trunk/fingers, bilateral arm preparation."""
import copy
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares,brentq
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .environment_contract_v1 import EnvironmentContract
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .elbow_wrist_strike_source_v1 import solve_pick
from .left_neck_near_geometry_v1 import FACETS
from .left_neck_three_face_geometry_v1 import measurements,placement_pass

A=ROOT/'stability_adapter_2';D=ROOT/'docs/2026-10-19/stability_adapter_2';P=D/'results/right_shift_initial_v1'
B=D/'results/left_neck_three_face_v1';CFG=B/'search_v5/station20mm/config.json';BASE=B/'native_off_v1/initial_values.json'


def main():
    out=P/'search_v1';out.mkdir(parents=True,exist_ok=False)
    anchors=[Path(__file__).resolve(),A/'RIGHT_SHIFT_INITIAL_PLAN_V1.md',CFG,BASE,FACETS,A/'assets/om_body_geometry_v3/manifest.json',ASSET,A/'config.json']
    discovery={str(p):sha(p) for p in anchors};save(out/'discovery_before.json',discovery)
    cfg=read(CFG);geometry=read(anchors[-3]);asset=Path(geometry['asset'])
    paths=anchors+[asset,Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+list(A.glob('*.py'))+[Path(x) for x in geometry['input_sha256']]+[Path(x['path']) for x in geometry['meshes']]
    for xmlpath in (ASSET,asset):
        xml=ET.parse(xmlpath).getroot();meshdir=(xmlpath.parent/xml.find('compiler').get('meshdir')).resolve();paths.extend((meshdir/m.get('file')).resolve() for m in xml.findall('./asset/mesh'))
    inputs={str(p.resolve()):sha(p) for p in paths};assert all(inputs[p]==h for p,h in discovery.items());save(out/'inputs_before.json',inputs)
    contract=EnvironmentContract(CFG);assert all(inputs[p]==h for p,h in contract.inputs.items())
    seed=read(cfg['initial_candidate']);base=read(BASE);state=base['native_initial_state'];names,bodies=base['joint_names'],base['human_body_names'];q0=np.array(base['q_ref_rad'])
    assert np.array_equal(q0,seed['joint_angles_rad'])
    fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0);gp0,gr=pose(state['guitar_body_states'][0]);distance=CapsuleBodyDistance(asset,ASSET)
    axis=original['R_Hip'][0]-original['L_Hip'][0];axis[2]=0;axis/=np.linalg.norm(axis)
    left=np.array([i for i,n in enumerate(names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]);right=np.array([i for i,n in enumerate(names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]);distal=right[6:]
    frozen=np.ones(81,dtype=bool);frozen[np.r_[left,right]]=False;facets=read(FACETS)['facets'];row=seed['right_block_cradle'];station=seed['left_neck_near']['station_G_m'];front=seed['left_neck_near']['front_z_G_m']
    witness={n:row['capsule_body'][n] if n=='R_Thorax' else row['proximal_upper_arm30_witness'] for n in ('R_Thorax','R_Shoulder')}
    local={}
    for n,w in witness.items():
        ep,_=distance.capsules[n];local[n]=ep[0]+w['segment_fraction']*(ep[1]-ep[0])
    rows=[];selected=[];points=np.array(cfg['six_joint_strike_waypoints_G_m'])
    for shift in (.010,.020):
        delta=axis*shift
        def hip_gap(up):return min(distance.measure(original,n,gp0+delta+[0,0,up],gr)['gap_m'] for n in ('R_Hip','L_Hip'))-.0003
        if hip_gap(0)<0:
            if hip_gap(.005)<0:
                rows.append({'shift_m':shift,'accepted_for_native':False,'reason':'hip source clearance requires more than5mm upward correction'});continue
            delta[2]=brentq(hip_gap,0,.005,xtol=1e-10)
        gp=(gp0+delta).astype(np.float32).astype(float);delta=gp-gp0;q=q0.copy()
        for indices,side in ((left,'L'),(right,'R')):
            half=np.full(12,.3)
            if side=='R':half[:6]=.2
            lo=np.maximum(contract.lower[indices]+1e-6,q0[indices]-half);hi=np.minimum(contract.upper[indices]-1e-6,q0[indices]+half)
            def residual(v):
                trial=q.copy();trial[indices]=v;ps=fk(trial)
                if side=='L':
                    p,r=ps['L_Wrist'];goal,rotation=original['L_Wrist'];terms=np.r_[1200*(p-goal-delta),80*(rotation.inv()*r).as_rotvec()]
                else:
                    terms=[]
                    for n in ('R_Thorax','R_Shoulder'):
                        p,r=ps[n];oldp,oldr=original[n];terms.extend(450*(p+r.apply(local[n])-oldp-oldr.apply(local[n])-delta))
                    terms.extend(1200*(ps['RH:pick'][0]-original['RH:pick'][0]-delta))
                    terms.extend(8*(original['R_Wrist'][1].inv()*ps['R_Wrist'][1]).as_rotvec())
                return np.r_[terms,.03*(v-q0[indices]),120*np.maximum(np.linalg.norm(v.reshape(4,3),axis=1)-np.deg2rad(155),0)]
            fit=least_squares(residual,np.clip(q[indices],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=90,diff_step=1e-4);q[indices]=fit.x
        q=q.astype(np.float32).astype(float);ps=fk(q)
        caps={n:distance.measure(ps,n,gp,gr) for n in ('R_Thorax','R_Shoulder','R_Elbow','R_Hip','L_Hip','Torso','Spine','Chest')}
        faces=measurements(ps,gp,gr,station,front,facets)
        predicted=state_from_fk(state,bodies,q,fk)
        for s in predicted['guitar_body_states']:
            for k,v in zip('xyz',delta):s['pose']['p'][k]+=float(v)
        audit=source_audit(source_scene(predicted,bodies,asset),parents)
        samples=[];previous=q[distal].copy()
        for target in np.vstack([points,(points[1]+points[2])/2]):
            trial,error,_=solve_pick(fk,q,distal,contract.lower,contract.upper,q,gp+gr.apply(target),previous);previous=trial[distal];pathposes=fk(trial)
            samples.append({'target_G_m':target.tolist(),'q6_rad':trial[distal].tolist(),'position_error_m':error,'forearm_body_gap_m':distance.measure(pathposes,'R_Elbow',gp,gr)['gap_m'],'ball_norm_deg':np.rad2deg(np.linalg.norm(trial[distal].reshape(2,3),axis=1)).tolist()})
        pickerror=float(np.linalg.norm(ps['RH:pick'][0]-original['RH:pick'][0]-delta))
        accepted=bool(audit['source_clear'] and placement_pass(faces) and np.array_equal(q[frozen],q0[frozen]) and pickerror<.002 and
            all(np.linalg.norm(q[[names.index(prefix+'_'+a) for a in 'xyz']])<np.deg2rad(160) for prefix in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist')) and
            .00005<caps['R_Thorax']['gap_m']<.012 and .00005<caps['R_Shoulder']['gap_m']<.006 and
            all(s['position_error_m']<.002 and s['forearm_body_gap_m']>.00005 and max(s['ball_norm_deg'])<160 for s in samples))
        label='right%02dmm'%round(shift*1000);r={'label':label,'accepted_for_native':accepted,'source_audit':audit,'capsule_body':caps,'proximal_upper_arm30_witness':caps['R_Shoulder'],'proximal_upper_arm45_witness':caps['R_Shoulder'],'proximal_upper_arm65_witness':caps['R_Shoulder'],'full_upper_arm_witness':caps['R_Shoulder'],'legacy_key_note':'full upper-arm capsule, compatibility key; not fraction0..30%','guitar_delta_W_m':delta.tolist(),'human_right_axis_W':axis.tolist(),'joint_angles_rad':q.tolist(),'frozen57_exact':bool(np.array_equal(q[frozen],q0[frozen])),'face_measurements':faces,'station_G_m':station,'front_z_G_m':front,'initial_pick_translation_error_m':pickerror,'samples':samples}
        rows.append(r);save(out/(label+'_audit.json'),r);print(label,'accepted',accepted,'clear',audit['source_clear'],'faces',placement_pass(faces),'pickmm',pickerror*1000,'shiftmm',delta*1000,'gapsmm',{n:round(c['gap_m']*1000,3) for n,c in caps.items()},flush=True)
        if accepted:
            folder=out/label;folder.mkdir();candidate={**seed,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':rot.as_quat().tolist()} for n,(p,rot) in ps.items()},'predicted_guitar_body_states':predicted['guitar_body_states'],'right_block_cradle':r,'body_side_lean_axilla':r,'right_shift_initial':r,'left_neck_near':{**seed['left_neck_near'],'accepted_for_native':True,'face_measurements':faces,'source_audit':audit},'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']}}
            save(folder/'candidate.json',candidate);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json')});selected.append({'label':label,'config':str(folder/'config.json')})
    assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'native_runs':0,'scope':'small anatomical-right initial shift with finite-human preparation proposal, whole source LP; source EW6 waypoint IK checks are not continuous native clearance/playing success'})


if __name__=='__main__':main()
