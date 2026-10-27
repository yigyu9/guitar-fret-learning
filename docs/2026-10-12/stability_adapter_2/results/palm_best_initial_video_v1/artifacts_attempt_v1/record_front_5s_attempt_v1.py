"""Record a 5-second Isaac Gym front-camera replay of the selected constant target."""
import hashlib, json
from pathlib import Path
import numpy as np
ROOT=Path('/home/ajou/yigyu/3')
REF=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/axis_00'
OUT=Path(__file__).resolve().parent/'isaac_gym_5s_front'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def main():
    if OUT.exists(): raise FileExistsError(OUT)
    OUT.mkdir(parents=True)
    rp=REF/'report.json'; candidate=Path(read(rp)['candidate_path']); report=read(rp)
    paths=[Path(p) for p in report['source_sha256']]+[candidate,rp]+[REF/(n+'.json') for n in ('states','trace','tasks','contacts','controls')]
    hashes={str(p.resolve()):sha(p) for p in paths}
    if report['failure'] or not all(report['checks'].values()) or report['physics_steps']!=24: raise AssertionError('reference run invalid')
    if any(hashes[str(Path(p).resolve())]!=h for p,h in report['source_sha256'].items()): raise AssertionError('reference inputs changed')
    controls=read(REF/'controls.json')
    # Seal and read every project input above before importing the simulation helpers.
    from stability_adapter_2.probe_palm_contact_facet import PalmCameraEnvironment
    from stability_adapter_2.palm_side_feedback import context, SETTINGS
    from stability_adapter_2.palm_normal_task import prepare, error_from_state
    from stability_adapter_2.run_joint_hold import native_state, snapshot
    from stability_adapter_2.native_contacts import body_names, read_contacts
    from stability_adapter_2.build_fixed_lower_asset import read as read_settings, LOWER_BODIES
    from stability_adapter_2.environment import gymapi
    ctx=prepare(context()); arm=ctx['indices']; q0=ctx['q0'][arm]
    target=np.asarray(controls[0]['final_target_rad'],dtype=np.float32)
    bias=np.asarray(report['bias_rad'],dtype=np.float32)
    expected=q0.astype(np.float32)+bias
    if not np.array_equal(target,expected): raise AssertionError('candidate target does not reproduce saved command')
    env=PalmCameraEnvironment(read_settings(SETTINGS),ctx['shift']); names=body_names(env.gym,env.env)
    states0=native_state(env); trace=[]; tasks=[]; contacts=[]; images={}; commands=[]
    def record():
        st=native_state(env); tr=snapshot(env); task=error_from_state(st,ctx).tolist()
        if not tr['finite'] or not np.isfinite(np.asarray(task)).all(): raise FloatingPointError('nonfinite simulation state')
        trace.append(tr); tasks.append(task)
        return st
    def capture():
        before=native_state(env); env.gym.step_graphics(env.sim); env.gym.render_all_camera_sensors(env.sim)
        name='blue_front'; path=OUT/('front_'+str(env.steps).zfill(4)+'.png')
        env.gym.write_camera_image_to_file(env.sim,env.env,env.cameras[name],gymapi.IMAGE_COLOR,str(path))
        images[str(path.resolve())]={'sha256':sha(path),'physics_step':env.steps,'time_s':env.steps/240}
        if before!=native_state(env): raise AssertionError('camera changed simulation state')
    try:
        initial=record();
        if initial!=ctx['seed']: raise AssertionError('initial state mismatch')
        capture(); offsets=np.zeros(66,dtype=np.float32)
        for i,d in zip(arm,target-q0.astype(np.float32)): offsets[list(env.main_indices).index(i)]=d
        before=native_state(env); env.set_main_offsets(offsets)
        if before!=native_state(env): raise AssertionError('target command changed physical state')
        commands.append({'physics_step':0,'target_rad':env.target[arm].astype(float).tolist()})
        fixed=True; positive=[]; contacts_by_step=[]
        interval=env.config['physics_hz']//env.config['control_hz']
        if interval!=4 or env.config['physics_hz']!=240: raise AssertionError('unexpected simulator rate')
        for step in range(1200):
            env.step_physics(); st=record()
            fixed &= all(st['human_body_states'][env.human_bodies.index(n)]==states0['human_body_states'][env.human_bodies.index(n)] for n in ('Pelvis',)+LOWER_BODIES)
            rows=read_contacts(env.gym,env.env,names)
            palm=[c for c in rows if {c.get('body0_name'),c.get('body1_name')}=={'human/LH:palm','guitar/guitar'}]
            contacts_by_step.append({'physics_step':env.steps,'palm_guitar_rows':palm})
            if any(c['lambda']>0 for c in palm): positive.append(env.steps)
            if env.steps%16==0 or env.steps==1200: capture()
        checks={'initial_state_exact':initial==ctx['seed'],'root_and_lower_fixed':bool(fixed),
            'constant_target_exact':all(np.array_equal(env.target[arm],target) for _ in (0,)),
            'finite_trace':len(trace)==1201 and all(x['finite'] for x in trace),
            'camera_render_preserves_state':True,'front_images_76':len(images)==76,
            'candidate_inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
        out_report={'candidate_path':str(candidate),'candidate_sha256':hashes[str(candidate.resolve())],
            'reference_report':str(rp),'reference_report_sha256':hashes[str(rp.resolve())],
            'source_sha256':hashes,'native_initializations':1,'physics_steps':1200,'physics_hz':240,
            'control_hz':60,'duration_s':5.0,'camera_specs':env.camera_specs['blue_front'],
            'images':images,'positive_raw_palm_lambda_steps':positive,'checks':checks,
            'summary':{'max_guitar_position_error_mm':max(x['position_error_m'] for x in trace)*1000,
                'max_guitar_rotation_error_deg':max(x['rotation_error_deg'] for x in trace),
                'end_guitar_position_error_mm':trace[-1]['position_error_m']*1000,
                'end_guitar_rotation_error_deg':trace[-1]['rotation_error_deg'],
                'end_palm_point_error_mm':float(np.linalg.norm(tasks[-1][:3])*1000)},
            'scope':'fresh 5s native Isaac Gym PhysX run with same seed and saved constant PD target; not repeated/looped 0.1s video'}
        for n,v in [('report',out_report),('trace',trace),('tasks',tasks),('contacts',contacts_by_step),('commands',commands)]:
            (OUT/(n+'.json')).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
        if not all(checks.values()): raise AssertionError(checks)
        print(json.dumps({'checks':checks,'summary':out_report['summary'],'positive_lambda_steps':positive}),flush=True)
    except Exception as e:
        (OUT/'failure.json').write_text(json.dumps({'type':type(e).__name__,'message':str(e),'steps':env.steps},indent=2)+'\n'); raise
    finally: env.close()
if __name__=='__main__': main()
