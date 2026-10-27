"""Capture one camera frame from a deterministic Isaac Gym PhysX replay."""
import hashlib, json, os, sys
from pathlib import Path
import numpy as np
ROOT=Path('/home/ajou/yigyu/3'); REF=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/axis_00'
sys.path.insert(0,str(ROOT))
from stability_adapter_2.self_collision_environment import SelfCollisionEnvironment
from stability_adapter_2.environment import gymapi
from stability_adapter_2.palm_side_feedback import context,SETTINGS
from stability_adapter_2.palm_normal_task import prepare
from stability_adapter_2.run_physx_contacts import native_state
from stability_adapter_2.run_initialization import snapshot
from stability_adapter_2.build_fixed_lower_asset import read as read_settings

def read(p): return json.loads(Path(p).read_text())
def save(p,v):
 p=Path(p); t=Path(str(p)+'.tmp'); t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n'); os.replace(t,p)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class GraphicsGym:
 def __init__(self,g): self.g=g
 def __getattr__(self,n): return getattr(self.g,n)
 def create_sim(self,c,g,e,p): return self.g.create_sim(c,0,e,p)
class OneSensorEnvironment(SelfCollisionEnvironment):
 def __init__(self,settings,shift):
  acquire=gymapi.acquire_gym; gymapi.acquire_gym=lambda:GraphicsGym(acquire())
  try: super().__init__(settings,shift)
  finally: gymapi.acquire_gym=acquire
 def _create_scene(self):
  super()._create_scene()
  for actor,names in ((self.human,self.human_bodies),(self.guitar,self.guitar_bodies)):
   for i,n in enumerate(names):
    rgb=(.12,.65,.3) if n.startswith('LH:') else ((.8,.12,.5) if n.startswith('RH:') else ((.12,.3,.8) if actor==self.guitar else (.7,.7,.7)))
    self.gym.set_rigid_body_color(self.env,actor,i,gymapi.MESH_VISUAL_AND_COLLISION,gymapi.Vec3(*rgb))
  p=gymapi.CameraProperties(); p.width,p.height,p.horizontal_fov=1200,900,45.0
  self.camera=self.gym.create_camera_sensor(self.env,p)
  if self.camera<0: raise RuntimeError('camera creation failed')
  self.gym.set_camera_location(self.camera,self.env,gymapi.Vec3(0.0,3.40,1.38),gymapi.Vec3(0.0,-0.18,0.72))
def main():
 if len(sys.argv)!=3: raise SystemExit('usage: capture_physx_frame.py STEP OUTPUT_PNG')
 step=int(sys.argv[1]); image=Path(sys.argv[2]).resolve()
 if step<0 or step>1200 or step%60: raise ValueError('step must be 0..1200 in multiples of 60')
 image.parent.mkdir(parents=True,exist_ok=True)
 report=read(REF/'report.json'); controls=read(REF/'controls.json'); ctx=prepare(context()); arm=ctx['indices']; q0=ctx['q0'][arm]
 target=np.asarray(controls[0]['final_target_rad'],dtype=np.float32)
 if not np.array_equal(target,q0.astype(np.float32)+np.asarray(report['bias_rad'],dtype=np.float32)): raise AssertionError('arm target mismatch')
 env=OneSensorEnvironment(read(SETTINGS),ctx['shift'])
 try:
  initial=native_state(env)
  if initial!=ctx['seed']: raise AssertionError('initial axis_00 seed mismatch')
  offsets=np.zeros(66,dtype=np.float32)
  for idx,d in zip(arm,target-q0.astype(np.float32)): offsets[list(env.main_indices).index(idx)]=d
  env.set_main_offsets(offsets)
  if not np.array_equal(env.target[arm],target): raise AssertionError('applied target mismatch')
  for _ in range(step): env.step_physics()
  sample=snapshot(env)
  baseline=ROOT/'docs/2026-10-12/stability_adapter_2/results/isaac_gym_crash_diagnosis_v1/trace.jsonl'
  with baseline.open() as f: expected=json.loads(next(line for i,line in enumerate(f) if i==step))['sample']
  if sample!=expected: raise AssertionError(f'physics trace mismatch at step {step}')
  before=native_state(env); env.gym.step_graphics(env.sim); env.gym.render_all_camera_sensors(env.sim)
  env.gym.write_camera_image_to_file(env.sim,env.env,env.camera,gymapi.IMAGE_COLOR,str(image))
  result={'status':'one_native_isaac_gym_render_after_physics','physics_engine':'PhysX','physics_device':'CPU','gpu_pipeline':False,
   'physics_step':step,'simulation_time_s':step/env.config['physics_hz'],'seed_matches_axis_00':True,'saved_arm_target_applied':True,
   'sample_matches_baseline_trace_exactly':True,'camera_created_before_physics':True,'render_calls_during_physics':0,
   'one_render_per_fresh_simulator':True,'render_preserves_native_state':before==native_state(env),
   'image_path':str(image),'image_sha256':sha(image),'sample':sample}
  save(image.with_suffix('.json'),result)
  print(json.dumps({k:result[k] for k in ('status','physics_step','simulation_time_s','sample_matches_baseline_trace_exactly','render_preserves_native_state','image_sha256')}),flush=True)
 finally: env.close()
if __name__=='__main__': main()
