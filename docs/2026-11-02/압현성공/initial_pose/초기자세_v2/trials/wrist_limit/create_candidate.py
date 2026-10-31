"""왼팔·손목만 보정한 초기 자세 후보를 원모델 FK로 비교 시각화한다."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import least_squares, minimize, differential_evolution
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parents[2]/'초기자세_v1'
sys.path.insert(0,str(BASE/'tools'))
from make_pose import PoseGeometry,FINGERS,load_prepared_reset_contract,write
OUT=Path(__file__).resolve().parents[1]


def main():
    c=load_prepared_reset_contract();g=PoseGeometry(c)
    original=json.loads((BASE/'initial_pose.json').read_text());q=np.asarray(original['q105_rad'])
    fk=g.fk(q);wp,wr=fk['L_Wrist']
    wanted_p=wp+np.array([-.040,.015,0.])+g.gr.apply([.040,0,.015])
    wanted_r=Rotation.from_rotvec(g.gr.apply([0,0,np.radians(25)]))*wr
    ids=[i for i,n in enumerate(g.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]
    native_low=np.asarray(c['initial']['native_PD_properties']['lower']);native_high=np.asarray(c['initial']['native_PD_properties']['upper'])
    lo=np.maximum(native_low[ids]+1e-7,q[ids]-np.radians(35));hi=np.minimum(native_high[ids]-1e-7,q[ids]+np.radians(35))
    def trial(x):
        v=q.copy();v[ids]=x;return v
    def residual(x):
        v=trial(x);p,r=g.fk(v)['L_Wrist']
        return np.r_[200*(p-wanted_p),10*(wanted_r.inv()*r).as_rotvec(),.06*(x-q[ids])]
    fit=least_squares(residual,np.clip(q[ids],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=300,ftol=1e-10,xtol=1e-10,gtol=1e-10)
    candidate=trial(fit.x)
    thumb_ids=[i for i,n in enumerate(g.names) if n.startswith('LH:thumb')]
    def thumb_cost(x):
        v=candidate.copy();v[thumb_ids]=x
        gaps=np.array(list(g.gaps(v,'thumb').values()))
        return 1e6*np.maximum(.015-gaps,0).dot(np.maximum(.015-gaps,0))+np.sum((x-q[thumb_ids])**2)
    thumb_bounds=list(zip(np.maximum(native_low[thumb_ids]+1e-7,q[thumb_ids]-np.radians(20)),np.minimum(native_high[thumb_ids]-1e-7,q[thumb_ids]+np.radians(20))))
    thumb_fit=minimize(thumb_cost,q[thumb_ids],bounds=thumb_bounds,method='L-BFGS-B')
    candidate[thumb_ids]=thumb_fit.x if min(g.gaps(candidate,'thumb').values())<.01 else q[thumb_ids]
    if min(g.gaps(candidate,'thumb').values())<.01:
        thumb_fit=differential_evolution(thumb_cost,thumb_bounds,seed=7,maxiter=80,popsize=8,polish=True)
        candidate[thumb_ids]=thumb_fit.x
    changed_ids=ids+thumb_ids
    poses=g.fk(candidate);p,r=poses['L_Wrist']
    gaps={f:min(g.gaps(candidate,f).values()) for f in FINGERS}
    if min(gaps.values())<.01:raise RuntimeError('후보 손가락 간격10mm 미달: '+str(gaps))
    if np.linalg.norm(p-wanted_p)>.003 or (wanted_r.inv()*r).magnitude()>np.radians(2):raise RuntimeError('요청 손목 보정 오차가 큼')
    state=copy.deepcopy(original['state'])
    for i in changed_ids:state['human_dof_states'][i]=dict(pos=float(candidate[i]),vel=0.)
    changed_bodies=[]
    for i,name in enumerate(c['initial']['human_body_names']):
        np_,nr=poses[name];op,orr=fk[name]
        if np.linalg.norm(np_-op)>1e-12 or (orr.inv()*nr).magnitude()>1e-12:
            state['human_body_states'][i]['pose']=dict(p=dict(zip('xyz',np_.tolist())),r=dict(zip('xyzw',nr.as_quat().tolist())))
            state['human_body_states'][i]['vel']=dict(linear=dict.fromkeys('xyz',0.),angular=dict.fromkeys('xyz',0.))
            changed_bodies.append(name)
    assert all(state['human_dof_states'][i]==original['state']['human_dof_states'][i] for i in range(105) if i not in changed_ids)
    assert state['guitar_body_states']==original['state']['guitar_body_states'] and state['chair_body_states']==original['state']['chair_body_states']
    target=np.array(original['target105_rad']);target[changed_ids]=candidate[changed_ids]
    artifact=dict(schema='left_standby_initial.v2',diagnostic_only=True,physical_hold_verified=False,joint_names=g.names,q105_rad=candidate.tolist(),target105_rad=target.tolist(),state=state,
        changed_arm_joint_names=[g.names[i] for i in ids],unchanged_nonthumb_finger_angles=True,thumb_clearance_adjusted=True,source_sha256=c['source_sha256'],base_pose_sha256=hashlib.sha256((BASE/'initial_pose.json').read_bytes()).hexdigest())
    write(OUT/'initial_pose.json',artifact)
    report=dict(scope='original model source FK visualization; no new physics or training',requested_wrist_translation_world_m=(wanted_p-wp).tolist(),actual_wrist_translation_world_m=(p-wp).tolist(),actual_wrist_rotation_deg=float((wr.inv()*r).magnitude()*180/np.pi),position_error_mm=float(np.linalg.norm(p-wanted_p)*1000),orientation_error_deg=float((wanted_r.inv()*r).magnitude()*180/np.pi),finger_neck_gap_lower_bound_mm={f:v*1000 for f,v in gaps.items()},old_elbow_world_m=fk['L_Elbow'][0].tolist(),new_elbow_world_m=poses['L_Elbow'][0].tolist(),changed_bodies=changed_bodies,
        thumb_joints=[dict(name=g.names[i],before_deg=float(q[i]*180/np.pi),after_deg=float(candidate[i]*180/np.pi)) for i in thumb_ids],arm_joints=[dict(name=g.names[i],before_deg=float(q[i]*180/np.pi),after_deg=float(candidate[i]*180/np.pi)) for i in ids])
    write(OUT/'measurements.json',report)
    render(c,original['state'],state,wp)
    print(json.dumps(report,ensure_ascii=False),flush=True)


def render(c,before,after,lookat):
    import mujoco
    from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model,set_body_poses,add_strings
    model,data,mapping,_=build_model(c['initial'])
    colors=((.95,.78,.18),(.20,.55,.95),(.15,.75,.52),(.96,.48,.20),(.70,.38,.92))
    for geom_id,body_id in enumerate(model.geom_bodyid):
        n=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,int(body_id)) or ''
        for f,col in zip(FINGERS,colors):
            if n.startswith('human/LH:'+f):model.geom_rgba[geom_id,:3]=col
    renderer=mujoco.Renderer(model,height=720,width=1280)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23)
    try:
        for label,state in [('before',before),('adjusted',after)]:
            set_body_poses(model,data,mapping,state)
            for view,az,elev,distance in [('front',270,-10,.60),('oblique',305,-15,.60),('full',270,-5,2.0)]:
                cam=mujoco.MjvCamera();mujoco.mjv_defaultCamera(cam)
                # Both states use exactly the same world look-at and camera.
                cam.lookat[:]=lookat if view!='full' else [-.1,0,.65]
                cam.distance=distance;cam.azimuth=az;cam.elevation=elev
                renderer.update_scene(data,camera=cam)
                endpoints=np.array([[[state['guitar_body_states'][c['initial']['guitar_body_names'].index(n)]['pose']['p'][a] for a in 'xyz'] for n in ('G:string%d'%i,'G:string%d_end'%i)] for i in range(1,7)])
                add_strings(renderer.scene,endpoints)
                im=Image.fromarray(renderer.render());draw=ImageDraw.Draw(im)
                draw.text((15,15),label+' | '+view+' | source FK preview',font=font,fill='white')
                im.save(OUT/(label+'_'+view+'.png'))
        sheet=Image.new('RGB',(1600,1350),'#171b24')
        for y,view in enumerate(('front','oblique','full')):
            for x,label in enumerate(('before','adjusted')):
                sheet.paste(Image.open(OUT/(label+'_'+view+'.png')).resize((800,450)),(x*800,y*450))
        sheet.save(OUT/'comparison.png')
    finally:renderer.close()


if __name__=='__main__':main()
