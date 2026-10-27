"""CPU counterexamples for resource routing and narrowly allowed ABI adoption."""
import copy
from types import SimpleNamespace
import unittest
from .deadline_graphics_v1 import graphics_wrapper, RENDER_APIS
from .deadline_graphics_migration_v1 import migrate_payload, digest

class Native:
    def __init__(self): self.calls=[]
    def create_sim(self,*args): self.calls.append(args);return self
    def step_graphics(self,sim): return sim
class Base:
    def __init__(self,gym):self.gym=gym
    def create_sim(self,compute,graphics,engine,params):return self.gym.create_sim(compute,0,engine,params)
    def __getattr__(self,name):return getattr(self.gym,name)

class GraphicsTests(unittest.TestCase):
    def test_training_native_forward(self):
        native=Native();wrapped=graphics_wrapper(Base,False)(native)
        params=SimpleNamespace(dt=1/240,use_gpu_pipeline=False,physx=SimpleNamespace(use_gpu=False))
        self.assertIsInstance(wrapped,Base)
        self.assertIs(wrapped.create_sim(3,0,'PHYSX',params),native)
        self.assertEqual(native.calls[0][:3],(3,-1,'PHYSX'))
        self.assertIs(native.calls[0][3],params)
        self.assertEqual(wrapped.graphics_creations[0]['forwarded_graphics_device_id'],-1)
    def test_all_training_render_lookups_rejected(self):
        wrapped=graphics_wrapper(Base,False)(Native())
        for name in RENDER_APIS:
            with self.subTest(name=name),self.assertRaises(RuntimeError):getattr(wrapped,name)
        self.assertEqual(wrapped.render_lookup_counts,{})
    def test_evaluation_native_forward_and_render(self):
        native=Native();wrapped=graphics_wrapper(Base,True)(native)
        params=SimpleNamespace(dt=1/240,use_gpu_pipeline=False,physx=SimpleNamespace(use_gpu=False))
        wrapped.create_sim(0,-1,'PHYSX',params)
        self.assertEqual(native.calls[0][:3],(0,0,'PHYSX'))
        self.assertIs(wrapped.step_graphics(native),native)
        self.assertEqual(wrapped.render_lookup_counts,{'step_graphics':1})

class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.old={'control':{'caps':[.03,.1,.3,.2]},'source_sha256':{'old.py':'oldhash'}}
        self.new=copy.deepcopy(self.old);self.new['source_sha256']['added.py']='newhash'
        self.payload={'schema':'deadline_pilot_ppo_v1','abi':self.old,'abi_sha256':digest(self.old),
            'ppo_config':{'lr':3e-5},'model':{'weights':[1,2]},'optimizer':{'adam':[3,4]},
            'rng':{'cpu':[5,6]},'updates':241,'transitions':61696,'resume_scope':'original'}
    def test_only_metadata_changes(self):
        original=copy.deepcopy(self.payload)
        result=migrate_payload(self.payload,self.new,{'lr':3e-5},['added.py'])
        self.assertEqual(self.payload,original)
        self.assertEqual(set(k for k in result if result[k]!=original[k]),{'abi','abi_sha256','resume_scope'})
        for k in ('model','optimizer','rng','updates','transitions'):self.assertIs(result[k],self.payload[k])
    def test_changed_control_rejected(self):
        self.new['control']['caps'][0]=.04
        with self.assertRaisesRegex(ValueError,'control ABI'):migrate_payload(self.payload,self.new,{'lr':3e-5},['added.py'])
    def test_changed_or_removed_old_source_rejected(self):
        for value in ('modified',None):
            new=copy.deepcopy(self.new)
            if value is None:del new['source_sha256']['old.py']
            else:new['source_sha256']['old.py']=value
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'existing source'):migrate_payload(self.payload,new,{'lr':3e-5},['added.py'])
    def test_unreviewed_addition_rejected(self):
        self.new['source_sha256']['unexpected.py']='x'
        with self.assertRaisesRegex(ValueError,'unreviewed'):migrate_payload(self.payload,self.new,{'lr':3e-5},['added.py'])
    def test_wrong_digest_or_schema_rejected(self):
        for field,value in (('abi_sha256','wrong'),('schema','other')):
            payload=dict(self.payload);payload[field]=value
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'schema/digest'):migrate_payload(payload,self.new,{'lr':3e-5},['added.py'])
    def test_changed_config_rejected(self):
        with self.assertRaisesRegex(ValueError,'configuration'):migrate_payload(self.payload,self.new,{'lr':1e-4},['added.py'])

if __name__=='__main__':unittest.main()
