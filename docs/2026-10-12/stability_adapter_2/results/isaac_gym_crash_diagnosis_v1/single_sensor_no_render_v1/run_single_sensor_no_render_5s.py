"""Control: one front camera sensor exists before physics; no render during 5s rollout."""
import hashlib, json, os, sys, time
from collections import Counter
from pathlib import Path
import numpy as np
ROOT=Path('/home/ajou/yigyu/3'); OUT=Path(__file__).resolve().parent
REF=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/axis_00'
sys.path.insert(0,str(ROOT))
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    tmp=Path(str(p)+'.tmp'); tmp.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n'); os.replace(tmp,p)
def contacts_summary(rows):
    pairs=Counter(tuple(sorted((r['body0_name'],r['body1_name']))) for r in rows)
    lambdas=[float(r.get('lambda',0.0)) for r in rows]
    return {'row_count':len(rows),'positive_raw_lambda_rows':sum(v>0 for v in lambdas),
        'max_raw_lambda':max(lambdas,default=0.0),
        'pair_row_counts':{' | '.join(k):v for k,v in sorted(pairs.items())}}

from stability_adapter_2.self_collision_environment import SelfCollisionEnvironment
from stability_adapter_2.environment import gymapi
from stability_adapter_2.palm_side_feedback import context, SETTINGS
from stability_adapter_2.palm_normal_task import prepare
from stability_adapter_2.run_physx_contacts import native_state
from stability_adapter_2.run_initialization import snapshot
from stability_adapter_2.native_contacts import body_names,read_contacts
from stability_adapter_2.build_fixed_lower_asset import read as read_settings,LOWER_BODIES

class GraphicsGym:
    def __init__(self,gym): self.gym=gym
    def __getattr__(self,name): return getattr(self.gym,name)
    def create_sim(self,compute,graphics,engine,params): return self.gym.create_sim(compute,0,engine,params)
class OneSensorEnvironment(SelfCollisionEnvironment):
    def __init__(self,settings,shift):
        acquire=gymapi.acquire_gym; gymapi.acquire_gym=lambda:GraphicsGym(acquire())
        try: super().__init__(settings,shift)
        finally: gymapi.acquire_gym=acquire
    def _create_scene(self):
        super()._create_scene()
        for actor,names in ((self.human,self.human_bodies),(self.guitar,self.guitar_bodies)):
            for i,name in enumerate(names):
                rgb=(.12,.65,.3) if name.startswith('LH:') else ((.8,.12,.5) if name.startswith('RH:') else ((.12,.3,.8) if actor==self.guitar else (.7,.7,.7)))
                self.gym.set_rigid_body_color(self.env,actor,i,gymapi.MESH_VISUAL_AND_COLLISION,gymapi.Vec3(*rgb))
        props=gymapi.CameraProperties(); props.width,props.height,props.horizontal_fov=1200,900,45.0
        self.camera=self.gym.create_camera_sensor(self.env,props)
        if self.camera<0: raise RuntimeError('camera creation failed')
        self.eye=(0.0,3.40,1.38); self.look=(0.0,-0.18,0.72)
        self.gym.set_camera_location(self.camera,self.env,gymapi.Vec3(*self.eye),gymapi.Vec3(*self.look))

