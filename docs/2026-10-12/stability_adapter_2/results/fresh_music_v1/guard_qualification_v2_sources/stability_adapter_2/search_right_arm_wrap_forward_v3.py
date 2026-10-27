"""Move Elbow3 slightly towards the guitar front, preserving the upright wrap pose."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .underneck_initial_search import source_scene as move_guitar
from .environment_contract_v1 import EnvironmentContract

A=ROOT/'stability_adapter_2';D=ROOT/'docs/2026-10-19/stability_adapter_2'
B=D/'results/right_arm_wrap_upright_v1';P=D/'results/right_arm_wrap_forward_v1'
CFG=B/'search_v7/relief20_fraction55/config.json';BASE=B/'native_wrap55_static/initial_values.json'
PLAN=A/'RIGHT_ARM_WRAP_FORWARD_PLAN_V3.md'

def main():
    out=P/'search_v3';out.mkdir(exist_ok=False)
    anchors=[Path(__file__).resolve(),PLAN,CFG,BASE,ASSET,A/'config.json',A/'assets/om_body_geometry_v3/manifest.json']
    discovery={str(p):sha(p) for p in anchors};save(out/'discovery_before.json',discovery)
    cfg=read(CFG);geometry=read(anchors[-1]);guitar_asset=Path(geometry['asset'])
    guitar_discovery={str(guitar_asset):sha(guitar_asset)};save(out/'guitar_xml_discovery_before.json',guitar_discovery)
    paths=anchors+[guitar_asset,Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+list(A.glob('*.py'))
    paths += [Path(p) for p in geometry['input_sha256']]+[Path(m['path']) for m in geometry['meshes']]
    for asset in (ASSET,guitar_asset):
        xml=ET.parse(asset).getroot();meshdir=(asset.parent/xml.find('compiler').get('meshdir')).resolve()
        paths += [(meshdir/m.get('file')).resolve() for m in xml.findall('./asset/mesh')]
    assert all(sha(p)==h for p,h in {**discovery,**guitar_discovery}.items())
    inputs={str(p):sha(p) for p in paths};save(out/'inputs_before.json',inputs)
    contract=EnvironmentContract(CFG);assert all(inputs[p]==h for p,h in contract.inputs.items())
    seed=contract.candidate;base=read(BASE);state=base['native_initial_state'];names=base['joint_names'];bodies=base['human_body_names']
    q0=contract.q_ref.copy();assert np.array_equal(q0,base['q_ref_rad'])
    fk,parents=calibrated_upper_fk(names,bodies,state,q0);start=fk(q0)
    gp=np.array(seed['position_W_m']);gr=Rotation.from_quat(seed['quaternion_xyzw'])
    forward=gr.apply([0,0,1]);forward[2]=0;forward/=np.linalg.norm(forward)
    right=start['R_Hip'][0]-start['L_Hip'][0];right[2]=0;right/=np.linalg.norm(right)
    distance=CapsuleBodyDistance(guitar_asset,ASSET)
    indices=np.array([i for i,n in enumerate(names) if n.startswith('R_Elbow_')]);assert len(indices)==3
    frozen=np.ones(81,dtype=bool);frozen[indices]=False
    lo=np.maximum(contract.lower[indices]+1e-6,q0[indices]-.12);hi=np.minimum(contract.upper[indices]-1e-6,q0[indices]+.12)
    elbow_y=list(indices).index(names.index('R_Elbow_y'))
    lo[elbow_y]=max(lo[elbow_y],contract.lower[indices[elbow_y]]+np.deg2rad(5)+1e-6)
    hi[elbow_y]=min(hi[elbow_y],contract.upper[indices[elbow_y]]-np.deg2rad(5)-1e-6)
    rows=[];selected=[]
    for mm in (5,10,15):
        def residual(v):
            q=q0.copy();q[indices]=v;ps=fk(q);delta=ps['R_Elbow'][0]-start['R_Elbow'][0];palm_delta=ps['RH:palm'][0]-start['RH:palm'][0]
            upper=distance.measure(ps,'R_Shoulder',gp,gr)['gap_m'];arm=distance.measure(ps,'R_Elbow',gp,gr)['gap_m']
            return np.r_[1000*(palm_delta@forward-mm/1000),200*(palm_delta-forward*(palm_delta@forward)),
                100000*min(upper-.00015,0),1000*max(upper-.0028,0),10000*min(arm-.012,0),.2*(v-q0[indices])]
        fit=least_squares(residual,np.clip(q0[indices],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=100,diff_step=1e-4)
        q=q0.copy();q[indices]=fit.x;q=q.astype(np.float32).astype(float);ps=fk(q)
        caps={n:distance.measure(ps,n,gp,gr) for n in distance.capsules if n in ps};upper=caps['R_Shoulder']
        _,predicted=move_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr)
        audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents)
        delta=ps['R_Elbow'][0]-start['R_Elbow'][0];palm=ps['RH:palm'][0]-start['RH:palm'][0]
        error=float(abs(delta@forward-mm/1000));orthogonal=float(np.linalg.norm(delta-forward*(delta@forward)))
        vector=np.array(upper['capsule_axis_G_m'])-np.array(upper['guitar_surface_G_m']);length=float(np.linalg.norm(vector));valid=length>1e-9
        normal=vector/length if valid else None
        palm_error=float(abs(palm@forward-mm/1000));palm_orthogonal=float(np.linalg.norm(palm-forward*(palm@forward)))
        el=ps['R_Elbow'][0]-ps['R_Shoulder'][0];wr=ps['R_Elbow'][0]-ps['R_Wrist'][0]
        accepted=bool(valid and audit['source_clear'] and min(v['gap_m'] for v in caps.values())>=.00005
            and .00005<=upper['gap_m']<.004 and upper['segment_fraction']>=.2 and -normal[0]>=.7
            and caps['R_Elbow']['gap_m']>=.012 and caps['Chest']['gap_m']>=.030 and min(caps[n]['gap_m'] for n in ('Torso','Spine'))>=.020
            and -el[2]>.019 and el@right>.105 and wr@right>.025 and np.linalg.norm(delta)<1e-8 and palm_error<=.002 and palm_orthogonal<=.012 and palm@forward>0
            and np.array_equal(q[frozen],q0[frozen]) and np.all(q>=contract.lower) and np.all(q<=contract.upper))
        static={k:seed['right_thigh_waist'][k] for k in ('waist_G_y_interval_m','waist_core_G_y_interval_m','waist_profile_t','waist_half_width_m','waist_region_rule','guitar_delta_W_m')}
        row={**static,'label':'forward%dmm'%mm,'accepted_for_native':accepted,'joint_angles_rad':q.tolist(),
             'fresh_capsule_body':caps,'capsule_body':{**caps,'R_Thorax':seed['right_thigh_waist']['capsule_body']['R_Thorax']},
             'full_upper_arm_witness':upper,'proximal_upper_arm30_witness':seed['right_thigh_waist']['proximal_upper_arm30_witness'],
             'proximal_upper_arm45_witness':seed['right_thigh_waist']['proximal_upper_arm45_witness'],'proximal_upper_arm65_witness':seed['right_thigh_waist']['proximal_upper_arm65_witness'],
             'controller_witness_reused_for_fixed_bodies':['R_Thorax','R_Shoulder'], 'controller_witness_source':str(Path(cfg['initial_candidate'])),
             'proximal_fraction_limit':1.,'legacy_key_note':'30/45/65 compatibility aliases; actual full R_Shoulder capsule',
             'source_audit':audit,'contact_normal_G':normal.tolist() if valid else None,'contact_normal_valid':valid,
             'arm_forward':{'requested_elbow_forward_mm':mm,'forward_unit_W':forward.tolist(),
                 'forward_definition':'guitar front +G_Z normal projected horizontally',
                 'elbow_delta_W_mm':(1000*delta).tolist(),'elbow_forward_mm':float(1000*delta@forward),'elbow_forward_error_mm':1000*error,
                 'elbow_orthogonal_displacement_mm':1000*orthogonal,'palm_delta_W_mm':(1000*palm).tolist(),'palm_forward_mm':float(1000*palm@forward),'palm_forward_error_mm':1000*palm_error,'palm_orthogonal_displacement_mm':1000*palm_orthogonal,
                 'elbow3_bounds_rad':{'lower':lo.tolist(),'upper':hi.tolist()},'elbow3_scalar_delta_rad':{names[i]:float(q[i]-q0[i]) for i in indices},
                 'frozen78_exact':bool(np.array_equal(q[frozen],q0[frozen])),'guitar_initial_pq_unchanged':True},
             'natural_geometry':{'elbow_below_m':float(-el[2]),'elbow_outward_m':float(el@right),'wrist_inward_m':float(wr@right)}}
        rows.append(row);save(out/(row['label']+'_audit.json'),row)
        print(row['label'],'accepted',accepted,'elbowforward/error/orth mm',1000*delta@forward,1000*error,1000*orthogonal,'fullupper/forearm mm',1000*upper['gap_m'],1000*caps['R_Elbow']['gap_m'],flush=True)
        if accepted:
            folder=out/row['label'];folder.mkdir()
            candidate={**seed,'joint_angles_rad':q.tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in ps.items()},
                'predicted_guitar_body_states':predicted['guitar_body_states'],'right_block_cradle':row,'body_side_lean_axilla':row,'right_thigh_waist':row,
                'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']}}
            save(folder/'candidate.json',candidate);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json'),'elbow_motion_amplitude_rad':0.0})
            selected.append({'label':row['label'],'config':str(folder/'config.json')})
    assert all(sha(p)==h for p,h in inputs.items())
    save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'native_runs':0,'scope':'source only; Elbow3 move, frozen78; exact baseline Thorax/Shoulder controller witness retained and guitar initialization unchanged'})

if __name__=='__main__':main()
