"""Inspect user scalar-degree pose at the confirmed guitar body-centre coordinate."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .environment_contract_v1 import EnvironmentContract
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .underneck_initial_search import source_scene as move_guitar
from .realistic_guitar_geometry_v1 import source_scene,source_audit

USER={'Torso':[10,0,-10],'Spine':[20,0,0],'Chest':[0,20,0],'R_Thorax':[0,-10,10],'R_Shoulder':[0,35,0]}
A=ROOT/'stability_adapter_2';D=ROOT/'docs/2026-10-19/stability_adapter_2/results';P=D/'user_guided_no_left_v1'
CFG=D/'right_arm_wrap_forward_v1/search_v4/forward10mm/config.json';BASE=D/'right_arm_wrap_forward_v1/native_elbow10_static/initial_values.json'

def main():
    out=P/'diagnostic_v1';out.mkdir(exist_ok=False)
    anchors=[Path(__file__).resolve(),A/'USER_GUIDED_NO_LEFT_PLAN_V1.md',CFG,BASE,ASSET,A/'config.json',A/'assets/om_body_geometry_v3/manifest.json']
    discovery={str(p):sha(p) for p in anchors};save(out/'discovery_before.json',discovery)
    cfg=read(CFG);g=read(anchors[-1]);guitar=Path(g['asset']);save(out/'guitar_xml_discovery_before.json',{str(guitar):sha(guitar)})
    paths=anchors+[guitar,Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+list(A.glob('*.py'))+[Path(p) for p in g['input_sha256']]+[Path(m['path']) for m in g['meshes']]
    for asset in (ASSET,guitar):
        xml=ET.parse(asset).getroot();md=(asset.parent/xml.find('compiler').get('meshdir')).resolve();paths +=[(md/m.get('file')).resolve() for m in xml.findall('./asset/mesh')]
    inputs={str(p):sha(p) for p in paths};save(out/'inputs_before.json',inputs)
    c=EnvironmentContract(CFG);assert all(inputs[p]==h for p,h in c.inputs.items())
    b=read(BASE);state=b['native_initial_state'];q0=c.q_ref.copy();names,bodies=b['joint_names'],b['human_body_names'];fk,parents=calibrated_upper_fk(names,bodies,state,q0)
    q=q0.copy()
    for body,angles in USER.items():
        for axis,value in zip('xyz',angles):q[names.index(body+'_'+axis)]=np.deg2rad(value)
    d=CapsuleBodyDistance(guitar,ASSET);v=np.vstack([p[0] for p in d.pieces]);centre=(v.min(0)+v.max(0))/2
    gr=pose(state['guitar_body_states'][0])[1];bc=np.array([.175,-.05,.665]);gp=bc-gr.apply(centre);ps=fk(q)
    caps={name:d.measure(ps,name,gp,gr) for name in ('Torso','Spine','Chest','R_Hip','L_Hip','R_Thorax','R_Shoulder','R_Elbow','L_Shoulder','L_Elbow')}
    _,pred=move_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr);audit=source_audit(source_scene(pred,bodies,guitar),parents)
    for name,row in caps.items():print(name,round(row['gap_m']*1000,3),'Gsurface',row['guitar_surface_G_m'],'fraction',row['segment_fraction'],flush=True)
    print('RH:palm G',gr.inv().apply(ps['RH:palm'][0]-gp),'LH:palm G',gr.inv().apply(ps['LH:palm'][0]-gp),flush=True)
    print('audit',audit,flush=True)
    assert all(sha(p)==h for p,h in inputs.items());save(out/'diagnostic.json',{'input_sha256':inputs,'user_scalar_angles_deg':USER,'guitar_BB_centre_W_m':bc.tolist(),'guitar_actor_root_W_m':gp.tolist(),'guitar_centre_G_m':centre.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'joint_angles_rad':q.tolist(),'capsules':caps,'poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in ps.items()},'audit':audit,'scope':'source only; no native simulation'})

if __name__=='__main__':main()
