"""Static source-mesh thumb pose previews; no physics, policy or source updates."""
from pathlib import Path
import copy,json,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
import trimesh
from guitar_learning.native.paths import resolve_input_path
from guitar_learning.core.geometry_v1 import frame
ROOT=Path('/home/ajou/yigyu/3');P=ROOT/'docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1'
initial=json.loads((P/'initial_values.json').read_text());state=json.loads((P/'prepared.json').read_text())['sample']['native'];names=initial['joint_names'];bodies=initial['human_body_names'];q0=np.array([r['pos'] for r in state['human_dof_states']]);original={n:frame(r) for n,r in zip(bodies,state['human_body_states'])};gp,gr=frame(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')]);asset=resolve_input_path(initial['loaded_assets'][0]['path']);xml=ET.parse(asset);parents={c.get('name'):b.get('name') for b in xml.findall('.//body') for c in b.findall('body')};source={b.get('name'):b for b in xml.findall('.//body')};meshes={m.get('name'):m for m in xml.findall('./asset/mesh')};chain=['LH:thumb1','LH:thumb2','LH:thumb3','LH:thumb_pad','LH:thumb_top'];rows=[];indices=[i for i,n in enumerate(names) if n.startswith('LH:thumb')]
for n in chain:
 b=source[n];pa=parents[n];bp,br=original[n];pp,pr=original[pa];j=b.findall('joint');ix=[names.index(x.get('name')) for x in j];axes=np.column_stack([np.fromstring(x.get('axis'),sep=' ') for x in j]) if j else np.zeros((3,0));zero=Rotation.from_rotvec(axes@q0[ix]).inv()*(pr.inv()*br) if ix else pr.inv()*br;rows.append((n,pa,pr.inv().apply(bp-pp),zero,axes,ix))
def fk(v):
 q=q0.copy();q[indices]=v;poses=dict(original)
 for n,pa,t,zero,axes,ix in rows:
  pp,pr=poses[pa];poses[n]=(pp+pr.apply(t),pr*(Rotation.from_rotvec(axes@q[ix])*zero))
 return poses
verts={}
for n in chain[:3]:
 g=source[n].find('geom');m=meshes[g.get('mesh')];v=trimesh.load(asset.parent/'mesh'/m.get('file'),process=False).vertices.copy();v*=np.fromstring(m.get('scale','1 1 1'),sep=' ');v+=np.fromstring(g.get('pos','0 0 0'),sep=' ');verts[n]=np.unique(v,axis=0)

def transformed(v):
 poses=fk(v);return {n:gr.inv().apply(p[0]+p[1].apply(verts[n])-gp) for n,p in poses.items() if n in verts}
lo=np.deg2rad([0,-90,0,0,-5]);hi=np.deg2rad([40,0,90,90,90]);start=np.clip(q0[indices],lo+1e-7,hi-1e-7)

if __name__ == '__main__':
 import mujoco,hashlib
 from PIL import Image,ImageDraw,ImageFont
 from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model,set_body_poses,asset_paths
 OUT=ROOT/'docs/2026-10-26/thumb_neck_preview_v1'
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 sources={P/'initial_values.json',P/'prepared.json',Path(__file__).resolve(),ROOT/'guitar_learning/assets/native_provenance.json',Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')}
 for a in initial['loaded_assets']:sources.update(asset_paths(Path(a['path'])))
 sources.update(OUT/('probe_%03d.json'%k) for k in (85,90,93))
 sources.update(ROOT/p for p in ['guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py','guitar_learning/native/initial_pose_video60_v1/replay_v6.py','guitar_learning/native/paths.py','guitar_learning/core/geometry_v1.py'])
 inputs={str(p):sha(p) for p in sources}
 model,data,mapping,xmltext=build_model(initial)
 for g in range(model.ngeom):
  n=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,int(model.geom_bodyid[g])) or ''
  if n.startswith('human/LH:thumb'):color=(1.,.55,.12,1.)
  elif n.startswith('human/LH:') or n=='human/L_Wrist':color=(.22,.56,.76,1.)
  elif n.startswith('guitar/'):color=(.62,.65,.69,1.)
  else:color=(0,0,0,0)
  model.geom_rgba[g]=color
 model.vis.headlight.ambient[:]=.55
 model.vis.headlight.diffuse[:]=.7
 model.vis.map.znear=.0001
 model.vis.global_.offwidth=1024;model.vis.global_.offheight=768
 model.vis.rgba.haze[:]=[.96,.97,.99,1]
 renderer=mujoco.Renderer(model,height=768,width=1024)
 fontpath='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
 font=ImageFont.truetype(fontpath,29);small=ImageFont.truetype(fontpath,20);title=ImageFont.truetype(fontpath,34)
 sheet=Image.new('RGB',(3072,1744),(245,247,250));draw=ImageDraw.Draw(sheet)
 draw.text((30,10),'넥 뒷면 중앙 · 가볍게 닿는 엄지 자세 후보',font=title,fill=(25,36,50))
 draw.text((30,60),'주황: 엄지 / 파랑: 다른 손가락 / 회색: 현재 넥 / 초록점: 표면상 접촉 후보 위치',font=small,fill=(45,60,70))
 camera=mujoco.MjvCamera();camera.type=mujoco.mjtCamera.mjCAMERA_FREE
 records=[]
 cases=[('A',85,'완만하게 굽힘'),('B',90,'가볍게 편 자세'),('C',93,'거의 편 자세')]
 try:
  for col,(label,number,name) in enumerate(cases):
   d=json.loads((OUT/('probe_%03d.json'%number)).read_text());v=np.array(d['q_rad']);poses=fk(v);candidate=copy.deepcopy(state)
   clouds=transformed(v)
   assert all(cloud[:,2].max()<-.008 for cloud in clouds.values())
   visible=clouds['LH:thumb3'];measured_witness=visible[np.argmax(visible[:,2])]
   assert np.linalg.norm(measured_witness-np.asarray(d['witness']))<1e-9
   assert 0<=-.008-measured_witness[2]<.0005 and abs(measured_witness[0])<.002
   assert np.all(v>=lo) and np.all(v<=hi)
   for n in chain:
    p,r=poses[n];candidate['human_body_states'][bodies.index(n)]['pose']={'p':dict(zip('xyz',p.tolist())),'r':dict(zip('xyzw',r.as_quat().tolist()))}
   for k,val in zip(indices,v):candidate['human_dof_states'][k]['pos']=float(val)
   for n in bodies:
    if n not in chain:assert candidate['human_body_states'][bodies.index(n)]==state['human_body_states'][bodies.index(n)]
   readback=set_body_poses(model,data,mapping,candidate)
   for row,(look,offset,viewname) in enumerate([([.025,.045,-.025],[.09,.08,-.30],'뒤쪽 확대'),([.015,.048,-.02],[.24,.03,-.15],'사선 확대')]):
    camera.lookat[:]=gp+gr.apply(look);direction=-gr.apply(offset);camera.distance=np.linalg.norm(direction);camera.azimuth=np.rad2deg(np.arctan2(direction[1],direction[0]));camera.elevation=np.rad2deg(np.arctan2(direction[2],np.linalg.norm(direction[:2])))
    renderer.update_scene(data,camera=camera)
    camera_G=gr.inv().apply((renderer.scene.camera[0].pos+renderer.scene.camera[1].pos)/2-gp)
    assert camera_G[2] < -.05, 'rear neck camera must be behind guitar' 
    point=gp+gr.apply(d['witness']);geom=renderer.scene.geoms[renderer.scene.ngeom]
    mujoco.mjv_initGeom(geom,mujoco.mjtGeom.mjGEOM_SPHERE,np.array([.0016]*3),point,np.eye(3).ravel(),np.array([.1,.9,.4,1],dtype=np.float32));renderer.scene.ngeom+=1
    im=Image.fromarray(renderer.render());dr=ImageDraw.Draw(im)
    cam=renderer.scene.camera[0];pos=(renderer.scene.camera[0].pos+renderer.scene.camera[1].pos)/2
    forward=np.asarray(cam.forward);up=np.asarray(cam.up);right=np.cross(forward,up)
    delta=point-pos;depth=np.dot(delta,forward);focal=768/(2*np.tan(np.deg2rad(model.vis.global_.fovy)/2))
    u=512+focal*np.dot(delta,right)/depth;vv=384-focal*np.dot(delta,up)/depth
    assert 0<u<1024 and 60<vv<768
    dr.ellipse((u-10,vv-10,u+10,vv+10),outline=(35,245,115),width=4)
    dr.line((u,vv-13,u+42,vv-55),fill=(35,245,115),width=3)
    dr.text((u+45,vv-81),'접촉 후보',font=small,fill=(80,255,140),stroke_width=1,stroke_fill=(0,0,0))
    dr.rectangle((0,0,1024,57),fill=(239,243,247));dr.text((20,9),label+'  '+name+' · '+viewname,font=font,fill=(23,38,52))
    im.save(OUT/(label+'_'+str(row+1)+'.png'));sheet.paste(im,(col*1024,112+row*768))
   record=dict(label=label,description=name,thumb_joint_names=[names[k] for k in indices],q_rad=v.tolist(),q_deg=np.rad2deg(v).tolist(),target_G_m=d['target'],visible_pad_witness_G_m=d['witness'],visible_plane_gap_m=-.008-d['witness'][2],thumb_mesh_max_G_z_m={n:float(c[:,2].max()) for n,c in clouds.items()},pose_readback=readback,unchanged_other_bodies=True)
   records.append(record);(OUT/(label+'_candidate.json')).write_text(json.dumps(dict(record,state=candidate),indent=2)+'\n')
  draw=ImageDraw.Draw(sheet);draw.text((30,1660),'현재 원본 3D 모델의 정지 자세 비교 · 엄지만 변경 · 학습/물리 실행 0 · 아직 초기 자세에 미적용',font=small,fill=(35,45,60))
  sheet.save(OUT/'thumb_candidates.png')
 finally:renderer.close()
 assert all(sha(Path(p))==h for p,h in inputs.items())
 (OUT/'report.json').write_text(json.dumps(dict(completed=True,scope='source mesh static kinematic proposals; not native contact/force verification',training_updates=0,physics_steps=0,main_configuration_modified=False,candidates=records,inputs_sha256=inputs,images_sha256={p.name:sha(p) for p in OUT.glob('*.png')}),ensure_ascii=False,indent=2)+'\n')
 print('Rendered static thumb candidates; training and physics steps: 0')
