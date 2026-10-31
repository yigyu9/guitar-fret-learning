"""Keep fitted user torso/right cradle; route left forearm in front of the neck."""
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .environment_contract_v1 import EnvironmentContract
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance,segment_convex
from .underneck_initial_search import source_scene as move_guitar
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .initial_overlap import build_probe,query_pairs
from .left_arm_clearance_source_v2 import clearance_function
from .face_referenced_geometry import face_geometry
from .diagnose_user_guided_no_left_v1 import USER,CFG,BASE,A,P


def left_certificate(model,data,shapes):
    meshes={s['geom_id']:face_geometry(model,data,s) for s in shapes}
    guitar=[s for s in shapes if s['actor']=='guitar'];planes={g['geom_id']:ConvexHull(meshes[g['geom_id']].vertices).equations for g in guitar}
    pairs=[];checked=0
    for h in [s for s in shapes if s['actor']=='human' and s['body'].startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:'))]:
        i=h['geom_id'];kind=model.geom_type[i];a=meshes[i]
        if kind==mujoco.mjtGeom.mjGEOM_CAPSULE:
            axis=data.geom_xmat[i].reshape(3,3)[:,2]*model.geom_size[i,1];ends=np.array([data.geom_xpos[i]-axis,data.geom_xpos[i]+axis]);radius=model.geom_size[i,0];bounds=np.array([ends.min(0)-radius,ends.max(0)+radius])
        elif kind==mujoco.mjtGeom.mjGEOM_SPHERE:
            ends=data.geom_xpos[i][None,:];radius=model.geom_size[i,0];bounds=np.array([ends[0]-radius,ends[0]+radius])
        else:ends=None;radius=None;bounds=a.bounds;ap=ConvexHull(a.vertices).equations
        for g in guitar:
            b=meshes[g['geom_id']];bp=planes[g['geom_id']];checked+=1
            delta=np.maximum(np.maximum(bounds[0]-b.bounds[1],b.bounds[0]-bounds[1]),0)
            if np.linalg.norm(delta)>=.01:continue
            if ends is not None:separation=(ends@bp[:,:3].T+bp[:,3]-radius).min(0).max()
            else:separation=max((a.vertices@bp[:,:3].T+bp[:,3]).min(0).max(),(b.vertices@ap[:,:3].T+ap[:,3]).min(0).max())
            if ends is not None and separation<.01:
                segment=ends if len(ends)==2 else np.repeat(ends,2,axis=0)
                separation=segment_convex(*segment,b.vertices,bp)[0]-radius
            if separation<.01:pairs.append({'human':h['body'],'guitar':g['body'],'separation_lower_bound_m':float(separation)})
    return {'checked_pairs':checked,'uncertified_pairs':pairs,'margin_m':.01,'scope':'source primitive capsules/spheres exact support and AABB; face-used guitar convex hulls; mesh/box face-plane lower bound; native LEFTcontact0 still required'}


def main():
    out=P/'search_v8';out.mkdir(exist_ok=False)
    oldpaths=[P/'search_v7'/(name+'_audit.json') for name in ('upper50','upper65')]
    anchors=[Path(__file__).resolve(),A/'USER_GUIDED_NO_LEFT_PLAN_V8.md',CFG,BASE,ASSET,A/'config.json',A/'assets/om_body_geometry_v3/manifest.json']+oldpaths
    discovery={str(p):sha(p) for p in anchors};save(out/'discovery_before.json',discovery)
    cfg=read(CFG);geometry=read(anchors[6]);guitar=Path(geometry['asset']);gd={str(guitar):sha(guitar)};save(out/'guitar_xml_discovery_before.json',gd)
    paths=anchors+[guitar,Path(cfg['initial_candidate']),Path(cfg['native_reference'])]+list(A.glob('*.py'))+[Path(p) for p in geometry['input_sha256']]+[Path(m['path']) for m in geometry['meshes']]
    for asset in (ASSET,guitar):
        xml=ET.parse(asset).getroot();md=(asset.parent/xml.find('compiler').get('meshdir')).resolve();paths +=[(md/m.get('file')).resolve() for m in xml.findall('./asset/mesh')]
    assert all(sha(p)==h for p,h in {**discovery,**gd}.items());inputs={str(p):sha(p) for p in paths};save(out/'inputs_before.json',inputs)
    c=EnvironmentContract(CFG);assert all(inputs[p]==h for p,h in c.inputs.items())
    b=read(BASE);state=b['native_initial_state'];q0=c.q_ref.copy();names,bodies=b['joint_names'],b['human_body_names'];fk,parents=calibrated_upper_fk(names,bodies,state,q0)
    original=fk(q0);gp0,gr=pose(state['guitar_body_states'][0]);distance=CapsuleBodyDistance(guitar,ASSET);v=np.vstack([v[0] for v in distance.pieces]);centre=(v.min(0)+v.max(0))/2
    m,d,s=build_probe(source_scene(state,bodies,guitar));neck=[]
    for shape in s:
        if shape['actor']=='guitar' and shape['body']=='guitar':
            verts=gr.inv().apply(face_geometry(m,d,shape).vertices-gp0);neck.append((verts,ConvexHull(verts).equations))
    left=np.array([i for i,n in enumerate(names) if n.startswith(('L_Thorax_','L_Shoulder_','L_Elbow_','L_Wrist_'))]);mask=np.ones(81,dtype=bool);mask[left]=False;rows=[];selected=[]
    clearance=clearance_function(ASSET,distance,original)
    for oldpath in oldpaths:
        prior=read(oldpath);qbase=np.array(prior['joint_angles_rad']);gp=np.array(prior['guitar_BBcentre_W_m'])-gr.apply(centre);goal=gp+gr.apply([.025,.10,.12]);q=qbase.copy()
        lo=np.maximum(c.lower[left]+1e-6,q0[left]-1.5);hi=np.minimum(c.upper[left]-1e-6,q0[left]+1.5)
        def residual(v):
            z=qbase.copy();z[left]=v;ps=fk(z);p,r=ps['LH:palm'];ep,radius=distance.capsules['L_Elbow'];points=gr.inv().apply(ps['L_Elbow'][0]+ps['L_Elbow'][1].apply(ep)-gp)
            neckgap=min(segment_convex(*points,verts,planes)[0]-radius for verts,planes in neck)
            elbow=gr.inv().apply(ps['L_Elbow'][0]-gp)
            return np.r_[1000*(p-goal),1*(original['LH:palm'][1].inv()*r).as_rotvec(),15000*min(neckgap-.017,0),
                20000*np.minimum(clearance(ps)-.004,0),10*(elbow-[-.17,-.03,.12]),1000*np.maximum(np.linalg.norm(v.reshape(4,3),axis=1)-np.deg2rad(150),0),2*(v-q0[left])]
        fit=least_squares(residual,np.clip(qbase[left],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=150,diff_step=1e-4)
        q[left]=fit.x;q=q.astype(np.float32).astype(float);gp=gp.astype(np.float32).astype(float);ps=fk(q)
        caps={n:distance.measure(ps,n,gp,gr) for n in distance.capsules if n in ps};_,pred=move_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr);scene=source_scene(pred,bodies,guitar);audit=source_audit(scene,parents);m,d,s=build_probe(scene);cert=left_certificate(m,d,s)
        err=float(np.linalg.norm(ps['LH:palm'][0]-goal));ball_norms=np.rad2deg(np.linalg.norm(q[left].reshape(4,3),axis=1))
        accepted=bool(np.all(ball_norms<160) and audit['source_clear'] and not cert['uncertified_pairs'] and min(w['gap_m'] for w in caps.values())>.00005 and err<.02 and np.array_equal(q[mask],qbase[mask]) and np.all(q>=c.lower) and np.all(q<=c.upper))
        label=prior['label'];row={**prior,'proximal_upper_arm45_witness':prior['full_upper_arm_witness'],'proximal_upper_arm65_witness':prior['full_upper_arm_witness'],'legacy_key_note':'30/45/65 are aliases of full-upper witness, not fractions','accepted_for_native':accepted,'joint_angles_rad':q.tolist(),'capsule_body':caps,'source_audit':audit,'face_used_left_10mm_certificate':cert,'LH_target_error_m':err,'LH_palm_target_G_m':[.025,.10,.12],'frozen69_from_V7_exact':True,'raw_MuJoCo_proximity_scope':'inherited V7 left geometry diagnostic; fresh exact source certificate is current','left_fit_nfev':fit.nfev,'left_ball_rotation_vector_norm_deg':ball_norms.tolist(),'left_ball_principal_safe':bool(np.all(ball_norms<160)),'scope':'source corrected exact primitive clearance, no native result yet'}
        save(out/(label+'_audit.json'),row);rows.append(row);print(label,'accepted',accepted,'LHerror_mm',err*1000,'uncertified',cert['uncertified_pairs'],'audit',audit,flush=True)
        if accepted:
            folder=out/label;folder.mkdir();candidate={**c.candidate,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in ps.items()},'predicted_guitar_body_states':pred['guitar_body_states'],'right_block_cradle':row,'body_side_lean_axilla':row,'right_thigh_waist':row,'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']},'left_hand_off':{'accepted_for_native':True,'scope':'t0 separated left arm; trackingOFF'}}
            save(folder/'candidate.json',candidate);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json'),'left_wrist_tracking_off':True});selected.append({'label':label,'config':str(folder/'config.json')})
    assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'native_runs':0,'scope':'2 left-route proposals retaining V7 torso/right/G; no repeated upper optimization'})

if __name__=='__main__':main()
