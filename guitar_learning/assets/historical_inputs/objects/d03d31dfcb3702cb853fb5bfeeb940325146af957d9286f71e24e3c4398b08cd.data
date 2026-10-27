"""Source-only right upper-arm front clamp; other69 and guitar pose stay unchanged."""
import numpy as np
from scipy.optimize import least_squares
from . import search_om_no_strap_upper_arm_v6 as old
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
P=old.P;BASE=P/'native_v10/three_support_relative_effort_microgap/initial_values.json';PLAN=old.ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V16.md'
def main():
 from .environment_contract_v1 import EnvironmentContract
 from pathlib import Path
 c=EnvironmentContract(old.CONFIG);base=read(BASE);state=base['native_initial_state'];q0=np.array(base['q_ref_rad']);names=base['joint_names'];bodies=base['human_body_names'];fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0);gp,gr=pose(state['guitar_body_states'][0]);geometry=read(old.GEOMETRY);distance=CapsuleBodyDistance(geometry['asset'],old.ASSET)
 inputs={str(p):sha(p)for p in [BASE,old.CONFIG,old.GEOMETRY,PLAN,old.ASSET,Path(__file__).resolve()]};inputs.update(c.inputs);inputs.update({str(p):sha(p)for p in Path(__file__).parent.glob('*.py')});inputs[geometry['asset']]=geometry['asset_sha256'];inputs.update({m['path']:m['sha256']for m in geometry['meshes']})
 out=P/'search_v8';out.mkdir(exist_ok=False);save(out/'attempt.json',{'input_sha256':inputs,'native_runs':0});right=np.array([i for i,n in enumerate(names)if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]);lo=np.maximum(c.lower[right],q0[right]-1.2);hi=np.minimum(c.upper[right],q0[right]+1.2)
 def res(v):
  q=q0.copy();q[right]=v;ps=fk(q);m=distance.measure(ps,'R_Shoulder',gp,gr);s=np.array(m['guitar_surface_G_m']);normal=np.array(m['capsule_axis_G_m'])-s;normal/=np.linalg.norm(normal);p,r=ps['RH:palm']
  return np.r_[10000*(m['gap_m']-.00005),50*(normal-[-1,0,0]),100*(s[1]+.27),3*(p-original['RH:palm'][0]),.05*(v-q0[right])]
 fit=least_squares(res,np.clip(q0[right],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=180,diff_step=1e-4);q=q0.copy();q[right]=fit.x;q=q.astype(np.float32).astype(float);ps=fk(q);caps={n:distance.measure(ps,n,gp,gr)for n in distance.capsules if n in ps};m=caps['R_Shoulder'];normal=np.array(m['capsule_axis_G_m'])-m['guitar_surface_G_m'];normal/=np.linalg.norm(normal);audit=source_audit(source_scene(state_from_fk(state,bodies,q,fk),bodies,geometry['asset']),parents)
 row={'label':'upper_arm_neck_side' ,'proximal_support':m,'support_region':'full upper arm neck-side upper-rim witness; legacy key name','source_normal_W':gr.apply(normal).tolist(),'capsule_body':caps,'source_audit':audit,'right_initial_max_delta_rad':float(abs(q[right]-q0[right]).max()),'initial_other69_same':bool(np.array_equal(np.delete(q,right),np.delete(q0,right)))};row['accepted_for_native']=bool(audit['source_clear']and min(v['gap_m']for v in caps.values())>=.00001 and .00001<m['gap_m']<.0002 and gr.apply(normal)[2]>.7 and m['guitar_surface_G_m'][1]>-.34);save(out/'audit.json',row);selected=[]
 if row['accepted_for_native']:
  folder=out/row['label'];folder.mkdir();save(folder/'candidate.json',{'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in ps.items()},'no_strap_upper_arm_proposal':row});cfg=read(old.CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'));save(folder/'config.json',cfg);selected=[{'label':row['label'],'config':str(folder/'config.json')}]
 assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'selected':selected,'rows':[row],'native_runs':0});print(row)
if __name__=='__main__':main()
