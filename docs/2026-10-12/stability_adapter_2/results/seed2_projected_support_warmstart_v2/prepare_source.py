"""Check initial left33 blends of observed support coordinates; no native dynamics."""
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1'
PHASE=OLD.parent/'seed2_projected_support_warmstart_v2'
TRIALS=ROOT/'stability_adapter_2/trials/seed2_projected_support_warmstart_v2'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    PHASE.mkdir(exist_ok=False);TRIALS.mkdir(exist_ok=False)
    path=OLD/'analysis.json';hashes={str(path):sha(path)};prior=read(path)
    paths=[Path(p) for p in prior['input_sha256']]+[Path(__file__).resolve(),ROOT/'stability_adapter_2/SEED2_SUPPORT_POSE_WARMSTART_PLAN.md',ROOT/'stability_adapter_2/warmstart_targets.py',ROOT/'stability_adapter_2/SEED2_SUPPORT_WARMSTART_EXECUTION.md',ROOT/'stability_adapter_2/SEED2_PROJECTED_SUPPORT_WARMSTART_PLAN.md',OLD.parent/'seed2_support_warmstart_v1/proposal.json',OLD.parent/'seed2_support_warmstart_v1/source_only_outcome.json',OLD.parent/'multi_face_grip_v3/search.json',OLD/'proposal.json']
    hashes.update({str(p):sha(p) for p in paths});save(PHASE/'attempt.json',{'input_sha256':hashes,'native_initializations':0,'physics_steps':0})
    if not all(prior['checks'].values()) or any(sha(p)!=h for p,h in prior['input_sha256'].items()):raise AssertionError('previous input closure changed')
    from .environment import np
    from .search_multi_face_grip import prepare_geometry,left_fk
    from .build_fixed_lower_asset import pose
    from .render_best_run_video import set_saved_pose
    from .palm_side_source_checks import source_checks,intersection
    from .audit_palm_side_target import closest_polygon
    from .warmstart_targets import compose
    from scipy.spatial.transform import Rotation
    import mujoco
    initial=read(OLD/'native/constant_0p016/initial_values.json');grip=read(OLD/'proposal.json');base=initial['input_trial']
    raw_end=json.loads((OLD/'native/constant_0p016/states.jsonl').read_text().splitlines()[-1]);control=json.loads((OLD/'native/constant_0p016/controls.jsonl').read_text().splitlines()[-1])
    if raw_end['physics_step']!=1200 or control['physics_step']!=1200:raise AssertionError('completed five-second source required')
    names=initial['human_joint_names'];q0=np.array(initial['initial_PD_target_rad']);qend=np.array([d['pos'] for d in raw_end['human_dof_states']])
    left=np.array([i for i,n in enumerate(names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:'))]);main=np.array([names.index(n) for n in initial['main_control_joint_names']]);other=np.setdiff1d(np.arange(81),left)
    arm=np.array([i for i,n in enumerate(names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]);c02=np.array(read(OLD.parent/'palm_stiffness_only_v1/kp_1/initial_values.json')['initial_PD_target_rad'])
    if len(left)!=33 or len(arm)!=12 or len(other)!=48 or len(main)!=66:raise AssertionError('33/48/66 coordinate ownership')
    target=q0.astype(np.float32);target[arm]=np.array(control['final_target_rad'],dtype=np.float32)
    lower=np.array(initial['PD_properties']['lower']);upper=np.array(initial['PD_properties']['upper'])
    report,probe,_,_,_,gp,gr,_,z=prepare_geometry(initial);model,data,shapes=probe;bodies=report['human_body_names'];fk,parents=left_fk(names,bodies,initial['native_initial_state'],q0)
    proxy=np.array(read(OLD.parent/'palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local'])
    def distance(a,b):
        chain=[];current=a
        while current in parents:chain.append(current);current=parents[current]
        chain.append(current);steps=0;current=b
        while current not in chain and current in parents:steps+=1;current=parents[current]
        return steps+chain.index(current) if current in chain else 99
    rows=[];rejected=[]
    def evaluate(alpha,label):
        q=q0.copy();desired=q0[left]+alpha*(qend[left]-q0[left]);lo=np.maximum(lower[left],target[left].astype(float)-.3);hi=np.minimum(upper[left],target[left].astype(float)+.3)
        arm_positions=[k for k,i in enumerate(left) if i in arm]
        for k in arm_positions:lo[k]=max(lo[k],c02[left[k]]-.3);hi[k]=min(hi[k],c02[left[k]]+.3)
        low32=lo.astype(np.float32);high32=hi.astype(np.float32)
        low32=np.where(low32.astype(float)<lo,np.nextafter(low32,np.float32(np.inf)),low32);high32=np.where(high32.astype(float)>hi,np.nextafter(high32,np.float32(-np.inf)),high32)
        if np.any(low32>high32):raise AssertionError('empty representable initial interval')
        q[left]=np.clip(desired.astype(np.float32),low32,high32).astype(float)
        limited=[{'joint':names[i],'desired_initial_angle_rad':float(desired[k]),'effective_initial_angle_rad':float(q[i]),'projection_delta_rad':float(q[i]-desired[k]),'admissible_lower_rad':float(low32[k]),'admissible_upper_rad':float(high32[k])} for k,i in enumerate(left) if desired[k]<low32[k] or desired[k]>high32[k]]
        offsets={names[i]:float(target[i])-float(q[i]) for i in left};reasons=[]
        if np.any(q<lower) or np.any(q>upper):reasons.append('native_initial_angle_bounds')
        if np.any(np.abs(q[arm]-c02[arm])>.3):reasons.append('C02_arm_initial_range')
        if any(abs(v)>.3 for v in offsets.values()):reasons.append('relative_offset_range')
        if reasons:return {'label':label,'alpha':alpha,'accepted_for_fresh_native':False,'reasons':reasons}
        expected=compose(q.astype(np.float32),main,np.array([offsets.get(names[i],0.) for i in main]),lower,upper)
        if not np.array_equal(expected,target):raise AssertionError('preserved absolute target float32 mismatch')
        poses=fk(q);state=copy.deepcopy(initial['native_initial_state'])
        for name,(p,r) in poses.items():state['human_body_states'][bodies.index(name)]['pose']={'p':dict(zip('xyz',p)),'r':dict(zip('xyzw',r.as_quat()))}
        for i,value in enumerate(q):state['human_dof_states'][i]['pos']=float(value)
        set_saved_pose(model,mujoco,report,state);mujoco.mj_forward(model,data);meshes,overlaps,crosshands=source_checks(probe)
        hand=[s for s in shapes if s['body'].startswith('LH:') or s['body'] in ('L_Wrist','L_Elbow')]
        self_cross=[{'a':a['body'],'b':b['body'],'common_radius_m':radius} for i,a in enumerate(hand) for b in hand[i+1:] if distance(a['body'],b['body'])>2 for radius in [intersection(meshes[a['geom_id']],meshes[b['geom_id']])]]
        self_cross=[r for r in self_cross if r['common_radius_m']>1e-7]
        up=float(poses['LH:palm'][1].apply(proxy)[2]);gaps={}
        for name in grip['facets']:
            face='palm' if name=='LH:palm' else 'thumb' if name=='LH:thumb3' else 'front';poly=np.array(grip['regions_G_m'][face])
            if face=='front':poly[:,2]=z
            mesh=meshes[next(s['geom_id'] for s in shapes if s['body']==name)];gaps[name]=dict(closest_polygon(mesh,gr.apply(poly)+gp),face=face)
        if overlaps:reasons.append('source_human_guitar_intersection')
        if crosshands:reasons.append('source_cross_hands_intersection')
        if self_cross:reasons.append('source_nonadjacent_left_hand_intersection')
        if up<=0:reasons.append('palm_up_proxy')
        trial=copy.deepcopy(base)
        if alpha:
            trial['initial_settings']['joint_angles_rad'].update({names[i]:float(q[i]) for i in left});trial['main_target_offsets_rad']=offsets
        else:trial['main_target_offsets_rad']=offsets
        path=TRIALS/(label+'.json');save(path,trial)
        return {'label':label,'alpha':alpha,'projected_coordinates':limited,'accepted_for_fresh_native':not reasons,'reasons':reasons,'trial_path':str(path),'trial_sha256':sha(path),'expected_initial_angles_rad':q.tolist(),'expected_absolute_targets_rad':target.astype(float).tolist(),'absolute_strap_rest_length_m':initial['absolute_strap_rest_length_m'],'target_clearance_m':.001,'source_state':state,'palm_up_proxy_z':up,'source_hull_to_faces':gaps,'three_face_source_approach_satisfied':max(g['distance_m'] for g in gaps.values())<=.003,'source_intersections':overlaps,'cross_hand_intersections':crosshands,'nonadjacent_left_hand_intersections':self_cross}
    for alpha,label in [(0.,'baseline_repeat'),(.25,'projected_0p25'),(.5,'projected_0p5')]:
        row=evaluate(alpha,label);(rows if row['accepted_for_fresh_native'] else rejected).append(row);save(PHASE/'partial_selection.json',{'rows':rows,'rejected':rejected});print(json.dumps({'label':label,'accepted':row['accepted_for_fresh_native'],'reasons':row['reasons'],'gap_mm':{n:g['distance_m']*1000 for n,g in row.get('source_hull_to_faces',{}).items()}}),flush=True)
    if not rows or rows[0]['label']!='baseline_repeat':raise AssertionError('saved baseline source no longer admitted')
    checks={'preserved_absolute_float32_targets_native_bounds':True,'left33_initial_blend_other48_held':True,'source_admitted_rows_only':all(r['accepted_for_fresh_native'] for r in rows),'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    save(PHASE/'proposal.json',{'checks':checks,'input_sha256':hashes,'rows':rows,'rejected':rejected,'facets':grip['facets'],'regions_G_m':grip['regions_G_m'],'front_outer_source_z_G_m':z,'old_initial_angles_rad':q0.tolist(),'observed_end_angles_rad':qend.tolist(),'C02_angles_rad':c02.tolist(),'left33_names':[names[i] for i in left],'same_absolute_targets_rad':target.astype(float).tolist(),'native_initializations':0,'physics_steps':0,'scope':'explicitly projected initial source/FK candidates from observed joint coordinates only; same absolute native targets using float64 composition then float32 submit; no body/G pose or velocity transfer; no cooked clearance certification'})


if __name__=='__main__':main()
