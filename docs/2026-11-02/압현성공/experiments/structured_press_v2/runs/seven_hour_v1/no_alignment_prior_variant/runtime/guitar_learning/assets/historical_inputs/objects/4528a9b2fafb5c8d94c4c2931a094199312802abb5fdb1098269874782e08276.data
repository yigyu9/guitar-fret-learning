"""Adopt unchanged source-clear shoulder-side proximity seeds for native diagnosis."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha
from .upper_arm_static_geometry_v1 import ROOT
A=ROOT/'stability_adapter_2';D=ROOT/'docs/2026-10-19/stability_adapter_2';P=D/'results/upper_bout_axilla_v1'
def main():
 from .environment_contract_v1 import EnvironmentContract
 source=P/'search_v1/search.json';data=read(source);assert all(sha(p)==h for p,h in data['input_sha256'].items());cfgpath=D/'results/body_side_lean_axilla_v1/search_v5/right4_close_support/config.json';cfg=read(cfgpath);seed=read(cfg['initial_candidate']);c=EnvironmentContract(cfgpath);qs=np.array(seed['joint_angles_rad']);names=seed['joint_names'];body=c.body;head=np.array([i for i,n in enumerate(names)if n.startswith(('Neck_','Head_'))]);right=np.array([i for i,n in enumerate(names)if n.startswith(('R_Thorax','R_Shoulder','R_Elbow'))]);fixed=np.ones(81,dtype=bool);fixed[np.r_[body,head,right]]=False
 files=[Path(__file__).resolve(),A/'UPPER_BOUT_AXILLA_PLAN_V2.md',A/'run_upper_bout_axilla_v2.py',source,cfgpath,Path(cfg['initial_candidate'])];inputs=dict(data['input_sha256']);inputs.update({str(p):sha(p)for p in files});out=P/'search_v2';out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs);selected=[];rows=[]
 for raw in data['rows']:
  q=np.array(raw['joint_angles_rad']);prox=raw['proximal_upper_arm35_witness'];shape=raw['posture_shape'];surface=np.array(prox['guitar_surface_G_m']);bounds=raw['bounds_rad'];assert raw['source_audit']['source_clear']and min(v['gap_m']for v in raw['capsule_body'].values())>=.00005 and .00005<=prox['gap_m']<.006
  assert shape['elbow_outside_shoulder_m']>=.18 and shape['elbow_below_shoulder_m']>=.015 and shape['wrist_inward_from_elbow_m']>=.03 and raw['hand_position_error_m']<.04 and raw['body_goal_max_error_deg']<.2 and raw['head_orientation_error_deg']<.5 and surface[0]<-.17 and -.55<=surface[1]<=-.43 and raw['source_proximal_normal_W'][2]>.35
  assert np.array_equal(q[fixed],qs[fixed])and np.all(q>=c.lower-1e-7)and np.all(q<=c.upper+1e-7)and np.all(q[right]>=np.array(bounds['lower'])-1e-7)and np.all(q[right]<=np.array(bounds['upper'])+1e-7)
  row={**raw,'accepted_for_native':True,'adoption_scope':'same rejectedV1 source pose; proximal35%6mm and elbowbelow15mm heuristics for native proximity diagnosis only'};folder=out/raw['label'];folder.mkdir();candidate={'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':seed['position_W_m'],'quaternion_xyzw':seed['quaternion_xyzw'],'no_strap_upper_arm_proposal':{'proximal_support':raw['capsule_body']['R_Elbow']},'body_side_lean_axilla':row};save(folder/'candidate.json',candidate);newcfg={**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json')};save(folder/'config.json',newcfg);selected.append({'label':raw['label'],'config':str(folder/'config.json')});rows.append(row)
 assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'selected':selected,'rows':rows,'native_runs':0,'scope':'unchanged source-close seeds for native diagnosis; not final adoption or cookedcontact certification'})
if __name__=='__main__':main()
