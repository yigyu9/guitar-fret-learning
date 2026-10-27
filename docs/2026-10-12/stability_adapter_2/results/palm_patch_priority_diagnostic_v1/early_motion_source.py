"""Read saved early source-palm approach and separate exact Chest/arm world displacement."""
import hashlib,json
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
PHASE=BASE/'palm_patch_priority_diagnostic_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    output=PHASE/'early_motion_audit.json';assert not output.exists()
    analysis=read(PHASE/'analysis.json');inputs=dict(analysis['input_sha256']);inputs[str(PHASE/'analysis.json')]=sha(PHASE/'analysis.json')
    for p in [Path(__file__).resolve(),ROOT/'stability_adapter_2/PALM_PRIORITY_EARLY_MOTION_AUDIT.md',PHASE/'native_feature_analysis.json',BASE/'three_face_support_loss_v1/native/saved_finger_targets/shape_properties.json']:inputs[str(p)]=sha(p)
    from .environment import np
    from .build_fixed_lower_asset import ASSET,pose
    from .initial_overlap import build_probe
    from .face_referenced_geometry import face_geometry
    from .source_patch_interval import certified_distance
    from scipy.spatial.transform import Rotation
    states=[json.loads(v) for v in (PHASE/'native/states.jsonl').read_text().splitlines()];init=read(PHASE/'native/initial_values.json');proposal=read(PHASE/'proposal.json');row=proposal['rows'][0];hn=init['human_body_names'];gn=[r['body'] for r in read(BASE/'three_face_support_loss_v1/native/saved_finger_targets/shape_properties.json')['actors']['guitar']['body_ranges']];config=read(ROOT/'stability_adapter_2/config.json');config['humanoid_asset']=str(ASSET)
    anchor=np.array(row['source_anchors']['LH:palm']['source_point_local_m']);poly=np.array(proposal['regions_G_m']['palm']);proxy=np.array(read(BASE/'palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local']);arm=[i for i,n in enumerate(init['human_joint_names']) if n.startswith(('L_Thorax_','L_Shoulder_','L_Elbow_','L_Wrist_'))]
    def point(s):p,q=pose(s['human_body_states'][hn.index('LH:palm')]);return p+Rotation.from_quat(q).apply(anchor)
    pc0,qc0=pose(states[0]['human_body_states'][hn.index('Chest')]);rc0=Rotation.from_quat(qc0);p0=point(states[0]);relative0=rc0.inv().apply(p0-pc0);samples=[]
    for step in (0,1,4,8,12,24,60,120,240,1200):
        s=states[step];p=point(s);pc,qc=pose(s['human_body_states'][hn.index('Chest')]);rc=Rotation.from_quat(qc);relative=rc.inv().apply(p-pc)
        chest=pc-pc0+rc.apply(relative0)-rc0.apply(relative0);chain=rc.apply(relative-relative0);delta=p-p0;assert np.linalg.norm(chest+chain-delta)<1e-12
        gp,gq=pose(s['guitar_body_states'][0]);gr=Rotation.from_quat(gq);pointG=gr.inv().apply(p-gp)
        scene=SimpleNamespace(config=config,human=0,guitar=1,env=None,gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:hn if actor==0 else gn),bodies=lambda actor:s['human_body_states'] if actor==0 else s['guitar_body_states'])
        model,data,shapes=build_probe(scene);shape=next(sh for sh in shapes if sh['actor']=='human' and sh['body']=='LH:palm');mesh=face_geometry(model,data,shape);gap=certified_distance(mesh,gr.apply(poly)+gp)
        palmq=Rotation.from_quat(pose(s['human_body_states'][hn.index('LH:palm')])[1]);normalG=gr.inv().apply(palmq.apply(row['source_anchors']['LH:palm']['source_normal_local']));desired=-np.array([1.,.01631590413943356,0.]);desired/=np.linalg.norm(desired)
        q=np.array([d['pos'] for d in s['human_dof_states']]);targets=np.array(row['expected_absolute_targets_rad'])
        samples.append(dict(physics_step=step,time_s=step/240,palm_anchor_W_m=p.tolist(),palm_anchor_G_m=pointG.tolist(),world_anchor_delta_mm=(delta*1000).tolist(),Chest_pose_contribution_W_mm=(chest*1000).tolist(),arm_chain_contribution_W_mm=(chain*1000).tolist(),source_palm_patch_interval=gap,palm_side_inward_alignment_dot=float(normalG@desired),palm_up_proxy_z=float(palmq.apply(proxy)[2]),actual_left_arm_minus_PD_target_rad={init['human_joint_names'][i]:float(q[i]-targets[i]) for i in arm}))
    features=read(PHASE/'native_feature_analysis.json')['rows'];palm=[v for v in features if v['human_body']=='LH:palm'];positive=[v for v in palm if v['raw_lambda']>0]
    checks=dict(exact_Chest_plus_arm_vector_equals_actual_world_anchor_displacement=True,ten_saved_step_queries_no_native_initialization=True,finite_source_interval_witnesses=True,inputs_unchanged=all(sha(p)==h for p,h in inputs.items()));assert all(checks.values())
    output.write_text(json.dumps(dict(checks=checks,input_sha256=inputs,samples=samples,first_palm_body_contact_step=min((v['physics_step'] for v in palm),default=None),first_positive_palm_body_step=min((v['physics_step'] for v in positive),default=None),first_requested_palm_patch_positive_step=min((v['physics_step'] for v in positive if v['post_pose_feature_within2mm']),default=None),native_initializations=0,physics_steps=0,scope='saved actual body poses source anchor/hull approach; exact vector decomposition, no causal isolation; source interval not cooked gap; preserved old81PD targets; no stability or physical face certification'),indent=2)+'\n')
    print(json.dumps(dict(checks=checks,first_positive_palm_body_step=min((v['physics_step'] for v in positive),default=None),summary=[dict(step=v['physics_step'],gap_upper_mm=v['source_palm_patch_interval']['distance_m']*1000,Chest_mm=float(np.linalg.norm(v['Chest_pose_contribution_W_mm'])),arm_mm=float(np.linalg.norm(v['arm_chain_contribution_W_mm']))) for v in samples]),indent=2))
if __name__=='__main__':main()
