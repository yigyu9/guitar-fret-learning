"""원본·새 초기 자세와 실제5초 유지 상태를 동일 카메라에서 그린다."""
import copy
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image, ImageDraw, ImageFont
from make_pose import PoseGeometry, FINGERS, load_prepared_reset_contract, write
OUT=Path(__file__).resolve().parents[1]


def main():
    import mujoco
    from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model,set_body_poses,add_strings
    c=load_prepared_reset_contract();artifact=json.loads((OUT/'initial_pose.json').read_text());geometry=PoseGeometry(c)
    model,data,mapping,_=build_model(c['initial'])
    colors=((.95,.78,.18),(.20,.55,.95),(.15,.75,.52),(.96,.48,.20),(.70,.38,.92))
    for geom_id,body_id in enumerate(model.geom_bodyid):
        name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,int(body_id)) or ''
        for f,color in zip(FINGERS,colors):
            if name.startswith('human/LH:'+f):model.geom_rgba[geom_id,:3]=color
    renderer=mujoco.Renderer(model,height=720,width=1280)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    states={'before':c['state'],'initial':artifact['state']}
    native=OUT/'native_hold.npz';report={}
    if native.exists():
        traces=np.load(native);meta=json.loads((OUT/'native_metadata.json').read_text())
        def state_at(index):
            state=copy.deepcopy(c['state']);bodies=traces['body_state'][index]
            for i,n in enumerate(meta['body_names']):
                kind,name=n.split('/',1);names=meta.get(kind+'_body_names',['box']);k=names.index(name)
                state[kind+'_body_states'][k]['pose']=dict(p=dict(zip('xyz',bodies[i,:3].tolist())),r=dict(zip('xyzw',bodies[i,3:7].tolist())))
            return state
        states['reset_snapshot']=state_at(0);states['native_5s']=state_at(-1)
        # Static state and actual native readback are measured independently using exact body poses.
        rows=[]
        for t in range(len(traces['q'])):
            bodies=traces['body_state'][t];gb=bodies[meta['body_names'].index('guitar/guitar')];gr=Rotation.from_quat(gb[3:7]);mins=[]
            for f in FINGERS:
                gaps=[]
                for n,verts in geometry.parts.items():
                    if n.startswith('LH:'+f):
                        body=bodies[meta['body_names'].index('human/'+n)];pts=gr.inv().apply(body[:3]+Rotation.from_quat(body[3:7]).apply(verts)-gb[:3])
                        gaps.append(min(float(np.max(np.min(pts@p[:,:3].T+p[:,3],axis=0))) for p in geometry.envelopes))
                mins.append(min(gaps))
            rows.append(mins)
        finger_ids=[i for i,n in enumerate(meta['joint_names']) if n.startswith('LH:')]
        other=[i for i in range(105) if i not in finger_ids]
        original_q=geometry.q0;goal=np.asarray(artifact['q105_rad']);q=traces['q'];bs=traces['body_state'];gid=meta['body_names'].index('guitar/guitar')
        contact_ids=[i for i,n in enumerate(meta['body_names']) if any(n.startswith('human/LH:'+f) for f in FINGERS)]
        reports=[]
        for j,f in enumerate(FINGERS):
            joints=[i for i,n in enumerate(meta['joint_names']) if n.startswith('LH:'+f)]
            ids=[i for i,n in enumerate(meta['body_names']) if n.startswith('human/LH:'+f)]
            reports.append(dict(finger=f,minimum_neck_clearance_lower_bound_mm=float(np.min(np.array(rows)[:,j])*1000),
                final_neck_clearance_lower_bound_mm=float(rows[-1][j]*1000),final_joint_error_max_deg=float(np.max(np.abs(q[-1,joints]-goal[joints]))*180/np.pi),
                maximum_segment_net_contact_force_N=float(np.linalg.norm(traces['contact_force'][:,ids],axis=-1).max())))
        report=dict(fingers=reports,initial_nonfinger_q_error_max_rad=float(np.max(np.abs(q[0,other]-original_q[other]))),
            initial_finger_q_error_max_rad=float(np.max(np.abs(q[0,finger_ids]-goal[finger_ids]))),
            maximum_guitar_displacement_mm=float(np.linalg.norm(bs[:,gid,:3]-bs[0,gid,:3],axis=-1).max()*1000),
            maximum_nonfinger_q_drift_deg=float(np.max(np.abs(q[:,other]-q[0,other]))*180/np.pi),
            scope='5s hold at60Hz; t0 body pose is reset cache/source FK, subsequent60Hz samples are actual native bodies; nonfinger initial q exact; natural physical movement permitted; source geometry envelope clearance bound, not cooked shape or contact-pair certification')
        write(OUT/'verification.json',report)
    try:
        for stage,state in states.items():
            set_body_poses(model,data,mapping,state)
            for view,azimuth,elev in [('front',270,-10),('oblique',305,-15),('full',270,-5)]:
                cam=mujoco.MjvCamera();mujoco.mjv_defaultCamera(cam)
                wrist=state['human_body_states'][c['initial']['human_body_names'].index('L_Wrist')]['pose']['p']
                cam.lookat[:]=[wrist[a] for a in 'xyz'] if view!='full' else [-.1,0,.65]
                cam.distance=.42 if view!='full' else 2.0;cam.azimuth=azimuth;cam.elevation=elev
                renderer.update_scene(data,camera=cam)
                endpoints=np.array([[[state['guitar_body_states'][c['initial']['guitar_body_names'].index(n)]['pose']['p'][a] for a in 'xyz'] for n in ('G:string%d'%i,'G:string%d_end'%i)] for i in range(1,7)])
                add_strings(renderer.scene,endpoints)
                im=Image.fromarray(renderer.render());draw=ImageDraw.Draw(im)
                draw.text((15,15),stage+' | '+view,fill='white',font=font)
                for j,(f,color) in enumerate(zip(FINGERS,colors)):
                    draw.text((15+j*185,680),f,fill=tuple(int(v*255) for v in color),font=font)
                im.save(OUT/(stage+'_'+view+'.png'))
        # A single comparison sheet for easy review.
        sheet=Image.new('RGB',(1600,1350),'#171b24')
        for y,stage in enumerate(('before','initial','native_5s') if native.exists() else ('before','initial')):
            for x,view in enumerate(('front','oblique')):
                sheet.paste(Image.open(OUT/(stage+'_'+view+'.png')).resize((800,450)),(x*800,y*450))
        sheet.save(OUT/'comparison.png')
    finally:renderer.close()
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
