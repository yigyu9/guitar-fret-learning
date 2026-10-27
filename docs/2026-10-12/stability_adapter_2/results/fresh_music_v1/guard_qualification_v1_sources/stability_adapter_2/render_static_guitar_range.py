"""Render bounded, zero-physics guitar placement comparisons in native Isaac Gym."""
import argparse
from pathlib import Path
from .guitar_pose_static import Editor
from .interactive_guitar_pose_static import save, read, np, Rotation, sha, gymapi, BASELINE
from .run_joint_hold import native_state

BODY_CENTER_LOCAL = np.array([0., -.4, -.0217])
CAMERAS = {
    'front': {'position_W_m': [0., 1.35, .92], 'target_W_m': [0., .025, .78]},
    'side': {'position_W_m': [1.25, 0., .92], 'target_W_m': [-.1, .02, .78]},
}


def cases():
    rows=[{'id':'baseline','translation_W_m':[0.,0.,0.],'rotation_delta_deg':[0.,0.,0.]}]
    for axis,name in enumerate('xyz'):
        for amount in (-.04,-.02,.02,.04):
            translation=[0.,0.,0.];translation[axis]=amount
            rows.append({'id':name+('%+03dmm'%round(amount*1000)),
                'translation_W_m':translation,'rotation_delta_deg':[0.,0.,0.]})
    for axis,name in enumerate(('elevation','audience_yaw','board_recline')):
        for amount in (-10.,-5.,5.,10.):
            angles=[0.,0.,0.];angles[axis]=amount
            rows.append({'id':name+('%+03ddeg'%amount),
                'translation_W_m':[0.,0.,0.],'rotation_delta_deg':angles})
    return rows


def placement(reference, translation, angles):
    p0,q0=reference;rotation=Rotation.from_quat(q0)
    translation=np.asarray(translation,dtype=float);angles=np.asarray(angles,dtype=float)
    if translation.shape!=(3,) or angles.shape!=(3,) or not np.isfinite(translation).all() or not np.isfinite(angles).all():
        raise ValueError('finite translation xyz and semantic three-angle deltas required')
    if np.max(np.abs(translation))>.04 or np.max(np.abs(angles))>10:
        raise ValueError('bounded static comparison: max4cm and10deg per coordinate')
    neck=rotation.apply([0.,1.,0.]);horizontal=neck.copy();horizontal[2]=0
    horizontal/=np.linalg.norm(horizontal)
    raise_axis=np.cross(horizontal,[0.,0.,1.])
    elevated=Rotation.from_rotvec(raise_axis*np.radians(angles[0]))*rotation
    yawed=Rotation.from_rotvec([0.,0.,-np.radians(angles[1])])*elevated
    neck=yawed.apply([0.,1.,0.])
    final=Rotation.from_rotvec(-neck*np.radians(angles[2]))*yawed
    center=p0+rotation.apply(BODY_CENTER_LOCAL)+translation
    return center-final.apply(BODY_CENTER_LOCAL),final.as_quat()


def metrics(editor):
    rotation=Rotation.from_quat(editor.quaternion)
    neck=rotation.apply([0.,1.,0.]);face=rotation.apply([0.,0.,1.])
    return {'body_center_W_m':(editor.position+rotation.apply(BODY_CENTER_LOCAL)).tolist(),
            'neck_elevation_deg':float(np.degrees(np.arcsin(np.clip(neck[2],-1,1)))),
            'neck_audience_yaw_deg':float(np.degrees(np.arctan2(neck[1],-neck[0]))),
            'front_normal_elevation_deg':float(np.degrees(np.arcsin(np.clip(face[2],-1,1))))}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--cases',type=Path)
    args=parser.parse_args()
    rows=read(args.cases) if args.cases else cases()
    limit=5 if args.cases else 25
    if not isinstance(rows,list) or not 1<=len(rows)<=limit or len({row['id'] for row in rows})!=len(rows):
        raise ValueError('bounded list of uniquely named cases required')
    args.out.mkdir(parents=True,exist_ok=False)
    inputs=[Path(__file__).resolve(),Path(__file__).with_name('STATIC_GUITAR_NATURAL_RANGE_PLAN.md'),BASELINE]
    inputs += [Path(__file__).with_name(n) for n in ('guitar_pose_static.py','interactive_guitar_pose_static.py','guitar_pose_edit.py','capture_isaac_gym_initial.py')]
    if args.cases:inputs.append(args.cases.resolve())
    hashes={str(path):sha(path) for path in inputs}
    save(args.out/'attempt.json',{'cases':rows,'input_sha256':hashes,'renderer':'Isaac Gym native cameras',
        'camera_configuration':CAMERAS,'rotation_pivot':'G:body local center [0,-.4,-.0217]m',
        'physics_steps_requested':0,'scope':'static visual comparisons only; no stability or contact certification'})
    editor=Editor(args.out/'scene',strap=False,viewer=False)
    results=[]
    try:
        reference=(editor.position.copy(),editor.quaternion.copy())
        initial=native_state(editor.env)
        save(args.out/'initial_state.json',initial)
        extra={}
        for name,config in CAMERAS.items():
            props=gymapi.CameraProperties();props.width,props.height=1280,720
            camera=editor.env.gym.create_camera_sensor(editor.env.env,props)
            if camera<0:raise RuntimeError('native camera creation failed: '+name)
            editor.env.gym.set_camera_location(camera,editor.env.env,
                gymapi.Vec3(*config['position_W_m']),gymapi.Vec3(*config['target_W_m']))
            extra[name]=camera
        for row in rows:
            editor.position,editor.quaternion=placement(reference,row['translation_W_m'],row['rotation_delta_deg'])
            editor.install_pose()
            folder=editor.save_candidate()
            before=native_state(editor.env)
            editor.env.gym.step_graphics(editor.env.sim)
            editor.env.gym.render_all_camera_sensors(editor.env.sim)
            images={}
            for name,camera in extra.items():
                path=folder/(name+'.png')
                editor.env.gym.write_camera_image_to_file(editor.env.sim,editor.env.env,camera,gymapi.IMAGE_COLOR,str(path))
                if not path.is_file() or not path.stat().st_size:
                    raise RuntimeError('native image write failed: '+name)
                images[str(path)]=sha(path)
            after=native_state(editor.env)
            checks={'zero_physics_steps':editor.env.steps==0,
                    'human_exact':after['human_body_states']==initial['human_body_states'] and after['human_dof_states']==initial['human_dof_states'],
                    'extra_camera_render_readonly':before==after,
                    'no_force_or_integration_attempts':editor.env.gym.blocked_physics_calls==0}
            save(folder/'comparison.json',dict(row,**metrics(editor),checks=checks,extra_image_sha256=images,
                camera_configuration=CAMERAS,native_state=after))
            if not all(checks.values()):raise AssertionError(checks)
            results.append(dict(row,path=str(folder),**metrics(editor)))
            print('rendered',row['id'],flush=True)
        final_checks={'all_cases_completed':len(results)==len(rows),'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
        save(args.out/'comparison.json',{'rows':results,'baseline':metrics_at_reference(reference),
            'camera_configuration':CAMERAS,'physics_steps':0,'input_sha256':hashes,
            'checks':final_checks})
        if not all(final_checks.values()):raise AssertionError(final_checks)
    finally:editor.close_scene()


def metrics_at_reference(reference):
    class Pose:
        position,quaternion=reference
    return metrics(Pose())


if __name__=='__main__':main()
