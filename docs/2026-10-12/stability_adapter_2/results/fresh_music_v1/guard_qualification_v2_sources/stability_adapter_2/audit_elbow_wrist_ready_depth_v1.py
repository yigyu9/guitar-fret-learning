"""Fresh full-source shape audits at selected and interpolated six-scalar poses."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .environment_contract_v1 import EnvironmentContract
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .elbow_wrist_strike_source_v1 import solve_pick
from .search_elbow_wrist_ready_pose_v1 import P,A,INITIAL


def main():
    out=P/'depth_audit_v1';out.mkdir(exist_ok=False);cfg=P/'search_v3/close90/config.json'
    anchors=[Path(__file__).resolve(),A/'ELBOW_WRIST_READY_DEPTH_PLAN_V1.md',cfg,INITIAL,ASSET,A/'config.json',A/'assets/om_body_geometry_v3/manifest.json',P/'search_v3/report.json']
    before={str(f):sha(f) for f in anchors};save(out/'discovery_before.json',before)
    geometry=read(A/'assets/om_body_geometry_v3/manifest.json');asset=Path(geometry['asset']);save(out/'guitar_discovery_before.json',{str(asset):sha(asset)})
    config=read(cfg);paths=anchors+[asset,Path(config['initial_candidate']),Path(config['native_reference'])]+list(A.glob('*.py'))+[Path(x) for x in geometry['input_sha256']]+[Path(x['path']) for x in geometry['meshes']]
    for f in (ASSET,asset):
        x=ET.parse(f).getroot();md=(f.parent/x.find('compiler').get('meshdir')).resolve();paths +=[(md/m.get('file')).resolve() for m in x.findall('./asset/mesh')]
    assert all(sha(f)==h for f,h in before.items());inputs={str(f):sha(f) for f in paths};save(out/'inputs_before.json',inputs)
    c=EnvironmentContract(cfg);b=read(INITIAL);state=b['native_initial_state'];original=np.array(b['q_ref_rad']);fk,parents=calibrated_upper_fk(b['joint_names'],b['human_body_names'],state,original);q=c.q_ref.copy();gp,gr=pose(state['guitar_body_states'][0]);idx=np.array([b['joint_names'].index(n+'_'+ax) for n in ('R_Elbow','R_Wrist') for ax in 'xyz']);points=np.array(c.config['six_joint_strike_waypoints_G_m']);targets=np.array([point+np.array([0,0,z]) for point in [points[1],points[2],(points[1]+points[2])/2] for z in [-.006,.006]])
    rows=[];previous=q[idx].copy()
    for i,target in enumerate(targets):
        trial,error,_=solve_pick(fk,q,idx,c.lower,c.upper,q,gp+gr.apply(target),previous);previous=trial[idx];audit=source_audit(source_scene(state_from_fk(state,b['human_body_names'],trial,fk),b['human_body_names'],asset),parents)
        rows.append({'sample_index':i,'target_G_m':target.tolist(),'q6_rad':trial[idx].tolist(),'position_error_m':error,'audit':audit});print(i,'clear',audit['source_clear'],'error_mm',error*1000,flush=True)
    assert all(sha(f)==h for f,h in inputs.items());save(out/'report.json',{'input_sha256':inputs,'rows':rows,'accepted_for_native':all(row['audit']['source_clear'] and row['position_error_m']<=.002 for row in rows),'scope':'sampled complete source convex audit; not continuous or PhysX cooking certificate; no native simulation'})


if __name__=='__main__':main()
