"""손목의 큰 편향을 줄이고 어깨·팔꿈치로 왼팔 대기 방향을 만든다."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from guitar_learning.native.paths import HUMAN
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'초기자세_v1'
sys.path.insert(0,str(BASE/'tools'))
from make_pose import PoseGeometry,FINGERS,load_prepared_reset_contract,write
sys.path.insert(0,str(ROOT/'초기자세_v2/tools'))
import create_candidate as media
OUT=Path(__file__).resolve().parents[1]


def main():
    c=load_prepared_reset_contract();g=PoseGeometry(c)
    original=json.loads((BASE/'initial_pose.json').read_text());q=np.asarray(original['q105_rad'])
    previous=json.loads((ROOT/'초기자세_v2/initial_pose.json').read_text())
    wrist=[i for i,n in enumerate(g.names) if n.startswith('L_Wrist')]
    arm=[i for i,n in enumerate(g.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow'))]
    ids=arm+wrist
    fixed=q.copy()
    native_low=np.asarray(c['initial']['native_PD_properties']['lower']);native_high=np.asarray(c['initial']['native_PD_properties']['upper'])
    lo=np.maximum(native_low[ids]+np.radians(3),q[ids]-np.radians(100));hi=np.minimum(native_high[ids]-np.radians(3),q[ids]+np.radians(100))
    for j,i in enumerate(ids):
        if i in wrist:lo[j],hi[j]=np.radians(-15),np.radians(15)
    wanted_wrist=np.array([-.32,-.07,.60]);wanted_elbow=np.array([-.12,-.19,.73])
    old=g.fk(q);axis=old['LH:palm'][1].apply([0,-1,0]);wanted_r=Rotation.from_rotvec(-np.radians(35)*axis)*old['L_Wrist'][1]
    capsules={}
    for body in ET.parse(HUMAN).iter('body'):
        if body.get('name') in ('L_Shoulder','L_Elbow'):
            geom=body.find('geom');capsules[body.get('name')]=(np.fromstring(geom.get('fromto'),sep=' ').reshape(2,3),float(geom.get('size')))
    def arm_gaps(poses):
        result=[]
        for name,(ends,radius) in capsules.items():
            p,r=poses[name];points=g.gr.inv().apply(p+r.apply(ends)-g.gp)
            result.append(min(float(np.max(np.min(points@planes[:,:3].T+planes[:,3],axis=0)-radius)) for planes in g.envelopes))
        return np.array(result)
    def trial(x):
        v=fixed.copy();v[ids]=x;return v
    def residual(x):
        poses=g.fk(trial(x));wp,wr=poses['L_Wrist'];ep,_=poses['L_Elbow'];pp,pr=poses['LH:palm']
        return np.r_[200*(wp-wanted_wrist),8*(ep-wanted_elbow),20*(wanted_r.inv()*wr).as_rotvec(),1500*np.maximum(.005-arm_gaps(poses),0),3*trial(x)[wrist],.15*(x-q[ids])]
    seeds=[q[ids],np.asarray(previous['q105_rad'])[ids],(lo+hi)/2]
    fits=[least_squares(residual,np.clip(seed,lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=400,ftol=1e-10,xtol=1e-10,gtol=1e-10) for seed in seeds]
    fit=min(fits,key=lambda f:np.linalg.norm(residual(f.x)));candidate=trial(fit.x);poses=g.fk(candidate)
    gaps={f:min(g.gaps(candidate,f).values()) for f in FINGERS}
    print('candidate',arm_gaps(poses),gaps,'wrist',np.degrees(candidate[wrist]),flush=True)
    if min(arm_gaps(poses))<0:raise RuntimeError('팔과 넥 간격 확인 필요')
    if min(gaps.values())<.01:raise RuntimeError('손가락 간격10mm 미달: '+str(gaps))
    state=copy.deepcopy(original['state']);changed=ids
    for i in changed:state['human_dof_states'][i]=dict(pos=float(candidate[i]),vel=0.)
    old_poses=g.fk(q)
    for i,n in enumerate(c['initial']['human_body_names']):
        p,r=poses[n];op,orr=old_poses[n]
        if np.linalg.norm(p-op)>1e-12 or (orr.inv()*r).magnitude()>1e-12:
            state['human_body_states'][i]['pose']=dict(p=dict(zip('xyz',p.tolist())),r=dict(zip('xyzw',r.as_quat().tolist())))
            state['human_body_states'][i]['vel']=dict(linear=dict.fromkeys('xyz',0.),angular=dict.fromkeys('xyz',0.))
    assert all(state['human_dof_states'][i]==original['state']['human_dof_states'][i] for i in range(105) if i not in changed)
    assert state['guitar_body_states']==original['state']['guitar_body_states'] and state['chair_body_states']==original['state']['chair_body_states']
    target=np.asarray(original['target105_rad']);target[changed]=candidate[changed]
    artifact=dict(schema='left_standby_initial.v3',diagnostic_only=True,physical_hold_verified=False,joint_names=g.names,q105_rad=candidate.tolist(),target105_rad=target.tolist(),state=state,
        changed_joint_names=[g.names[i] for i in changed],all_finger_angles_unchanged=True,source_sha256=c['source_sha256'])
    write(OUT/'initial_pose.json',artifact)
    report=dict(scope='source FK only; shoulder/elbow IK, wrist within15deg each; not physics certification',wrist_input_degrees=np.degrees(candidate[wrist]).tolist(),arm_neck_gap_lower_bound_mm=(arm_gaps(poses)*1000).tolist(),hand_orientation_error_deg=float((wanted_r.inv()*poses['L_Wrist'][1]).magnitude()*180/np.pi),
        actual_wrist_world_m=poses['L_Wrist'][0].tolist(),actual_elbow_world_m=poses['L_Elbow'][0].tolist(),actual_shoulder_world_m=poses['L_Shoulder'][0].tolist(),
        wrist_goal_error_mm=float(np.linalg.norm(poses['L_Wrist'][0]-wanted_wrist)*1000),elbow_goal_error_mm=float(np.linalg.norm(poses['L_Elbow'][0]-wanted_elbow)*1000),
        palm_normal_world=poses['LH:palm'][1].apply([0,0,1]).tolist(),finger_neck_gap_lower_bound_mm={f:v*1000 for f,v in gaps.items()},
        joints=[dict(name=g.names[i],before_deg=float(q[i]*180/np.pi),after_deg=float(candidate[i]*180/np.pi),native_limit_margin_deg=float(min(candidate[i]-native_low[i],native_high[i]-candidate[i])*180/np.pi)) for i in changed])
    write(OUT/'measurements.json',report)
    media.OUT=OUT
    # v2와의 비교에서 손 위치에 따라 카메라가 바뀌지 않게 고정한다.
    media.render(c,previous['state'],state,old_poses['L_Wrist'][0])
    write(OUT/'source_pins.json',{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve(),BASE/'tools/make_pose.py',ROOT/'초기자세_v2/tools/create_candidate.py',BASE/'initial_pose.json',ROOT/'초기자세_v2/initial_pose.json')})
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
