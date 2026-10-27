"""Four-panel saved-pose comparison; fixed commands, not policy learning; physics0."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from guitar_learning.training import json_io


def require(ok,message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def write(path,value):
    with Path(path).open('x') as stream:
        json_io.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')


def pose_state(names,frame,initial):
    require(names==(['human/'+n for n in initial['human_body_names']]+['guitar/'+n for n in initial['guitar_body_names']]+['chair/box']), 'Original106 body order required')
    require(frame.shape==(106,13),'Actual106 body pose frame required')
    result={a+'_body_states':[] for a in ('human','guitar','chair')}
    for name,row in zip(names,frame):
        result[name.split('/',1)[0]+'_body_states'].append(dict(pose=dict(
            p=dict(zip('xyz',map(float,row[:3]))),r=dict(zip('xyzw',map(float,row[3:7]))))))
    return result


def video_indices(clock):
    import numpy as np
    clock=np.asarray(clock)
    require(clock.shape[1:]==(4,) and len(clock)>1 and
        np.array_equal(clock,np.repeat((np.arange(len(clock))*4)[:,None],4,axis=1)), 'Actual4-row60Hz clock required')
    return range(1,len(clock))


def fit_camera(model,low,high):
    import numpy as np
    center=(low+high)/2;half=(high-low)/2
    vertical=np.tan(np.deg2rad(float(model.cam_fovy[0]))/2)
    distance=max(half[2]/(.56*vertical),half[0]/(.9*vertical*1280/720),.08)
    model.cam_pos[0]=[center[0],high[1]+distance,center[2]]
    model.cam_quat[0]=[0.,0.,2**-.5,2**-.5]
    return dict(position=model.cam_pos[0].tolist(),quaternion_wxyz=model.cam_quat[0].tolist(),
        fovy_degrees=float(model.cam_fovy[0]),scope='One fixed camera across4 cases/all recorded frames; hand mesh bounds only. Visible portion of neck, not whole-neck fit.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();folder,out=args.probe.resolve(),args.out.resolve()
    pins={str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
    def read(path):
        pins[str(path)]=sha(path)
        return json.loads(path.read_text())
    report=read(folder/'report.json');meta=read(folder/'capture_metadata.json');initial=read(folder/'visual_initial.json')
    require(report['completed'] and report['gpu_scene']['closed'] and report['gpu_scene']['num_envs']==4 and
        report['gpu_scene']['physx_use_gpu'] and report['gpu_scene']['use_gpu_pipeline'],
        'Recorded4-row probe with normal close required')
    inputs=read(folder/'inputs_before.json')
    require(all(Path(p).is_file() and sha(p)==h for p,h in inputs.items()),'Original probe inputs changed')
    pins.update(inputs)
    import numpy as np
    path=folder/meta['capture']['path']
    require(sha(path)==meta['capture']['sha256']==report['capture_audit']['sha256'],'Actual capture SHA mismatch')
    pins[str(path)]=sha(path)
    with np.load(path,allow_pickle=False) as archive:
        arrays={k:archive[k].copy() for k in archive.files}
    indices=video_indices(arrays['clock']);ticks=len(indices)
    require(ticks==report['actual_control_ticks'] and arrays['body_state'].shape==(ticks+1,4,106,13) and
        arrays['q'].shape==arrays['target'].shape==(ticks+1,4,105) and arrays['action'].shape==(ticks+1,4,39) and
        all(np.isfinite(v).all() for v in arrays.values()),'Invalid source capture')
    require(report['gpu_scene']['physics_steps']==ticks*4,'Native capture step coverage differs')
    # Only the root executes this entry point after the GPU probe has closed.
    os.environ.setdefault('MUJOCO_GL','osmesa')
    os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE','1')
    import mujoco
    from PIL import Image,ImageDraw,ImageFont
    from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import asset_paths,build_model,set_body_poses,add_strings
    from guitar_learning.tool._rendering import encoder,probe,FONT
    assets=set().union(*(asset_paths(a['path']) for a in initial['loaded_assets']))
    require(all(inputs.get(str(p))==sha(p) for p in assets),'Visible source asset SHA differs')
    for path in assets|{FONT,ROOT/'guitar_learning/tool/_rendering.py',ROOT/'guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py',ROOT/'guitar_learning/native/initial_pose_video60_v1/replay_v6.py'}:
        pins[str(path)]=sha(path)
    out.mkdir(parents=True,exist_ok=False);write(out/'inputs_before.json',pins)
    model,data,mapping,xml=build_model(initial);(out/'source_visual.xml').write_text(xml)
    hand=np.array([i for i in range(model.ngeom) if model.body(int(model.geom_bodyid[i])).name.startswith('human/LH:')])
    require(hand.size>0,'Visible source left hand required')
    require(any(model.mesh(int(model.geom_dataid[i])).name.startswith('guitar/guitar_neck') for i in range(model.ngeom)
        if model.geom_type[i]==mujoco.mjtGeom.mjGEOM_MESH),'Original neck mesh required')
    radius=model.geom_rbound[hand,None];low=np.full(3,np.inf);high=np.full(3,-np.inf)
    max_position=max_rotation=0.
    for frame in indices:
        for env in range(4):
            audit=set_body_poses(model,data,mapping,pose_state(meta['body_names'],arrays['body_state'][frame,env],initial))
            max_position=max(max_position,audit['max_position_error_m']);max_rotation=max(max_rotation,audit['max_rotation_error_rad'])
            low=np.minimum(low,(data.geom_xpos[hand]-radius).min(0));high=np.maximum(high,(data.geom_xpos[hand]+radius).max(0))
    camera=fit_camera(model,low,high)
    write(out/'presentation.json',dict(camera=camera,width=1280,height=720,fps=60,frames=ticks,duration_s=ticks/60,
        source_probe=str(folder),schedule_completed=report['schedule_completed'],case_order=[0,1,2,3],
        scope='Four simultaneous actual cases at original60Hz cadence. No interpolation/new physics/policy or outcome-based case selection. Censored probes retain actual shorter duration.'))
    renderer=mujoco.Renderer(model,height=360,width=640)
    process=encoder(out/'joint_distribution_60fps.mp4')
    font=ImageFont.truetype(str(FONT),18);small=ImageFont.truetype(str(FONT),13)
    labels=['끝관절 집중','관절 분담','대기 목표','펴짐 목표'];finger_labels=['검지','중지','약지','소지']
    audits=[]
    try:
        for frame in indices:
            canvas=Image.new('RGB',(1280,720))
            for env in range(4):
                body=arrays['body_state'][frame,env]
                audit=set_body_poses(model,data,mapping,pose_state(meta['body_names'],body,initial))
                centers=data.geom_xpos[hand];r=model.geom_rbound[hand]
                depth=model.cam_pos[0,1]-centers[:,1]-r
                vertical=np.tan(np.deg2rad(float(model.cam_fovy[0]))/2)
                px=float(np.max((abs(centers[:,0]-model.cam_pos[0,0])+r)/(depth*vertical*1280/720)))
                py=float(np.max((abs(centers[:,2]-model.cam_pos[0,2])+r)/(depth*vertical)))
                require((depth>0).all() and px<=.900001 and py<=.560001,'Hand overlaps caption bounds')
                before=data.xpos.copy(),data.xquat.copy(),float(data.time)
                renderer.update_scene(data,camera='front')
                endpoints=np.array([[body[meta['body_names'].index('guitar/G:string%d%s'%(s,suffix)),:3] for suffix in ('','_end')] for s in range(1,7)])
                add_strings(renderer.scene,endpoints)
                panel=Image.fromarray(renderer.render());draw=ImageDraw.Draw(panel)
                draw.rectangle((0,0,640,55),fill=(22,27,34));draw.rectangle((0,281,640,360),fill=(22,27,34))
                draw.text((8,3),'고정명령 비교 · 정책 학습 아님 | env%d %s'%(env,labels[env]),font=font,fill='white')
                draw.text((8,29),'실측 %.3fs | 목표 1x/1z/PIP/DIP = %s°'%(arrays['clock'][frame,env]/240.,'/'.join(map(str,meta['cases'][env]['goal_per_finger_degrees']))),font=small,fill='white')
                angles=np.rad2deg(arrays['actual_song_angles'][frame,env])
                for f in range(4):
                    label = ('%s 실제 MCP/PIP/DIP = %+.1f / %+.1f / %+.1f°'%(finger_labels[f],*angles[f])
                        if arrays['actual_song_valid'][frame,env,f].all() else finger_labels[f]+' 기하 측정 무효(0각도로 해석하지 않음)')
                    draw.text((8,283+16*f),label,font=small,fill='white')
                draw.text((330,335),'원본60Hz · 추가 물리0 · 보간 없음',font=small,fill='white')
                require(np.array_equal(before[0],data.xpos) and np.array_equal(before[1],data.xquat) and before[2]==data.time==0,'Renderer changed actual body poses')
                canvas.paste(panel,((env%2)*640,(env//2)*360))
                audits.append(dict(frame=int(frame),env_id=env,source_clock=int(arrays['clock'][frame,env]),pose=audit,projection=[px,py]))
            if frame in (1,max(1,ticks//2),ticks):canvas.save(out/('preview_%04d.png'%frame))
            if frame==ticks:canvas.save(out/'joint_distribution_last_frame.png')
            process.stdin.write(canvas.tobytes())
        process.stdin.close();require(process.wait()==0,'ffmpeg failed')
        media=probe(out/'joint_distribution_60fps.mp4',ticks)
        require(all(Path(p).is_file() and sha(p)==h for p,h in pins.items()),'Render inputs changed')
        write(out/'pose_audit.json',dict(completed=True,frames=audits,max_position_error_m=max_position,max_rotation_error_rad=max_rotation,new_physics_steps=0))
        image=out/'joint_distribution_last_frame.png'
        write(out/'report.json',dict(completed=True,source_probe=str(folder),media=media,
            final_image=dict(path=str(image),sha256=sha(image)),new_physics_steps=0,inputs_unchanged=True,
            schedule_completed=report['schedule_completed'],scope='Four actual fixed-command cases; not new learned-policy performance or anatomical/pressure certification'))
        print(json_io.dumps(dict(completed=True,image=str(image),video=media['path'])))
    finally:
        if process.poll() is None:process.kill();process.wait()
        renderer.close()


if __name__=='__main__':
    main()
