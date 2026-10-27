"""CPU fakes verify graphics suppression and original Guard delegation only."""
import copy
import json
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from guitar_learning.runtime.headless_session import HeadlessPreparedSession, _headless_construction, _headless_guard_type, _headless_scene_type, _physics_signature, headless_session_factory
from guitar_learning.runtime.prepared_reset_v1 import PreparedSession


def parameters():
    return NS(dt=1/240,substeps=1,up_axis=2,gravity=NS(x=0.,y=0.,z=-9.81),
        use_gpu_pipeline=False,physx=NS(use_gpu=False,num_threads=8,solver_type=1,
        num_position_iterations=4,num_velocity_iterations=2,contact_collection=2,
        contact_offset=.002,rest_offset=0.,max_depenetration_velocity=10.))


class RawGym:
    def __init__(self): self.calls=[]
    def create_sim(self,c,g,e,p):
        self.calls.append(('create_sim',c,g,e,copy.deepcopy(p)))
        return 'native-sim'
    def simulate(self,sim): self.calls.append(('simulate',sim))


class OriginalGuard:
    def __init__(self,gym,owner): self.gym,self.owner=gym,owner
    def __getattr__(self,name):
        if name == 'create_sim': return lambda c,g,e,p:self.gym.create_sim(c,0,e,p)
        if name.startswith(('apply_','set_')):
            def forbidden(*a,**kw):
                self.owner.forbidden_calls.append(name)
                raise RuntimeError('original restriction: '+name)
            return forbidden
        return getattr(self.gym,name)


def modules():
    scene_module=NS(Guard=OriginalGuard)
    class OriginalScene:
        def __init__(self,config):
            self.config=config
            self.forbidden_calls=[]
            self.gym=scene_module.Guard(RawGym(),self)
            self.sim=self.gym.create_sim(2,7,'physx',parameters())
            self.cameras={}
            self.camera_spec={'whole_body':([0.,3.1,.8],[0.,0.,.72])}
            for key,value in self.camera_spec.items():
                self.cameras[key]=self.gym.create_camera_sensor(None,value)
            self.steps=0
            self.closed=False
        def close(self): self.closed=True
    return NS(Scene=OriginalScene),scene_module


class HeadlessTests(unittest.TestCase):
    def test_sim_physics_preserved_except_explicit_threads(self):
        owner=NS();raw=RawGym();p=parameters();before=_physics_signature(p)
        cls=_headless_guard_type(OriginalGuard,1)
        self.assertTrue(issubclass(cls,OriginalGuard))
        guard=cls(raw,owner)
        self.assertEqual(guard.create_sim(2,7,'physx',p),'native-sim')
        self.assertEqual(raw.calls[0][1:4],(2,-1,'physx'))
        self.assertEqual(p.physx.num_threads,1)
        self.assertEqual(_physics_signature(p),before)
        self.assertEqual(owner.headless_configuration['physx_num_threads_before'],8)
        json.dumps(owner.headless_configuration,allow_nan=False)

    def test_camera_loop_has_no_dummy_success(self):
        runtime,scene=modules()
        original_scene,original_guard=runtime.Scene,scene.Guard
        with _headless_construction(runtime,scene,1):
            instance=runtime.Scene({'unchanged':True})
            self.assertEqual(instance.cameras,{})
            self.assertEqual(instance.camera_spec,{})
            self.assertIn('whole_body',instance.declared_camera_spec)
            self.assertEqual(instance.camera_status,'disabled')
            self.assertEqual(len(instance.gym.gym.calls),1)
        self.assertIs(runtime.Scene,original_scene)
        self.assertIs(scene.Guard,original_guard)
        # Wrappers attached to the live scene still reject graphics after the
        # process-local construction patches have been removed.
        for name in ('create_camera_sensor','set_camera_location','get_camera_image',
                     'step_graphics','render_all_camera_sensors','create_viewer',
                     'start_access_image_tensors'):
            with self.subTest(name=name),self.assertRaisesRegex(RuntimeError,'disabled'):
                getattr(instance.gym,name)()

    def test_original_guard_force_state_restrictions_and_physics_delegated(self):
        runtime,scene=modules()
        with _headless_construction(runtime,scene,1): instance=runtime.Scene({})
        for name in ('apply_body_force','set_actor_rigid_body_states','set_actor_dof_properties'):
            with self.subTest(name=name),self.assertRaisesRegex(RuntimeError,'original restriction'):
                getattr(instance.gym,name)()
        self.assertEqual(len(instance.forbidden_calls),3)
        instance.gym.simulate(instance.sim)
        self.assertEqual(instance.gym.gym.calls[-1],('simulate','native-sim'))

    def test_construction_failure_restores_both_bindings(self):
        runtime,scene=modules();original_scene,original_guard=runtime.Scene,scene.Guard
        with self.assertRaisesRegex(RuntimeError,'constructor failure'):
            with _headless_construction(runtime,scene,1):
                raise RuntimeError('constructor failure')
        self.assertIs(runtime.Scene,original_scene)
        self.assertIs(scene.Guard,original_guard)

    def test_session_retains_prepared_superclass_and_metadata(self):
        runtime,scene=modules()
        original_scene,original_guard=runtime.Scene,scene.Guard
        config={'exact':'original config'}
        def prepared_init(self,cfg,out):
            self.scene=runtime.Scene(cfg)
            self.prepared_reset_description={'unchanged_prepared_metadata':True}
        with patch('guitar_learning.runtime.headless_session._native_modules',return_value=(runtime,scene)), \
             patch.object(PreparedSession,'__init__',prepared_init):
            session=headless_session_factory(config,'unused')
        self.assertIs(session.scene.config,config)
        self.assertIsInstance(session,PreparedSession)
        self.assertEqual(session.scene.steps,0)
        self.assertTrue(session.prepared_reset_description['unchanged_prepared_metadata'])
        self.assertEqual(session.headless_description['camera_count'],0)
        json.dumps(session.prepared_reset_description,allow_nan=False)
        self.assertIs(runtime.Scene,original_scene);self.assertIs(scene.Guard,original_guard)
        with self.assertRaisesRegex(RuntimeError,'disabled'):session.render()
        native_scene=session.scene;session.close();self.assertTrue(native_scene.closed)

    def test_invalid_threads_fail_before_native_import_and_gpu_params_rejected(self):
        for invalid in (True,0,-1,1.5):
            with patch('guitar_learning.runtime.headless_session._native_modules') as native:
                with self.assertRaises(ValueError):HeadlessPreparedSession({},'unused',physics_threads=invalid)
                native.assert_not_called()
        guard=_headless_guard_type(OriginalGuard,1)(RawGym(),NS())
        p=parameters();p.physx.use_gpu=True
        with self.assertRaisesRegex(ValueError,'CPU'):guard.create_sim(0,0,'physx',p)
        self.assertEqual(p.physx.num_threads,8)

if __name__=='__main__':unittest.main()
