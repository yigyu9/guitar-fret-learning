"""Six-scalar pick reach and source collision checks; no native simulation."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk
from .environment_contract_v1 import EnvironmentContract

A=ROOT/'stability_adapter_2'
B=ROOT/'docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1'
P=B.parent/'elbow_wrist_strike_v1'
CFG=B/'search_v13/upper50/config.json'
INITIAL=B/'native_upper50_v13_static/initial_values.json'


def string_segments(initial):
    state=initial['native_initial_state'];gp,gr=pose(state['guitar_body_states'][0]);names=initial['guitar_body_names']
    point=lambda n:gr.inv().apply(pose(state['guitar_body_states'][names.index(n)])[0]-gp)
    return np.array([point('G:string%d'%i) for i in range(1,7)]),np.array([point('G:string%d_end'%i) for i in range(1,7)])


def solve_pick(fk,qbase,indices,lower,upper,qref,goal,start):
    lo=np.maximum(lower[indices]+1e-6,qref[indices]-1.);hi=np.minimum(upper[indices]-1e-6,qref[indices]+1.)
    def residual(v):
        q=qbase.copy();q[indices]=v
        return np.r_[1000*(fk(q)['RH:pick'][0]-goal),.1*(v-qref[indices]),1000*np.maximum(np.linalg.norm(v.reshape(2,3),axis=1)-np.deg2rad(158),0)]
    fit=least_squares(residual,np.clip(start,lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=60,ftol=1e-8,xtol=1e-8,gtol=1e-8)
    q=qbase.copy();q[indices]=fit.x
    return q,float(np.linalg.norm(fk(q)['RH:pick'][0]-goal)),fit.nfev


def path_points(start,end,lane,kind):
    u=(lane-start[:,1])/(end[:,1]-start[:,1]);points=start+u[:,None]*(end-start)
    xs=points[:,0] if kind=='strum' else points[2:3,0]
    depth=float(points[:,2].mean())-.004
    return np.array([[xs.min()-.012,lane,depth+.024],[xs.min()-.012,lane,depth],[xs.max()+.012,lane,depth],[xs.min()-.012,lane,depth],[xs.min()-.012,lane,depth+.024]])


def trajectory(time,initial_pick,waypoints):
    times=np.array([2.,3.,3.35,3.8,4.35,5.])
    points=np.vstack([initial_pick,waypoints])
    if time<=2:return initial_pick.copy()
    index=min(np.searchsorted(times,time,side='right')-1,len(times)-2)
    alpha=np.clip((time-times[index])/(times[index+1]-times[index]),0,1)
    # Linear constant-speed crossings; near ends the real PD/rate limiter remains active.
    return (1-alpha)*points[index]+alpha*points[index+1]


def main():
    import mujoco
    from .initial_overlap import build_probe
    from .realistic_guitar_geometry_v1 import source_scene
    out=P/'source_v1';out.mkdir(exist_ok=False)
    anchors=[Path(__file__).resolve(),A/'ELBOW_WRIST_STRIKE_PLAN_V1.md',CFG,INITIAL,ASSET,A/'config.json',A/'assets/om_body_geometry_v3/manifest.json']
    discovery={str(f):sha(f) for f in anchors};save(out/'discovery_before.json',discovery)
    geometry=read(anchors[-1]);guitar=Path(geometry['asset']);save(out/'guitar_discovery_before.json',{str(guitar):sha(guitar)})
    cfg=read(CFG);paths=anchors+[guitar,Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+list(A.glob('*.py'))+[Path(f) for f in geometry['input_sha256']]+[Path(m['path']) for m in geometry['meshes']]
    for asset in (ASSET,guitar):
        xml=ET.parse(asset).getroot();md=(asset.parent/xml.find('compiler').get('meshdir')).resolve();paths +=[(md/m.get('file')).resolve() for m in xml.findall('./asset/mesh')]
    assert all(sha(f)==h for f,h in discovery.items())
    inputs={str(f):sha(f) for f in paths};save(out/'inputs_before.json',inputs)
    c=EnvironmentContract(CFG);assert all(inputs[f]==h for f,h in c.inputs.items())
    b=read(INITIAL);state=b['native_initial_state'];q0=np.array(b['q_ref_rad']);names=b['joint_names'];bodies=b['human_body_names']
    fk,parents=calibrated_upper_fk(names,bodies,state,q0);gp,gr=pose(state['guitar_body_states'][0]);start,end=string_segments(b)
    idx=np.array([names.index(n+'_'+ax) for n in ('R_Elbow','R_Wrist') for ax in 'xyz']);other=np.array([i for i in range(81) if i not in idx])
    model,data,shapes=build_probe(source_scene(state,bodies,guitar));human=[s for s in shapes if s['actor']=='human'];gshapes=[s for s in shapes if s['actor']=='guitar']
    hids={n:mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'human/'+n) for n in bodies}
    moving=lambda n:n in ('R_Elbow','R_Wrist') or n.startswith('RH:')
    def adjacent(a,b):
        chain=[]
        while a in parents:chain.append(a);a=parents[a]
        chain.append(a);steps=0
        while b not in chain and b in parents:steps+=1;b=parents[b]
        return b in chain and steps+chain.index(b)<=2
    pairs=[(h,g) for h in human if moving(h['body']) for g in gshapes]
    pairs +=[(h,g) for i,h in enumerate(human) for g in human[i+1:] if (moving(h['body']) or moving(g['body'])) and not adjacent(h['body'],g['body']) and not(h['body'].startswith('RH:') and g['body'].startswith('RH:'))]
    rows=[]
    for kind,lane in [('single',-.325),('strum',-.350),('strum',-.325),('strum',-.300)]:
        waypoints=path_points(start,end,lane,kind);label=kind+'_y'+str(round(lane*1000));previous=q0[idx].copy();samples=[]
        initial_pick=gr.inv().apply(fk(q0)['RH:pick'][0]-gp)
        for time in np.linspace(2,5,31):
            target=trajectory(float(time),initial_pick,waypoints);q,error,nfev=solve_pick(fk,q0,idx,c.lower,c.upper,q0,gp+gr.apply(target),previous);previous=q[idx]
            ps=fk(q)
            for n,i in hids.items():
                if i>=0:model.body_pos[i]=ps[n][0];model.body_quat[i]=ps[n][1].as_quat()[[3,0,1,2]]
            mujoco.mj_forward(model,data);negative=[];minimum=.05
            for h,g in pairs:
                gap=float(mujoco.mj_geomDistance(model,data,h['geom_id'],g['geom_id'],.05,None));minimum=min(minimum,gap)
                if gap< -1e-6:negative.append({'a':h['actor']+'/'+h['body'],'b':g['actor']+'/'+g['body'],'signed_gap_m':gap})
            assert np.array_equal(q[other],q0[other])
            samples.append({'time_s':float(time),'target_G_m':target.tolist(),'q6_rad':q[idx].tolist(),'position_error_m':error,'nfev':nfev,'ball_norm_deg':np.rad2deg(np.linalg.norm(q[idx].reshape(2,3),axis=1)).tolist(),'minimum_source_signed_gap_m':minimum,'negative_source_pairs':negative})
        row={'label':label,'kind':kind,'lane_G_y_m':lane,'waypoints_G_m':waypoints.tolist(),'indices':idx.tolist(),'names':[names[i] for i in idx],'samples':samples,
             'reachable':all(s['position_error_m']<=.002 and max(s['ball_norm_deg'])<160 for s in samples),'source_clear':all(not s['negative_source_pairs'] for s in samples),'other75_targets_exact':True}
        rows.append(row);print(label,'reachable',row['reachable'],'clear',row['source_clear'],'maxerr_mm',max(s['position_error_m'] for s in samples)*1000,'min_gap_mm',min(s['minimum_source_signed_gap_m'] for s in samples)*1000,flush=True)
    assert all(sha(f)==h for f,h in inputs.items())
    save(out/'report.json',{'input_sha256':inputs,'initial_pick_G_m':initial_pick.tolist(),'string_start_G_m':start.tolist(),'string_end_G_m':end.tolist(),'body_front_max_G_z_m':geometry['body_front_max_G_z_m'],'string_plane_above_max_front_m':float(start[:,2].min()-geometry['body_front_max_G_z_m']),'rows':rows,'scope':'6 scalar positional IK; no native physics, orientation guarantee or strike success; source signed gaps not calibrated penetration depth or cooking certificate; constant same-hand shape relationships excluded'})


if __name__=='__main__':main()
