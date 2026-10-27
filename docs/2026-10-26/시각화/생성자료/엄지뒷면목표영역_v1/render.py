"""Actual-mesh static proposal: no training, stepping, or production edits."""
import os
os.environ.update(MUJOCO_GL='osmesa', PYOPENGL_PLATFORM='osmesa', LIBGL_ALWAYS_SOFTWARE='1', MPLCONFIGDIR='/tmp/thumb_rear_region_plot_v1')
from pathlib import Path
import sys, json, hashlib, copy, xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
import trimesh
import mujoco
from PIL import Image,ImageDraw,ImageFont
from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model,set_body_poses,asset_paths
from guitar_learning.gpu.press_surface import _extract_plane
from guitar_learning.gpu.fingertip_pad import _clip_polygon

OUT=HERE.parent.parent
BASE=ROOT/'docs/2026-10-23/guitar_learning_long_training_v16/evaluation_initial_1024'
FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def pose(row):
 p=row['pose'];return np.array([p['p'][a] for a in 'xyz']),Rotation.from_quat([p['r'][a] for a in 'xyzw'])
initial=json.loads((BASE/'visual_initial.json').read_text())
state=copy.deepcopy(initial['native_state'])
names=initial['joint_names'];bodies=initial['human_body_names']
original={n:pose(row) for n,row in zip(bodies,state['human_body_states'])}
gp,gr=pose(state['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
q0=np.array([r['pos'] for r in state['human_dof_states']])
source_path=Path(initial['loaded_assets'][0]['path']);source_xml=ET.parse(source_path)
source={x.get('name'):x for x in source_xml.findall('.//body')}
parents={c.get('name'):b.get('name') for b in source_xml.findall('.//body') for c in b.findall('body')}
meshes={x.get('name'):x for x in source_xml.findall('./asset/mesh')}
folder=source_path.parent/source_xml.find('compiler').get('meshdir','.')
chain=['LH:thumb1','LH:thumb2','LH:thumb3','LH:thumb_pad','LH:thumb_top']
indices=[k for k,n in enumerate(names) if n.startswith('LH:thumb')]
rows=[]
for n in chain:
 pa=parents[n];bp,br=original[n];pp,pr=original[pa];j=source[n].findall('joint')
 ix=[names.index(x.get('name')) for x in j]
 axes=np.column_stack([np.fromstring(x.get('axis'),sep=' ') for x in j]) if j else np.zeros((3,0))
 zero=Rotation.from_rotvec(axes@q0[ix]).inv()*(pr.inv()*br) if ix else pr.inv()*br
 rows.append((n,pa,pr.inv().apply(bp-pp),zero,axes,ix))
def fk(v):
 q=q0.copy();q[indices]=v;poses=dict(original)
 for n,pa,t,zero,axes,ix in rows:
  pp,pr=poses[pa];poses[n]=(pp+pr.apply(t),pr*Rotation.from_rotvec(axes@q[ix])*zero)
 return poses
triangles={}
for n in chain[:3]:
 geom=source[n].find('geom');asset=meshes[geom.get('mesh')]
 mesh=trimesh.load(folder/asset.get('file'),process=False)
 v=np.asarray(mesh.vertices)*np.fromstring(asset.get('scale','1 1 1'),sep=' ')
 quat=np.fromstring(geom.get('quat','1 0 0 0'),sep=' ')
 v=Rotation.from_quat(np.r_[quat[1:],quat[:1]]).apply(v)+np.fromstring(geom.get('pos','0 0 0'),sep=' ')
 triangles[n]=v[np.asarray(mesh.faces)]
# Experimental distal flexion-side patch; illustration only, no anatomy claim.
t=triangles['LH:thumb3'];cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normals=cross/np.maximum(np.linalg.norm(cross,axis=-1,keepdims=True),1e-30)
ymin,ymax=t[...,1].min(),t[...,1].max();pieces=[];piece_normals=[]
for triangle,normal in zip(t,normals):
 u=.25 if normal[2]<=-.25 else .75 if normal[1]<=-.4 and normal[2]<=0 else None
 if u is None:continue
 polygon=_clip_polygon(list(triangle),2,0.)
 polygon=_clip_polygon(polygon,1,ymax-u*(ymax-ymin))
 for k in range(1,len(polygon)-1):pieces.append(np.asarray([polygon[0],polygon[k],polygon[k+1]]));piece_normals.append(normal)
pieces=np.asarray(pieces);piece_normals=np.asarray(piece_normals)
assert len(pieces)>0
manifest_path=ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json'
manifest=json.loads(manifest_path.read_text());asset_dir=manifest_path.parent
expected={str((ROOT/p).resolve()):h for p,h in manifest['source_sha256'].items()}
expected[str((asset_dir/'guitar_compound.xml').resolve())]=manifest['asset_sha256']
playing,hulls,neckpins=_extract_plane(asset_dir/'guitar_compound.xml',expected)
rear=[]
for hull in hulls:
 candidates=hull[hull[:,2]<-.5];assert len(candidates)>0 and np.allclose(candidates,candidates[0],atol=1e-9)
 rear.append(candidates[0])
assert np.allclose(rear,rear[0],atol=1e-9)
plane=rear[0];normal=plane[:3]
z_at=lambda y:-(plane[1]*y+plane[3])/plane[2]
track_path=ROOT/'data/song_bundles/05_BN2-131-B_solo/training/hand_position_targets.json'
track=json.loads(track_path.read_text())['frames'][0];span=track['allowed_fret_range']
positions=dict(zip(manifest['logical_body_names'],manifest['logical_position_root_m']))
fret_y=np.array([positions['G:nut'][1]]+[positions['G:fret%d'%k][1] for k in range(1,23)])
center=.5*(fret_y[span[0]-1]+fret_y[span[1]])
ylo,yhi=center-.04,center+.04

def edges(y):
 z=z_at(y);out=[]
 for hull in hulls:
  lo,hi=-np.inf,np.inf;valid=True
  for nx,ny,nz,d in hull:
   rest=ny*y+nz*z+d
   if nx>1e-9:hi=min(hi,-rest/nx)
   elif nx<-1e-9:lo=max(lo,-rest/nx)
   elif rest>1e-8:valid=False
  if valid and lo<=hi+1e-8:out.append((lo,hi))
 assert out,y
 return min(a for a,b in out),max(b for a,b in out)
def band(y):
 a,b=edges(y);mid=(a+b)/2;half=(b-a)/4
 return mid-half,mid+half

def transform(poses,n,v):
 p,r=poses[n];return gr.inv().apply(p+r.apply(np.asarray(v).reshape(-1,3))-gp).reshape(np.asarray(v).shape)
# Find a comfortable static example, starting from the previous B candidate.
prior_path=ROOT/'docs/2026-10-26/엄지 접촉/B_candidate.json'
prior=np.array(json.loads(prior_path.read_text())['q_rad'])
lo=np.array(initial['native_PD_properties']['lower'])[indices];hi=np.array(initial['native_PD_properties']['upper'])[indices]
seedposes=fk(prior);patch_G=transform(seedposes,'LH:thumb3',pieces)
face_G=gr.inv()*seedposes['LH:thumb3'][1]
normal_G=face_G.apply(piece_normals)
centroids=patch_G.mean(1)
quality=np.abs(centroids@normal+plane[3])+.02*np.maximum(normal_G@normal+.5,0)
k=int(np.argmin(quality))
# Contact vertex and normal are from the same selected source face.
face=pieces[k];vertex=int(np.argmin(patch_G[k]@normal+plane[3]));witness_local=face[vertex];witness_normal=piece_normals[k]
target_y=min(yhi-.008,center+.025);target=np.array([0.,target_y,z_at(target_y)])+normal*.0008
vertices={n:np.unique(t.reshape(-1,3),axis=0) for n,t in triangles.items()}
def residual(q):
 poses=fk(q);w=transform(poses,'LH:thumb3',witness_local)
 rn=gr.inv()*poses['LH:thumb3'][1];ng=rn.apply(witness_normal)
 cloud=np.concatenate([transform(poses,n,v) for n,v in vertices.items()])
 gap=cloud@normal+plane[3]
 return np.r_[w-target,.0015*(ng+normal),10*np.minimum(gap.min()-.00015,0),.00015*(q-prior)]
solutions=[]
for seed in [prior,np.clip(q0[indices],lo+1e-7,hi-1e-7)]:
 result=least_squares(residual,np.clip(seed,lo+1e-7,hi-1e-7),bounds=(lo,hi),max_nfev=600,ftol=1e-12,xtol=1e-12,gtol=1e-12)
 solutions.append(result)
result=min(solutions,key=lambda r:np.linalg.norm(r.fun));q=result.x;poses=fk(q)
# Read the nearest qualifying real patch vertex after fitting; the fit's
# seed vertex need not remain the closest one as the thumb rotates.
patch_points=transform(poses,'LH:thumb3',pieces).reshape(-1,3)
patch_normals=(gr.inv()*poses['LH:thumb3'][1]).apply(np.repeat(piece_normals,3,axis=0))
patch_gap=patch_points@normal+plane[3]
projected=patch_points-patch_gap[:,None]*normal
usable=(patch_gap>=0)&(projected[:,1]>=ylo)&(projected[:,1]<=yhi)&((patch_normals@normal)<=-.1)
for i in np.flatnonzero(usable):
 a,b=band(projected[i,1]);usable[i]=a<=projected[i,0]<=b
assert usable.any()
selected=int(np.where(usable,patch_gap,np.inf).argmin())
witness_local=pieces.reshape(-1,3)[selected];witness_normal=np.repeat(piece_normals,3,axis=0)[selected]
witness=patch_points[selected];projection=projected[selected];gap=float(patch_gap[selected])
clouds={n:transform(poses,n,v) for n,v in vertices.items()}
min_gap=min(float((v@normal+plane[3]).min()) for v in clouds.values())
assert 0<=gap<=.003,gap
assert min_gap>=-.00002,min_gap
assert ylo<=projection[1]<=yhi and band(projection[1])[0]<=projection[0]<=band(projection[1])[1]
assert (q>=lo).all() and (q<=hi).all()
candidate=copy.deepcopy(state)
for n in chain:
 p,r=poses[n];candidate['human_body_states'][bodies.index(n)]['pose']={'p':dict(zip('xyz',p.tolist())),'r':dict(zip('xyzw',r.as_quat().tolist()))}
for k,v in zip(indices,q):candidate['human_dof_states'][k]['pos']=float(v)
assert all(candidate['human_body_states'][k]==state['human_body_states'][k] for k,n in enumerate(bodies) if n not in chain)

# Reuse original visual meshes; all new overlay geometry is presentation-only.
model,data,mapping,xmltext=build_model(initial)
assert model.nq == 0 and model.nv == 0
for k in range(model.ngeom):
 name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,int(model.geom_bodyid[k])) or ''
 if name.startswith('human/LH:thumb'):color=(1.,.52,.12,1.)
 elif name.startswith('human/LH:') or name=='human/L_Wrist':color=(.24,.51,.7,1.)
 elif name.startswith('guitar/'):color=(.62,.66,.72,1.)
 else:color=(0,0,0,0)
 model.geom_rgba[k]=color
model.vis.headlight.ambient[:]=.6;model.vis.headlight.diffuse[:]=.7
model.vis.map.znear=.0001;model.vis.global_.offwidth=1200;model.vis.global_.offheight=850
pose_audit=set_body_poses(model,data,mapping,candidate)
renderer=mujoco.Renderer(model,height=850,width=1200)
font=lambda size:ImageFont.truetype(str(FONT),size)

def world(v):return gp+gr.apply(np.asarray(v))
def line(a,b,color,radius=.00045):
 geom=renderer.scene.geoms[renderer.scene.ngeom]
 mujoco.mjv_initGeom(geom,mujoco.mjtGeom.mjGEOM_CAPSULE,np.ones(3),np.zeros(3),np.eye(3).ravel(),np.array(color,dtype=np.float32))
 mujoco.mjv_connector(geom,mujoco.mjtGeom.mjGEOM_CAPSULE,radius,world(a),world(b));renderer.scene.ngeom+=1

def project(v):
 cam=renderer.scene.camera[0];pos=(renderer.scene.camera[0].pos+renderer.scene.camera[1].pos)/2
 forward=np.asarray(cam.forward);up=np.asarray(cam.up);right=np.cross(forward,up)
 delta=world(v)-pos;depth=delta@forward;focal=850/(2*np.tan(np.deg2rad(float(model.vis.global_.fovy))/2))
 return np.array([600+focal*(delta@right)/depth,425-focal*(delta@up)/depth])

def overlays():
 # Dense stripes at the actual sloping rear surface, offset 0.18mm to avoid z-fighting.
 for y in np.linspace(ylo,yhi,53):
  a,b=band(y);offset=normal*.00018
  line(np.array([a,y,z_at(y)])+offset,np.array([b,y,z_at(y)])+offset,[.12,.87,.52,.85],.00072)
 for y in (ylo,yhi):
  a,b=band(y);line([a,y,z_at(y)+normal[2]*.0003],[b,y,z_at(y)+normal[2]*.0003],[.03,.48,.26,1],.00065)
 for side in (0,1):
  ys=np.linspace(ylo,yhi,20)
  for a,b in zip(ys[:-1],ys[1:]):
   line([band(a)[side],a,z_at(a)+normal[2]*.0003],[band(b)[side],b,z_at(b)+normal[2]*.0003],[.03,.48,.26,1],.00065)
 # Highlight proposed thumb3 patch using source face edges; no anatomical label claim.
 patch=transform(poses,'LH:thumb3',pieces)
 for triangle in patch[::max(1,len(patch)//70)]:
  for a,b in zip(triangle,np.roll(triangle,-1,axis=0)):
   line(a,b,[1.,.86,.18,1],.00018)
 point=renderer.scene.geoms[renderer.scene.ngeom]
 mujoco.mjv_initGeom(point,mujoco.mjtGeom.mjGEOM_SPHERE,np.array([.001]*3),world(witness),np.eye(3).ravel(),np.array([.9,.16,.24,1],dtype=np.float32));renderer.scene.ngeom+=1

sheet=Image.new('RGB',(2400,1090),(245,248,252));draw=ImageDraw.Draw(sheet)
draw.text((35,18),'엄지는 넥 뒤 어디에 닿도록 할까?',font=font(42),fill='#203347')
draw.text((35,78),'초록: 제안한 넥 뒷면 영역  ·  주황: 엄지  ·  노랑: 끝마디 안쪽 패드 후보  ·  빨강: 예시 근접점',font=font(25),fill='#44566a')
views=[]
try:
 for col,(offset,title) in enumerate([([.045,.015,-.32],'① 넥 뒤에서 본 접촉 영역'),([.24,.018,-.18],'② 사선에서 본 엄지 패드')]):
  look=np.array([.018,center+.007,-.027]);cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE
  cam.lookat[:]=world(look);direction=-gr.apply(offset);cam.distance=np.linalg.norm(direction);cam.azimuth=np.rad2deg(np.arctan2(direction[1],direction[0]));cam.elevation=np.rad2deg(np.arctan2(direction[2],np.linalg.norm(direction[:2])))
  renderer.update_scene(data,camera=cam);overlays();im=Image.fromarray(renderer.render());dr=ImageDraw.Draw(im)
  dr.rectangle((0,0,1200,62),fill='#edf2f7');dr.text((20,12),title,font=font(30),fill='#203347')
  uv=project(witness);label=uv+np.array([100,-110]);label=np.clip(label,[50,110],[875,660])
  dr.line([tuple(uv),tuple(label+[0,42])],fill='#ff5364',width=4);dr.ellipse((uv[0]-10,uv[1]-10,uv[0]+10,uv[1]+10),outline='#ff5364',width=3)
  dr.rounded_rectangle((label[0]-8,label[1]-5,label[0]+295,label[1]+65),radius=8,fill='#182332');dr.text(tuple(label),'패드로 가볍게 근접',font=font(24),fill='white');dr.text(tuple(label+[0,32]),'예시 간격 %.2f mm'%(gap*1000),font=font(21),fill='#ffd7da')
  path=HERE/('rear.png' if col==0 else 'oblique.png');im.save(path);sheet.paste(im,(col*1200,140));views.append(dict(camera_guitar=(gr.inv().apply((renderer.scene.camera[0].pos+renderer.scene.camera[1].pos)/2-gp)).tolist(),image=str(path)))
finally:renderer.close()
draw=ImageDraw.Draw(sheet);draw.text((35,1000),'넥 폭 가운데 50% × 작업 프렛 중심 ±4cm  |  실제 뒷면에서 0~3mm 근접 대역 제안',font=font(28),fill='#203347')
draw.text((35,1045),'정지 예시 · 엄지만 변경 · 관절각 고정 요구 아님 · 학습/물리 적분 0 · 보상 및 초기 자세 미적용',font=font(23),fill='#596b7e')
main=OUT/'엄지_넥뒷면_목표영역_v1.png';sheet.save(main)

# Orthographic dimensional map and explicitly schematic normal-gap inset.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager,FontProperties
from matplotlib.patches import Polygon,Rectangle
fontManager.addfont(str(FONT));plt.rcParams.update({'font.family':FontProperties(fname=str(FONT)).get_name(),'axes.unicode_minus':False})
fig,axes=plt.subplots(1,2,figsize=(15,7),gridspec_kw={'width_ratios':[1.1,1.]},facecolor='#f6f8fb')
ax=axes[0];ys=np.linspace(ylo-.065,yhi+.065,120);outer=np.array([[edges(y)[0],y] for y in ys]+[[edges(y)[1],y] for y in ys[::-1]])*1000
ax.add_patch(Polygon(outer,fc='#c6ced8',ec='#6d7d8f'))
ys=np.linspace(ylo,yhi,60);poly=np.array([[band(y)[0],y] for y in ys]+[[band(y)[1],y] for y in ys[::-1]])*1000
ax.add_patch(Polygon(poly,fc='#49d99d',ec='#087c4d',lw=2))
ax.axhline(center*1000,color='#627eaa',ls='--',lw=1);ax.scatter(*projection[:2]*1000,c='#e84358',s=80,zorder=5)
ax.annotate('정지 예시의 근접 위치',projection[:2]*1000,xytext=(40,20),textcoords='offset points',fontsize=12,color='#bd263d',arrowprops={'arrowstyle':'->','color':'#bd263d'})
for y,text in [(ylo,'−4cm'),(center,'작업 범위 중심'),(yhi,'+4cm')]:ax.text(-45,y*1000,text,ha='right',va='center',fontsize=11)
ax.annotate('',xy=(45,yhi*1000),xytext=(45,ylo*1000),arrowprops={'arrowstyle':'<->','color':'#087c4d','lw':2});ax.text(48,center*1000,'총 8cm',va='center',fontsize=12,color='#087c4d')
a,b=edges(center);u,v=band(center);yy=(yhi+.023)*1000
ax.annotate('',xy=(u*1000,yy),xytext=(v*1000,yy),arrowprops={'arrowstyle':'<->','color':'#087c4d','lw':2});ax.text(0,yy+5,'이 위치 넥 폭의 가운데 50%',ha='center',fontsize=12,color='#087c4d')
ax.set(xlim=(-82,82),ylim=((ylo-.055)*1000,(yhi+.06)*1000),xlabel='넥 폭 방향 Gx (mm)',ylabel='넥 길이 방향 Gy (mm)',title='③ 실제 넥 뒷면의 허용 위치 제안');ax.set_aspect('equal');ax.grid(alpha=.15)
ax=axes[1];ax.set_xlim(-3,16);ax.set_ylim(-3,10)
ax.add_patch(Rectangle((-3,-3),3,13,fc='#b9c3cf'));ax.axvspan(0,3,color='#49d99d',alpha=.7);ax.axvline(0,color='#506275',lw=2)
ax.text(-1.4,5,'넥\n내부',ha='center',fontsize=13);ax.text(1.5,8.5,'최대 보상\n제안 대역',ha='center',fontsize=13,color='#075d3b');ax.text(9,8.5,'멀수록 보상 감소',ha='center',fontsize=13,color='#526477')
ax.plot([gap*1000,gap*1000+2.5,gap*1000+6.0],[0,1.4,1.8],color='#f69635',lw=22,solid_capstyle='round');ax.scatter([gap*1000],[0],color='#e84358',s=90,zorder=5)
ax.annotate('',xy=(0,-1.3),xytext=(3,-1.3),arrowprops={'arrowstyle':'<->','color':'#087c4d','lw':2});ax.text(1.5,-2.2,'0〜3 mm',ha='center',fontsize=13)
ax.text(8,4.1,'엄지 끝마디 패드가\n표면을 향하도록',ha='center',fontsize=14,color='#9b531e')
ax.set(xlabel='실제 뒷면 법선 방향의 바깥 간격 (mm)',yticks=[],title='④ 간격 개념도 — 엄지 모양은 도식');ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
fig.suptitle('엄지 뒷면 보상에 사용할 영역 제안',fontsize=21,x=.04,ha='left',y=.98)
fig.text(.04,.9,'첫 작업 프렛 범위 4~9 기준 예시 · 위치/간격 조건이며 특정 엄지 관절각을 요구하지 않음',fontsize=12,color='#526477')
fig.subplots_adjust(left=.1,right=.98,top=.83,bottom=.16,wspace=.37)
fig.text(.04,.04,'0~3mm는 실제 접촉 인증이 아닌 기하 근접 대역입니다. 침투·힘 증가를 보상하지 않는 방향으로 설계하며 아직 학습에 적용하지 않았습니다.',fontsize=11,color='#526477')
dims=OUT/'엄지_넥뒷면_범위설명_v1.png';fig.savefig(dims,dpi=150);plt.close(fig)

sourcepins=json.loads((ROOT/'docs/2026-10-23/guitar_learning_long_training_v16/training_source_manifest.json').read_text())['source']
assert all(sha(p)==h for p,h in sourcepins.items())
inputs={BASE/'visual_initial.json',manifest_path,track_path,prior_path,Path(__file__).resolve(),FONT}
for a in initial['loaded_assets']:inputs|=asset_paths(a['path'])
inputs|={Path(p) for p in neckpins}
record=dict(completed=True,scope='static original-mesh proposal; not a learned pose or contact certification',new_physics_steps=0,training_updates=0,production_modified=False,active_python_pins_verified=len(sourcepins),rear_plane_G=plane.tolist(),work_frets=span,work_center_Gy_m=center,length_bounds_Gy_m=[ylo,yhi],width_fraction=.5,near_band_m=[0,.003],thumb_patch='experimental distal source flexion-side triangle clip, not anatomical segmentation; not yet a production reward patch',thumb_patch_triangles=len(pieces),joint_names=[names[k] for k in indices],joint_q_rad=q.tolist(),within_native_limits=True,nonthumb_bodies_unchanged=True,guitar_unchanged=candidate['guitar_body_states']==state['guitar_body_states'],witness_G_m=witness.tolist(),witness_normal_G=(gr.inv()*poses['LH:thumb3'][1]).apply(witness_normal).tolist(),rear_projection_G_m=projection.tolist(),witness_gap_m=gap,all_thumb_vertex_min_rear_gap_m=min_gap,pose_readback=pose_audit,renderer_nq=int(model.nq),renderer_nv=int(model.nv),witness_facing_cos=float(-((gr.inv()*poses['LH:thumb3'][1]).apply(witness_normal)@normal)),views=views,inputs_sha256={str(p):sha(p) for p in inputs},outputs_sha256={str(p):sha(p) for p in [main,dims,HERE/'rear.png',HERE/'oblique.png']})
write(HERE/'verification.json',record);write(HERE/'candidate_state.json',candidate)
print(json.dumps({k:record[k] for k in ['completed','work_center_Gy_m','length_bounds_Gy_m','witness_gap_m','all_thumb_vertex_min_rear_gap_m','thumb_patch_triangles','active_python_pins_verified']}))
