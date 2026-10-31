"""넥 아래 손목, 뒷면 엄지, 줄 앞 네 손가락을 갖는 초기 후보를 찾는다."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from guitar_learning.native.paths import HUMAN

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'초기자세_v1'
sys.path.insert(0,str(BASE/'tools'))
from make_pose import PoseGeometry,FINGERS,load_prepared_reset_contract,write
sys.path.insert(0,str(ROOT/'초기자세_v4/tools'))
from create_pose import hand_axes
from guitar_learning.gpu.contact import load_fingertip_pad,load_thumb_support,load_press_surface
OUT=Path(__file__).resolve().parents[1]


def unit(v):return v/np.linalg.norm(v)


def main():
    c=load_prepared_reset_contract();g=PoseGeometry(c)
    original=json.loads((BASE/'initial_pose.json').read_text());q=np.array(original['q105_rad'])
    before=json.loads((ROOT/'초기자세_v4/initial_pose.json').read_text())
    ids=[i for i,n in enumerate(g.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:'))]
    wrist=[i for i,n in enumerate(g.names) if n.startswith('L_Wrist')]
    fingers=[i for i,n in enumerate(g.names) if n.startswith('LH:')]
    lo=np.asarray(c['initial']['native_PD_properties']['lower'])[ids]+np.radians(1)
    hi=np.asarray(c['initial']['native_PD_properties']['upper'])[ids]-np.radians(1)
    pad=load_fingertip_pad();thumb=load_thumb_support();front=load_press_surface([2],[6])['plane_G']
    local=[thumb['points_local'].mean(0)]+[points.mean(0) for points in pad['points_local']]
    body=['LH:thumb3']+['LH:'+f+'3' for f in FINGERS[1:]]
    wanted=np.array([[.003,.025,-.023],[.006,.055,.030],[.006,.035,.030],[.006,.015,.030],[.006,-.005,.030]])
    wanted_wrist=np.array([.085,.02,-.045])
    capsules={}
    for b in ET.parse(HUMAN).iter('body'):
        if b.get('name') in ('L_Shoulder','L_Elbow'):
            geom=b.find('geom');capsules[b.get('name')]=(np.fromstring(geom.get('fromto'),sep=' ').reshape(2,3),float(geom.get('size')))
    def geometry(poses):
        points=np.array([g.gr.inv().apply(poses[b][0]+poses[b][1].apply(p)-g.gp) for b,p in zip(body,local)])
        wp=g.gr.inv().apply(poses['L_Wrist'][0]-g.gp)
        gaps=[]
        for n,(ends,radius) in capsules.items():
            p,r=poses[n];v=g.gr.inv().apply(p+r.apply(ends)-g.gp)
            gaps.append(min(float(np.max(np.min(v@plane[:,:3].T+plane[:,3],axis=0)-radius)) for plane in g.envelopes))
        return points,wp,np.array(gaps)
    def trial(x):
        v=q.copy();v[ids]=x;return v
    def residual(x):
        v=trial(x);poses=g.fk(v);points,wp,gaps=geometry(poses)
        hf,hn=hand_axes(poses);fa=unit(poses['L_Wrist'][0]-poses['L_Elbow'][0])
        return np.r_[300*(points-wanted).flatten(),80*(wp-wanted_wrist),
            3*(hn-[0,0,1]),1*(hf-[0,1,0]),1*(fa-[0,1,0]),
            500*np.maximum(.005-gaps,0),.2*(v[fingers]-q[fingers]),.2*v[wrist],.04*(x-q[ids])]
    rng=np.random.RandomState(7)
    seeds=[q[ids],np.array(before['q105_rad'])[ids],(lo+hi)/2]
    # 기존 후보와 여러 유한한 시작점에서 탐색한다.
    for v in ('초기자세_v2','초기자세_v3'):
        seeds.append(np.array(json.loads((ROOT/v/'initial_pose.json').read_text())['q105_rad'])[ids])
    seeds.extend(q[ids]+rng.normal(0,.45,len(ids)) for _ in range(3))
    fits=[]
    for k,seed in enumerate(seeds):
        fit=least_squares(residual,np.clip(seed,lo+1e-7,hi-1e-7),bounds=(lo,hi),max_nfev=400,ftol=1e-8,xtol=1e-8,gtol=1e-8)
        fits.append(fit);print('fit',k,float(np.linalg.norm(residual(fit.x))),flush=True)
    fit=min(fits,key=lambda f:np.linalg.norm(residual(f.x)));v=trial(fit.x);poses=g.fk(v);points,wp,armgaps=geometry(poses)
    hf,hn=hand_axes(poses);fa=unit(poses['L_Wrist'][0]-poses['L_Elbow'][0])
    angle=lambda a,b:float(np.degrees(np.arccos(np.clip(a@b,-1,1))))
    full_gaps={f:min(g.gaps(v,f).values()) for f in FINGERS}
    metrics=dict(scope='original model FK search; no new physics',wrist_G_m=wp.tolist(),pad_centers_G_m={f:p.tolist() for f,p in zip(FINGERS,points)},
        rear_plane_G=thumb['plane'].tolist(),front_plane_G=np.asarray(front).tolist(),
        hand_axes_world=dict(forward=hf.tolist(),palmar=hn.tolist(),forearm=fa.tolist()),errors_deg=dict(palm_up=angle(hn,np.array([0,0,1.])),hand_forward=angle(hf,np.array([0,1.,0])),forearm_forward=angle(fa,np.array([0,1.,0]))),
        source_gap_lower_bound_mm={f:d*1000 for f,d in full_gaps.items()},arm_gap_lower_bound_mm=(armgaps*1000).tolist(),
        target_pad_error_mm=(np.linalg.norm(points-wanted,axis=1)*1000).tolist(),joints=[dict(name=g.names[i],degrees=float(v[i]*180/np.pi),native_margin_deg=float(min(v[i]-lo[j],hi[j]-v[i])*180/np.pi+1)) for j,i in enumerate(ids)])
    print(json.dumps(metrics,ensure_ascii=False),flush=True)
    write(OUT/'search_result.json',metrics)
    state=copy.deepcopy(original['state']);old=g.fk(q)
    for i in ids:state['human_dof_states'][i]=dict(pos=float(v[i]),vel=0.)
    for i,n in enumerate(c['initial']['human_body_names']):
        p,r=poses[n];op,orr=old[n]
        if np.linalg.norm(p-op)>1e-12 or (orr.inv()*r).magnitude()>1e-12:
            state['human_body_states'][i]['pose']=dict(p=dict(zip('xyz',p.tolist())),r=dict(zip('xyzw',r.as_quat().tolist())))
            state['human_body_states'][i]['vel']=dict(linear=dict.fromkeys('xyz',0.),angular=dict.fromkeys('xyz',0.))
    assert all(state['human_dof_states'][i]==original['state']['human_dof_states'][i] for i in range(105) if i not in ids)
    assert state['guitar_body_states']==original['state']['guitar_body_states'] and state['chair_body_states']==original['state']['chair_body_states']
    target=np.array(original['target105_rad']);target[ids]=v[ids]
    write(OUT/'candidate.json',dict(schema='left_standby_initial.v5_candidate',diagnostic_only=True,physical_hold_verified=False,joint_names=g.names,q105_rad=v.tolist(),target105_rad=target.tolist(),state=state,changed_joint_names=[g.names[i] for i in ids],source_sha256=c['source_sha256']))


if __name__=='__main__':main()
