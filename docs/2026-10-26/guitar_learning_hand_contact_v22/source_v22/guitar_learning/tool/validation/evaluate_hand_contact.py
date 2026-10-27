"""Strict current-contract first-song evaluation, with optional native env0 cameras."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--checkpoint',default='final.pt')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--video',action='store_true')
    args=parser.parse_args()
    import isaacgym
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import GpuPool,FIELDS
    from guitar_learning.training.ppo import PPOTrainer,PPOConfig
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
    from guitar_learning.tool.validation.hand_contact_comparison import install_ablation
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym
    from guitar_learning.training.recording import digest
    from guitar_learning.training import json_io

    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    run=args.run.resolve();settings=json.loads((run/'settings.json').read_text())
    checkpoint=run/args.checkpoint
    if Path(args.checkpoint).name!=args.checkpoint:raise ValueError('Checkpoint filename required')
    arm=settings['song'].get('hand_contact_comparison')
    if arm:install_ablation(arm)
    paths=set(Path('guitar_learning').resolve().rglob('*.py'))
    paths={p for p in paths if 'archive' not in p.parts}
    paths.update([run/'settings.json',checkpoint])
    pins={str(p):digest(p) for p in sorted(paths)}
    (out/'inputs_before.json').write_text(json.dumps(pins,indent=2))
    torch.set_num_threads(1)
    original=gymapi.acquire_gym
    pool=None;videos={};completed={};capture=[];frames=0;failure=None;started=time.monotonic()
    try:
        if args.video:gymapi.acquire_gym=lambda:GraphicsGym(original())
        try:pool=GpuPool(settings,out/'scene')
        finally:gymapi.acquire_gym=original
        policy=SpecialistPolicy(pool.observation['state'].shape[-1],size=settings['size'],role='left',contract=pool.contract).to(settings['device'])
        coordinator=CurriculumCoordinator(policy,pool)
        trainer=PPOTrainer(policy,PPOConfig(**settings['ppo']))
        trainer.load(checkpoint)
        pool.observation=coordinator.restore()
        model_before={k:v.detach().clone() for k,v in policy.state_dict().items()}
        cameras={}
        if args.video:
            positions={'hand':((-.65,.22,.84),(-.27,-.09,.66)),
                       'fullbody':((-.10,2.7,1.1),(-.15,-.10,.65))}
            colors={'thumb':(.94,.24,.27),'index':(.18,.52,.87),'middle':(.10,.67,.49),
                    'ring':(.94,.57,.18),'pinky':(.63,.38,.82)}
            for i,name in enumerate(pool.scene.human_bodies):
                for finger,color in colors.items():
                    if name.startswith('LH:'+finger):
                        pool.scene.gym.set_rigid_body_color(pool.scene.envs[0],pool.scene.actors[0][0],i,gymapi.MESH_VISUAL,gymapi.Vec3(*color))
            for name,(position,target) in positions.items():
                props=gymapi.CameraProperties();props.width=1280;props.height=720;props.horizontal_fov=55.
                camera=pool.scene.gym.create_camera_sensor(pool.scene.envs[0],props)
                if camera<0:raise RuntimeError('Native camera unavailable')
                pool.scene.gym.set_camera_location(camera,pool.scene.envs[0],gymapi.Vec3(*position),gymapi.Vec3(*target))
                cameras[name]=camera
                videos[name]=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-n','-f','rawvideo','-pix_fmt','rgb24',
                    '-s','1280x720','-r','30','-i','-','-an','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(out/(name+'.mp4'))],stdin=subprocess.PIPE)
        ticks=0
        with torch.no_grad():
            while len(completed)<pool.num_envs:
                action=policy.act(*(pool.observation[k] for k in FIELDS),deterministic=True)['action']
                capture_zero=0 not in completed
                observation,reward,cost,terminated,truncated,episodes=pool.step(action)
                ticks+=1
                if capture_zero:
                    s=pool.scene.snapshot()
                    row={k:s[k][0].cpu().numpy().copy() for k in ('q','qd','target','body_state','contact_force','physics_step')}
                    row['action']=action[0].cpu().numpy().copy();capture.append(row)
                    if args.video and ticks%2==0:
                        pool.scene.gym.step_graphics(pool.scene.sim);pool.scene.gym.render_all_camera_sensors(pool.scene.sim)
                        for name,camera in cameras.items():
                            rgba=pool.scene.gym.get_camera_image(pool.scene.sim,pool.scene.envs[0],camera,gymapi.IMAGE_COLOR)
                            videos[name].stdin.write(np.asarray(rgba).reshape(720,1280,4)[...,:3].copy().tobytes())
                        frames+=1
                for episode in episodes:
                    completed.setdefault(episode['env_id'],episode)
                if len(completed)<pool.num_envs:
                    ids=(terminated|truncated).nonzero().flatten()
                    if ids.numel():pool.reset(ids)
                if ticks%300==0:print('evaluation_tick',ticks,'first_ended',len(completed),flush=True)
                if ticks>settings['song_training']['control_ticks']+1:raise RuntimeError('First-song evaluation exceeded fixed score duration')
        if any(not torch.equal(v,model_before[k]) for k,v in policy.state_dict().items()):
            raise AssertionError('Evaluation changed model or curriculum')
        with (out/'episodes.jsonl').open('x') as stream:
            for i in range(pool.num_envs):stream.write(json_io.dumps(completed[i],allow_nan=False)+'\n')
        np.savez_compressed(out/'poses_env0000.npz',**{k:np.stack([r[k] for r in capture]) for k in capture[0]})
        (out/'capture_metadata.json').write_text(json.dumps(dict(joint_names=pool.scene.names,body_names=pool.scene.body_names,
            capture_hz=60,source_physics_hz=240,environment=0,first_clock=4,last_clock=int(capture[-1]['physics_step']),
            frame_mapping='30fps frame n is physical(n+1)/30s; no t0 camera frame; odd final60Hz endpoint has no30fps frame',
            scope='predeclared env0; native Gym pixels, fixed-policy first-song evaluation, no PPO'),indent=2))
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        gymapi.acquire_gym=original
        video_codes={};cleanup_errors=[]
        for name,process in videos.items():
            try:process.stdin.close()
            except OSError as error:cleanup_errors.append(dict(component=name,error=str(error)))
            try:video_codes[name]=process.wait()
            except Exception as error:cleanup_errors.append(dict(component=name,error=str(error)))
        if capture and not (out/'poses_env0000.npz').exists():
            try:np.savez_compressed(out/'partial_poses_env0000.npz',**{k:np.stack([r[k] for r in capture]) for k in capture[0]})
            except Exception as error:cleanup_errors.append(dict(component='partial_capture',error=str(error)))
        if pool:
            try:pool.close()
            except Exception as error:cleanup_errors.append(dict(component='scene_close',error=str(error)))
        changed=[p for p,h in pins.items() if digest(p)!=h]
        episodes=list(completed.values());n=len(episodes)
        report=dict(completed=failure is None and not changed and not cleanup_errors and all(v==0 for v in video_codes.values()),failure=failure,
            checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),arm=arm,requested_first_episodes=settings['num_envs'],first_episodes=n,
            safe_first=sum(e['reason']=='timeline_complete' and e['left_curriculum']['full_safe'] for e in episodes),
            mean_achieved_notes=sum(e['song']['left_success_count'] for e in episodes)/n if n else None,
            deterministic=True,training_updates=0,wall_s=time.monotonic()-started,changed_inputs=changed,
            native_video=args.video,video_frames=frames,video_exit_codes=video_codes,cleanup_errors=cleanup_errors,
            scene=pool.scene.diagnostics if pool else None,
            limitation='One training seed; finite source geometric/load candidates are not calibrated pressure or sound; first episodes include physical failures.')
        (out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False))
        if failure is None and not report['completed']:raise RuntimeError('Evaluation immutability or encoder audit failed')


if __name__=='__main__':main()
