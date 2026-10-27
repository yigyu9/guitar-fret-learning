#!/usr/bin/env python3
"""Build source-mesh views and DXF depth sample plot only; never loads Isaac Gym."""
from pathlib import Path
import hashlib,json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/om_body_matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1'
A=P/'artifacts_v1'
ASSET=ROOT/'stability_adapter_2/assets/om_body_geometry_v2'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())

inputs={}
def pin(path,expected=None):
 path=Path(path); actual=sha(path)
 if expected is not None: assert actual==expected,(path,actual,expected)
 inputs[str(path)]=actual
 return path

depth=read(pin(P/'depth_v1.json'))
build=read(pin(P/'build_v2.json'))
manifest=read(pin(ASSET/'manifest.json'))
assert depth['passed'] and build['checks']['visual_closed_positive']
assert build['checks']['collision_XY_errors_below_0_5mm']
visual=ASSET/'body_visual.obj'
expected=next(x['sha256'] for x in build['input_sha256'].values() if False) if False else None
# Pin the body visual output from the builder's recorded output entry.
visual_sha=None
for section in ['meshes','outputs','input_sha256']:
 value=build.get(section)
 if isinstance(value,list):
  for item in value:
   if item.get('path')==str(visual): visual_sha=item.get('sha256')
 if isinstance(value,dict) and str(visual) in value: visual_sha=value[str(visual)]
assert visual_sha
pin(visual,visual_sha)
# Pin the source/helper/depth chain relevant to these plots.
for dataset in [depth,build,manifest]:
 for q,h in dataset.get('input_sha256',{}).items():
  path=Path(q) if Path(q).is_absolute() else ROOT/q
  if path.is_file(): pin(path,h)
for q in [ASSET/'ATTRIBUTION.md',ROOT/'stability_adapter_2/build_om_body_geometry_v2.py',ROOT/'stability_adapter_2/extract_om_depth_v1.py',ROOT/'stability_adapter_2/OM_BODY_GEOMETRY_PLAN_V1.md',FONT]:
 pin(q)

# Parse actual mesh triangles from OBJ (metre coordinates); no schematic substitute.
verts=[]; faces=[]
for line in visual.open():
 if line.startswith('v '): verts.append([float(x) for x in line.split()[1:4]])
 elif line.startswith('f '):
  ids=[int(x.split('/')[0])-1 for x in line.split()[1:]]
  for i in range(1,len(ids)-1): faces.append([ids[0],ids[i],ids[i+1]])
assert len(verts)>100 and len(faces)>100
font=FontProperties(fname=str(FONT))
plt.rcParams['font.family']=font.get_name()
plt.rcParams['axes.unicode_minus']=False
fig=plt.figure(figsize=(18,6.6),facecolor='white')
views=[('정면 · local XY',90,-90),('측면 · local YZ',0,0),('사선 · source mesh',24,-48)]
import numpy as np
v=np.asarray(verts); f=np.asarray(faces); tris=v[f]
bounds=np.array([v.min(axis=0),v.max(axis=0)])
center=v.mean(axis=0); span=bounds[1]-bounds[0]; radius=max(span)*.53
for i,(title,elev,azim) in enumerate(views,1):
 ax=fig.add_subplot(1,3,i,projection='3d')
 poly=Poly3DCollection(tris,facecolor='#8f969d',edgecolor='none',linewidth=0,antialiased=False)
 ax.add_collection3d(poly)
 ax.set_xlim(center[0]-radius,center[0]+radius); ax.set_ylim(center[1]-radius,center[1]+radius); ax.set_zlim(center[2]-radius,center[2]+radius)
 ax.set_box_aspect((1,1,1)); ax.view_init(elev=elev,azim=azim); ax.set_proj_type('ortho')
 ax.set_title(title,fontproperties=font,pad=8)
 ax.set_axis_off()
fig.suptitle('body_visual.obj 실제 source mesh · Isaac Gym 렌더/PhysX cooked mesh 아님 · local coordinates in metres',fontproperties=font,fontsize=16,y=.99)
fig.tight_layout(rect=[0,0,.99,.94]); fig.savefig(A/'source_mesh_three_views.png',dpi=170,bbox_inches='tight'); plt.close(fig)

# Plot exactly the samples supplied by depth_v1; no interpolation or new depth samples.
samples=np.asarray(depth['depth_samples_mm'],dtype=float)
fig,ax=plt.subplots(figsize=(11,6.8),facecolor='white')
fig.subplots_adjust(top=.81,bottom=.24)
ax.scatter(samples[:,0],samples[:,1],s=70,color='#217c91',label='depth_v1.json 샘플')
mx=float(depth['maximum_depth_side_x_mm']); my=float(depth['maximum_centerline_depth_mm'])
ax.scatter([mx],[my],s=130,marker='*',color='#ba5e2b',label='계산된 중심선 최대')

ax.set_xlabel('side-axis local position (mm, tail → neck)',fontproperties=font)
ax.set_ylabel('DXF local depth (mm)',fontproperties=font)
fig.suptitle('depth_v1.json local depth 샘플 · 값은 mm',fontproperties=font,fontsize=15,y=.98)
fig.text(.5,.89,f'계산된 중심선 최대 {my:.5f} mm · side-axis 위치 {mx:.5f} mm',ha='center',fontproperties=font,fontsize=11)
ax.grid(True,alpha=.25); ax.legend(prop=font,loc='lower left')
# Secondary axes make unit conversion visible without changing plotted coordinates.
secx=ax.secondary_xaxis('top',functions=(lambda mm:mm/10,lambda cm:cm*10)); secx.set_xlabel('같은 위치 (cm)',fontproperties=font)
secy=ax.secondary_yaxis('right',functions=(lambda mm:mm/10,lambda cm:cm*10)); secy.set_ylabel('같은 깊이 (cm)',fontproperties=font)
fig.text(.5,.10,'점만 표시(연결 보간선 없음) · tail 104 mm / neck 85 mm · side axis 491.0 mm = 49.10 cm · plan axis 491.957 mm = 49.1957 cm',ha='center',fontproperties=font,fontsize=10)
fig.savefig(A/'local_depth_samples.png',dpi=170,bbox_inches='tight'); plt.close(fig)

out={str(q):sha(q) for q in sorted(A.glob('*.png'))}
prov={'schema':'om-body-source-views-provenance-v1','stage':'source geometry only; native results not consumed','input_sha256_before_after':{q:{'before':h,'after':sha(q)} for q,h in inputs.items()},'body_visual_obj_sha256':sha(visual),'body_visual_vertices':len(verts),'body_visual_triangles':len(faces),'depth_source_units':depth['source_units'],'depth_samples_mm':depth['depth_samples_mm'],'max_centerline_depth_mm':depth['maximum_centerline_depth_mm'],'side_axis_length_mm':depth['side_axis_length_mm'],'plan_axis_length_mm':depth['plan_axis_length_mm'],'font':{'path':str(FONT),'sha256':sha(FONT)},'render_libraries':{'matplotlib':matplotlib.__version__},'outputs_sha256':out,'producer_sha256':sha(Path(__file__))}
(A/'source_provenance_v1.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'outputs':out,'producer_sha256':prov['producer_sha256'],'input_count':len(inputs)},ensure_ascii=False,indent=2))
