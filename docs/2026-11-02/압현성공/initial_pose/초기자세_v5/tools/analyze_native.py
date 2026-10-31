"""5초 실제 물리 기록에서 넥 앞뒤 배치를 다시 측정하고 마지막 모습을 그린다."""
import copy
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.transform import Rotation

OUT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(OUT.parent/'초기자세_v1/tools'))
from make_pose import PoseGeometry,FINGERS,load_prepared_reset_contract,write
from guitar_learning.gpu.contact import load_fingertip_pad,load_thumb_support,load_press_surface
from validate_render import render
import validate_render as visual


def main():
    c=load_prepared_reset_contract();g=PoseGeometry(c);data=np.load(OUT/'native_hold.npz');meta=json.loads((OUT/'native_metadata.json').read_text())
    pad=load_fingertip_pad();thumb=load_thumb_support();rear=np.asarray(thumb['plane']);front=np.asarray(load_press_surface([2],[6])['plane_G'])
    body_names=meta['body_names'];gid=body_names.index('guitar/guitar')
    locals=[thumb['points_local']]+[p[v] for p,v in zip(pad['points_local'],pad['valid'])]
    sides=[];wrist_below=[];whole=[]
    for bodies in data['body_state'][1:]:
        gp=bodies[gid,:3];gr=Rotation.from_quat(bodies[gid,3:7]);wg=gr.inv().apply(bodies[body_names.index('human/L_Wrist'),:3]-gp)
        wrist_below.append((wg[0]-.027908)*1000)
        row=[];gaprow=[]
        for f,local in zip(FINGERS,locals):
            b=bodies[body_names.index('human/LH:'+f+'3')];p=gr.inv().apply(b[:3]+Rotation.from_quat(b[3:7]).apply(local)-gp)
            plane=rear if f=='thumb' else front;row.append((p@plane[:3]+plane[3]).min()*1000)
            gaps=[]
            for name,points in g.parts.items():
                if name.startswith('LH:'+f):
                    b=bodies[body_names.index('human/'+name)];pts=gr.inv().apply(b[:3]+Rotation.from_quat(b[3:7]).apply(points)-gp)
                    gaps.append(min(float(np.max(np.min(pts@e[:,:3].T+e[:,3],axis=0))) for e in g.envelopes)*1000)
            gaprow.append(min(gaps))
        sides.append(row);whole.append(gaprow)
    sides=np.asarray(sides);whole=np.asarray(whole);records=[]
    for i,f in enumerate(FINGERS):
        ids=[k for k,n in enumerate(body_names) if n.startswith('human/LH:'+f)]
        records.append(dict(finger=f,side='rear' if f=='thumb' else 'front',minimum_signed_pad_gap_mm=float(sides[:,i].min()),final_signed_pad_gap_mm=float(sides[-1,i]),samples_on_required_side_fraction=float((sides[:,i]>0).mean()),minimum_whole_source_gap_mm=float(whole[:,i].min()),maximum_segment_net_force_N=float(np.linalg.norm(data['contact_force'][1:,ids],axis=-1).max())))
    a=json.loads((OUT/'initial_pose.json').read_text());changed=[meta['joint_names'].index(n) for n in a['changed_joint_names']];baseq=np.array(a['q105_rad']);q=data['q'];other=[i for i in range(105) if i not in changed]
    report=dict(scope='actual GPU PhysX1200steps/5s; 300 post-reset samples60Hz, excludes t0 reset body cache; no policy training',physics_steps=meta['physics_steps'],reset_calls=meta['reset_calls'],fingers=records,
        minimum_wrist_below_neck_bound_mm=float(min(wrist_below)),guitar_maximum_displacement_mm=float(np.linalg.norm(data['body_state'][:,gid,:3]-data['body_state'][0,gid,:3],axis=-1).max()*1000),
        initial_changed_q_error_max_rad=float(np.abs(q[0,changed]-baseq[changed]).max()),initial_unchanged_q_error_max_rad=float(np.abs(q[0,other]-baseq[other]).max()),
        interpretation='front uses source press/fretboard planeGz.0093, rearGz-.008; source geometry transformed by actual native bodies; net forces do not identify contact partners')
    report['placement_retained_at_all_recorded_samples']=bool(min(wrist_below)>0 and (sides>0).all())
    write(OUT/'native_verification.json',report)
    state=copy.deepcopy(c['state']);bodies=data['body_state'][-1]
    for i,name in enumerate(body_names):
        kind,n=name.split('/',1);names=c['initial'].get(kind+'_body_names',['box']);k=names.index(n)
        state[kind+'_body_states'][k]['pose']=dict(p=dict(zip('xyz',bodies[i,:3].tolist())),r=dict(zip('xyzw',bodies[i,3:7].tolist())))
    native_dir=OUT/'native_images';native_dir.mkdir(exist_ok=True);visual.OUT=native_dir
    render(c,a['state'],state,after_scope='GPU PhysX recorded at 5s',before_scope='reset FK reference')
    a['physical_hold_verified']=report['placement_retained_at_all_recorded_samples'];a['physical_hold_verification_scope']='5s, actual60Hz recorded placement, not song success or all instantaneous contact-free certification';write(OUT/'initial_pose.json',a)
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
