"""Soft user-pose search with source geometry; accepted candidates require native verification."""
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from scipy.optimize import least_squares
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .environment_contract_v1 import EnvironmentContract
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .underneck_initial_search import source_scene as move_guitar
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .initial_overlap import build_probe,query_pairs
from .left_arm_clearance_source_v2 import clearance_function
from .diagnose_user_guided_no_left_v1 import USER,CFG,BASE,A,P


def main():
    out=P/'search_v1';out.mkdir(exist_ok=False)
    anchors=[Path(__file__).resolve(),A/'USER_GUIDED_NO_LEFT_PLAN_V1.md',CFG,BASE,ASSET,A/'config.json',A/'assets/om_body_geometry_v3/manifest.json',P/'diagnostic_v1/diagnostic.json']
    discovery={str(p):sha(p) for p in anchors};save(out/'discovery_before.json',discovery)
    cfg=read(CFG);geometry=read(anchors[6]);guitar=Path(geometry['asset']);save(out/'guitar_xml_discovery_before.json',{str(guitar):sha(guitar)})
    paths=anchors+[guitar,Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+list(A.glob('*.py'))+[Path(p) for p in geometry['input_sha256']]+[Path(m['path']) for m in geometry['meshes']]
    for asset in (ASSET,guitar):
        xml=ET.parse(asset).getroot();md=(asset.parent/xml.find('compiler').get('meshdir')).resolve();paths +=[(md/m.get('file')).resolve() for m in xml.findall('./asset/mesh')]
    inputs={str(p):sha(p) for p in paths};save(out/'inputs_before.json',inputs)
    contract=EnvironmentContract(CFG);assert all(inputs[p]==h for p,h in contract.inputs.items())
    seed=contract.candidate;b=read(BASE);state=b['native_initial_state'];q0=contract.q_ref.copy();names,bodies=b['joint_names'],b['human_body_names']
    fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0);qref=q0.copy()
    for n,angles in USER.items():
        for axis,deg in zip('xyz',angles):qref[names.index(n+'_'+axis)]=np.deg2rad(deg)
    distance=CapsuleBodyDistance(guitar,ASSET);vertices=np.vstack([v[0] for v in distance.pieces]);centre=(vertices.min(0)+vertices.max(0))/2
    gp0,gr=pose(state['guitar_body_states'][0]);bc=np.array([.175,-.05,.665]);gpuser=bc-gr.apply(centre)
    posed=fk(qref);scene=source_scene(state,bodies,guitar);model,data,shapes=build_probe(scene)
    # The compiled model is a static distance query, never a simulation or a native pose write.
    human_ids={n:mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'human/'+n) for n in bodies}
    gnames=[s['body'] for s in shapes if s['actor']=='guitar'];gids={n:mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'guitar/'+n) for n in set(gnames)}
    gstates={n:pose(s) for n,s in zip(b['guitar_body_names'],state['guitar_body_states'])}
    glocal={n:(gr.inv().apply(gstates[n][0]-gp0),gr.inv()*gstates[n][1]) for n in gids}
    human_geoms={n:[s['geom_id'] for s in shapes if s['actor']=='human' and s['body']==n] for n in bodies}
    body_geoms=[s['geom_id'] for s in shapes if s['actor']=='guitar' and s['body']=='G:body'];all_g=[s['geom_id'] for s in shapes if s['actor']=='guitar']
    def update(ps,gp):
        for n,i in human_ids.items():
            if i>=0:model.body_pos[i]=ps[n][0];model.body_quat[i]=ps[n][1].as_quat()[[3,0,1,2]]
        for n,i in gids.items():
            lp,lr=glocal[n];model.body_pos[i]=gp+gr.apply(lp);model.body_quat[i]=(gr*lr).as_quat()[[3,0,1,2]]
        mujoco.mj_forward(model,data)
    def gap(n,gs=body_geoms):
        return min((mujoco.mj_geomDistance(model,data,h,g,.5,None) for h in human_geoms[n] for g in gs),default=.5)
    def human_gap(n,m):return min(mujoco.mj_geomDistance(model,data,h,g,.5,None) for h in human_geoms[n] for g in human_geoms[m])
    body=contract.body;prox=np.array([names.index(n+'_'+ax) for n in ('R_Thorax','R_Shoulder') for ax in 'xyz']);active=np.r_[body,prox]
    rightdist=np.array([names.index(n+'_'+ax) for n in ('R_Elbow','R_Wrist') for ax in 'xyz']);left=np.array([i for i,n in enumerate(names) if n.startswith(('L_Thorax_','L_Shoulder_','L_Elbow_','L_Wrist_'))]);head=np.array([i for i,n in enumerate(names) if n.startswith(('Neck_','Head_'))])
    half=np.deg2rad(np.r_[np.full(9,15),np.full(3,20),np.full(3,30)])
    lo=np.r_[np.maximum(contract.lower[active]+1e-6,qref[active]-half),bc-[.06,.06,.04]];hi=np.r_[np.minimum(contract.upper[active]-1e-6,qref[active]+half),bc+[.06,.06,.04]]
    left_clear=clearance_function(ASSET,distance,original);rows=[];selected=[]
    userw=read(anchors[-1])['capsules']['R_Shoulder'];surface=np.array(userw['guitar_surface_G_m']);normal=np.array(userw['capsule_axis_G_m'])-surface;normal/=np.linalg.norm(normal)
    segment,radius=distance.capsules['R_Shoulder'];target_axis_G=surface+normal*(radius+.0006)
    profile=np.array(geometry['half_width_profile_t_m']);region=profile[(profile[:,0]>.25)&(profile[:,0]<.5)];t,width=region[np.argmin(region[:,1])];narrow=region[region[:,1]<=width+.015];ys=-.4+geometry['new_body_length_m']*(.5-narrow[:,0]);waist_interval=[float(ys.min()),float(ys.max())]
    for fraction in (.45,.60,.75):
        local=segment[0]+fraction*(segment[1]-segment[0])
        def upper_res(v):
            q=qref.copy();q[active]=v[:-3];ps=fk(q);gp=v[-3:]-gr.apply(centre);update(ps,gp)
            p,r=ps['R_Shoulder'];point=p+r.apply(local)
            gaps={n:gap(n) for n in ('R_Hip','L_Hip','Torso','Spine','Chest','R_Thorax','R_Shoulder')}
            return np.r_[2000*(point-gp-gr.apply(target_axis_G)),8000*(gaps['R_Shoulder']-.0006),10000*(gaps['R_Hip']-.0004),
                20000*min(gaps['L_Hip']-.0015,0),20000*np.minimum([gaps[n]-.005 for n in ('Torso','Spine','Chest','R_Thorax')],0),
                20000*min(human_gap('R_Shoulder','Torso')-.003,0),150*(v[-3:]-bc),12*(v[:-3]-qref[active])]
        fit=least_squares(upper_res,np.clip(np.r_[qref[active],bc+[0,.01,.01]],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=90,diff_step=1e-4)
        q=qref.copy();q[active]=fit.x[:-3];gp=fit.x[-3:]-gr.apply(centre)
        # Distal right arm can move independently of the rigid upper-arm cradle.
        rgoal=gp+gr.apply([.015,-.328,.09]);rl=np.maximum(contract.lower[rightdist]+1e-6,q0[rightdist]-1.2);rh=np.minimum(contract.upper[rightdist]-1e-6,q0[rightdist]+1.2)
        def right_res(v):
            z=q.copy();z[rightdist]=v;ps=fk(z);update(ps,gp)
            return np.r_[1000*(ps['RH:palm'][0]-rgoal),15*(original['RH:palm'][1].inv()*ps['RH:palm'][1]).as_rotvec(),
                15000*min(gap('R_Elbow',all_g)-.015,0),15000*min(gap('RH:palm',all_g)-.025,0),
                15000*min(human_gap('R_Elbow','Torso')-.005,0),.5*(v-q0[rightdist])]
        q[rightdist]=least_squares(right_res,np.clip(q0[rightdist],rl+1e-8,rh-1e-8),bounds=(rl,rh),max_nfev=90).x
        lgoal=gp+gr.apply([.075,.06,.06]);ll=np.maximum(contract.lower[left]+1e-6,q0[left]-1.4);lh=np.minimum(contract.upper[left]-1e-6,q0[left]+1.4)
        left_checks=['L_Shoulder','L_Elbow','L_Wrist','LH:palm','LH:thumb3','LH:index3','LH:middle3','LH:ring3','LH:pinky3'];left_checks=[n for n in left_checks if human_geoms.get(n)]
        def left_res(v):
            z=q.copy();z[left]=v;ps=fk(z);update(ps,gp)
            return np.r_[1000*(ps['LH:palm'][0]-lgoal),15*(original['LH:palm'][1].inv()*ps['LH:palm'][1]).as_rotvec(),
                20000*np.minimum([gap(n,all_g)-.015 for n in left_checks],0),20000*np.minimum(left_clear(ps)-.004,0),.1*(v-q0[left])]
        q[left]=least_squares(left_res,np.clip(q0[left],ll+1e-8,lh-1e-8),bounds=(ll,lh),max_nfev=100).x
        def head_res(v):
            z=q.copy();z[head]=v;return np.r_[100*(original['Head'][1].inv()*fk(z)['Head'][1]).as_rotvec(),.1*(v-q0[head])]
        hl=np.maximum(contract.lower[head]+1e-6,q0[head]-1.0);hh=np.minimum(contract.upper[head]-1e-6,q0[head]+1.0)
        q[head]=least_squares(head_res,np.clip(q0[head],hl+1e-8,hh-1e-8),bounds=(hl,hh),max_nfev=90).x
        q=q.astype(np.float32).astype(float);gp=gp.astype(np.float32).astype(float);ps=fk(q)
        caps={n:distance.measure(ps,n,gp,gr) for n in distance.capsules if n in ps};upper=caps['R_Shoulder']
        _,predicted=move_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr);scene=source_scene(predicted,bodies,guitar);audit=source_audit(scene,parents)
        m,d,s=build_probe(scene);left_shapes=[x for x in s if x['actor']=='guitar' or x['body'].startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:'))];near=query_pairs(m,d,left_shapes,.01)
        rerror=float(np.linalg.norm(ps['RH:palm'][0]-rgoal));lerror=float(np.linalg.norm(ps['LH:palm'][0]-lgoal));fingers=[i for i,n in enumerate(names) if n.startswith(('LH:','RH:'))]
        accepted=bool(audit['source_clear'] and not near['pairs_within_limit'] and min(w['gap_m'] for w in caps.values())>.00005 and .00005<upper['gap_m']<.004 and caps['R_Hip']['gap_m']<.004 and rerror<.025 and lerror<.015 and np.array_equal(q[fingers],q0[fingers]) and np.all(q>=contract.lower) and np.all(q<=contract.upper))
        label='upper%d'%round(100*fraction);row={'label':label,'accepted_for_native':accepted,'user_scalar_angles_deg':USER,'user_BBcentre_W_m':bc.tolist(),'guitar_BBcentre_W_m':(gp+gr.apply(centre)).tolist(),'joint_angles_rad':q.tolist(),'capsule_body':caps,'proximal_upper_arm30_witness':upper,'full_upper_arm_witness':upper,'proximal_fraction_limit':1.,'requested_axis_fraction':fraction,'contact_normal_G':normal.tolist(),'waist_G_y_interval_m':waist_interval,'waist_profile_t':float(t),'waist_half_width_m':float(width),'source_audit':audit,'left_guitar_pairs_under10mm':near,'RH_palm_target_G_m':[.015,-.328,.09],'LH_palm_target_G_m':[.075,.06,.06],'RH_target_error_m':rerror,'LH_target_error_m':lerror,'fingers42_exact':True,'fit_nfev':fit.nfev,'scope':'source only; BBcentre versus actorroot explicit; left contact0 mandatory native'}
        save(out/(label+'_audit.json'),row);rows.append(row);print(label,'accepted',accepted,'centre',row['guitar_BBcentre_W_m'],'gaps_mm',{n:round(caps[n]['gap_m']*1000,3) for n in ('R_Shoulder','R_Hip','L_Hip','Chest','Spine')},'LHnear',len(near['pairs_within_limit']),'r/lerr_mm',rerror*1000,lerror*1000,'audit',audit,flush=True)
        if accepted:
            folder=out/label;folder.mkdir();candidate={**seed,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in ps.items()},'predicted_guitar_body_states':predicted['guitar_body_states'],'right_block_cradle':row,'body_side_lean_axilla':row,'right_thigh_waist':row,'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']},'left_hand_off':{'accepted_for_native':True,'scope':'initial left-away, not runtime release'}}
            save(folder/'candidate.json',candidate);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json'),'left_wrist_tracking_off':True});selected.append({'label':label,'config':str(folder/'config.json')})
    assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'native_runs':0})

if __name__=='__main__':main()
