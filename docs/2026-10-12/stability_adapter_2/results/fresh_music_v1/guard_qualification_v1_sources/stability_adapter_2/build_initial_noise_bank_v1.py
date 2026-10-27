"""Reject unsafe proposals and preserve fresh native validated bank entries."""
import argparse
import copy
from pathlib import Path
from unittest.mock import patch
from .initial_pose_noise_v1 import RANGES,fit_hands,pose,read,save,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--count',type=int,default=4);p.add_argument('--seed',type=int,default=20261012);args=p.parse_args()
    if not 2<=args.count<=32:p.error('request 2..32 noisy candidates')
    # Native dependency must load before any Torch-dependent geometry helpers.
    from .dual_music_scene_v1 import DualMusicScene
    from . import dual_music_scene_v1 as dual
    from . import capture_isaac_gym_initial as cameras
    from .deadline_native_v4 import _strap_scene_class
    from .deadline_graphics_v1 import graphics_wrapper
    from .environment_contract_v1 import EnvironmentContract,CONFIG
    from .run_joint_hold import native_state
    from .underneck_initial_search import calibrated_fk,source_scene,FACETS
    from .initial_overlap import build_probe
    from .palm_side_source_checks import source_checks,intersection
    from .build_fixed_lower_asset import LOWER_BODIES
    from .deadline_rotation_v3 import RotationEnvelope
    import numpy as np
    from scipy.spatial.transform import Rotation
    from .face_referenced_geometry import face_geometry
    args.out.mkdir(parents=True,exist_ok=False)
    contract=EnvironmentContract();original=copy.deepcopy(contract.candidate);reference=copy.deepcopy(contract.reference)
    with patch.object(cameras,'GraphicsGym',graphics_wrapper(cameras.GraphicsGym,False)):
        base=_strap_scene_class(False,True)(5.)
    try:
        state0=native_state(base);bodies=list(base.human_bodies);q0=contract.q_ref.copy();gp=np.array(original['position_W_m']);gr=Rotation.from_quat(original['quaternion_xyzw']);fixed=[bodies.index(n) for n in ('Pelvis',)+LOWER_BODIES]
    finally:base.close()
    fk,parents=calibrated_fk(contract.names,bodies,state0,q0);envelope=RotationEnvelope();rng=np.random.default_rng(args.seed)
    def distance(a,b):
        path=[]
        while a in parents:path.append(a);a=parents[a]
        path.append(a);n=0
        while b not in path and b in parents:n+=1;b=parents[b]
        return n+path.index(b) if b in path else 99
    def audit(state,p,r):
        scene,_=source_scene(state,{'human_body_names':bodies},p,r);probe=build_probe(scene)
        meshes,overlap,cross=source_checks(probe);shapes=probe[2]
        human=[s for s in shapes if s['actor']=='human'];selfcross=[]
        for i,a in enumerate(human):
            for b in human[i+1:]:
                if not any(n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:','R_Thorax','R_Shoulder','R_Elbow','R_Wrist','RH:')) for n in (a['body'],b['body'])) or distance(a['body'],b['body'])<=2:continue
                radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
                if radius>1e-7:selfcross.append({'a':a['body'],'b':b['body'],'common_radius_m':radius})
        return {'guitar_human':overlap,'crosshands':cross,'nonadjacent_human':selfcross,'source_clear':not(overlap or cross or selfcross)}
    rows=[];entries=[];configs={};inputs=dict(contract.inputs)
    inputs[str(FACETS)]=sha(FACETS);normal_local=np.array(read(FACETS)['facets']['LH:palm']['normal_local'])
    for asset in ('humanoid_fixed_lower.xml',):
        asset_path=Path(__file__).with_name('assets')/asset;inputs[str(asset_path)]=sha(asset_path)
    # Include validated original as an explicit zero-noise distribution sample.
    for trial in range(33):
        if len(entries)>=args.count+1:break
        dp=np.zeros(3) if trial==0 else rng.uniform(RANGES['translation_lower_m'],RANGES['translation_upper_m'])
        rv=np.zeros(3) if trial==0 else rng.uniform(-1,1,3)
        q,p,r,goals,metrics=fit_hands(fk,q0,contract.names,contract.lower,contract.upper,gp,gr,dp,rv)
        if trial==0:q=q0.copy()
        row={'trial':trial,'delta_position_W_m':dp.tolist(),'world_rotvec_deg':rv.tolist(),'IK_source':metrics}
        if any(m['position_error_m']>.002 or m['orientation_error_deg']>1 for m in metrics.values()):rows.append(dict(row,rejection='IK'));continue
        if not envelope.distance(r.as_quat())['inside']:rows.append(dict(row,rejection='absolute_rotation_envelope'));continue
        z=state0['human_body_states'][bodies.index('Chest')]['pose']['p']['z']
        if np.any(p<[-.50,-.15,.65]) or np.any(p>[-.15,.15,z]):rows.append(dict(row,rejection='position_box'));continue
        source=copy.deepcopy(state0)
        for n,(bp,br) in fk(q).items():source['human_body_states'][bodies.index(n)]['pose']={'p':dict(zip('xyz',bp.tolist())),'r':dict(zip('xyzw',br.as_quat().tolist()))}
        for i,v in enumerate(q):source['human_dof_states'][i]['pos']=float(v)
        check=audit(source,p,r);row['source_audit']=check
        row['palm_up_proxy_z']=float(fk(q)['LH:palm'][1].apply(normal_local)[2])
        if row['palm_up_proxy_z']<0:rows.append(dict(row,rejection='palm_down'));continue
        if not check['source_clear']:rows.append(dict(row,rejection='source_overlap'));continue
        folder=args.out/('proposal_%02d'%trial);folder.mkdir()
        candidate={'joint_names':contract.names,'joint_angles_rad':q.tolist(),'position_W_m':p.tolist(),'quaternion_xyzw':r.as_quat().tolist(),'noise_parent':str(CONFIG),'predicted_human_poses':{n:{'p':bp.tolist(),'q':br.as_quat().tolist()} for n,(bp,br) in fk(q).items()},'noise':row,'scope':'coupled arm-only initial noise candidate; source and native audits stored separately'}
        save(folder/'candidate.json',candidate)
        proposal=read(CONFIG);proposal.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'))
        save(folder/'proposal_config.json',proposal)
        with patch.object(dual,'EnvironmentContract',lambda:EnvironmentContract(folder/'proposal_config.json')),patch.object(cameras,'GraphicsGym',graphics_wrapper(cameras.GraphicsGym,False)):
            scene=_strap_scene_class(False,True)(5.)
        try:
            actual=native_state(scene);errors={}
            for n,(tp,tr) in goals.items():
                ap,ar=pose(actual['human_body_states'][bodies.index(n)]);errors[n]={'position_error_m':float(np.linalg.norm(ap-tp)),'orientation_error_deg':float(np.rad2deg((tr.inv()*ar).magnitude()))}
            actualp,actualr=pose(actual['guitar_body_states'][0]);nativecheck=audit(actual,actualp,actualr)
            native_normal=pose(actual['human_body_states'][bodies.index('LH:palm')])[1].apply(normal_local)
            row['native_palm_up_proxy_z']=float(native_normal[2])
            valid=native_normal[2]>=0 and all(v['position_error_m']<=.002 and v['orientation_error_deg']<=1 for v in errors.values()) and nativecheck['source_clear'] and all(actual['human_body_states'][i]==state0['human_body_states'][i] for i in fixed)
            valid=valid and not scene.forbidden_calls and all(s['vel']==0 for s in actual['human_dof_states']) and all(v==0 for s in actual['guitar_body_states'] for key in ('linear','angular') for v in s['vel'][key].values())
            valid=bool(valid)
            row.update(native_palm_error=errors,native_source_audit=nativecheck,validated_native=valid,initial_state_writes=scene.initial_state_write_calls)
            save(folder/'native_audit.json',dict(row,actual=actual,human_body_names=bodies))
            if valid:
                ref=copy.deepcopy(reference);ref['native_initial_state']=actual;ref['candidate']=candidate
                save(folder/'native_reference.json',ref)
                cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'),native_reference=str(folder/'native_reference.json'),native_reference_sha256=sha(folder/'native_reference.json'),reset_randomization=True)
                save(folder/'config.json',cfg);configs[str(folder/'config.json')]=cfg
                for path in (folder/'config.json',folder/'candidate.json',folder/'native_reference.json',folder/'native_audit.json'):inputs[str(path)]=sha(path)
                entries.append(dict(row,config_path=str(folder/'config.json'),source_clear=True))
        finally:scene.close()
        rows.append(row);save(args.out/('progress_%02d.json'%trial),{'entries':len(entries),'row':row})
    save(args.out/'search.json',{'rows':rows,'accepted':len(entries),'requested_noisy':args.count,'seed':args.seed,'ranges':RANGES,'scope':'source hull proxies checked; no cooked PhysX contact-force certification'})
    if len(entries)<3 or entries[0]['trial']!=0:raise RuntimeError('need validated zero reference and at least two valid noise entries')
    save(args.out/'bank.json',{'schema':'sa2_coupled_initial_pose_bank_v1','entries':entries,'configs':configs,'input_sha256':inputs,'ranges':RANGES,'seed':args.seed,'sampling':'uniform discrete validated bank including zero reference'})
    print({'accepted':len(entries),'proposals':len(rows)},flush=True)
if __name__=='__main__':main()
