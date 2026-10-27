"""Report diagnostics without promoting source geometry to actual support success."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 inputs={str(Path(__file__).resolve()):sha(Path(__file__).resolve())};cases={};region=read(P/'contact_region_v1.json');inputs[str(P/'contact_region_v1.json')]=sha(P/'contact_region_v1.json')
 centre=None
 for vp in sorted(P.glob('analysis_v*/*/verification.json')):
  data=read(vp);inputs[str(vp)]=sha(vp);centre=np.array(data['source_body_bbox_centre_G_m'])
  for name,v in data['cases'].items():
   folder=Path(v['videos']['whole_body']['path']).parents[1];paths=[folder/'initial_values.json',folder/'trace.json',folder/'media/physics_endpoint_contacts.json']
   for p in paths:inputs[str(p)]=sha(p)
   initial=read(paths[0]);trace=read(paths[1]);ep=read(paths[2])['rows'];poses=[Rotation.from_quat(t['quaternion_xyzw'])for t in trace];bc=np.array([np.array(t['position_W_m'])+rot.apply(centre)for t,rot in zip(trace,poses)]);delta=float(np.linalg.norm(bc[150:]-bc[150],axis=1).max()*1000);ang=max(float(np.rad2deg((poses[150].inv()*r).magnitude()))for r in poses[150:]);reg=region['cases'][name];rc=[c['human_segment_fraction_clipped']for r in reg['rows']for c in r['contacts']]
   gate=bool(v['endpoints']['head_presence']==0 and v['endpoints']['left_arm_hand_presence']==0 and v['right_distal_after_2p5_presence']==0 and v['right_upper_last_half_second_presence']>=100 and v['final_body_bbox_centre_change_mm']<80 and v['final_rotation_change_deg']<20 and v['body_centre_2_to_2p5s_mm']<1 and v['rotation_2_to_2p5s_deg']<.5)
   cases[name]={**v,'native_folder':str(folder),'temporary_stationary_motion_entry_gate':gate,'post_2p5_max_body_delta_mm':delta,'post_2p5_max_rotation_deg':ang,'actual_declared_shoulder_side35_contact_samples':reg['declared_region_contact_samples'],'actual_contact_fraction_min_max':([min(rc),max(rc)]if rc else None),'scope':'source diagnostic, finite human torque support; actual anatomical armpit/support force share not certified'}
 save(P/'result_summary_v1.json',{'input_sha256':inputs,'cases':cases,'scope':'stationary gate is diagnostic only; moving-elbow success requires matched OFF/ON and measured native elbow motion'});assert all(sha(Path(p))==h for p,h in inputs.items());print(json.dumps({k:{a:v[a]for a in ('final_body_bbox_centre_change_mm','final_rotation_change_deg','endpoints','temporary_stationary_motion_entry_gate','post_2p5_max_body_delta_mm','post_2p5_max_rotation_deg','actual_declared_shoulder_side35_contact_samples')}for k,v in cases.items()},indent=2))
if __name__=='__main__':main()
