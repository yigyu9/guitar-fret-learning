"""Select unchanged source geometry using actual virtual-pick preparation-region coordinates."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ASSET,calibrated_upper_fk,state_from_fk
from .environment_contract_v1 import EnvironmentContract
from .underneck_initial_search import source_scene as move_guitar
from .diagnose_user_guided_no_left_v1 import A,P,BASE,CFG


def main():
    out=P/'package_v12';out.mkdir(exist_ok=False);sources=[P/'search_v11'/(n+'_audit.json') for n in ('upper50','upper65')]
    cfg=read(CFG);anchors=[Path(__file__).resolve(),A/'USER_GUIDED_NO_LEFT_PACKAGE_V12_PLAN.md',BASE,CFG,ASSET,A/'assets/om_body_geometry_v3/manifest.json']+sources
    paths=anchors+list(A.glob('*.py'))+[Path(cfg['initial_candidate']),Path(cfg['native_reference'])]
    inputs={str(p):sha(p) for p in paths};save(out/'inputs_before.json',inputs)
    c=EnvironmentContract(CFG);b=read(BASE);state=b['native_initial_state'];names,bodies=b['joint_names'],b['human_body_names'];fk,_=calibrated_upper_fk(names,bodies,state,c.q_ref);gr=pose(state['guitar_body_states'][0])[1]
    centre=np.array(read(P/'diagnostic_v1/diagnostic.json')['guitar_centre_G_m']);assert np.allclose(centre,[0,-.4,-.055937985],atol=1e-9,rtol=0)
    selected=[];rows=[]
    for source in sources:
        old=read(source);q=np.array(old['joint_angles_rad']);ps=fk(q);gp=np.array(old['guitar_BBcentre_W_m'])-gr.apply(centre);pick=gr.inv().apply(ps['RH:pick'][0]-gp);palm=gr.inv().apply(ps['RH:palm'][0]-gp)
        right=np.array([i for i,n in enumerate(names) if n.startswith(('R_Thorax_','R_Shoulder_','R_Elbow_','R_Wrist_'))]);norms=np.rad2deg(np.linalg.norm(q[right].reshape(4,3),axis=1));caps=old['capsule_body']
        ready=bool(-.06<=pick[0]<=.06 and -.46<=pick[1]<=-.20 and .025<=pick[2]<=.18)
        assert old['source_audit']['source_clear'] and not old['face_used_left_10mm_certificate']['uncertified_pairs']
        assert min(v['gap_m'] for v in caps.values())>.00005 and .00005<caps['R_Shoulder']['gap_m']<.004 and .00005<caps['R_Elbow']['gap_m']<.004 and .00005<caps['R_Hip']['gap_m']<.004
        assert np.all(norms<160) and np.all(np.array(old['left_ball_rotation_vector_norm_deg'])<160) and np.all(q>=c.lower) and np.all(q<=c.upper)
        row={**old,'accepted_for_native':ready,'previous_RH_palm_target_error_m':old['RH_target_error_m'],'right_preparation':{'pick_G_m':pick.tolist(),'palm_G_m':palm.tolist(),'pick_region_G':{'x_m':[-.06,.06],'y_m':[-.46,-.20],'z_m':[.025,.18]},'right_ball_norm_deg':norms.tolist(),'accepted':ready,'scope':'coarse initial preparation region in front of pluck_range; not direct checkpoint handoff/strike accuracy'},'selection_rule':'physical geometry/left isolation unchanged; replace unnecessary exact palm target with actual pick preparation region'}
        save(out/(row['label']+'_selection.json'),row);rows.append(row)
        if ready:
            folder=out/row['label'];folder.mkdir();_,pred=move_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr)
            new={**c.candidate,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in ps.items()},'predicted_guitar_body_states':pred['guitar_body_states'],'right_block_cradle':row,'body_side_lean_axilla':row,'right_thigh_waist':row,'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']},'left_hand_off':{'accepted_for_native':True,'scope':'released near neck behind/below; trackingOFF'}}
            assert new['joint_angles_rad']==old['joint_angles_rad'];save(folder/'candidate.json',new);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json'),'left_wrist_tracking_off':True});selected.append({'label':row['label'],'config':str(folder/'config.json'),'physical_q_and_G_exact_to_V11':True})
    assert all(sha(p)==h for p,h in inputs.items());save(out/'package.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'geometry_solver_proposals':0,'scope':'coarse pick-region metadata selection; prior V11 exact-palm rejects preserved; no geometry reoptimization'})

if __name__=='__main__':main()
