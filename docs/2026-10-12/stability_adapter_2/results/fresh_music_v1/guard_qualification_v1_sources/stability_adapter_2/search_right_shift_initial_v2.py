"""Re-audit small shifts against the measured baseline proximal separation."""
import copy
from pathlib import Path
import numpy as np
from .search_right_shift_initial_v1 import A,B,P,CFG,BASE,ASSET
from .initial_pose_noise_v1 import read,save,sha,pose
from .environment_contract_v1 import EnvironmentContract
from .upper_arm_static_geometry_v1 import calibrated_upper_fk,state_from_fk
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .left_neck_near_geometry_v1 import FACETS
from .left_neck_three_face_geometry_v1 import measurements,placement_pass


def main():
    out=P/'search_v2';out.mkdir(exist_ok=False)
    report=P/'search_v1/search.json';before=P/'search_v1/inputs_before.json'
    anchors=[Path(__file__).resolve(),A/'RIGHT_SHIFT_INITIAL_PLAN_V2.md',report,before]
    discovery={str(p.resolve()):sha(p) for p in anchors};save(out/'discovery_before.json',discovery)
    oldinputs=read(before);paths=list(map(Path,oldinputs))+anchors+list(A.glob('*.py'))
    inputs={str(p.resolve()):sha(p) for p in paths};assert all(inputs[p]==h for p,h in discovery.items());assert all(inputs[p]==h for p,h in oldinputs.items());save(out/'inputs_before.json',inputs)
    config=read(CFG);contract=EnvironmentContract(CFG);seed=read(config['initial_candidate']);base=read(BASE);state=base['native_initial_state'];names,bodies=base['joint_names'],base['human_body_names'];q0=np.array(base['q_ref_rad'])
    fk,parents=calibrated_upper_fk(names,bodies,state,q0);gp0,gr=pose(state['guitar_body_states'][0]);geometry=read(A/'assets/om_body_geometry_v3/manifest.json');distance=CapsuleBodyDistance(geometry['asset'],ASSET)
    original=fk(q0);baseline={n:distance.measure(original,n,gp0,gr) for n in ('R_Thorax','R_Shoulder','R_Hip')};save(out/'baseline_capsule_body.json',baseline);print('baseline gap mm',{n:v['gap_m']*1000 for n,v in baseline.items()},flush=True)
    arms=[i for i,n in enumerate(names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))];frozen=np.ones(81,dtype=bool);frozen[arms]=False
    facets=read(FACETS)['facets'];rows=[];selected=[]
    for old in read(report)['rows']:
        if 'joint_angles_rad' not in old:rows.append(old);continue
        q=np.array(old['joint_angles_rad']);delta=np.array(old['guitar_delta_W_m']);gp=gp0+delta;poses=fk(q);pred=state_from_fk(state,bodies,q,fk)
        for s in pred['guitar_body_states']:
            for k,v in zip('xyz',delta):s['pose']['p'][k]+=float(v)
        audit=source_audit(source_scene(pred,bodies,geometry['asset']),parents);faces=measurements(poses,gp,gr,old['station_G_m'],old['front_z_G_m'],facets)
        caps={n:distance.measure(poses,n,gp,gr) for n in old['capsule_body']}
        samples=old['samples']
        accepted=bool(audit['source_clear'] and placement_pass(faces) and np.array_equal(q[frozen],q0[frozen]) and np.all(q>=contract.lower) and np.all(q<=contract.upper) and old['initial_pick_translation_error_m']<.002 and
            all(np.linalg.norm(q[[names.index(prefix+'_'+a) for a in 'xyz']])<np.deg2rad(160) for prefix in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist')) and
            .00005<caps['R_Thorax']['gap_m']<baseline['R_Thorax']['gap_m']+.005 and .00005<caps['R_Shoulder']['gap_m']<.006 and
            all(s['position_error_m']<.002 and s['forearm_body_gap_m']>.00005 and max(s['ball_norm_deg'])<160 for s in samples))
        row={**old,'accepted_for_native':accepted,'source_audit':audit,'face_measurements':faces,'capsule_body':caps,'proximal_upper_arm30_witness':caps['R_Shoulder'],'proximal_upper_arm45_witness':caps['R_Shoulder'],'proximal_upper_arm65_witness':caps['R_Shoulder'],'full_upper_arm_witness':caps['R_Shoulder'],'thorax_gap_upper_bound_m':baseline['R_Thorax']['gap_m']+.005,'revalidated_from':str(report)}
        rows.append(row);save(out/(row['label']+'_audit.json'),row);print(row['label'],'accepted',accepted,'shouldermm',caps['R_Shoulder']['gap_m']*1000,flush=True)
        if accepted:
            folder=out/row['label'];folder.mkdir();candidate={**seed,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in poses.items()},'predicted_guitar_body_states':pred['guitar_body_states'],'right_block_cradle':row,'body_side_lean_axilla':row,'right_shift_initial':row,'left_neck_near':{**seed['left_neck_near'],'accepted_for_native':True,'face_measurements':faces,'source_audit':audit},'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']}}
            save(folder/'candidate.json',candidate);save(folder/'config.json',{**config,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json')});selected.append({'label':row['label'],'config':str(folder/'config.json')})
    assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'baseline_capsule_body':baseline,'rows':rows,'selected':selected,'native_runs':0,'scope':'fresh actual source geometry re-audit of V1 angles; baseline-relative Thorax gap criterion; EW6 source waypoint metrics inherited from pinned V1, not continuous collision or measured playing success'})


if __name__=='__main__':main()
