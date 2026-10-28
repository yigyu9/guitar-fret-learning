"""Graphics-only observer of the unchanged no-NN repro/cap collectors; root GPU only."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
from contextlib import contextmanager

HERE=Path(__file__).resolve().parent
module_spec=importlib.util.spec_from_file_location('observed_effort_probe',HERE.parent/'probe.py')
cap=importlib.util.module_from_spec(module_spec); sys.modules[module_spec.name]=cap; module_spec.loader.exec_module(cap)
repro,parent=cap.repro,cap.parent
CONDITIONS=('baseline20','cap025')
CAP_REVIEW=HERE.parent/'analysis/results_v1/review.json'
HELPERS=(parent.ROOT/'guitar_learning/tool/demonstration/render_finger_skill.py',
         parent.ROOT/'guitar_learning/tool/validation/hand_contact_probe.py')


def reviewed_paths(path):
    review=parent.read(path)
    assert review['verdict']=='PASS' and not review['findings']
    paths={path}
    for p,h in review['reviewed_sha256'].items():
        assert parent.sha(p)==h,p; paths.add(Path(p))
    verification_path=path.parent/'verification.json'; assert verification_path in paths
    verification=parent.read(verification_path)
    for key in ('input_sha256','verified_input_sha256'):
        for p,h in verification[key].items():
            assert parent.sha(p)==h,p; paths.add(Path(p))
    return paths


def collect_with_capture(collector,pool,document,reference,capture):
    """Return the original collector result; observe after its original step, never add/reset one."""
    original=pool.step; had_instance='step' in pool.__dict__; saved=pool.__dict__.get('step')
    def step(action):
        result=original(action); count=len(capture.samples)
        try: capture.record(count,*result[1:])
        finally:
            if len(capture.samples)>count:
                import numpy as np
                env=pool.environment; i=env.selected_index; row=capture.samples[-1]
                row.update(scripted_action=action[0].cpu().numpy().copy(),
                    executed_action=pool.last_executed_action[0].cpu().numpy().copy(),
                    source_time_s=np.asarray(float(env._score_time()[0])),candidate=np.asarray(bool(env.candidate[0,i])),
                    wrong=np.asarray(bool(env.wrong[0,i])),surface_distance_m=np.asarray(float(env.surface_distance[0,i])),
                    surface_height_m=np.asarray(float(env.surface_height[0,i])))
                for target,source in (('wrist_feedback_active','active'),('wrist_pose_error_world','pose_error_world'),
                    ('wrist_requested_delta_rad','requested_delta_rad'),('wrist_requested_arm_rad','requested_arm_rad'),
                    ('wrist_candidate_arm_rad','candidate_arm_rad'),('wrist_goal_G_m','position_goal_G_m'),('wrist_goal_G_xyzw','quaternion_goal_G_xyzw')):
                    row[target]=pool.last_wrist_feedback[source][0].cpu().numpy().copy()
        return result
    pool.step=step
    try: return collector(pool,document,reference)
    finally:
        if had_instance: pool.step=saved
        else: del pool.step


@contextmanager
def graphics_observer(gymapi,native_render,GraphicsGym,state,out):
    original_gym=gymapi.acquire_gym; original_cameras=native_render.CAMERAS; original_collect=parent.collect
    settings=copy.deepcopy(original_cameras); settings['fullbody']=((-.10,3.4,1.1),(-.15,-.10,.65))
    def collect(pool,document,reference):
        assert state['capture'] is None
        scene=pool.scene; colors={}; collector_failed=False
        try:
            for i,name in enumerate(scene.human_bodies):
                if any(name.startswith('LH:'+finger) for finger in native_render.COLORS):
                    color=scene.gym.get_rigid_body_color(scene.envs[0],scene.actors[0][0],i,gymapi.MESH_VISUAL)
                    colors[i]=gymapi.Vec3(color.x,color.y,color.z)
            cameras=native_render._create_cameras(scene,gymapi)
            for name in cameras: state['videos'][name]=native_render._encoder(out/(name+'.mp4'))
            import numpy as np
            capture=native_render._EnvZeroCapture(pool,gymapi,np,cameras,state['videos']); state['capture']=capture
            state['wrist_control']=copy.deepcopy(pool.spec['wrist_control'])
            state['joint_names']=scene.names; state['body_names']=scene.body_names
            state['camera_settings']=settings
            return collect_with_capture(original_collect,pool,document,reference,capture)
        except BaseException:
            collector_failed=True; raise
        finally:
            problems=[]
            for i,color in colors.items():
                try: scene.gym.set_rigid_body_color(scene.envs[0],scene.actors[0][0],i,gymapi.MESH_VISUAL,color)
                except BaseException as e: problems.append(dict(component='visual_color_restore',error=str(e)))
            state['cleanup_errors'].extend(problems); state['visual_colors_restored']=not problems
            if problems and not collector_failed: raise RuntimeError('Visual color restore failed')
    gymapi.acquire_gym=lambda: GraphicsGym(original_gym()); native_render.CAMERAS=settings; parent.collect=collect
    try: yield
    finally:
        gymapi.acquire_gym=original_gym; native_render.CAMERAS=original_cameras; parent.collect=original_collect
        state['observer_aliases_restored']=True


def self_test():
    import io
    import tempfile
    from types import SimpleNamespace
    import numpy as np
    import torch
    from guitar_learning.tool.demonstration import render_finger_skill as render
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym,finish_video
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    class Gym:
        def __init__(self): self.frames=0
        def step_graphics(self,sim): self.frames+=1
        def render_all_camera_sensors(self,sim): pass
        def get_camera_image(self,*args): return np.zeros((720,1280,4),dtype=np.uint8)
        def create_sim(self,*args): return args
    class Pool:
        def __init__(self):
            self.tick=0; self.actions=[]; self.last_executed_action=torch.zeros(1,39)
            self.scene=SimpleNamespace(gym=Gym(),sim=0,envs=[0])
            self.scene.snapshot=lambda:dict(q=torch.zeros(1,105),qd=torch.zeros(1,105),target=torch.zeros(1,105),
                body_state=torch.zeros(1,2,13),contact_force=torch.zeros(1,2,3),physics_step=torch.tensor([4*self.tick]))
            self.contract={}; self.environment=SimpleNamespace(action=torch.zeros(1,39),selected_index=0,
                candidate=torch.ones(1,1,dtype=torch.bool),wrong=torch.zeros(1,1,dtype=torch.bool),
                surface_distance=torch.zeros(1,1),surface_height=torch.zeros(1,1))
            self.environment._score_time=lambda:torch.tensor([self.tick/60.])
            self.last_wrist_feedback={k:torch.zeros(1,n) for k,n in (('active',1),('pose_error_world',6),('requested_delta_rad',12),
                ('requested_arm_rad',12),('candidate_arm_rad',12),('position_goal_G_m',3),('quaternion_goal_G_xyzw',4))}
        def step(self,action):
            self.tick+=1; self.actions.append(action.clone()); zero=torch.zeros(1); no=torch.zeros(1,dtype=torch.bool)
            return {},zero,zero,no,no,[dict(env_id=0)] if self.tick==3 else []
    pool=Pool(); streams={k:SimpleNamespace(stdin=io.BytesIO()) for k in ('hand','fullbody')}
    capture=render._EnvZeroCapture(pool,SimpleNamespace(IMAGE_COLOR=0),np,dict(hand=0,fullbody=1),streams)
    token=object(); action=torch.ones(1,39)
    def collector(p,d,r):
        for _ in range(4): p.step(action)
        return token
    original=pool.step.__func__; assert collect_with_capture(collector,pool,None,None,capture) is token
    assert pool.step.__func__ is original and 'step' not in pool.__dict__ and pool.tick==4 and len(capture.samples)==3
    assert len(capture.frame_times_s)==1 and capture.frame_times_s==[2/60.] and pool.scene.gym.frames==1
    assert all(torch.equal(a,action) for a in pool.actions) and all(len(v.stdin.getvalue())==1280*720*3 for v in streams.values())
    class Broken:
        samples=[]
        def record(self,*args): raise RuntimeError('capture failure')
    try: collect_with_capture(collector,pool,None,None,Broken())
    except RuntimeError as e: assert str(e)=='capture failure'
    else: raise AssertionError('Capture error swallowed')
    assert pool.step.__func__ is original and 'step' not in pool.__dict__
    class BrokenPipe(io.BytesIO):
        def write(self,data): raise BrokenPipeError('encoder pipe')
    pool3=Pool(); videos={k:SimpleNamespace(stdin=BrokenPipe()) for k in ('hand','fullbody')}
    partial=render._EnvZeroCapture(pool3,SimpleNamespace(IMAGE_COLOR=0),np,dict(hand=0,fullbody=1),videos)
    try: collect_with_capture(collector,pool3,None,None,partial)
    except BrokenPipeError as e: assert str(e)=='encoder pipe'
    else: raise AssertionError('Encoder pipe error swallowed')
    arrays={key:np.stack([row[key] for row in partial.samples]) for key in partial.samples[0]}
    assert len(partial.samples)==2 and pool3.tick==2 and pool3.step.__func__ is original and 'step' not in pool3.__dict__
    assert arrays['scripted_action'].shape==(2,39) and arrays['wrist_candidate_arm_rad'].shape==(2,12)
    assert np.array_equal(arrays['physics_step'],[4,8])
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'partial.npz'; np.savez_compressed(path,**arrays)
        with np.load(path) as saved: assert saved['q'].shape==(2,105) and np.array_equal(saved['physics_step'],[4,8])
    assert GraphicsGym(Gym()).create_sim(3,-1,1,2)==(3,3,1,2)
    with tempfile.TemporaryDirectory() as tmp:
        link=Path(tmp)/'old'; link.symlink_to(Path(tmp)/'missing')
        try: cap.reject_existing(link)
        except FileExistsError: pass
        else: raise AssertionError('Dangling output accepted')
    assert finish_video(SimpleNamespace(stdin=io.BytesIO(),wait=lambda:0))==(0,[])
    api=SimpleNamespace(acquire_gym=lambda:Gym()); old_gym=api.acquire_gym; old_cameras=render.CAMERAS; old_collect=parent.collect
    state=dict(capture=None,videos={},cleanup_errors=[])
    try:
        with graphics_observer(api,render,GraphicsGym,state,Path('/unused')):
            assert render.CAMERAS['fullbody'][0][1]==3.4 and parent.collect is not old_collect
            assert isinstance(api.acquire_gym(),GraphicsGym)
            raise RuntimeError('observer failure')
    except RuntimeError as e: assert str(e)=='observer failure'
    assert api.acquire_gym is old_gym and render.CAMERAS is old_cameras and parent.collect is old_collect and state['observer_aliases_restored']
    pool2=Pool(); pool2.spec=dict(wrist_control={'fixture':'only'}); scene=pool2.scene
    scene.human_bodies=['LH:index1']; scene.actors=[[0]]; scene.names=['q']; scene.body_names=['body']
    vector=lambda *v:SimpleNamespace(x=v[0],y=v[1],z=v[2])
    api=SimpleNamespace(acquire_gym=lambda:scene.gym,MESH_VISUAL=0,IMAGE_COLOR=0,CameraProperties=SimpleNamespace,Vec3=vector)
    original_color=vector(.2,.3,.4); colors={0:original_color}; camera_calls=[]
    scene.gym.get_rigid_body_color=lambda env,actor,i,kind:colors[i]
    scene.gym.set_rigid_body_color=lambda env,actor,i,kind,color:colors.__setitem__(i,color)
    scene.gym.create_camera_sensor=lambda env,props:0
    scene.gym.set_camera_location=lambda camera,env,position,target:camera_calls.append(position)
    old_encoder=render._encoder; parent.collect=collector
    state=dict(capture=None,videos={},cleanup_errors=[])
    try:
        render._encoder=lambda path:SimpleNamespace(stdin=io.BytesIO())
        with graphics_observer(api,render,GraphicsGym,state,Path('/unused')):
            assert parent.collect(pool2,None,None) is token
    finally: render._encoder=old_encoder; parent.collect=old_collect
    assert state['observer_aliases_restored'] and state['visual_colors_restored'] and pool2.tick==4
    assert (colors[0].x,colors[0].y,colors[0].z)==(.2,.3,.4) and len(camera_calls)==2 and camera_calls[1].y==3.4
    assert len(state['capture'].samples)==3 and len(state['capture'].frame_times_s)==1
    return dict(CPU_only=True,GPU_executed=False,CUDA_initialized=False,
        checks=['original collector return/actions/four steps unchanged','env0 first three endpoints only despite fourth step',
            'actual capture writer two RGB streams/one30Hz frame/no t0','current scripted/wrist fields','step binding restored on success/error',
            'capture error propagates/encoder BrokenPipe retains complete partial raw prefix','actual camera-helper/observer collector path/visual color restore','graphics device only adapter/global camera+gym+collect aliases restored on error','dangling output rejected','finish encoder helper'])


def prepare():
    from guitar_learning.tool.experiments.short_finger_learning import runner
    result=self_test(); paths={Path(__file__).resolve(),HERE/'PLAN.md',*HELPERS}
    paths.update(cap.baseline_actual_gate()); paths.update(reviewed_paths(CAP_REVIEW))
    for seal_path in (repro.HERE/'preparation_seal.json',HERE.parent/'preparation_seal.json'):
        seal=parent.read(seal_path); assert seal['independent_review']=='passed_no_findings'
        paths.add(seal_path)
        for p,h in seal['input_pins'].items(): assert parent.sha(p)==h,p; paths.add(Path(p))
    inputs=HERE/'cpu_inputs'; cap.reject_existing(inputs); cap.reject_existing(HERE/'preparation_seal.json'); inputs.mkdir()
    cases=[]
    for condition in CONDITIONS:
        for finger in repro.SELECTED:
            config=parent.settings(finger,4)
            assert config==parent.read(repro.HERE/'cpu_inputs'/(finger+'_settings.json'))==parent.read(HERE.parent/'cpu_inputs'/(finger+'_settings.json'))
            cases.append(dict(condition=condition,finger=finger,cap_Nm=20. if condition=='baseline20' else cap.CAP,
                selected_grid_index=repro.SELECTED[finger],num_envs=4,detail_env_id=0,first_attempt=True,
                out=str(HERE/'runs'/(condition+'_'+finger)),
                argv=[parent.PYTHON,'-B',str(Path(__file__).resolve()),'--condition',condition,'--finger',finger,'--execute']))
    parent.write(inputs/'cases.json',cases); parent.write(inputs/'settings.json',parent.settings('index',4))
    parent.write(HERE/'cpu_verification.json',dict(result,cases=cases,native_pixels_unverified=True,
        execution_gate='parent cap and baseline actual independent PASS with current hashes, then own preparation PASS',
        scope='No NN/checkpoint; fresh scenes and env0 only; no naturalness/pressure/4seed claim'))
    paths.update((inputs/'cases.json',inputs/'settings.json',HERE/'cpu_verification.json'))
    pins=runner._pins(parent.settings('index',4),inputs,paths)
    parent.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=pins,GPU_executed=False))
    print(json.dumps(dict(CPU_only=True,pins=len(pins),cases=4,MP4_expected=8)))


def execute(condition,finger,out,seal):
    import isaacgym
    from isaacgym import gymapi
    import numpy as np
    from guitar_learning.tool.demonstration import render_finger_skill as render
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym,finish_video
    state=dict(capture=None,videos={},cleanup_errors=[],visual_colors_restored=False,observer_aliases_restored=False)
    failure=None; codes={}; errors=[]
    call_seal=copy.deepcopy(seal)
    call_seal['input_pins'][str(HERE/'preparation_seal.json')]=parent.sha(HERE/'preparation_seal.json')
    try:
        with graphics_observer(gymapi,render,GraphicsGym,state,out):
            if condition=='baseline20': repro.execute(finger,out,call_seal)
            else:
                out.mkdir(parents=True,exist_ok=False); identity=(out.stat().st_dev,out.stat().st_ino)
                cap.execute(finger,out,identity,call_seal,cap.baseline_actual_gate())
    except BaseException as e:
        failure=dict(type=type(e).__name__,message=str(e)); raise
    finally:
        if not out.exists(): out.mkdir(parents=True,exist_ok=False)
        for name,process in state['videos'].items():
            code,problems=finish_video(process); codes[name]=code; errors.extend(dict(component=name,error=p) for p in problems)
        errors.extend(state['cleanup_errors'])
        capture=state['capture']; finite=clock=False
        if capture and capture.samples:
            try:
                arrays={k:np.stack([r[k] for r in capture.samples]) for k in capture.samples[0]}
                finite=all(np.isfinite(v).all() for v in arrays.values()); clock=np.array_equal(arrays['physics_step'],4*np.arange(1,len(capture.samples)+1))
                np.savez_compressed(out/('poses_env0000.npz' if failure is None else 'partial_poses_env0000.npz'),**arrays)
                parent.write(out/'capture_metadata.json',dict(condition=condition,finger=finger,environment=0,first_attempt=True,
                    no_NN_checkpoint=True,policy_performance=False,selection='predeclared env0 first scripted attempt; not selected by performance',
                    native_pixels=True,width=1280,height=720,video_fps=30,capture_hz=60,physics_hz=240,
                    frames=len(capture.frame_times_s),frame_times_s=capture.frame_times_s,control_endpoints=len(capture.samples),
                    joint_names=state['joint_names'],body_names=state['body_names'],camera_settings=state['camera_settings'],wrist_control=state['wrist_control'],
                    frame_mapping='frame n maps to endpoint2*(n+1); no t0; odd final endpoint has no frame',
                    scope='new four-env scripted collector run; movie only env0 first attempt; not original untraced env2 or pressure/naturalness certification',
                    qd_scope='native velocity coordinates, not q-position rotvec derivative',
                    raw_force_mapping='contact_force is scene net body resultant; corresponding parent trace key is net_body_force_n',
                    wrist_scope='saved current v3 contract: precontrol candidate/proposal correction; snapshot q/body/target poststep; inactive candidate=proposal/delta0'))
            except BaseException as e: errors.append(dict(component='raw_capture',error=str(e)))
        original=parent.read(out/'report.json') if (out/'report.json').is_file() else {}
        paths=call_seal['input_pins']; changed=[p for p,h in paths.items() if not Path(p).is_file() or parent.sha(p)!=h]
        files={name:dict(path=str(out/(name+'.mp4')),bytes=(out/(name+'.mp4')).stat().st_size if (out/(name+'.mp4')).is_file() else 0) for name in codes}
        completed=bool(failure is None and original.get('completed') and original.get('closed') and not changed and not errors and finite and clock and
            capture and capture.episode and len(capture.frame_times_s)==len(capture.samples)//2 and len(codes)==2 and all(c==0 for c in codes.values()) and
            all(v['bytes']>0 for v in files.values()) and state['observer_aliases_restored'] and state['visual_colors_restored'])
        parent.write(out/'render_report.json',dict(completed=completed,failure=failure,condition=condition,finger=finger,
            no_NN_checkpoint=True,policy_performance=False,source_pins_unchanged=not changed,changed_inputs=changed,
            trace_finite=bool(finite),physics_clock_contiguous=bool(clock),encoding_exit_codes=codes,cleanup_errors=errors,video_files=files,
            observer_aliases_restored=state['observer_aliases_restored'],visual_colors_restored=state['visual_colors_restored'],
            original_run_completed=original.get('completed',False),scene_closed=original.get('closed',False),
            scope='graphics observation only; parent collector retains all four first attempts and original physical/source checks'))
        if failure is None and not completed: raise RuntimeError('Native video/source/clock/encoder/scene validation failed; outputs preserved')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    for name in ('self-test','prepare','execute'): group.add_argument('--'+name,action='store_true')
    parser.add_argument('--condition',choices=CONDITIONS); parser.add_argument('--finger',choices=tuple(repro.SELECTED)); args=parser.parse_args()
    sys.path.insert(0,str(parent.ROOT))
    if args.self_test: print(json.dumps(self_test())); return
    if args.prepare: prepare(); return
    if args.condition is None or args.finger is None: raise ValueError('Predeclared condition/finger required')
    out=HERE/'runs'/(args.condition+'_'+args.finger); cap.reject_existing(out)
    seal=parent.read(HERE/'preparation_seal.json')
    assert seal['independent_review']=='passed_no_findings'
    assert all(Path(p).is_file() and parent.sha(p)==h for p,h in seal['input_pins'].items())
    cap.baseline_actual_gate(); reviewed_paths(CAP_REVIEW)  # Fail before native import; music acceptance need not pass.
    try: execute(args.condition,args.finger,out,seal)
    except BaseException as e:
        if not out.exists(): out.mkdir(parents=True,exist_ok=False)
        if not (out/'render_report.json').exists(): parent.write(out/'render_report.json',dict(completed=False,scene_closed=False,
            failure=dict(type=type(e).__name__,message=str(e)),scope='Failure before normal graphics lifecycle report; original error propagated'))
        raise


if __name__=='__main__': main()
