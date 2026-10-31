"""v7의 검지~소지 뿌리 굽힘만 각각15도 더 줄인다."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

OUT=Path(__file__).resolve().parents[1]
BASE=OUT.parent/'초기자세_v7'
sys.path.insert(0,str(OUT.parent/'초기자세_v1/tools'))
from make_pose import PoseGeometry,FINGERS,load_prepared_reset_contract,write
sys.path.insert(0,str(OUT.parent/'초기자세_v5/tools'))
import validate_render as visual
from guitar_learning.gpu.contact import load_fingertip_pad,load_thumb_support,load_press_surface


def main():
    c=load_prepared_reset_contract();g=PoseGeometry(c);base=json.loads((BASE/'initial_pose.json').read_text());a=copy.deepcopy(base)
    before=np.array(base['q105_rad']);q=before.copy();target=np.array(base['target105_rad']);names=base['joint_names']
    changed=['LH:'+f+'1_x' for f in FINGERS[1:]];ids=[names.index(n) for n in changed]
    q[ids]-=np.radians(15);target[ids]-=np.radians(15)
    poses=g.fk(q)
    for i in ids:a['state']['human_dof_states'][i]=dict(pos=float(q[i]),vel=0.)
    for i,n in enumerate(c['initial']['human_body_names']):
        if any(n.startswith('LH:'+f) for f in FINGERS[1:]):
            p,r=poses[n];a['state']['human_body_states'][i]['pose']=dict(p=dict(zip('xyz',p.tolist())),r=dict(zip('xyzw',r.as_quat().tolist())))
    assert all(a['state']['human_dof_states'][i]==base['state']['human_dof_states'][i] for i in range(105) if i not in ids)
    assert all(a['state']['human_body_states'][i]==base['state']['human_body_states'][i] for i,n in enumerate(c['initial']['human_body_names']) if not any(n.startswith('LH:'+f) for f in FINGERS[1:]))
    assert a['state']['guitar_body_states']==base['state']['guitar_body_states'] and a['state']['chair_body_states']==base['state']['chair_body_states']
    assert np.array_equal(target[[i for i in range(105) if i not in ids]],np.array(base['target105_rad'])[[i for i in range(105) if i not in ids]])
    low=np.asarray(c['initial']['native_PD_properties']['lower']);hi=np.asarray(c['initial']['native_PD_properties']['upper']);assert np.all((q[ids]>=low[ids])&(q[ids]<=hi[ids]))
    pad=load_fingertip_pad();thumb=load_thumb_support();plane=np.asarray(load_press_surface([2],[6])['plane_G']);records=[]
    samples=[thumb['points_local']]+[p[v] for p,v in zip(pad['points_local'],pad['valid'])]
    for f,points in zip(FINGERS,samples):
        p,r=poses['LH:'+f+'3'];v=g.gr.inv().apply(p+r.apply(points)-g.gp);surf=np.asarray(thumb['plane']) if f=='thumb' else plane;gap=v@surf[:3]+surf[3]
        whole=min(g.gaps(q,f).values())*1000;assert gap.min()>.002 and whole>0
        records.append(dict(finger=f,minimum_signed_pad_gap_mm=float(gap.min()*1000),whole_source_gap_lower_bound_mm=whole))
    audit=visual.audit_fingers(g,poses);assert audit['maximum_signed_common_inscribed_radius_mm']<0
    a.pop('delta_from_v5_joint_names',None)
    a.pop('delta_from_v6_joint_names',None)
    a.update(schema='left_standby_initial.v8',q105_rad=q.tolist(),target105_rad=target.tolist(),physical_hold_verified=False,physical_hold_verification_scope=None,delta_from_v7_joint_names=changed,delta_degrees=-15.,base_pose_sha256=hashlib.sha256((BASE/'initial_pose.json').read_bytes()).hexdigest())
    report=dict(changed_joints=[dict(name=n,before_degrees=float(before[i]*180/np.pi),after_degrees=float(q[i]*180/np.pi)) for n,i in zip(changed,ids)],other_joint_states_and_targets_unchanged=True,fingers=records,finger_pair_audit=audit)
    write(OUT/'initial_pose.json',a);write(OUT/'verification.json',report)
    visual.OUT=OUT;visual.render(c,base['state'],a['state'],before_scope='v7 reference FK',after_scope='v8 MCP minus15deg FK')
    write(OUT/'source_pins.json',{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve(),BASE/'initial_pose.json',OUT.parent/'초기자세_v5/tools/validate_render.py',OUT.parent/'초기자세_v1/tools/make_pose.py')})
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
