"""Withdraw only the left arm from the current free-guitar posture; source checks only."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .environment_contract_v1 import EnvironmentContract
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .underneck_initial_search import source_scene as move_guitar
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .left_arm_clearance_source_v2 import clearance_function
from .initial_overlap import build_probe,query_pairs

A=ROOT/'stability_adapter_2';D=ROOT/'docs/2026-10-19/stability_adapter_2'
B=D/'results/right_arm_wrap_forward_v1';P=D/'results/left_hand_off_current_v1'
CFG=B/'search_v4/forward10mm/config.json';BASE=B/'native_elbow10_static/initial_values.json'

def main():
    out=P/'search_v1';out.mkdir(exist_ok=False)
    anchors=[Path(__file__).resolve(),A/'LEFT_HAND_OFF_CURRENT_PLAN_V1.md',CFG,BASE,ASSET,A/'config.json',A/'assets/om_body_geometry_v3/manifest.json']
    discovery={str(p):sha(p) for p in anchors};save(out/'discovery_before.json',discovery)
    cfg=read(CFG);geometry=read(anchors[-1]);guitar=Path(geometry['asset'])
    gd={str(guitar):sha(guitar)};save(out/'guitar_xml_discovery_before.json',gd)
    paths=anchors+[guitar,Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+list(A.glob('*.py'))
    paths += [Path(p) for p in geometry['input_sha256']]+[Path(m['path']) for m in geometry['meshes']]
    for asset in (ASSET,guitar):
        xml=ET.parse(asset).getroot();meshdir=(asset.parent/xml.find('compiler').get('meshdir')).resolve()
        paths += [(meshdir/m.get('file')).resolve() for m in xml.findall('./asset/mesh')]
    assert all(sha(p)==h for p,h in {**discovery,**gd}.items())
    inputs={str(p):sha(p) for p in paths};save(out/'inputs_before.json',inputs)
    c=EnvironmentContract(CFG);assert all(inputs[p]==h for p,h in c.inputs.items())
    seed=c.candidate;base=read(BASE);state=base['native_initial_state'];q0=c.q_ref.copy();names,bodies=base['joint_names'],base['human_body_names']
    assert np.array_equal(q0,base['q_ref_rad'])
    fk,parents=calibrated_upper_fk(names,bodies,state,q0);start=fk(q0)
    gp=np.array(seed['position_W_m']);gr=Rotation.from_quat(seed['quaternion_xyzw']);distance=CapsuleBodyDistance(guitar,ASSET)
    forward=gr.apply([0,0,1]);forward[2]=0;forward/=np.linalg.norm(forward)
    left=np.array([i for i,n in enumerate(names) if n.startswith(('L_Thorax_','L_Shoulder_','L_Elbow_','L_Wrist_'))]);assert len(left)==12
    frozen=np.ones(81,dtype=bool);frozen[left]=False
    lo=np.maximum(c.lower[left]+1e-6,q0[left]-.8);hi=np.minimum(c.upper[left]-1e-6,q0[left]+.8)
    clearance=clearance_function(ASSET,distance,start);rows=[];selected=[]
    for front_m,down_m in ((.12,.06),(.18,.08)):
        target=start['LH:palm'][0]+front_m*forward-[0,0,down_m]
        def residual(v):
            q=q0.copy();q[left]=v;ps=fk(q);p,r=ps['LH:palm']
            return np.r_[1000*(p-target),20*(start['LH:palm'][1].inv()*r).as_rotvec(),10000*np.minimum(clearance(ps)-.003,0),.05*(v-q0[left])]
        fit=least_squares(residual,np.clip(q0[left],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=160)
        q=q0.copy();q[left]=fit.x;q=q.astype(np.float32).astype(float);ps=fk(q)
        _,predicted=move_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr)
        scene=source_scene(predicted,bodies,geometry['asset']);audit=source_audit(scene,parents)
        model,data,shapes=build_probe(scene)
        active=[s for s in shapes if s['actor']=='guitar' or s['body'].startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:'))]
        proximity=query_pairs(model,data,active,.02);caps={n:distance.measure(ps,n,gp,gr) for n in distance.capsules if n in ps}
        error=float(np.linalg.norm(ps['LH:palm'][0]-target));clear=clearance(ps)
        accepted=bool(audit['source_clear'] and not proximity['pairs_within_limit'] and error<.005 and np.all(clear>=.003)
            and min(v['gap_m'] for v in caps.values())>=.00005 and np.array_equal(q[frozen],q0[frozen]) and np.all(q>=c.lower) and np.all(q<=c.upper))
        label='away%dmm'%round(front_m*1000)
        row={'label':label,'accepted_for_native':accepted,'joint_angles_rad':q.tolist(),'left_palm_goal_W_m':target.tolist(),
             'requested_forward_m':front_m,'requested_down_m':down_m,'forward_unit_W':forward.tolist(),'left_palm_error_m':error,
             'left_palm_delta_W_m':(ps['LH:palm'][0]-start['LH:palm'][0]).tolist(),'left_arm_human_clearance_m':clear.tolist(),
             'frozen69_initial_q_exact':bool(np.array_equal(q[frozen],q0[frozen])),'left12_delta_rad':{names[i]:float(q[i]-q0[i]) for i in left},
             'source_audit':audit,'source_left_guitar_pairs_under20mm':proximity,'fresh_capsule_body':caps,
             'scope':'source proxy checks; left geoms outside20mm truncated query, native contact0 remains mandatory'}
        rows.append(row);save(out/(label+'_audit.json'),row);print(label,'accepted',accepted,'palm_error_mm',error*1000,'near_pairs',len(proximity['pairs_within_limit']),'sourceclear',audit['source_clear'],flush=True)
        if accepted:
            folder=out/label;folder.mkdir();candidate={**seed,'joint_angles_rad':q.tolist(),
                'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in ps.items()},
                'predicted_guitar_body_states':predicted['guitar_body_states'],'left_hand_off':row}
            # The three right-support metadata records remain valid: right/trunk/guitar are unchanged.
            save(folder/'candidate.json',candidate);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),
                'initial_candidate_sha256':sha(folder/'candidate.json'),'left_wrist_tracking_off':True})
            selected.append({'label':label,'config':str(folder/'config.json')})
    assert all(sha(p)==h for p,h in inputs.items())
    save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'native_runs':0,'scope':'left-away initialization, not runtime release; right/trunk/G initial pose preserved'})

if __name__=='__main__':main()
