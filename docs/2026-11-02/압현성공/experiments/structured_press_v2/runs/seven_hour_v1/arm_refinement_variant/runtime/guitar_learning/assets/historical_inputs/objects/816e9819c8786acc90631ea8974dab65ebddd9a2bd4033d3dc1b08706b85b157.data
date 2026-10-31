"""Source-only three-support initial poses with a bounded clavicle posture."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance

P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
BASE=P/'native_v5/upper_arm_right_hold/initial_values.json'
CONFIG=P/'right_hold_config_v1.json'
LOW=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/native_v1/thigh_gap3mm/initial_values.json'
GEOMETRY=ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json'
PLAN=ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V10.md'

def main():
    from .environment_contract_v1 import EnvironmentContract
    from .underneck_initial_search import source_scene as transform_guitar
    c=EnvironmentContract(CONFIG);base=read(BASE);state=base['native_initial_state'];q0=np.array(base['q_ref_rad']);names=base['joint_names'];bodies=base['human_body_names'];fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0);gp0,gr=pose(state['guitar_body_states'][0]);geometry=read(GEOMETRY);distance=CapsuleBodyDistance(geometry['asset'],ASSET)
    inputs={str(p):sha(p)for p in [BASE,CONFIG,LOW,GEOMETRY,PLAN,ASSET,Path(__file__).resolve()]};inputs.update(c.inputs);inputs.update({str(p):sha(p)for p in Path(__file__).parent.glob('*.py')});inputs.update(geometry['input_sha256']);inputs[geometry['asset']]=geometry['asset_sha256']
    for m in geometry['meshes']:inputs[m['path']]=m['sha256']
    out=P/'search_v5';out.mkdir(exist_ok=False);save(out/'attempt.json',{'input_sha256':inputs,'native_runs':0})
    group=lambda prefixes:np.array([i for i,n in enumerate(names)if n.startswith(prefixes)])
    body=c.body;head=group(('Neck_','Head_'));left=group(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'));right=group(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'));thorax=group(('R_Thorax',));lowq=np.array(read(LOW)['q_ref_rad']);forward=original['Pelvis'][1].apply([0,-1.,0]);forward[2]=0;forward/=np.linalg.norm(forward);axis=np.cross([0,0,1.],forward);rows=[];selected=[]
    for lean in (4,8,12):
        q=q0.copy();targets={n:Rotation.from_rotvec(axis*np.deg2rad(lean*f))*original[n][1]for n,f in zip(('Torso','Spine','Chest'),(.25,.625,1))};lo=np.maximum(c.lower[body],q0[body]-np.deg2rad(8));hi=np.minimum(c.upper[body],q0[body]+np.deg2rad(8))
        def body_res(v):
            z=q.copy();z[body]=v;ps=fk(z);return np.r_[np.concatenate([100*(targets[n].inv()*ps[n][1]).as_rotvec()for n in targets]),.01*(v-q0[body])]
        fit=least_squares(body_res,np.clip(q[body],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=80);q[body]=fit.x
        for idx,name in [(head,'Head'),(left,'LH:palm')]:
            lo=np.maximum(c.lower[idx],q0[idx]-.3);hi=np.minimum(c.upper[idx],q0[idx]+.3)
            def res(v):
                z=q.copy();z[idx]=v;p,r=fk(z)[name];parts=[100*(original[name][1].inv()*r).as_rotvec(),.01*(v-q0[idx])]
                if name=='LH:palm':parts.insert(0,1000*(p-original[name][0]))
                return np.concatenate(parts)
            fit=least_squares(res,np.clip(q[idx],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=100);q[idx]=fit.x
        ps=fk(q)
        def guitar_res(v):
            gp=gp0+[0,v[0],v[1]];chest=distance.measure(ps,'Chest',gp,gr)['gap_m'];hip=min(distance.measure(ps,n,gp,gr)['gap_m']for n in ('L_Hip','R_Hip'));return [1000*(chest-.003),1000*(hip-.003)]
        fit=least_squares(guitar_res,[-.01,0],bounds=([-.03,-.015],[0,.015]),max_nfev=60,diff_step=1e-4);delta=np.array([0,fit.x[0],fit.x[1]]);gp=gp0+delta
        lo=np.maximum(c.lower[right],q0[right]-.8);hi=np.minimum(c.upper[right],q0[right]+.8)
        for j,i in enumerate(right):
            if i in thorax:lo[j]=max(c.lower[i],lowq[i]-.05);hi[j]=min(c.upper[i],lowq[i]+.05)
        palm_target=original['RH:palm'][0]+delta
        def right_res(v):
            z=q.copy();z[right]=v;poses=fk(z);full=distance.measure(poses,'R_Shoulder',gp,gr);prox=distance.measure(poses,'R_Shoulder',gp,gr,.65);point=prox['guitar_surface_G_m'];p,r=poses['RH:palm']
            return np.r_[1000*(prox['gap_m']-.001),500*max(.0005-full['gap_m'],0),200*max(point[0]+.1,0),200*max(-.55-point[1],0),200*max(point[1]+.25,0),30*(p-palm_target),2*(original['RH:palm'][1].inv()*r).as_rotvec(),.1*(v-q0[right])]
        fit=least_squares(right_res,np.clip(q[right],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=180,diff_step=1e-4);q[right]=fit.x;q=q.astype(np.float32).astype(float);poses=fk(q);capsules={n:distance.measure(poses,n,gp,gr)for n in distance.capsules if n in poses};prox=distance.measure(poses,'R_Shoulder',gp,gr,.65)
        _,predicted=transform_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr);audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents);lp,lr=poses['LH:palm'];body_error={n:float(np.rad2deg((targets[n].inv()*poses[n][1]).magnitude()))for n in targets};label='three_support_lean%d'%lean
        row={'label':label,'additional_chest_world_lean_deg':lean,'guitar_initial_delta_W_m':delta.tolist(),'proximal_support':prox,'capsule_body':capsules,'source_audit':audit,'body_goal_orientation_errors_deg':body_error,'body_max_initial_scalar_change_deg':float(np.rad2deg(abs(q[body]-q0[body])).max()),'head_orientation_error_deg':float(np.rad2deg((original['Head'][1].inv()*poses['Head'][1]).magnitude())),'left_palm_position_error_m':float(np.linalg.norm(lp-original['LH:palm'][0])),'left_palm_orientation_error_deg':float(np.rad2deg((original['LH:palm'][1].inv()*lr).magnitude())),'right_palm_position_error_m':float(np.linalg.norm(poses['RH:palm'][0]-palm_target)),'right_thorax_delta_from_low_reference_rad':(q[thorax]-lowq[thorax]).tolist()}
        row['accepted_for_native']=bool(audit['source_clear'] and min(v['gap_m']for v in capsules.values())>=.0002 and .0002<prox['gap_m']<.003 and .0002<capsules['Chest']['gap_m']<.006 and .0002<min(capsules[n]['gap_m']for n in ('L_Hip','R_Hip'))<.006 and row['left_palm_position_error_m']<.002 and row['left_palm_orientation_error_deg']<1 and row['right_palm_position_error_m']<.075 and max(body_error.values())<.2 and row['head_orientation_error_deg']<.2)
        rows.append(row);save(out/(label+'_audit.json'),row);print(label,'accepted',row['accepted_for_native'],'chestgap_mm',capsules['Chest']['gap_m']*1000,'proxgap_mm',prox['gap_m']*1000,'rightpalm_error_mm',row['right_palm_position_error_m']*1000,'delta',delta.tolist(),flush=True)
        if row['accepted_for_native']:
            folder=out/label;folder.mkdir();save(folder/'candidate.json',{'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in poses.items()},'no_strap_upper_arm_proposal':row});cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'));save(folder/'config.json',cfg);selected.append({'label':label,'config':str(folder/'config.json')})
    assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'selected':selected,'rows':rows,'native_runs':0,'scope':'source three-support geometry; not native cooked or physical stability certification'})

if __name__=='__main__':main()
