"""Near-bridge six-scalar reach with an analytic forearm/body clearance task."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares
from . import elbow_wrist_strike_source_v1 as parent
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ASSET,calibrated_upper_fk,state_from_fk
from .environment_contract_v1 import EnvironmentContract
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .realistic_guitar_geometry_v1 import source_scene,source_audit

A,P,CFG,INITIAL=parent.A,parent.P,parent.CFG,parent.INITIAL


def main():
    out=P/'source_v2';out.mkdir(exist_ok=False)
    anchors=[Path(__file__).resolve(),A/'ELBOW_WRIST_STRIKE_PLAN_V2.md',CFG,INITIAL,ASSET,A/'config.json',A/'assets/om_body_geometry_v3/manifest.json',P/'source_v1/report.json']
    before={str(f):sha(f) for f in anchors};save(out/'discovery_before.json',before)
    g=read(A/'assets/om_body_geometry_v3/manifest.json');asset=Path(g['asset']);save(out/'guitar_discovery_before.json',{str(asset):sha(asset)})
    cfg=read(CFG);paths=anchors+[asset,Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+list(A.glob('*.py'))+[Path(f) for f in g['input_sha256']]+[Path(m['path']) for m in g['meshes']]
    for f in (ASSET,asset):
        xml=ET.parse(f).getroot();md=(f.parent/xml.find('compiler').get('meshdir')).resolve();paths +=[(md/m.get('file')).resolve() for m in xml.findall('./asset/mesh')]
    assert all(sha(f)==h for f,h in before.items());inputs={str(f):sha(f) for f in paths};save(out/'inputs_before.json',inputs)
    c=EnvironmentContract(CFG);b=read(INITIAL);state=b['native_initial_state'];names=b['joint_names'];bodies=b['human_body_names'];q0=np.array(b['q_ref_rad']);fk,parents=calibrated_upper_fk(names,bodies,state,q0)
    gp,gr=pose(state['guitar_body_states'][0]);idx=np.array([names.index(n+'_'+ax) for n in ('R_Elbow','R_Wrist') for ax in 'xyz']);other=np.array([i for i in range(81) if i not in idx])
    distance=CapsuleBodyDistance(asset,ASSET);start,end=parent.string_segments(b);initial_pick=gr.inv().apply(fk(q0)['RH:pick'][0]-gp)
    ps=fk(q0);maximum=float(np.linalg.norm(ps['R_Wrist'][0]-ps['R_Elbow'][0])+np.linalg.norm(ps['RH:pick'][0]-ps['R_Wrist'][0]))
    baseline=distance.measure(ps,'R_Elbow',gp,gr);rows=[]
    lo=np.maximum(c.lower[idx]+1e-6,q0[idx]-1);hi=np.minimum(c.upper[idx]-1e-6,q0[idx]+1)
    for kind,lane in [('single',-.360),('strum',-.375),('strum',-.365)]:
        waypoints=parent.path_points(start,end,lane,kind);previous=q0[idx].copy();samples=[]
        for time in np.linspace(2,5,16):
            target=parent.trajectory(float(time),initial_pick,waypoints);world=gp+gr.apply(target)
            def residual(v):
                q=q0.copy();q[idx]=v;ps=fk(q);gap=distance.measure(ps,'R_Elbow',gp,gr)['gap_m']
                return np.r_[1000*(ps['RH:pick'][0]-world),20000*min(gap-.00005,0),.1*(v-q0[idx]),1000*np.maximum(np.linalg.norm(v.reshape(2,3),axis=1)-np.deg2rad(158),0)]
            fit=least_squares(residual,np.clip(previous,lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=60)
            q=q0.copy();q[idx]=fit.x;previous=fit.x;ps=fk(q);gap=distance.measure(ps,'R_Elbow',gp,gr)['gap_m']
            error=float(np.linalg.norm(ps['RH:pick'][0]-world));assert np.array_equal(q[other],q0[other])
            samples.append({'time_s':float(time),'target_G_m':target.tolist(),'q6_rad':q[idx].tolist(),'position_error_m':error,'forearm_body_gap_m':gap,'ball_norm_deg':np.rad2deg(np.linalg.norm(q[idx].reshape(2,3),axis=1)).tolist(),'radial_error_lower_bound_m':float(max(0,np.linalg.norm(world-ps['R_Elbow'][0])-maximum))})
        reachable=all(s['position_error_m']<=.002 and max(s['ball_norm_deg'])<160 for s in samples);clear=all(s['forearm_body_gap_m']>=.000049 for s in samples)
        audits=[]
        if reachable and clear:
            for k in (0,5,7,9,12,15):
                q=q0.copy();q[idx]=samples[k]['q6_rad'];audit=source_audit(source_scene(state_from_fk(state,bodies,q,fk),bodies,asset),parents);audits.append({'sample_index':k,'audit':audit})
        row={'label':kind+'_y'+str(round(lane*1000)),'kind':kind,'lane_G_y_m':lane,'waypoints_G_m':waypoints.tolist(),'indices':idx.tolist(),'samples':samples,'reachable':reachable,'analytic_forearm_clear':clear,'sampled_full_source_audits':audits,'accepted_for_native':bool(reachable and clear and audits and all(x['audit']['source_clear'] for x in audits)),'other75_targets_exact':True}
        rows.append(row);print(row['label'],'reachable',reachable,'forearmclear',clear,'accepted',row['accepted_for_native'],'maxerr_mm',max(s['position_error_m'] for s in samples)*1000,flush=True)
    assert all(sha(f)==h for f,h in inputs.items());save(out/'report.json',{'input_sha256':inputs,'initial_pick_G_m':initial_pick.tolist(),'maximum_fixed_elbow_pick_radius_m':maximum,'baseline_analytic_forearm_body':baseline,'rows':rows,'scope':'source-only geometry/reach; initial fixed proximal frame; sampled full audit is not continuous clearance or native collision certificate'})


if __name__=='__main__':main()
