"""Keep the three-support pose, reducing only the right upper-arm source gap."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
BASE=P/'native_v9/three_support_right_effort/initial_values.json'
CONFIG=P/'right_effort_config_v1.json'
GEOMETRY=ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json'
PLAN=ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V14.md'

def main():
    from .environment_contract_v1 import EnvironmentContract
    c=EnvironmentContract(CONFIG);base=read(BASE);state=base['native_initial_state'];q0=np.array(base['q_ref_rad']);names=base['joint_names'];bodies=base['human_body_names'];fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0);gp,gr=pose(state['guitar_body_states'][0]);geometry=read(GEOMETRY);distance=CapsuleBodyDistance(geometry['asset'],ASSET)
    inputs={str(p):sha(p)for p in [BASE,CONFIG,GEOMETRY,PLAN,ASSET,Path(__file__).resolve()]};inputs.update(c.inputs);inputs.update({str(p):sha(p)for p in Path(__file__).parent.glob('*.py')});inputs[geometry['asset']]=geometry['asset_sha256']
    for m in geometry['meshes']:inputs[m['path']]=m['sha256']
    out=P/'search_v6';out.mkdir(exist_ok=False);save(out/'attempt.json',{'input_sha256':inputs,'native_runs':0});right=np.array([i for i,n in enumerate(names)if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]);lo=np.maximum(c.lower[right],q0[right]-.05);hi=np.minimum(c.upper[right],q0[right]+.05)
    def residual(v):
        z=q0.copy();z[right]=v;ps=fk(z);prox=distance.measure(ps,'R_Shoulder',gp,gr,.65);full=distance.measure(ps,'R_Shoulder',gp,gr);p,r=ps['RH:palm']
        return np.r_[1000*(prox['gap_m']-.00005),1000*max(.000025-full['gap_m'],0),30*(p-original['RH:palm'][0]),3*(original['RH:palm'][1].inv()*r).as_rotvec(),.1*(v-q0[right])]
    fit=least_squares(residual,np.clip(q0[right],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=100,diff_step=1e-4);q=q0.copy();q[right]=fit.x;q=q.astype(np.float32).astype(float);ps=fk(q);caps={n:distance.measure(ps,n,gp,gr)for n in distance.capsules if n in ps};prox=distance.measure(ps,'R_Shoulder',gp,gr,.65);audit=source_audit(source_scene(state_from_fk(state,bodies,q,fk),bodies,geometry['asset']),parents)
    row={'label':'three_support_microgap','proximal_support':prox,'capsule_body':caps,'source_audit':audit,'right_initial_max_delta_rad':float(abs(q[right]-q0[right]).max()),'right_palm_position_change_m':float(np.linalg.norm(ps['RH:palm'][0]-original['RH:palm'][0])),'source_gap_acceptance_min_m':.00001,'initial_other69_same':bool(np.array_equal(np.delete(q,right),np.delete(q0,right)))}
    row['accepted_for_native']=bool(audit['source_clear'] and min(v['gap_m']for v in caps.values())>=.00001 and .00001<=prox['gap_m']<.0001 and row['right_palm_position_change_m']<.002 and row['initial_other69_same']);save(out/'audit.json',row)
    selected=[]
    if row['accepted_for_native']:
        folder=out/'three_support_microgap';folder.mkdir();save(folder/'candidate.json',{'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in ps.items()},'no_strap_upper_arm_proposal':row});cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'));save(folder/'config.json',cfg);selected=[{'label':row['label'],'config':str(folder/'config.json')}]
    assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'selected':selected,'rows':[row],'native_runs':0,'scope':'positive source microgap; native cooked and first-step contact not certified'});print(row['accepted_for_native'],prox,row['right_initial_max_delta_rad'])

if __name__=='__main__':main()
