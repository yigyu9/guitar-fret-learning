"""Record visual-only acoustic upgrade with exact prior collision and body properties."""
import argparse
from pathlib import Path
from unittest.mock import patch
from .initial_pose_noise_v1 import read,save,sha,pose

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--geometry',type=Path);p.add_argument('--reference-properties',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    from .dual_music_scene_v1 import DualMusicScene
    from . import dual_music_scene_v1 as dual
    from .environment import gymapi
    from .construction_property_guard_v1 import ConstructionPropertyGuard
    from .deadline_native_v4 import _strap_scene_class
    from .environment_contract_v1 import EnvironmentContract
    from .run_joint_hold import native_state
    from .strap_trial_recording import StrapTrialRecording
    from .upper_arm_static_geometry_v1 import calibrated_upper_fk
    from .realistic_guitar_geometry_v1 import source_audit
    from .build_fixed_lower_asset import LOWER_BODIES
    from .native_contacts import body_names,read_contacts
    from .trial_settings import source_hashes
    import numpy as np
    from scipy.spatial.transform import Rotation
    from PIL import Image
    geometry=read(a.geometry) if a.geometry else None;reference=read(a.reference_properties) if a.reference_properties else None
    if bool(geometry)!=bool(reference):raise ValueError('new geometry requires reference native properties')
    original=EnvironmentContract();closure=source_hashes();closure.update(original.inputs)
    for path in Path(__file__).resolve().parent.glob('*.py'):closure[str(path)]=sha(path)
    cfg=read(a.config);closure[str(a.config)]=sha(a.config);closure[cfg['initial_candidate']]=sha(cfg['initial_candidate'])
    if geometry:
        closure[str(a.geometry)]=sha(a.geometry);closure[str(a.reference_properties)]=sha(a.reference_properties);closure.update(geometry['input_sha256']);closure[str(Path(__file__).resolve().parent/'ACOUSTIC_GUITAR_APPEARANCE_PLAN_V1.md')]=sha(Path(__file__).resolve().parent/'ACOUSTIC_GUITAR_APPEARANCE_PLAN_V1.md');closure[geometry['asset']]=geometry['asset_sha256']
        for e in geometry['meshes']:closure[e['path']]=e['sha256']
    if not all(sha(path)==h for path,h in closure.items()):raise ValueError('input SHA differs before native construction')
    save(a.out/'attempt.json',{'input_sha256':closure,'geometry':str(a.geometry) if geometry else None,'reference_properties':str(a.reference_properties) if reference else None,'music_actors':0,'policy_calls':0,'checkpoint_loads':0,'initial_noise':False,'target_rule':'initial q_ref constant; no preload/PI/runtime IK','duration_s':5,'mass_control':'exact prior native per-body mass/COM/inertia and collider properties' if geometry else 'original imported properties unchanged'})
    def serialize(names,props):
        return [{'name':n,'mass_kg':float(v.mass),'COM_body_m':[float(getattr(v.com,k)) for k in 'xyz'],'inertia_COM_kg_m2':[[float(getattr(getattr(v.inertia,i),j)) for j in 'xyz'] for i in 'xyz']} for n,v in zip(names,props)]
    class PropertyGym:
        def __init__(self,gym,owner):self.gym,self.owner=gym,owner
        def __getattr__(self,name):return getattr(self.gym,name)
        def load_asset(self,sim,folder,file,options):
            if geometry and str(Path(folder)/file)==geometry['asset']:
                options.use_mesh_materials=True
                asset=self.gym.load_asset(sim,folder,file,options)
                old_path=Path(geometry['physics_reference_asset'])
                baseline=self.gym.load_asset(sim,str(old_path.parent),old_path.name,options)
                def snapshot(value):
                    return {'names':list(self.gym.get_asset_rigid_body_names(value)),
                        'ranges':[[int(e.start),int(e.count)] for e in self.gym.get_asset_rigid_body_shape_indices(value)],
                        'shapes':[{k:getattr(e,k) for k in ('filter','friction','restitution','rolling_friction','torsion_friction','contact_offset','rest_offset')} for e in self.gym.get_asset_rigid_shape_properties(value)]}
                new,old=snapshot(asset),snapshot(baseline)
                self.owner.collision_comparison={'new':new,'reference':old,'exact':new==old}
                if new!=old:raise RuntimeError('visual addition changed native collision shape ABI/properties')
                return asset
            return self.gym.load_asset(sim,folder,file,options)
        def set_rigid_body_color(self,env,actor,*args):
            if getattr(self.owner,'visual_guitar_actor',None)==actor:return
            return self.gym.set_rigid_body_color(env,actor,*args)
        def create_actor(self,*args,**kwargs):
            actor=self.gym.create_actor(*args,**kwargs)
            if args[3]!='guitar':return actor
            self.owner.visual_guitar_actor=actor
            env=args[0];names=list(self.gym.get_actor_rigid_body_names(env,actor));props=self.gym.get_actor_rigid_body_properties(env,actor);before=serialize(names,props)
            if reference:
                target=reference['applied'];assert names==[e['name'] for e in target]
                if self.owner.initialization_complete:raise RuntimeError('mass setter after initialization')
                for value,e in zip(props,target):
                    value.mass=e['mass_kg']
                    for index,i in enumerate('xyz'):
                        setattr(value.com,i,e['COM_body_m'][index])
                        for column,j in enumerate('xyz'):setattr(getattr(value.inertia,i),j,e['inertia_COM_kg_m2'][index][column])
                requested=serialize(names,props);self.owner.property_submission_allowed=True
                try:
                    if self.gym.set_actor_rigid_body_properties(env,actor,props,False) is False:raise RuntimeError('native mass/inertia rejected')
                finally:self.owner.property_submission_allowed=False
            else:requested=before
            applied=serialize(names,self.gym.get_actor_rigid_body_properties(env,actor))
            if any(abs(e['mass_kg']-t['mass_kg'])>1e-6 or not np.allclose(e['COM_body_m'],t['COM_body_m'],atol=1e-7,rtol=1e-6) or not np.allclose(e['inertia_COM_kg_m2'],t['inertia_COM_kg_m2'],atol=1e-9,rtol=1e-5) for e,t in zip(applied,requested)):raise RuntimeError('mass/COM/inertia readback differs')
            for e in applied:
                matrix=np.asarray(e['inertia_COM_kg_m2']);assert e['mass_kg']>0 and np.isfinite(matrix).all() and np.linalg.eigvalsh(matrix).min()>0
            self.owner.mass_properties={'imported':before,'requested':requested,'applied':applied,'total_mass_kg':sum(e['mass_kg'] for e in applied),'setter_calls_before_initialization':self.owner.property_setter_calls,'property_setter_rejections':self.owner.property_setter_rejections,'rule':'exact prior native mass/COM/full inertia restored before initialization; visual geometry adds no intended physical effect'}
            return actor
    Parent=_strap_scene_class(True,True)
    class Scene(Parent):
        def _create_scene(self):
            if geometry:self.config['guitar_asset']=geometry['asset'];self.config['strap']['buttons_G_m']=geometry['strap_buttons_G_m']
            self.property_submission_allowed=False;self.property_setter_calls=0;self.property_setter_rejections=0
            old=self.gym;old.gym=ConstructionPropertyGuard(old.gym.gym,self);self.gym=PropertyGym(old,self)
            try:super()._create_scene()
            finally:self.gym=old
            props=gymapi.CameraProperties();props.width,props.height=1280,720;props.use_collision_geometry=True;camera=self.gym.create_camera_sensor(self.env,props);self.cameras['whole_body_collision']=camera
            self.gym.set_camera_location(camera,self.env,gymapi.Vec3(.9,1.8,1.15),gymapi.Vec3(-.06,0,.68))
    scene=None;recorder=None;rows=[];contacts=[]
    try:
        with patch.object(dual,'EnvironmentContract',lambda:EnvironmentContract(a.config)):scene=Scene(5.)
        save(a.out/'collision_comparison.json',scene.collision_comparison);save(a.out/'native_properties.json',scene.mass_properties);initial=native_state(scene);names=scene.human_bodies;fixed=[names.index(n) for n in ('Pelvis',)+LOWER_BODIES];qref=scene.contract.q_ref;fk,parents=calibrated_upper_fk(scene.names,names,initial,qref);audit=source_audit(scene,parents);save(a.out/'source_audit.json',audit)
        gp,gr=pose(initial['guitar_body_states'][0]);target=gp+gr.apply([0,-.34,-.02]);camera_position=target+gr.apply([.24,0,1.05])
        camera_props=gymapi.CameraProperties();camera_props.width,camera_props.height=1280,960
        guitar_camera=scene.gym.create_camera_sensor(scene.env,camera_props)
        scene.gym.set_camera_location(guitar_camera,scene.env,gymapi.Vec3(*camera_position),gymapi.Vec3(*target))
        scene.cameras['guitar_appearance']=guitar_camera
        recorder=StrapTrialRecording(scene,a.out/'media');recorder.capture();
        close=np.asarray(scene.gym.get_camera_image(scene.sim,scene.env,guitar_camera,gymapi.IMAGE_COLOR)).reshape(960,1280,4)
        Image.fromarray(close[:,:,:3]).save(a.out/'initial_guitar_appearance.png');collision=np.asarray(scene.gym.get_camera_image(scene.sim,scene.env,scene.cameras['whole_body_collision'],gymapi.IMAGE_COLOR)).reshape(720,1280,4);Image.fromarray(collision[:,:,:3]).save(a.out/'initial_collision.png')
        if not audit['source_clear']:raise RuntimeError('initial source overlap with actual scene asset')
        before=read(original.config['native_reference'])['native_initial_state'];assert all(initial['human_body_states'][i]==before['human_body_states'][i] for i in fixed)
        gp0,gr0=pose(initial['guitar_body_states'][0]);expected=scene.contract.candidate['predicted_human_poses'];errors={n:{'position_error_m':float(np.linalg.norm(bp-np.array(expected[n]['p']))),'orientation_error_deg':float(np.rad2deg((Rotation.from_quat(expected[n]['q']).inv()*br).magnitude()))} for n,(bp,br) in fk(qref).items()};assert max(e['position_error_m'] for e in errors.values())<1e-5 and max(e['orientation_error_deg'] for e in errors.values())<.01
        if np.linalg.norm(gp0-np.array(scene.contract.candidate['position_W_m']))>1e-6 or (Rotation.from_quat(scene.contract.candidate['quaternion_xyzw']).inv()*gr0).magnitude()>1e-5:raise RuntimeError('initial guitar p/q mismatch')
        assert all(v['vel']==0 for v in initial['human_dof_states']) and all(x==0 for v in initial['guitar_body_states'] for k in ('linear','angular') for x in v['vel'][k].values())
        assert abs(scene.guitar_mass-scene.mass_properties['total_mass_kg'])<1e-6
        applied={e['name']:np.array(e['COM_body_m']) for e in scene.mass_properties['applied']};cache_checks={'guitar_total_mass_exact':abs(scene.guitar_mass-scene.mass_properties['total_mass_kg'])<1e-6,'guitar_route_COM_endpoints_exact':all(np.allclose(scene.route_com[i],applied[scene.guitar_bodies[0]],atol=1e-7,rtol=0) for i in (0,-1)),'guitar_observation_COM_exact':all(np.allclose(scene.com[n],v,atol=1e-7,rtol=0) for n,v in applied.items())};assert all(cache_checks.values()),cache_checks;save(a.out/'property_cache_checks.json',cache_checks)
        save(a.out/'initial_values.json',{'native_initial_state':initial,'joint_names':scene.names,'human_body_names':names,'guitar_body_names':scene.guitar_bodies,'q_ref_rad':qref.tolist(),'PD_properties':{k:scene.pd_properties[k].tolist() for k in scene.pd_properties.dtype.names},'source_audit':audit,'native_FK_error':errors,'mass_properties':scene.mass_properties,'strap_initial':scene.strap_initial,'actual_guitar_asset':scene.config['guitar_asset'],'guitar_mass_cache_kg':scene.guitar_mass,'initial_state_write_calls':scene.initial_state_write_calls})
        mapping=body_names(scene.gym,scene.env)
        def sample():
            s=native_state(scene);q=np.array([e['pos'] for e in s['human_dof_states']]);v=np.array([e['vel'] for e in s['human_dof_states']]);gp,gr=pose(s['guitar_body_states'][0])
            assert np.isfinite(np.r_[q,v,gp,gr.as_quat()]).all() and abs(v).max()<=50 and all(s['human_body_states'][i]==initial['human_body_states'][i] for i in fixed) and not scene.forbidden_calls
            rows.append({'physics_step':scene.steps,'time_s':scene.steps/240,'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'position_change_m':float(np.linalg.norm(gp-gp0)),'rotation_change_deg':float(np.rad2deg((gr0.inv()*gr).magnitude())),'q_rad':q.tolist(),'qdot_rad_s':v.tolist(),'submitted_target_rad':scene.target.tolist()})
        sample()
        for tick in range(300):
            contacts.append({'before_control':tick,'physics_step':scene.steps,'contacts':read_contacts(scene.gym,scene.env,mapping)});scene.step(scene.contract.neutral_action());sample()
            if scene.steps%recorder.interval==0:recorder.capture()
        assert scene.property_setter_calls==int(bool(reference)) and scene.property_setter_rejections==0 and not scene.property_submission_allowed
        videos=recorder.encode();save(a.out/'report.json',{'completed':True,'physics_steps':scene.steps,'controls':300,'physics_seconds':scene.steps/240,'music_actors':0,'policy_calls':0,'checkpoint_loads':0,'forbidden_calls':scene.forbidden_calls,'strap_force_calls':scene.gym.allowed_calls,'initial_state_write_calls':scene.initial_state_write_calls,'rows':rows,'videos':videos,'source_audit':audit,'mass_properties':scene.mass_properties,'property_setter_calls':scene.property_setter_calls,'property_setter_rejections':scene.property_setter_rejections,'property_cache_checks':cache_checks,'scope':'visual-only upgrade five-second diagnostic; no music or stabilization policy; prior mass/COM/inertia and collision ABI preserved'})
    except BaseException as e:
        save(a.out/'failure.json',{'type':type(e).__name__,'message':str(e)})
        if recorder is not None:recorder.encode()
        raise
    finally:
        save(a.out/'trace.json',rows);save(a.out/'contacts.json',contacts)
        if scene is not None:scene.close()
    assert all(sha(p)==h for p,h in closure.items()),'consumed input changed';save(a.out/'inputs_verified.json',{'unchanged':True,'input_count':len(closure)})
if __name__=='__main__':main()
