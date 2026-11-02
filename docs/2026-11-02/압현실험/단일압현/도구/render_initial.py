"""초기 자세 미확보 조합의 실제 native 유지 명령 진단 영상. 학습 정책이 아니다."""
if __name__=='__main__':
    import isaacgym
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('single18_runtime',HERE/'runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)


def main():
    from isaacgym import gymapi
    import numpy as np
    import torch
    from guitar_learning.tool.demonstration.render_finger_skill import _create_cameras,_encoder
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym,finish_video
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--provenance',type=Path,required=True)
    parser.add_argument('--case',required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--num-envs',type=int,default=4)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(1)
    pool=None;videos={};cleanup=[];episode=None;frames=0;failure=None
    pins={str(p):runtime.digest(p) for p in (Path(__file__),HERE/'runtime.py',args.catalog,args.provenance)}
    provenance=json.loads(args.provenance.read_text())
    for name,expected in provenance['active_physical_inputs'].items():
        path=Path(name) if Path(name).is_absolute() else runtime.ROOT/name
        if runtime.digest(path)!=expected:raise ValueError('초기 진단 물리 입력 변경: '+name)
        pins[str(path)]=expected
    try:
        with runtime.configuration_runtime(args.catalog,args.provenance,args.case,unverified=True) as (config,row):
            settings=runtime.build_settings(config,row,num_envs=4)
            with runtime.experiment_runtime(config):
                original=gymapi.acquire_gym
                gymapi.acquire_gym=lambda:GraphicsGym(original())
                try:pool=runtime.natural.NaturalPool(settings,args.out/'scene')
                finally:gymapi.acquire_gym=original
                cameras=_create_cameras(pool.scene,gymapi)
                videos={name:_encoder(args.out/(name+'.mp4')) for name in cameras}
                for tick in range(300):
                    _,_,_,terminated,truncated,episodes=pool.step(pool.execution_hold_action.clone())
                    for value in episodes:
                        if value['env_id']==0:episode=value
                    done=bool(terminated[0] or truncated[0])
                    if (tick+1)%2==0 or done:
                        pool.scene.gym.step_graphics(pool.scene.sim)
                        pool.scene.gym.render_all_camera_sensors(pool.scene.sim)
                        for name,camera in cameras.items():
                            pixels=pool.scene.gym.get_camera_image(pool.scene.sim,pool.scene.envs[0],camera,gymapi.IMAGE_COLOR)
                            rgb=np.asarray(pixels).reshape(720,1280,4)[...,:3].copy()
                            # 첫tick 종료도 확인 가능한1초 정지화면으로 보존한다.
                            repeats=30 if done and frames==0 else 1
                            for _ in range(repeats):videos[name].stdin.write(rgb.tobytes())
                        frames+=repeats
                    if done:break
    except BaseException as error:
        failure=repr(error)
    finally:
        for name,video in videos.items():
            code,errors=finish_video(video);cleanup+=errors
            if code:cleanup.append(name+' encoder '+str(code))
        if pool is not None:
            try:pool.close()
            except BaseException as error:cleanup.append(repr(error))
    changed=[p for p,h in pins.items() if runtime.digest(p)!=h]
    report=dict(completed=failure is None and not cleanup and not changed and frames>0,
        failure=failure,cleanup_errors=cleanup,changed_inputs=changed,case=args.case,frames=frames,
        learned_policy=False,scope='unverified initial-placement finite hold diagnostic; no learned pressing claim',pins=pins)
    runtime.write(args.out/'report.json',report)
    runtime.write(args.out/'episode_env0000.json',episode or {'left_note_ledger': {'values': {'left': [False]}}})
    if not report['completed']:raise RuntimeError('초기 진단 영상 실패 '+str(report))


if __name__=='__main__':main()
