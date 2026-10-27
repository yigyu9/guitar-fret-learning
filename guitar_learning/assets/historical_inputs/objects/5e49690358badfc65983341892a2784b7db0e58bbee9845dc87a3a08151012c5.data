"""Change proximal preparation only, retain free-guitar geometry, test six-scalar paths."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .environment_contract_v1 import EnvironmentContract
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .elbow_wrist_strike_source_v1 import string_segments,solve_pick
from .left_arm_clearance_source_v2 import segment_gap
from .underneck_initial_search import source_scene as move_guitar

A=ROOT/'stability_adapter_2';D=ROOT/'docs/2026-10-19/stability_adapter_2/results';B=D/'user_guided_no_left_v1';P=D/'elbow_wrist_ready_pose_v1'
CFG=B/'search_v13/upper50/config.json';INITIAL=B/'native_upper50_v13_static/initial_values.json'


def waypoints(start,end):
    lane=-.325;u=(lane-start[:,1])/(end[:,1]-start[:,1]);p=start+u[:,None]*(end-start);z=float(p[:,2].mean())-.003
    return np.array([[p[:,0].min()-.008,lane,z+.019],[p[:,0].min()-.008,lane,z],[p[:,0].max()+.008,lane,z],[p[:,0].min()-.008,lane,z],[p[:,0].min()-.008,lane,z+.019]])


def trajectory(time,initial,points):
    times=np.array([2.,3.,3.3,3.65,4.05,4.4,5.]);vertices=np.vstack([initial,points[0],points[1],points[2],points[2],points[3],points[4]])
    if time<=2:return initial.copy()
    k=min(np.searchsorted(times,time,side='right')-1,len(times)-2);t=np.clip((time-times[k])/(times[k+1]-times[k]),0,1)
    return (1-t)*vertices[k]+t*vertices[k+1]


def main():
    out=P/'search_v3';out.mkdir(exist_ok=False)
    anchors=[Path(__file__).resolve(),A/'ELBOW_WRIST_READY_POSE_PLAN_V3.md',CFG,INITIAL,ASSET,A/'config.json',A/'assets/om_body_geometry_v3/manifest.json',P/'search_v2/report.json']
    discovery={str(f):sha(f) for f in anchors};save(out/'discovery_before.json',discovery)
    geometry=read(A/'assets/om_body_geometry_v3/manifest.json');asset=Path(geometry['asset']);save(out/'guitar_discovery_before.json',{str(asset):sha(asset)})
    cfg=read(CFG);paths=anchors+[asset,Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+list(A.glob('*.py'))+[Path(x) for x in geometry['input_sha256']]+[Path(x['path']) for x in geometry['meshes']]
    for f in (ASSET,asset):
        x=ET.parse(f).getroot();md=(f.parent/x.find('compiler').get('meshdir')).resolve();paths +=[(md/m.get('file')).resolve() for m in x.findall('./asset/mesh')]
    assert all(sha(f)==h for f,h in discovery.items());inputs={str(f):sha(f) for f in paths};save(out/'inputs_before.json',inputs)
    c=EnvironmentContract(CFG);assert all(inputs[f]==h for f,h in c.inputs.items())
    b=read(INITIAL);state=b['native_initial_state'];q0=np.array(b['q_ref_rad']);names=b['joint_names'];bodies=b['human_body_names'];fk,parents=calibrated_upper_fk(names,bodies,state,q0)
    gp,gr=pose(state['guitar_body_states'][0]);distance=CapsuleBodyDistance(asset,ASSET);original=fk(q0);start,end=string_segments(b);points=waypoints(start,end)
    active=np.array([names.index(n+'_'+ax) for n in ('R_Thorax','R_Shoulder','R_Elbow','R_Wrist') for ax in 'xyz']);distal=active[6:];other=np.array([i for i in range(81) if i not in active])
    half=np.r_[np.full(3,.25),np.full(3,.35),np.full(6,1.)];lo=np.maximum(c.lower[active]+1e-6,q0[active]-half);hi=np.minimum(c.upper[active]-1e-6,q0[active]+half)
    row=c.candidate['right_block_cradle'];w=row['proximal_upper_arm30_witness'];surface=np.array(w['guitar_surface_G_m']);normal=np.array(w['capsule_axis_G_m'])-surface;normal/=np.linalg.norm(normal)
    sp,sr=original['R_Shoulder'];reference=sr.inv().apply(gp+gr.apply(surface+normal*w['gap_m'])-sp)
    rows=[]
    for label,goal in [('close80',[-.12,-.60,.05]),('close90',[-.12,-.59,.06])]:
        def residual(v):
            q=q0.copy();q[active]=v;ps=fk(q);sp,sr=ps['R_Shoulder'];point=sp+sr.apply(reference)
            upper_gap=distance.measure(ps,'R_Shoulder',gp,gr)['gap_m']
            ua,ur=distance.capsules['R_Shoulder'];ta,tr=distance.capsules['Torso']
            tp,rr=ps['Torso'];self_gap=segment_gap(*(sp+sr.apply(ua)),*(tp+rr.apply(ta)))-ur-tr
            return np.r_[600*(ps['RH:pick'][0]-gp-gr.apply(points[0])),100*(ps['R_Elbow'][0]-gp-gr.apply(goal)),
                         10000*(upper_gap-.0006),100000*min(upper_gap-.00005,0),20000*min(self_gap-.003,0),
                         2*(point-gp-gr.apply(surface+normal*.0006)),4*(v-q0[active]),1000*np.maximum(np.linalg.norm(v.reshape(4,3),axis=1)-np.deg2rad(150),0)]
        fit=least_squares(residual,np.clip(q0[active],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=80)
        q=q0.copy();q[active]=fit.x;q=q.astype(np.float32).astype(float);ps=fk(q)
        caps={n:distance.measure(ps,n,gp,gr) for n in ('R_Thorax','R_Shoulder','R_Elbow','R_Hip','L_Hip','Torso','Spine','Chest')}
        initial_error=float(np.linalg.norm(ps['RH:pick'][0]-gp-gr.apply(points[0])));samples=[];previous=q[distal].copy()
        for k,target in enumerate(np.vstack([points,np.array([(points[1]+points[2])/2])])):
            trial,error,nfev=solve_pick(fk,q,distal,c.lower,c.upper,q,gp+gr.apply(target),previous);previous=trial[distal];pp=fk(trial);forearm=distance.measure(pp,'R_Elbow',gp,gr)
            samples.append({'waypoint_index':k,'target_G_m':target.tolist(),'q6_rad':trial[distal].tolist(),'position_error_m':error,'forearm_body':forearm,'ball_norm_deg':np.rad2deg(np.linalg.norm(trial[distal].reshape(2,3),axis=1)).tolist()})
        _,pred=move_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr);audit=source_audit(source_scene(pred,bodies,asset),parents)
        accepted=bool(initial_error<=.002 and .00005<caps['R_Shoulder']['gap_m']<.004 and caps['R_Thorax']['gap_m']>.00005 and caps['R_Elbow']['gap_m']>.00005 and audit['source_clear'] and all(s['position_error_m']<=.002 and s['forearm_body']['gap_m']>.00005 and max(s['ball_norm_deg'])<160 for s in samples))
        newrow={**row,'accepted_for_native':accepted,'capsule_body':caps,'proximal_upper_arm30_witness':caps['R_Shoulder'],'proximal_upper_arm45_witness':caps['R_Shoulder'],'proximal_upper_arm65_witness':caps['R_Shoulder'],'full_upper_arm_witness':caps['R_Shoulder'],'legacy_key_note':'full rigid upper-arm capsule; aliases not fractional segments','source_audit':audit}
        result={'label':label,'accepted_for_native':accepted,'initial_pick_error_m':initial_error,'initial_q_rad':q.tolist(),'initial_elbow_G_m':gr.inv().apply(ps['R_Elbow'][0]-gp).tolist(),'capsule_body':caps,'samples':samples,'source_audit':audit,'other69_exact':bool(np.array_equal(q[other],q0[other]))}
        rows.append(result);print(label,'accept',accepted,'pickerr_mm',initial_error*1000,'gapsmm',{n:round(v['gap_m']*1000,3) for n,v in caps.items()},'maxpatherrmm',max(s['position_error_m'] for s in samples)*1000,'minforearmmm',min(s['forearm_body']['gap_m'] for s in samples)*1000,flush=True)
        if accepted:
            folder=out/label;folder.mkdir();candidate={**c.candidate,'joint_angles_rad':q.tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in ps.items()},'predicted_guitar_body_states':pred['guitar_body_states'],'right_block_cradle':newrow,'body_side_lean_axilla':newrow,'right_thigh_waist':newrow,'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']}}
            save(folder/'candidate.json',candidate);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json'),'elbow_motion_amplitude_rad':0.,'six_joint_strike_waypoints_G_m':points.tolist(),'six_joint_strike_enabled':False})
    assert all(sha(f)==h for f,h in inputs.items());save(out/'report.json',{'input_sha256':inputs,'rows':rows,'waypoints_G_m':points.tolist(),'scope':'initial right12 fit; path changes6 only; source only, no actual strike/physics; waypoint checks are not continuous clearance certificate'})


if __name__=='__main__':main()
