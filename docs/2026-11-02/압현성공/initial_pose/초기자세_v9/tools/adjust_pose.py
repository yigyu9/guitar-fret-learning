"""v8 손가락을 부채꼴로 벌리고 팔의 역기구학으로 손목을1cm 올린다."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import least_squares
OUT=Path(__file__).resolve().parents[1]
BASE=OUT.parent/'초기자세_v8'
sys.path.insert(0,str(OUT.parent/'초기자세_v1/tools'))
from make_pose import PoseGeometry,FINGERS,load_prepared_reset_contract,write
sys.path.insert(0,str(OUT.parent/'초기자세_v5/tools'))
import validate_render as visual
from guitar_learning.gpu.contact import load_fingertip_pad,load_thumb_support,load_press_surface


def main():
    c=load_prepared_reset_contract();g=PoseGeometry(c)
    base=json.loads((BASE/'initial_pose.json').read_text());a=copy.deepcopy(base)
    before=np.array(base['q105_rad']);q=before.copy();names=g.names
    spread=[names.index('LH:'+f+'1_z') for f in FINGERS[1:]]
    q[spread]+=np.radians([-6.,-2.,2.,6.])
    # 손목 방향은 유지하고 팔꿈치 비틀림을 유지하고 어깨·팔꿈치 굽힘·손목을 써서 세계 위쪽으로10mm 이동한다.
    arm=[i for i,n in enumerate(names) if n.startswith(('L_Shoulder','L_Wrist')) or n=='L_Elbow_x']
    p0,r0=g.fk(before)['L_Wrist'];wanted=p0+np.array([0.,0.,.010])
    low=np.asarray(c['initial']['native_PD_properties']['lower']);high=np.asarray(c['initial']['native_PD_properties']['upper'])
    def trial(x):
        v=q.copy();v[arm]=x;return v
    def residual(x):
        p,r=g.fk(trial(x))['L_Wrist']
        return np.r_[1000*(p-wanted),10*(r0.inv()*r).as_rotvec(),.03*(x-before[arm])]
    fit=least_squares(residual,before[arm],bounds=(low[arm]+1e-5,high[arm]-1e-5),max_nfev=150)
    q=trial(fit.x);poses=g.fk(q);old=g.fk(before)
    ids=arm+spread
    assert np.all((q[ids]>=low[ids]-1e-6)&(q[ids]<=high[ids]+1e-6))
    target=np.array(base['target105_rad']);target[ids]+=q[ids]-before[ids]
    for i in ids:a['state']['human_dof_states'][i]=dict(pos=float(q[i]),vel=0.)
    for i,n in enumerate(c['initial']['human_body_names']):
        p,r=poses[n];op,orr=old[n]
        if np.linalg.norm(p-op)>1e-12 or (orr.inv()*r).magnitude()>1e-12:
            a['state']['human_body_states'][i]['pose']=dict(p=dict(zip('xyz',p.tolist())),r=dict(zip('xyzw',r.as_quat().tolist())))
    assert all(a['state']['human_dof_states'][i]==base['state']['human_dof_states'][i] for i in range(105) if i not in ids)
    pad=load_fingertip_pad();thumb=load_thumb_support();plane=np.asarray(load_press_surface([2],[6])['plane_G'])
    samples=[thumb['points_local']]+[p[v] for p,v in zip(pad['points_local'],pad['valid'])]
    records=[];centers=[];oldcenters=[]
    for f,points in zip(FINGERS,samples):
        p,r=poses['LH:'+f+'3'];v=g.gr.inv().apply(p+r.apply(points)-g.gp)
        op,orr=old['LH:'+f+'3'];ov=g.gr.inv().apply(op+orr.apply(points)-g.gp)
        surf=np.asarray(thumb['plane']) if f=='thumb' else plane;gap=v@surf[:3]+surf[3]
        whole=min(g.gaps(q,f).values())*1000
        assert gap.min()>.002 and whole>0
        centers.append(v.mean(0));oldcenters.append(ov.mean(0))
        records.append(dict(finger=f,minimum_signed_pad_gap_mm=float(gap.min()*1000),whole_source_gap_lower_bound_mm=whole))
    audit=visual.audit_fingers(g,poses);assert audit['maximum_signed_common_inscribed_radius_mm']<0
    p,r=poses['L_Wrist'];assert np.linalg.norm(p-wanted)<.0001
    for key in list(a):
        if key.startswith('delta_from_'):a.pop(key)
    a.pop('delta_degrees',None)
    a.update(schema='left_standby_initial.v9',q105_rad=q.tolist(),target105_rad=target.tolist(),physical_hold_verified=False,physical_hold_verification_scope=None,delta_from_v8_joint_names=[names[i] for i in ids],base_pose_sha256=hashlib.sha256((BASE/'initial_pose.json').read_bytes()).hexdigest())
    centers=np.array(centers);oldcenters=np.array(oldcenters)
    report=dict(changed_joints=[dict(name=names[i],before_degrees=float(np.degrees(before[i])),after_degrees=float(np.degrees(q[i]))) for i in ids],wrist_world_delta_mm=((p-p0)*1000).tolist(),wrist_orientation_change_degrees=float(np.degrees((r0.inv()*r).magnitude())),adjacent_pad_center_distance_before_mm=(np.linalg.norm(np.diff(oldcenters[1:],axis=0),axis=1)*1000).tolist(),adjacent_pad_center_distance_after_mm=(np.linalg.norm(np.diff(centers[1:],axis=0),axis=1)*1000).tolist(),fingers=records,finger_pair_audit=audit)
    write(OUT/'initial_pose.json',a);write(OUT/'verification.json',report)
    visual.OUT=OUT;visual.render(c,base['state'],a['state'],before_scope='v8 reference FK',after_scope='v9 spread and wrist up10mm FK')
    write(OUT/'source_pins.json',{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve(),BASE/'initial_pose.json',OUT.parent/'초기자세_v5/tools/validate_render.py',OUT.parent/'초기자세_v1/tools/make_pose.py')})
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
