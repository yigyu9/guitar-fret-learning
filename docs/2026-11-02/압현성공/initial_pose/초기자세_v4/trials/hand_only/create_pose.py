"""손바닥은 위, MCP가 향하는 길이축과 전완은 정면으로 맞춘다."""
import copy
import hashlib
from pathlib import Path
import sys
import json
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from guitar_learning.native.paths import HUMAN

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'초기자세_v1'
sys.path.insert(0,str(BASE/'tools'))
from make_pose import PoseGeometry,FINGERS,load_prepared_reset_contract,write
sys.path.insert(0,str(ROOT/'초기자세_v2/tools'))
import create_candidate as media
OUT=Path(__file__).resolve().parents[1]


def unit(v):return v/np.linalg.norm(v)


def hand_axes(poses):
    palm=poses['LH:palm'][0]
    mean=np.mean([poses['LH:'+f+'1'][0] for f in ('index','middle','ring','pinky')],axis=0)
    forward=unit(mean-palm)
    lateral=poses['LH:pinky1'][0]-poses['LH:index1'][0]
    normal=unit(np.cross(lateral,forward))
    if normal@poses['LH:palm'][1].apply([0,0,-1])<0:normal=-normal
    return forward,normal


def main():
    c=load_prepared_reset_contract();g=PoseGeometry(c)
    original=json.loads((BASE/'initial_pose.json').read_text());q=np.asarray(original['q105_rad'])
    previous=json.loads((ROOT/'초기자세_v3/initial_pose.json').read_text())
    ids=[i for i,n in enumerate(g.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]
    wrist=[i for i,n in enumerate(g.names) if n.startswith('L_Wrist')]
    low=np.asarray(c['initial']['native_PD_properties']['lower']);high=np.asarray(c['initial']['native_PD_properties']['upper'])
    lo=low[ids]+np.radians(3);hi=high[ids]-np.radians(3)
    for j,i in enumerate(ids):
        if i in wrist:lo[j],hi[j]=max(lo[j],np.radians(-35)),min(hi[j],np.radians(35))
    capsules={}
    for b in ET.parse(HUMAN).iter('body'):
        if b.get('name') in ('L_Shoulder','L_Elbow'):
            geom=b.find('geom');capsules[b.get('name')]=(np.fromstring(geom.get('fromto'),sep=' ').reshape(2,3),float(geom.get('size')))
    def arm_gaps(poses):
        values=[]
        for name,(ends,radius) in capsules.items():
            p,r=poses[name];points=g.gr.inv().apply(p+r.apply(ends)-g.gp)
            values.append(min(float(np.max(np.min(points@p[:,:3].T+p[:,3],axis=0)-radius)) for p in g.envelopes))
        return np.asarray(values)
    def trial(x):
        value=q.copy();value[ids]=x;return value
    forward=np.array([0.,1.,0.]);up=np.array([0.,0.,1.])
    wanted_wp=np.array([-.24,.03,.60]);wanted_ep=np.array([-.24,-.22,.72])
    def residual(x):
        v=trial(x);poses=g.fk(v);wp=poses['L_Wrist'][0];ep=poses['L_Elbow'][0]
        hf,hn=hand_axes(poses);forearm=unit(wp-ep)
        return np.r_[80*(wp-wanted_wp),20*(ep-wanted_ep),30*(hf-forward),30*(hn-up),5*(forearm-forward),
            1800*np.maximum(.006-arm_gaps(poses),0),1.0*v[wrist],.1*(x-q[ids])]
    rng=np.random.RandomState(7)
    seeds=[q[ids],np.asarray(previous['q105_rad'])[ids],(lo+hi)/2]
    seeds.extend(q[ids]+rng.normal(0,.7,len(ids)) for _ in range(5))
    fits=[]
    for k,seed in enumerate(seeds):
        fit=least_squares(residual,np.clip(seed,lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=350,ftol=1e-9,xtol=1e-9,gtol=1e-9)
        fits.append(fit);print('fit',k,float(np.linalg.norm(residual(fit.x))),flush=True)
    fit=min(fits,key=lambda f:np.linalg.norm(residual(f.x)));v=trial(fit.x);poses=g.fk(v)
    hf,hn=hand_axes(poses);fa=unit(poses['L_Wrist'][0]-poses['L_Elbow'][0])
    angle=lambda a,b:float(np.degrees(np.arccos(np.clip(a@b,-1,1))))
    gaps={f:min(g.gaps(v,f).values()) for f in FINGERS}
    metrics=dict(scope='original model FK preview; no new physics',axes=dict(front_world=forward.tolist(),up_world=up.tolist(),hand_forward_world=hf.tolist(),palmar_normal_world=hn.tolist(),forearm_world=fa.tolist()),
        errors_deg=dict(hand_forward=angle(hf,forward),palm_up=angle(hn,up),forearm_forward=angle(fa,forward),forearm_hand=angle(fa,hf)),
        wrist_input_degrees=np.degrees(v[wrist]).tolist(),finger_neck_gap_lower_bound_mm={f:d*1000 for f,d in gaps.items()},arm_neck_gap_lower_bound_mm=(arm_gaps(poses)*1000).tolist(),
        elbow_world_m=poses['L_Elbow'][0].tolist(),wrist_world_m=poses['L_Wrist'][0].tolist(),shoulder_world_m=poses['L_Shoulder'][0].tolist(),
        joints=[dict(name=g.names[i],before_deg=float(q[i]*180/np.pi),after_deg=float(v[i]*180/np.pi),native_margin_deg=float(min(v[i]-low[i],high[i]-v[i])*180/np.pi)) for i in ids])
    print(json.dumps(metrics,ensure_ascii=False),flush=True)
    if max(metrics['errors_deg']['hand_forward'],metrics['errors_deg']['palm_up'])>10:raise RuntimeError('손 방향 오차10도 초과')
    if min(gaps.values())<.01 or min(arm_gaps(poses))<0:raise RuntimeError('넥 간격 확인 필요')
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
    write(OUT/'initial_pose.json',dict(schema='left_standby_initial.v4',diagnostic_only=True,physical_hold_verified=False,joint_names=g.names,q105_rad=v.tolist(),target105_rad=target.tolist(),state=state,changed_joint_names=[g.names[i] for i in ids],all_finger_angles_unchanged=True,source_sha256=c['source_sha256']))
    write(OUT/'measurements.json',metrics)
    media.OUT=OUT;media.render(c,previous['state'],state,old['L_Wrist'][0])
    write(OUT/'source_pins.json',{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve(),BASE/'tools/make_pose.py',ROOT/'초기자세_v2/tools/create_candidate.py',BASE/'initial_pose.json',ROOT/'초기자세_v3/initial_pose.json')})


if __name__=='__main__':main()
