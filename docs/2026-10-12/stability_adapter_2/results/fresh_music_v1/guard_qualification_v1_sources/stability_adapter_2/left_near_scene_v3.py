"""Existing OM property construction on the shoulder EFFORT scene."""
from pathlib import Path
from . import left_near_arm_effort_v3 as support
from .initial_pose_noise_v1 import read
from .environment import gymapi
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def scene_class():
    geometry=read(ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json')
    reference=read(ROOT/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/native_realistic_v2/native_properties.json')
    def serialize(names,props):
        return [{'name':n,'mass_kg':float(v.mass),'COM_body_m':[float(getattr(v.com,k)) for k in 'xyz'],'inertia_COM_kg_m2':[[float(getattr(getattr(v.inertia,i),j)) for j in 'xyz'] for i in 'xyz']} for n,v in zip(names,props)]
    class PropertyGym:
        def __init__(self,gym,owner):self.gym,self.owner=gym,owner
        def __getattr__(self,name):return getattr(self.gym,name)
        def load_asset(self,sim,folder,file,options):
            asset=self.gym.load_asset(sim,folder,file,options)
            if geometry and str(Path(folder)/file)==geometry['asset']:
                if asset is None:raise RuntimeError('OM asset load failed')
                ranges=self.gym.get_asset_rigid_body_shape_indices(asset)
                self.owner.om_shape_record={'body_names':list(self.gym.get_asset_rigid_body_names(asset)),
                    'shape_ranges':[[int(e.start),int(e.count)] for e in ranges],
                    'shape_count':int(self.gym.get_asset_rigid_shape_count(asset))}
                index=self.owner.om_shape_record['body_names'].index('G:body')
                if ranges[index].count!=geometry['collision_piece_count']:raise RuntimeError('OM native collision piece count mismatch')
            return asset
        def set_rigid_body_color(self,env,actor,*args):
            if getattr(self.owner,'om_actor',None)==actor:return
            return self.gym.set_rigid_body_color(env,actor,*args)
        def create_actor(self,*args,**kwargs):
            actor=self.gym.create_actor(*args,**kwargs)
            if args[3]!='guitar':return actor
            self.owner.om_actor=actor
            env=args[0];names=list(self.gym.get_actor_rigid_body_names(env,actor));props=self.gym.get_actor_rigid_body_properties(env,actor);before=serialize(names,props)
            if reference:
                target=reference['applied'];assert names==[e['name'] for e in target]
                if self.owner.initialization_complete:raise RuntimeError('mass setter after initialization')
                for value,e in zip(props,target):
                    ratio=e['mass_kg']/value.mass;value.mass=e['mass_kg']
                    for i in 'xyz':
                        for j in 'xyz':setattr(getattr(value.inertia,i),j,float(getattr(getattr(value.inertia,i),j))*ratio)
                requested=serialize(names,props);self.owner.property_submission_allowed=True
                try:
                    if self.gym.set_actor_rigid_body_properties(env,actor,props,False) is False:raise RuntimeError('native mass/inertia rejected')
                finally:self.owner.property_submission_allowed=False
            else:requested=before
            applied=serialize(names,self.gym.get_actor_rigid_body_properties(env,actor))
            if any(abs(e['mass_kg']-t['mass_kg'])>1e-6 or not np.allclose(e['COM_body_m'],t['COM_body_m'],atol=1e-7,rtol=1e-6) or not np.allclose(e['inertia_COM_kg_m2'],t['inertia_COM_kg_m2'],atol=1e-9,rtol=1e-5) for e,t in zip(applied,requested)):raise RuntimeError('mass/COM/inertia readback differs')
            for e in applied:
                matrix=np.asarray(e['inertia_COM_kg_m2']);assert e['mass_kg']>0 and np.isfinite(matrix).all() and np.linalg.eigvalsh(matrix).min()>0
            self.owner.mass_properties={'imported':before,'requested':requested,'applied':applied,'total_mass_kg':sum(e['mass_kg'] for e in applied),'setter_calls_before_initialization':self.owner.property_setter_calls,'property_setter_rejections':self.owner.property_setter_rejections,'rule':'COM from new geometry; inertia scaled linearly by old/new mass; not a measured hollow-wood mass distribution'}
            return actor
    Parent=support.factory(True,False)
    class Scene(Parent):
        def _create_scene(self):
            if geometry:self.config['guitar_asset']=geometry['asset'];self.config['strap']['buttons_G_m']=geometry['strap_buttons_G_m']
            self.property_submission_allowed=False;self.property_setter_calls=0;self.property_setter_rejections=0
            old=self.gym;old.gym=support.ArmEffortGuard(old.gym.gym,self);self.gym=PropertyGym(old,self)
            try:super()._create_scene()
            finally:self.gym=old
            self.gym.set_rigid_body_color(self.env,self.guitar,0,gymapi.MESH_VISUAL_AND_COLLISION,gymapi.Vec3(.65,.65,.65))
            props=gymapi.CameraProperties();props.width,props.height=1280,720;props.use_collision_geometry=True;camera=self.gym.create_camera_sensor(self.env,props);self.cameras['whole_body_collision']=camera
            self.gym.set_camera_location(camera,self.env,gymapi.Vec3(.9,1.8,1.15),gymapi.Vec3(-.06,0,.68))
    return Scene
