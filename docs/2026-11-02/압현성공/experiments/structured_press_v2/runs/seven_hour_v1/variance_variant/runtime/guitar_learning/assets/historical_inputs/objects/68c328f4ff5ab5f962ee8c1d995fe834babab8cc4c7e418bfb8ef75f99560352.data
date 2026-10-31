"""Add genuine calibrated FK poses without changing the prepared trial states."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha
from .upper_arm_static_geometry_v1 import ROOT,calibrated_upper_fk
A=ROOT/'stability_adapter_2';D=ROOT/'docs/2026-10-19/stability_adapter_2';P=D/'results/upper_bout_axilla_v1'
def main():
 source=P/'search_v2/search.json';data=read(source);assert all(sha(p)==h for p,h in data['input_sha256'].items());basepath=D/'results/natural_right_arm_v1/native_v2/front160mm/initial_values.json';base=read(basepath);fk,_=calibrated_upper_fk(base['joint_names'],base['human_body_names'],base['native_initial_state'],np.array(base['q_ref_rad']));inputs=dict(data['input_sha256']);inputs.update({str(p):sha(p)for p in [Path(__file__).resolve(),source,basepath,A/'UPPER_BOUT_AXILLA_PLAN_V3.md',A/'run_upper_bout_axilla_v3.py']});out=P/'search_v3';out.mkdir(exist_ok=False);selected=[]
 for item in data['selected']:
  configpath=Path(item['config']);cfg=read(configpath);oldpath=Path(cfg['initial_candidate']);old=read(oldpath);assert sha(oldpath)==cfg['initial_candidate_sha256'];inputs.update({str(configpath):sha(configpath),str(oldpath):sha(oldpath)});poses=fk(np.array(old['joint_angles_rad']));new={**old,'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in poses.items()}};assert all(new[k]==old[k]for k in old);folder=out/item['label'];folder.mkdir();save(folder/'candidate.json',new);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json')});selected.append({'label':item['label'],'config':str(folder/'config.json')})
 assert all(sha(p)==h for p,h in inputs.items());save(out/'inputs_before.json',inputs);save(out/'search.json',{'input_sha256':inputs,'selected':selected,'rows':data['rows'],'native_runs':0,'scope':'same V2q/G state, added calibrated actual-q humanFK for mandatory native initial-state validation'})
if __name__=='__main__':main()
