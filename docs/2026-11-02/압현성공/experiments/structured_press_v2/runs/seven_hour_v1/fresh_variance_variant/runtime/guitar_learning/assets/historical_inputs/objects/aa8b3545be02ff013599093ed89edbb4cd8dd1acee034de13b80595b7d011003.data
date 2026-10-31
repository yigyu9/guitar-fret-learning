"""Upright trunk with a proximal right-arm cradle and a clear chest."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares, brentq
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read, save, sha, pose
from .upper_arm_static_geometry_v1 import ROOT, ASSET, calibrated_upper_fk, state_from_fk
from .realistic_guitar_geometry_v1 import source_scene, source_audit
from .underneck_initial_search import source_scene as move_guitar
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .environment_contract_v1 import EnvironmentContract
from .left_arm_clearance_source_v2 import clearance_function

A = ROOT/'stability_adapter_2'
B = ROOT/'docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1'
P = B.parent/'right_arm_wrap_upright_v1'
CFG = B/'search_v1/relief8_arm0mm/config.json'
BASE = B/'native_add8_static/initial_values.json'


def main():
    out=P/'search_v7';out.mkdir(exist_ok=False)
    anchors=[Path(__file__).resolve(),A/'RIGHT_ARM_WRAP_UPRIGHT_PLAN_V7.md',CFG,BASE,ASSET,
             A/'config.json',A/'assets/om_body_geometry_v3/manifest.json']
    discovery={str(p):sha(p) for p in anchors};save(out/'discovery_before.json',discovery)
    cfg=read(CFG);shared=read(A/'config.json');geometry=read(A/'assets/om_body_geometry_v3/manifest.json')
    guitar_asset=Path(geometry['asset'])
    guitar_discovery={str(guitar_asset):sha(guitar_asset)};save(out/'guitar_xml_discovery_before.json',guitar_discovery)
    human_xml=ET.parse(ASSET).getroot();meshdir=(ASSET.parent/human_xml.find('compiler').get('meshdir')).resolve()
    guitar_xml=ET.parse(guitar_asset).getroot();guitar_meshdir=(guitar_asset.parent/guitar_xml.find('compiler').get('meshdir')).resolve()
    paths=anchors+[guitar_asset,ROOT/shared['guitar_asset'],Path(cfg['initial_candidate']),Path(cfg['native_reference'])]
    paths += [(meshdir/m.get('file')).resolve() for m in human_xml.findall('./asset/mesh')]
    paths += [(guitar_meshdir/m.get('file')).resolve() for m in guitar_xml.findall('./asset/mesh')]
    paths += list(A.glob('*.py'))+[Path(m['path']) for m in geometry['meshes']]
    assert all(sha(p)==h for p,h in {**discovery,**guitar_discovery}.items())
    inputs={str(p):sha(p) for p in paths};save(out/'inputs_before.json',inputs)
    contract=EnvironmentContract(CFG);assert all(inputs[p]==h for p,h in contract.inputs.items())
    seed=contract.candidate;base=read(BASE);state=base['native_initial_state'];names,bodies=base['joint_names'],base['human_body_names']
    q0=contract.q_ref.copy();gp0,gr0=pose(state['guitar_body_states'][0])
    fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0)
    distance=CapsuleBodyDistance(guitar_asset,ASSET)
    profile=np.array(geometry['half_width_profile_t_m']);region=profile[(profile[:,0]>.25)&(profile[:,0]<.5)]
    t,width=region[np.argmin(region[:,1])];waist_y=-.4+geometry['new_body_length_m']*(.5-t)
    core=region[region[:,1]<=width+.005];core_y=-.4+geometry['new_body_length_m']*(.5-core[:,0])
    narrow=region[region[:,1]<=width+.015];ys=-.4+geometry['new_body_length_m']*(.5-narrow[:,0]);waist_interval=[float(ys.min()),float(ys.max())]
    left_clearance=clearance_function(ASSET,distance,original)
    right_axis=original['R_Hip'][0]-original['L_Hip'][0];right_axis[2]=0;right_axis/=np.linalg.norm(right_axis)
    right=np.array([i for i,n in enumerate(names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
    left=np.array([i for i,n in enumerate(names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))])
    head=np.array([i for i,n in enumerate(names) if n.startswith(('Neck_','Head_'))])
    rows=[];selected=[]
    front_axis=np.array([-right_axis[1],right_axis[0],0.])
    vertices=np.vstack([v[0] for v in distance.pieces]);centre=(vertices.min(0)+vertices.max(0))/2
    centre_W=gp0+gr0.apply(centre)
    arm_inward=centre_W-original['R_Elbow'][0];arm_inward/=np.linalg.norm(arm_inward)
    def front_tilt(poses):
        up=poses['Chest'][1].apply([0,0,1]);return float(np.rad2deg(np.arctan2(up@front_axis,up[2])))
    for relief_deg,inset_m,axis_fraction in ((20.,.025,.40),(20.,.025,.55)):
        inward_m=0.;gr=gr0;delta=-front_axis*inset_m
        def hip_gap(down):
            return min(distance.measure(original,n,gp0+delta-[0,0,down],gr)['gap_m'] for n in ('R_Hip','L_Hip'))-.0003
        down=brentq(hip_gap,-.025,.12,xtol=1e-10)
        gp=(gp0+delta-[0,0,down]).astype(np.float32).astype(float);delta=gp-gp0
        q=q0.copy();body=contract.body
        targets={n:Rotation.from_rotvec(right_axis*np.deg2rad(relief_deg)*f)*original[n][1]
                 for n,f in zip(('Torso','Spine','Chest'),(.65,.85,1.))}
        blo=np.maximum(contract.lower[body]+1e-6,q0[body]-.25)
        bhi=np.minimum(contract.upper[body]-1e-6,q0[body]+.25)
        def body_res(v):
            z=q0.copy();z[body]=v;ps=fk(z)
            return np.r_[np.concatenate([300*(targets[n].inv()*ps[n][1]).as_rotvec() for n in targets]),.1*(v-q0[body])]
        body_fit=least_squares(body_res,np.clip(q0[body],blo+1e-8,bhi-1e-8),bounds=(blo,bhi),max_nfev=120)
        q[body]=body_fit.x
        initial_range=np.array([.9 if names[i].startswith(('R_Shoulder','R_Elbow')) else .6 for i in right])
        lo=np.maximum(contract.lower[right]+1e-6,q0[right]-initial_range)
        hi=np.minimum(contract.upper[right]-1e-6,q0[right]+initial_range)
        ej=list(right).index(names.index('R_Elbow_y'))
        lo[ej]=max(lo[ej],contract.lower[right[ej]]+np.deg2rad(5)+1e-6)
        hi[ej]=min(hi[ej],contract.upper[right[ej]]-np.deg2rad(5)-1e-6)
        elbow_goal=original['R_Elbow'][0]+delta
        segment,radius=distance.capsules['R_Shoulder']
        axis_local=segment[0]+axis_fraction*(segment[1]-segment[0])
        target_y=-.52;target_t=.5-(target_y+.4)/geometry['new_body_length_m']
        target_width=float(np.interp(target_t,profile[:,0],profile[:,1]))
        axis_goal_G=np.array([-target_width-radius-.0008,target_y,.5*(vertices[:,2].min()+vertices[:,2].max())])
        axis_goal_W=gp+gr.apply(axis_goal_G)
        def residual(v):
            z=q.copy();z[right]=v;poses=fk(z)
            gaps={n:distance.measure(poses,n,gp,gr)['gap_m'] for n in ('R_Thorax','R_Shoulder','R_Elbow')}
            upper=distance.measure(poses,'R_Shoulder',gp,gr,1.)['gap_m']
            el=poses['R_Elbow'][0]-poses['R_Shoulder'][0];wr=poses['R_Elbow'][0]-poses['R_Wrist'][0]
            return np.r_[4000*(poses['R_Shoulder'][0]+poses['R_Shoulder'][1].apply(axis_local)-axis_goal_W),6000*(upper-.0008),
                20000*min(gaps['R_Thorax']-.0001,0),100000*min(gaps['R_Shoulder']-.0001,0),
                6000*min(gaps['R_Elbow']-.014,0),10000*max(.02+el[2],0),
                1000*max(.105-el@right_axis,0),1000*max(.025-wr@right_axis,0),
                400*(poses['R_Elbow'][0]-elbow_goal),
                50*(poses['RH:palm'][0]-gp-gr.apply(gr0.inv().apply(original['RH:palm'][0]-gp0))),
                8*(original['RH:palm'][1].inv()*poses['RH:palm'][1]).as_rotvec(),2*(v-q0[right])]
        fit=least_squares(residual,np.clip(q0[right],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=120,diff_step=1e-4,ftol=1e-9,xtol=1e-9,gtol=1e-8)
        q[right]=fit.x
        def left_res(v):
            z=q.copy();z[left]=v;ps=fk(z);p,r=ps['L_Wrist'];return np.r_[1000*(p-gp-gr.apply(gr0.inv().apply(original['L_Wrist'][0]-gp0))),80*((gr*gr0.inv()*original['L_Wrist'][1]).inv()*r).as_rotvec(),10000*np.minimum(left_clearance(ps)-.003,0),.1*(v-q0[left])]
        llo=np.maximum(contract.lower[left]+1e-6,q0[left]-.6);lhi=np.minimum(contract.upper[left]-1e-6,q0[left]+.6)
        q[left]=least_squares(left_res,np.clip(q0[left],llo+1e-8,lhi-1e-8),bounds=(llo,lhi),max_nfev=120).x
        def head_res(v):
            z=q.copy();z[head]=v;return np.r_[100*(original['Head'][1].inv()*fk(z)['Head'][1]).as_rotvec(),.1*(v-q0[head])]
        hlo=np.maximum(contract.lower[head]+1e-6,q0[head]-.5);hhi=np.minimum(contract.upper[head]-1e-6,q0[head]+.5)
        q[head]=least_squares(head_res,np.clip(q0[head],hlo+1e-8,hhi-1e-8),bounds=(hlo,hhi),max_nfev=120).x
        q=q.astype(np.float32).astype(float);poses=fk(q);caps={n:distance.measure(poses,n,gp,gr) for n in ('R_Thorax','R_Shoulder','R_Elbow','R_Hip','L_Hip','Chest','Torso','Spine')}
        proximal=distance.measure(poses,'R_Shoulder',gp,gr,1.)
        _,predicted=move_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr)
        audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents)
        el=poses['R_Elbow'][0]-poses['R_Shoulder'][0];wr=poses['R_Elbow'][0]-poses['R_Wrist'][0]
        lerror=float(np.linalg.norm(poses['L_Wrist'][0]-gp-gr.apply(gr0.inv().apply(original['L_Wrist'][0]-gp0))));lr=float(np.rad2deg(((gr*gr0.inv()*original['L_Wrist'][1]).inv()*poses['L_Wrist'][1]).magnitude()));he=float(np.rad2deg((original['Head'][1].inv()*poses['Head'][1]).magnitude()))
        frozen=np.ones(81,dtype=bool);frozen[np.r_[body,right,left,head]]=False
        body_error=max(float(np.rad2deg((targets[n].inv()*poses[n][1]).magnitude())) for n in targets)
        tilt_reduction=front_tilt(original)-front_tilt(poses)
        elbow_inward=float((poses['R_Elbow'][0]-original['R_Elbow'][0])@arm_inward)
        elbow_distance_before=float(np.linalg.norm(centre_W-original['R_Elbow'][0]))
        elbow_distance_after=float(np.linalg.norm(gp+gr.apply(centre)-poses['R_Elbow'][0]))
        elbow_distance_reduction=elbow_distance_before-elbow_distance_after
        natural={'elbow_below_m':float(-el[2]),'elbow_outward_m':float(el@right_axis),'wrist_inward_m':float(wr@right_axis),'head_error_deg':he,'left_wrist_rotation_error_deg':lr}
        waist_ok=bool(waist_interval[0] <= caps['R_Hip']['guitar_surface_G_m'][1] <= waist_interval[1] and caps['R_Hip']['guitar_surface_G_m'][0]>0 and .00005<caps['R_Hip']['gap_m']<.004)
        contact_vector=np.array(proximal['capsule_axis_G_m'])-np.array(proximal['guitar_surface_G_m'])
        normal_length=float(np.linalg.norm(contact_vector));normal_valid=normal_length>1e-9
        contact_normal=contact_vector/normal_length if normal_valid else None
        axis_goal_error=float(np.linalg.norm(poses['R_Shoulder'][0]+poses['R_Shoulder'][1].apply(axis_local)-axis_goal_W))
        eligible=bool(normal_valid and .20<=proximal['segment_fraction']<=1. and -contact_normal[0]>=.7 and caps['Torso']['gap_m']>=.020 and caps['Spine']['gap_m']>=.020 and caps['Chest']['gap_m']>=.030 and proximal['guitar_surface_G_m'][0]<-.05 and body_error<.4 and tilt_reduction>.5*relief_deg and waist_ok and audit['source_clear'] and all(c['gap_m']>=.00005 for c in caps.values()) and .00005<proximal['gap_m']<.004 and caps['R_Elbow']['gap_m']>.012 and lerror<.005 and lr<1 and he<1 and -el[2]>.019 and el@right_axis>.105 and wr@right_axis>.025 and np.array_equal(q[frozen],q0[frozen]) and np.all(q>=contract.lower) and np.all(q<=contract.upper))
        row={'label':'relief%d_fraction%d'%(round(relief_deg),round(axis_fraction*100)),'right_initial_range_rad':initial_range.tolist(),'requested_upper_axis_fraction':axis_fraction,'upper_axis_goal_G_m':axis_goal_G.tolist(),'upper_axis_goal_error_m':axis_goal_error,'upper_axis_goal_is_soft_guide_only':True,'contact_normal_G':contact_normal.tolist() if normal_valid else None,'contact_normal_valid':normal_valid,'requested_chest_relief_deg':relief_deg,'requested_elbow_inward_m':inward_m,'actual_elbow_inward_m':elbow_inward,'elbow_bbox_distance_before_m':elbow_distance_before,'elbow_bbox_distance_after_m':elbow_distance_after,'elbow_bbox_distance_reduction_m':elbow_distance_reduction,'elbow_goal_error_m':float(np.linalg.norm(poses['R_Elbow'][0]-elbow_goal)),'elbow_inward_axis_W':arm_inward.tolist(),'Chest_front_tilt_before_deg':front_tilt(original),'Chest_front_tilt_after_deg':front_tilt(poses),'Chest_front_tilt_reduction_deg':tilt_reduction,'body_orientation_goal_max_error_deg':body_error,'body_fit_nfev':int(body_fit.nfev),'human_forward_axis_W':front_axis.tolist(),'baseline_config':str(CFG),'toward_body_m':inset_m,'accepted_for_native':eligible,'waist_source_region_ok':waist_ok,'waist_G_y_m':float(waist_y),'waist_G_y_interval_m':waist_interval,'waist_core_G_y_interval_m':[float(core_y.min()),float(core_y.max())],'left_arm_clearance_m':left_clearance(poses).tolist(),'waist_region_rule':'profile half-width <= minimum +15mm; concave flanks, +5mm central core reported separately','waist_profile_t':float(t),'waist_half_width_m':float(width),'local_G_Y_rotation_deg':0.,'guitar_delta_W_m':delta.tolist(),'human_right_axis_W':right_axis.tolist(),'joint_angles_rad':q.tolist(),'capsule_body':caps,'full_upper_arm_witness':proximal,'proximal_upper_arm45_witness':proximal,'proximal_upper_arm30_witness':proximal,'proximal_upper_arm65_witness':proximal,'proximal_fraction_limit':1.,'legacy_key_note':'30/65 are compatibility keys; actual source fraction0..100%; accepted closest fraction>=20%; one rigid R_Shoulder body independent of elbow angles','source_audit':audit,'natural_geometry':natural,'left_wrist_rigid_transform_error_m':lerror,'fingers42_exact':bool(np.array_equal(q[frozen],q0[frozen])),'rotation_preserved':bool(np.array_equal(gr.as_quat(),gr0.as_quat())),'fit_nfev':int(fit.nfev)}
        rows.append(row);save(out/(row['label']+'_audit.json'),row);print(row['label'],'accepted',eligible,'Chest_relief_deg',tilt_reduction,'elbow_inward_mm',elbow_inward*1000,'gaps_mm',{n:c['gap_m']*1000 for n,c in caps.items()},'Hip_y',caps['R_Hip']['guitar_surface_G_m'][1],'clear',audit['source_clear'],flush=True)
        if eligible:
            folder=out/row['label'];folder.mkdir();candidate={**seed,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in poses.items()},'predicted_guitar_body_states':predicted['guitar_body_states'],'right_block_cradle':row,'body_side_lean_axilla':row,'right_thigh_waist':row,'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']}}
            save(folder/'candidate.json',candidate);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json'),'elbow_motion_amplitude_rad':0.0,'proximal_point_parameters':{'R_Thorax':{'cap_N':10.,'depth_m':.004},'R_Shoulder':{'cap_N':20.,'depth_m':.008}}});selected.append({'label':row['label'],'config':str(folder/'config.json')})
    assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'native_runs':0,'scope':'upright trunk, source clear trunk and full rigid upper-arm guitar wrap, closest point not shoulder pivot; Thorax virtual request reduced10N/4mm; source check only'})


if __name__=='__main__': main()
