"""Compare native visual/collision cameras at preserved palm-priority t0; physics0."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
PHASE=BASE/'torso_hold_native_collision_v1'
OLD=BASE/'palm_patch_priority_diagnostic_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
    out=PHASE/'initial_collision';out.mkdir(exist_ok=False)
    baseline=read(OLD/'native/initial_values.json');inputs=dict(baseline['input_sha256'])
    trial_path=ROOT/'stability_adapter_2/trials/palm_patch_priority_diagnostic_v1/palm_wide_near17.json'
    for p in [Path(__file__).resolve(),trial_path,OLD/'native/initial_values.json',ROOT/'stability_adapter_2/TORSO_HOLD_EXECUTION.md',ROOT/'stability_adapter_2/run_three_face_shape_readback.py',ROOT/'stability_adapter_2/run_self_collision.py']:inputs[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in inputs.items());trial=read(trial_path)
    save(out/'attempt.json',dict(input_sha256=inputs,trial_path=str(trial_path),requested_physics_steps=0))
    from .capture_isaac_gym_initial import CameraEnvironment
    from .environment import np,gymapi
    from .run_joint_hold import native_state
    from .strap_trial_recording import StrapTrialRecording,draw_route
    from .run_three_face_shape_readback import read_native_shapes
    from .run_self_collision import audit
    env=CameraEnvironment(trial['initial_settings'],np.array(trial['guitar_initial_translation_m']))
    try:
        before=native_state(env);target=env.target.copy();props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
        assert before==baseline['native_initial_state'] and target.astype(float).tolist()==baseline['initial_PD_target_rad']
        properties={n:props[n].astype(int if n=='driveMode' else float).tolist() for n in props.dtype.names};assert properties==baseline['PD_properties']
        actors=read_native_shapes(env);matrix=audit(env)
        recorder=StrapTrialRecording(env,out);recorder.capture()
        camera=env.cameras['hands_collision'];raw=out/'hands_collision_raw.png';overlay=out/'hands_collision.png'
        if not env.gym.write_camera_image_to_file(env.sim,env.env,camera,gymapi.IMAGE_COLOR,str(raw)):raise RuntimeError('collision camera image write failed')
        view=np.asarray(env.gym.get_camera_view_matrix(env.sim,env.env,camera));projection=np.asarray(env.gym.get_camera_proj_matrix(env.sim,env.env,camera));depth=np.asarray(env.gym.get_camera_image(env.sim,env.env,camera,gymapi.IMAGE_DEPTH)).reshape(720,1280)
        visual=recorder.frames[0]['cameras']['hands'];assert view.tolist()==visual['view_matrix'] and projection.tolist()==visual['projection_matrix']
        points,_=env.route();counts=draw_route(raw,overlay,points,view,projection,depth,env.rest_length)
        check=dict(initial_state_exact_to_completed_baseline=before==baseline['native_initial_state'],PD_and_initial_target_exact_to_baseline=properties==baseline['PD_properties'],query_render_state_target_PD_unchanged=native_state(env)==before and np.array_equal(target,env.target) and np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human)),zero_physics_steps=env.steps==0,same_view_projection=True,selfcollision_matrix_held=all(matrix['checks'].values()),inputs_unchanged=all(sha(p)==h for p,h in inputs.items()))
        assert all(check.values())
        save(out/'shape_properties.json',dict(actors=actors,mask_audit=matrix,scope='read-only native body/shape ranges/filter/material; collision camera requested via use_collision_geometry; not cooked vertices/clearance certification'))
        save(out/'report.json',dict(checks=check,input_sha256=inputs,native_initializations=1,physics_steps=0,initial_state=before,initial_PD_properties=properties,output_sha256={str(p):sha(p) for p in (raw,overlay)},collision_camera=dict(use_collision_geometry=True,view_matrix=view.tolist(),projection_matrix=projection.tolist(),**counts),scope='native camera visual/collision at identical t0; actual strap overlay; initialization/query only, not extra5s trial or mesh replay'))
        print(json.dumps(dict(checks=check,shape_counts={n:v['shape_count'] for n,v in actors.items()},native_initializations=1,physics_steps=0)))
    finally:env.close()
if __name__=='__main__':main()
