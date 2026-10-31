"""넥 기준 앞·뒤·아래와 전체 형상 간격을 확인하고 후보를 그린다."""
import json
import sys
import hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
from PIL import Image,ImageDraw,ImageFont
from scipy.spatial.transform import Rotation

OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parent
sys.path.insert(0,str(ROOT/'초기자세_v1/tools'))
from make_pose import PoseGeometry,FINGERS,load_prepared_reset_contract,write
from guitar_learning.gpu.contact import load_fingertip_pad,load_thumb_support,load_press_surface


def main():
    c=load_prepared_reset_contract();g=PoseGeometry(c);a=json.loads((OUT/'candidate.json').read_text());q=np.array(a['q105_rad']);poses=g.fk(q)
    thumb=load_thumb_support();pad=load_fingertip_pad();front=np.asarray(load_press_surface([2],[6])['plane_G']);rear=np.asarray(thumb['plane'])
    rear=rear/np.linalg.norm(rear[:3]);front=front/np.linalg.norm(front[:3])
    records=[]
    locals=[thumb['points_local']]+[p[v] for p,v in zip(pad['points_local'],pad['valid'])]
    normals=[thumb['normals_local']]+[n[v] for n,v in zip(pad['normals_local'],pad['valid'])]
    for f,points,ns in zip(FINGERS,locals,normals):
        body='LH:'+f+'3';p,r=poses[body];points=g.gr.inv().apply(p+r.apply(points)-g.gp);ns=g.gr.inv().apply(r.apply(ns))
        plane=rear if f=='thumb' else front;d=points@plane[:3]+plane[3]
        records.append(dict(finger=f,side='rear' if f=='thumb' else 'front',samples=len(points),minimum_signed_gap_mm=float(d.min()*1000),maximum_signed_gap_mm=float(d.max()*1000),pad_center_G_m=points.mean(0).tolist(),
            facing_neck_mean_dot=float(np.mean(ns@(-plane[:3]))),source_mesh_gap_lower_bound_mm=min(g.gaps(q,f).values())*1000))
    wpG=g.gr.inv().apply(poses['L_Wrist'][0]-g.gp);max_neck_x=.027908
    center=g.gp+g.gr.apply([0,wpG[1],0]);vertical_below=center[2]-poses['L_Wrist'][0][2]
    report=dict(scope='source FK validation only; no physics hold/contact success',front_plane_G=front.tolist(),rear_plane_G=rear.tolist(),wrist_G_m=wpG.tolist(),wrist_below_global_neck_x_bound_mm=float((wpG[0]-max_neck_x)*1000),wrist_below_neck_reference_world_vertical_mm=float(vertical_below*1000),
        neck_Gy_range_m=[-.241803,.217197],fingers=records)
    # 초기 배치에서 모든 패드 표본이 요구한 쪽에 있는지 확인한다.
    assert -.241803<wpG[1]<.217197
    assert wpG[0]>max_neck_x+.01 and vertical_below>.01
    assert all(r['minimum_signed_gap_mm']>2 and r['source_mesh_gap_lower_bound_mm']>0 for r in records)
    base=json.loads((ROOT/'초기자세_v1/initial_pose.json').read_text());names=c['initial']['joint_names'];changed=a['changed_joint_names']
    assert all(a['state']['human_dof_states'][i]==base['state']['human_dof_states'][i] for i,n in enumerate(names) if n not in changed)
    assert a['state']['guitar_body_states']==base['state']['guitar_body_states'] and a['state']['chair_body_states']==base['state']['chair_body_states']
    low=np.asarray(c['initial']['native_PD_properties']['lower']);high=np.asarray(c['initial']['native_PD_properties']['upper'])
    changed_ids=[names.index(n) for n in changed]
    assert np.all((q[changed_ids]>=low[changed_ids])&(q[changed_ids]<=high[changed_ids]))
    report['finger_pair_audit']=audit_fingers(g,poses)
    assert not report['finger_pair_audit']['overlaps_over_0_1mm']
    source=json.loads((OUT/'search_result.json').read_text())
    assert min(source['arm_gap_lower_bound_mm'])>0
    for r in source['joints']:
        i=names.index(r['name']);r['native_margin_deg']=float(min(q[i]-low[i],high[i]-q[i])*180/np.pi)
    write(OUT/'measurements.json',source);write(OUT/'verification.json',report)
    a['schema']='left_standby_initial.v5';a['source_placement_verified']=True;write(OUT/'initial_pose.json',a)
    render(c,json.loads((ROOT/'초기자세_v4/initial_pose.json').read_text())['state'],a['state'])
    plot(g,poses,records,wpG)
    paths=[Path(__file__).resolve(),OUT/'tools/create_pose.py',ROOT/'초기자세_v1/tools/make_pose.py',ROOT/'초기자세_v4/tools/create_pose.py',ROOT/'초기자세_v1/initial_pose.json',ROOT/'초기자세_v4/initial_pose.json',OUT/'trials/extreme_fingers/candidate.json']
    write(OUT/'source_pins.json',{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    print(json.dumps(report,ensure_ascii=False),flush=True)


def audit_fingers(g,poses):
    from scipy.optimize import linprog
    parts=[]
    for name,vertices in g.parts.items():
        p,r=poses[name];points=g.gr.inv().apply(p+r.apply(vertices)-g.gp)
        finger=next(f for f in FINGERS if name.startswith('LH:'+f))
        parts.append((name,ConvexHull(points).equations,finger))
    hits=[];radii=[]
    for k,(name,e,finger) in enumerate(parts):
        for other,ee,other_finger in parts[k+1:]:
            if finger==other_finger:continue
            planes=np.vstack((e,ee))
            fit=linprog([0,0,0,-1],A_ub=np.c_[planes[:,:3],np.ones(len(planes))],b_ub=-planes[:,3],bounds=[(None,None)]*4,method='highs')
            if not fit.success:raise RuntimeError('손가락 볼록형상 대조 실패')
            radius=float(fit.x[3]*1000);radii.append(radius)
            if radius>.1:hits.append(dict(a=name,b=other,overlap_inscribed_radius_mm=radius))
    return dict(scope='cross-finger source convex hulls; conservative thumb capsule box; same-finger pairs excluded; positive maximum inscribed radius is convex-hull overlap, not native cooked collision',
        pairs_checked=len(radii),maximum_signed_common_inscribed_radius_mm=max(radii),overlaps_over_0_1mm=hits)


def render(c,before,after,after_scope='model FK preview',before_scope='model FK preview'):
    import mujoco
    from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model,set_body_poses,add_strings
    model,data,mapping,_=build_model(c['initial']);colors=((.95,.78,.18),(.20,.55,.95),(.15,.75,.52),(.96,.48,.20),(.70,.38,.92))
    for i,b in enumerate(model.geom_bodyid):
        name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,int(b)) or ''
        for f,color in zip(FINGERS,colors):
            if name.startswith('human/LH:'+f):model.geom_rgba[i,:3]=color
    renderer=mujoco.Renderer(model,height=720,width=1280);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    try:
        for label,state in [('before',before),('adjusted',after)]:
            set_body_poses(model,data,mapping,state)
            for view,az,elev,dist in [('front',270,-10,.85),('oblique',315,-15,.85),('side',0,-8,.85),('hand',305,-12,.45),('hand_side',0,-15,.45),('full',270,-5,2.6)]:
                if label=='before' and view in ('hand','hand_side'):continue
                camera=mujoco.MjvCamera();mujoco.mjv_defaultCamera(camera)
                camera.lookat[:]=[-.26,-.04,.69] if view!='full' else [-.1,0,.64]
                if view in ('hand','hand_side'):camera.lookat[:]=[-.28,-.11,.65]
                camera.distance=dist;camera.azimuth=az;camera.elevation=elev
                renderer.update_scene(data,camera=camera)
                endpoints=np.array([[[state['guitar_body_states'][c['initial']['guitar_body_names'].index(n)]['pose']['p'][a] for a in 'xyz'] for n in ('G:string%d'%k,'G:string%d_end'%k)] for k in range(1,7)])
                add_strings(renderer.scene,endpoints)
                image=Image.fromarray(renderer.render());draw=ImageDraw.Draw(image);draw.text((14,12),label+' | '+view+' | '+(before_scope if label=='before' else after_scope),fill='white',font=font)
                for k,(f,color) in enumerate(zip(FINGERS,colors)):draw.text((14+k*180,681),f,fill=tuple(int(x*255) for x in color),font=font)
                image.save(OUT/(label+'_'+view+'.png'))
        sheet=Image.new('RGB',(1600,1350),'#171b24')
        for y,view in enumerate(('oblique','side','full')):
            for x,label in enumerate(('before','adjusted')):sheet.paste(Image.open(OUT/(label+'_'+view+'.png')).resize((800,450)),(x*800,y*450))
        sheet.save(OUT/'comparison.png')
    finally:renderer.close()


def plot(g,poses,records,wp):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle,Polygon
    colors=['#e6b819','#338cee','#25bf85','#ed7b30','#ae62de']
    fig,ax=plt.subplots(figsize=(8,7))
    # Length projection, not one physical cross-section: different Gy values overlap.
    ax.add_patch(Rectangle((-.008,-.027908),.0173,.055816,color='#777777',alpha=.65,label='Neck length projection'))
    ax.axvline(.0093,color='#b74636',linestyle='--',label='Front/press plane')
    ax.axvline(-.008,color='#446493',linestyle='--',label='Rear plane')
    for f,col in zip(FINGERS,colors):
        for name,verts in g.parts.items():
            if name.startswith('LH:'+f):
                p,r=poses[name];v=g.gr.inv().apply(p+r.apply(verts)-g.gp);v=v[:,[2,0]]
                hull=ConvexHull(v);ax.add_patch(Polygon(v[hull.vertices],facecolor=col,edgecolor=col,alpha=.16))
    for j,(r,col) in enumerate(zip(records,colors)):
        p=np.array(r['pad_center_G_m']);ax.scatter(p[2],p[0],s=70,color=col)
        ax.annotate(r['finger'],xy=(p[2],p[0]),xytext=(-.095 if j==0 else .065,-.025+j*.015),arrowprops=dict(arrowstyle='-',color=col),color=col)
    ax.scatter(wp[2],wp[0],c='black',s=70);ax.annotate('Wrist below neck',xy=(wp[2],wp[0]),xytext=(-.10,.13),arrowprops=dict(arrowstyle='->'))
    ax.set(xlabel='Gz (m): rear < 0 < front',ylabel='Gx (m): below neck increases downward',title='Length projection in guitar frame (Gy varies)\nSource geometry; no new physics')
    ax.set_xlim(-.12,.12);ax.set_ylim(.15,-.055);ax.set_aspect('equal');ax.legend(fontsize=8,loc='upper right');ax.grid(alpha=.2);fig.tight_layout();fig.savefig(OUT/'layout_G.png',dpi=160);plt.close(fig)


if __name__=='__main__':main()