def main():
    if any((OUT/n).exists() for n in ('run_result.json','progress.json','trace.jsonl')):
        raise FileExistsError('preserve prior run; use fresh directory')
    rp=REF/'report.json'; report=read(rp); candidate=Path(report['candidate_path']); controls=read(REF/'controls.json')
    files=[Path(p) for p in report['source_sha256']]+[candidate,rp]+[REF/(n+'.json') for n in ('states','trace','tasks','contacts','controls')]
    hashes={str(p.resolve()):sha(p) for p in files}
    for p,h in report['source_sha256'].items():
        if hashes[str(Path(p).resolve())]!=h: raise AssertionError('reference input changed: '+p)
    if report.get('failure') or not all(report['checks'].values()) or report['physics_steps']!=24:
        raise AssertionError('selected axis_00 reference invalid')
    ctx=prepare(context()); arm=ctx['indices']; q0=ctx['q0'][arm]
    target=np.asarray(controls[0]['final_target_rad'],dtype=np.float32)
    if not np.array_equal(target,q0.astype(np.float32)+np.asarray(report['bias_rad'],dtype=np.float32)):
        raise AssertionError('selected arm PD target mismatch')
    env=OneSensorEnvironment(read_settings(SETTINGS),ctx['shift']); start=time.monotonic()
    try:
        initial=native_state(env)
        if initial!=ctx['seed']: raise AssertionError('initial seed mismatch')
        offsets=np.zeros(66,dtype=np.float32)
        for idx,delta in zip(arm,target-q0.astype(np.float32)): offsets[list(env.main_indices).index(idx)]=delta
        env.set_main_offsets(offsets)
        if not np.array_equal(env.target[arm],target): raise AssertionError('target readback mismatch')
        names=body_names(env.gym,env.env); samples=[snapshot(env)]
        with (OUT/'trace.jsonl').open('w') as trace,(OUT/'contact_summary.jsonl').open('w') as contact_file:
            trace.write(json.dumps({'physics_step':0,'sample':samples[0]},allow_nan=False)+'\n'); trace.flush()
            for _ in range(1200):
                env.step_physics(); s=snapshot(env); dofs=env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL)
                row={'physics_step':env.steps,'time_s':env.steps/env.config['physics_hz'],'sample':s,
                     'max_abs_dof_velocity_rad_s':float(np.max(np.abs(dofs['vel'])))}
                trace.write(json.dumps(row,allow_nan=False)+'\n'); trace.flush(); samples.append(s)
                if env.steps%24==0 or env.steps==1200:
                    cs=contacts_summary(read_contacts(env.gym,env.env,names))
                    contact_file.write(json.dumps({'physics_step':env.steps,'contacts':cs},allow_nan=False)+'\n'); contact_file.flush()
                    os.fsync(trace.fileno()); os.fsync(contact_file.fileno())
                    progress={'status':'physics_running','completed_physics_steps':env.steps,'time_s':env.steps/env.config['physics_hz'],
                        'camera_sensors':1,'camera_render_calls':0,'position_error_mm':s['position_error_m']*1000,
                        'rotation_error_deg':s['rotation_error_deg'],'linear_speed_mps':s['linear_speed_mps'],
                        'angular_speed_rad_s':s['angular_speed_rad_s'],'strap_length_m':s['strap_length_m'],
                        'last_applied_strap_tension_n':s['last_applied_tension_n'],'contacts':cs}
                    save(OUT/'progress.json',progress); print(json.dumps(progress,allow_nan=False),flush=True)
        final=native_state(env); fixed_names=('Pelvis',)+LOWER_BODIES
        fixed=all(initial['human_body_states'][env.human_bodies.index(n)]==final['human_body_states'][env.human_bodies.index(n)] for n in fixed_names)
        r={'status':'physics_completed','physics_steps':env.steps,'duration_s':env.steps/env.config['physics_hz'],
            'wall_time_s':time.monotonic()-start,'physics_device':'CPU','gpu_pipeline':False,
            'camera_sensors_created_before_physics':1,'camera_render_calls_during_physics':0,
            'initial_seed_exact':initial==ctx['seed'],'selected_pd_target_exact':bool(np.array_equal(env.target[arm],target)),
            'root_and_lower_body_fixed':fixed,'all_trace_samples_finite':len(samples)==1201 and all(s['finite'] for s in samples),
            'max_position_error_mm':max(s['position_error_m'] for s in samples)*1000,
            'max_rotation_error_deg':max(s['rotation_error_deg'] for s in samples),
            'initial_sample':samples[0],'final_sample':samples[-1],
            'input_sha256':hashes,'runner_sha256':sha(__file__)}
        if env.steps!=1200 or not r['all_trace_samples_finite']: raise AssertionError(r)
        save(OUT/'run_result.json',r)
        print(json.dumps({'status':'physics_completed','steps':env.steps,'duration_s':r['duration_s'],
            'wall_time_s':r['wall_time_s'],'max_position_error_mm':r['max_position_error_mm'],
            'max_rotation_error_deg':r['max_rotation_error_deg']}),flush=True)
        before=native_state(env); env.gym.step_graphics(env.sim); env.gym.render_all_camera_sensors(env.sim)
        image=OUT/'front_fullbody_step1200.png'
        env.gym.write_camera_image_to_file(env.sim,env.env,env.camera,gymapi.IMAGE_COLOR,str(image))
        cr={'status':'one_render_after_physics','physics_step':env.steps,'render_preserves_native_state':before==native_state(env),
            'image_sha256':sha(image),'camera_sensors_created_before_physics':1,'render_calls_during_physics':0}
        save(OUT/'camera_render_result.json',cr); save(OUT/'progress.json',{'status':'completed','completed_physics_steps':env.steps,'camera_render_calls_during_physics':0})
        print(json.dumps(cr),flush=True)
    except Exception as e:
        save(OUT/'failure.json',{'status':'python_exception','physics_steps_completed':env.steps,'error_type':type(e).__name__,'error':str(e)})
        raise
    finally: env.close()
if __name__=='__main__': main()
