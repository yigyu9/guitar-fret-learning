"""Place the free guitar's lower waist above the full fixed right-thigh capsule."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares, brentq
from .initial_pose_noise_v1 import read, save, sha, pose
from .upper_arm_static_geometry_v1 import ROOT, ASSET, calibrated_upper_fk, state_from_fk
from .realistic_guitar_geometry_v1 import source_scene, source_audit
from .underneck_initial_search import source_scene as move_guitar
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .environment_contract_v1 import EnvironmentContract
from .left_arm_clearance_source_v1 import clearance_function

A = ROOT/'stability_adapter_2'
B = ROOT/'docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1'
P = B.parent/'right_thigh_waist_v1'
CFG = B/'search_v7/seed0/config.json'
BASE = B/'native_elbow5_close/initial_values.json'


def main():
    contract = EnvironmentContract(CFG); cfg = read(CFG); seed = read(cfg['initial_candidate'])
    base = read(BASE); state = base['native_initial_state']; names, bodies = base['joint_names'], base['human_body_names']
    q0 = contract.q_ref.copy(); gp0, gr = pose(state['guitar_body_states'][0])
    fk, parents = calibrated_upper_fk(names,bodies,state,q0); original = fk(q0)
    geometry = read(A/'assets/om_body_geometry_v3/manifest.json'); distance = CapsuleBodyDistance(geometry['asset'],ASSET)
    profile = np.array(geometry['half_width_profile_t_m']); region = profile[(profile[:,0]>.25)&(profile[:,0]<.5)]
    t, width = region[np.argmin(region[:,1])]; waist_y = -.4+geometry['new_body_length_m']*(.5-t)
    core = region[region[:,1] <= width+.005]
    core_y = -.4+geometry['new_body_length_m']*(.5-core[:,0])
    narrow = region[region[:,1] <= width+.015]
    waist_interval = sorted((-.4+geometry['new_body_length_m']*(.5-narrow[:,0])).tolist())
    waist_interval = [waist_interval[0],waist_interval[-1]]
    left_clearance=clearance_function(ASSET,distance,original)
    right_axis = original['R_Hip'][0]-original['L_Hip'][0]; right_axis[2]=0; right_axis/=np.linalg.norm(right_axis)
    right = np.array([i for i,n in enumerate(names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
    left = np.array([i for i,n in enumerate(names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))])
    head = np.array([i for i,n in enumerate(names) if n.startswith(('Neck_','Head_'))]); active=np.r_[contract.body,right]
    paths = [Path(__file__).resolve(),A/'RIGHT_THIGH_WAIST_PLAN_V3.md',BASE,CFG,ASSET,A/'assets/om_body_geometry_v3/manifest.json',Path(geometry['asset'])]
    shared = read(A/'config.json')
    paths += [A/'config.json',ROOT/shared['guitar_asset']]
    human_xml=ET.parse(ASSET).getroot(); meshdir=(ASSET.parent/human_xml.find('compiler').get('meshdir')).resolve()
    paths += [meshdir/m.get('file') for m in human_xml.findall('./asset/mesh')]
    paths += [P/'search_v2/shift95_front30mm_audit.json']
    paths += list(A.glob('*.py'))+[Path(m['path']) for m in geometry['meshes']]
    inputs={str(p):sha(p) for p in paths}; inputs.update(contract.inputs)
    out=P/'search_v3'; out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs)
    rows=[]; selected=[]
    for number,(shift,front) in enumerate(((.098,.03),(.095,.03))):
        delta=right_axis*shift+np.array([0,front,0])
        def hip_gap(down): return min(distance.measure(original,n,gp0+delta-[0,0,down],gr)['gap_m'] for n in ('R_Hip','L_Hip'))-.0003
        down=brentq(hip_gap,-.02,.12,xtol=1e-10); delta-=np.array([0,0,down]);gp=(gp0+delta).astype(np.float32).astype(float)
        lo=np.maximum(contract.lower[active]+1e-6,q0[active]-np.r_[np.full(9,.3),np.full(12,.6)])
        hi=np.minimum(contract.upper[active]-1e-6,q0[active]+np.r_[np.full(9,.3),np.full(12,.6)])
        ej=list(active).index(names.index('R_Elbow_y')); lo[ej]=max(lo[ej],contract.lower[active[ej]]+np.deg2rad(5)+1e-6);hi[ej]=min(hi[ej],contract.upper[active[ej]]-np.deg2rad(5)-1e-6)
        # Preserve the source7 support region in the translated guitar frame.
        targets={n:gp+gr.apply(seed['right_block_cradle']['capsule_body'][n]['capsule_axis_G_m']) for n in ('R_Thorax','R_Shoulder')}
        fractions={n:seed['right_block_cradle']['capsule_body'][n]['segment_fraction'] for n in targets}
        def axis_point(poses,n):
            ep,_=distance.capsules[n];p,r=poses[n];return p+r.apply(ep[0]+fractions[n]*(ep[1]-ep[0]))
        def residual(v):
            q=q0.copy();q[active]=v;poses=fk(q)
            gaps={n:distance.measure(poses,n,gp,gr)['gap_m'] for n in ('R_Thorax','R_Shoulder','R_Elbow','Chest')}
            upper=distance.measure(poses,'R_Shoulder',gp,gr,.3)['gap_m'];el=poses['R_Elbow'][0]-poses['R_Shoulder'][0];wr=poses['R_Elbow'][0]-poses['R_Wrist'][0]
            return np.r_[1000*(axis_point(poses,'R_Thorax')-targets['R_Thorax']),1000*(axis_point(poses,'R_Shoulder')-targets['R_Shoulder']),
                6000*(gaps['R_Thorax']-.0003),6000*(upper-.002),20000*min(gaps['R_Thorax']-.0001,0),20000*min(gaps['R_Shoulder']-.0001,0),
                6000*min(gaps['R_Elbow']-.014,0),10000*min(gaps['Chest']-.001,0),10000*max(.02+el[2],0),
                1000*max(.12-el@right_axis,0),1000*max(.025-wr@right_axis,0),
                50*(poses['RH:palm'][0]-original['RH:palm'][0]-delta),8*(original['RH:palm'][1].inv()*poses['RH:palm'][1]).as_rotvec(),2*(v-q0[active])]
        fit=least_squares(residual,np.clip(np.array(read(P/'search_v2/shift95_front30mm_audit.json')['joint_angles_rad'])[active],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=120,diff_step=1e-4,ftol=1e-9,xtol=1e-9,gtol=1e-8)
        q=q0.copy();q[active]=fit.x
        def left_res(v):
            z=q.copy();z[left]=v;ps=fk(z);p,r=ps['L_Wrist'];return np.r_[1000*(p-original['L_Wrist'][0]-delta),80*(original['L_Wrist'][1].inv()*r).as_rotvec(),10000*np.minimum(left_clearance(ps)-.003,0),.1*(v-q0[left])]
        llo=np.maximum(contract.lower[left]+1e-6,q0[left]-.8);lhi=np.minimum(contract.upper[left]-1e-6,q0[left]+.8)
        q[left]=least_squares(left_res,np.clip(q0[left],llo+1e-8,lhi-1e-8),bounds=(llo,lhi),max_nfev=120).x
        def head_res(v):
            z=q.copy();z[head]=v;return np.r_[100*(original['Head'][1].inv()*fk(z)['Head'][1]).as_rotvec(),.1*(v-q0[head])]
        hlo=np.maximum(contract.lower[head]+1e-6,q0[head]-.6);hhi=np.minimum(contract.upper[head]-1e-6,q0[head]+.6)
        q[head]=least_squares(head_res,np.clip(q0[head],hlo+1e-8,hhi-1e-8),bounds=(hlo,hhi),max_nfev=120).x
        q=q.astype(np.float32).astype(float);poses=fk(q);caps={n:distance.measure(poses,n,gp,gr) for n in ('R_Thorax','R_Shoulder','R_Elbow','R_Hip','L_Hip','Chest')}
        proximal=distance.measure(poses,'R_Shoulder',gp,gr,.3)
        _,predicted=move_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr)
        audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents)
        el=poses['R_Elbow'][0]-poses['R_Shoulder'][0];wr=poses['R_Elbow'][0]-poses['R_Wrist'][0]
        lerror=float(np.linalg.norm(poses['L_Wrist'][0]-original['L_Wrist'][0]-delta));lr=float(np.rad2deg((original['L_Wrist'][1].inv()*poses['L_Wrist'][1]).magnitude()));he=float(np.rad2deg((original['Head'][1].inv()*poses['Head'][1]).magnitude()))
        frozen=np.ones(81,dtype=bool);frozen[np.r_[active,left,head]]=False
        natural={'elbow_below_m':float(-el[2]),'elbow_outward_m':float(el@right_axis),'wrist_inward_m':float(wr@right_axis),'head_error_deg':he,'left_wrist_rotation_error_deg':lr}
        waist_ok=bool(waist_interval[0] <= caps['R_Hip']['guitar_surface_G_m'][1] <= waist_interval[1] and caps['R_Hip']['guitar_surface_G_m'][0]>0 and .00005<caps['R_Hip']['gap_m']<.004)
        eligible=bool(waist_ok and audit['source_clear'] and all(c['gap_m']>=.00005 for c in caps.values()) and caps['R_Thorax']['gap_m']<.006 and .00005<proximal['gap_m']<.004 and caps['R_Elbow']['gap_m']>.012 and lerror<.005 and lr<1 and he<1 and -el[2]>.019 and el@right_axis>.12 and wr@right_axis>.025 and np.array_equal(q[frozen],q0[frozen]) and np.all(q>=contract.lower) and np.all(q<=contract.upper))
        row={'label':'shift%d_front%dmm'%(round(shift*1000),round(front*1000)),'accepted_for_native':eligible,'waist_source_region_ok':waist_ok,'waist_G_y_m':float(waist_y),'waist_G_y_interval_m':waist_interval,'waist_core_G_y_interval_m':[float(core_y.min()),float(core_y.max())],'left_arm_clearance_m':left_clearance(poses).tolist(),'waist_region_rule':'profile half-width <= minimum +15mm; concave flanks, +5mm central core reported separately','waist_profile_t':float(t),'waist_half_width_m':float(width),'guitar_delta_W_m':delta.tolist(),'human_right_axis_W':right_axis.tolist(),'joint_angles_rad':q.tolist(),'capsule_body':caps,'proximal_upper_arm30_witness':proximal,'proximal_upper_arm65_witness':proximal,'proximal_fraction_limit':.3,'source_audit':audit,'natural_geometry':natural,'left_wrist_translated_error_m':lerror,'fingers42_exact':bool(np.array_equal(q[frozen],q0[frozen])),'fit_nfev':int(fit.nfev)}
        rows.append(row);save(out/(row['label']+'_audit.json'),row);print(row['label'],'accepted',eligible,'delta_mm',delta*1000,'gaps_mm',{n:c['gap_m']*1000 for n,c in caps.items()},'Hip_y',caps['R_Hip']['guitar_surface_G_m'][1],'clear',audit['source_clear'],flush=True)
        if eligible:
            folder=out/row['label'];folder.mkdir();candidate={**seed,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':seed['quaternion_xyzw'],'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in poses.items()},'predicted_guitar_body_states':predicted['guitar_body_states'],'right_block_cradle':row,'body_side_lean_axilla':row,'right_thigh_waist':row,'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']}}
            save(folder/'candidate.json',candidate);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json'),'elbow_motion_amplitude_rad':0.0});selected.append({'label':row['label'],'config':str(folder/'config.json')});break
    assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'native_runs':0,'scope':'source waist-region seating plus full source overlap checks, not cooked support/force certification'})


if __name__=='__main__': main()
