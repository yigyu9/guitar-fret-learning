from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import xml.etree.ElementTree as ET
sys.path.insert(0,'/home/ajou/yigyu/3')
from guitar_learning.gpu.geometry import finger_mesh_surface_samples
root=Path('/home/ajou/yigyu/3');base=Path('/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v8_long/evaluations')
xmlpath=root/'guitar_learning/assets/gpu_rigid_guitar_v1/guitar_compound.xml';tree=ET.parse(xmlpath).getroot();folder=xmlpath.parent/tree.find('compiler').get('meshdir','.')
meshes={m.get('name'):m for m in tree.findall('./asset/mesh')};triangles=[];planes=[]
for geom in tree.findall('./worldbody/body/geom'):
 if geom.get('mesh') not in ('guitar_neck1','guitar_neck2') or (geom.get('contype')=='0' and geom.get('conaffinity')=='0'):continue
 m=meshes[geom.get('mesh')];v=np.array([[float(x) for x in line.split()[1:4]] for line in (folder/m.get('file')).read_text().splitlines() if line.startswith('v ')]);v*=np.fromstring(m.get('scale','1 1 1'),sep=' ')
 q=np.fromstring(geom.get('quat','1 0 0 0'),sep=' ');v=Rotation.from_quat(np.r_[q[1:],q[:1]]).apply(v)+np.fromstring(geom.get('pos','0 0 0'),sep=' ')
 h=ConvexHull(v);rear=h.equations[:,2]<-.5
 triangles.extend(v[h.simplices[rear]]);planes.extend(h.equations[rear])
triangles=np.array(triangles);planes=np.array(planes)
assert len(triangles)==4 and np.allclose(planes,planes[0],atol=1e-12)
plane=planes[0];samples,valid=finger_mesh_surface_samples(['LH:thumb2','LH:thumb3'])
def apply(q,p):
 q=q/np.linalg.norm(q,axis=-1,keepdims=True);v=q[...,:3];uv=np.cross(v,p);return p+2*(q[...,3:]*uv+np.cross(v,uv))
def triangle_distance2(p,t):
 a,b,c=t;ab=b-a;ac=c-a;n=np.cross(ab,ac);n/=np.linalg.norm(n)
 gap=(p-a)@n;projected=p-gap[...,None]*n;v=projected-a
 d00=ab@ab;d01=ab@ac;d11=ac@ac;d20=v@ab;d21=v@ac;denom=d00*d11-d01*d01
 u=(d11*d20-d01*d21)/denom;w=(d00*d21-d01*d20)/denom;inside=(u>=-1e-12)&(w>=-1e-12)&(u+w<=1+1e-12)
 edge=np.full(p.shape[:-1],np.inf)
 for start,end in [(a,b),(b,c),(c,a)]:
  line=end-start;f=np.clip(((p-start)@line)/(line@line),0,1);d=np.sum((p-(start+f[...,None]*line))**2,-1);edge=np.minimum(edge,d)
 return np.where(inside,gap**2,edge)
# Independent known cases: point over triangle interior, outside edge, exact vertex.
t=np.array([[0.,0,0],[1.,0,0],[0,1.,0]])
assert np.allclose(triangle_distance2(np.array([[.2,.2,.3],[2.,0,0],[0,0,0]]),t),[.09,1,0])
rows=[];input_pins={}
for label,sub in [(0,'initial'),(500,'update_0500'),(1000,'update_1000'),(1500,'update_1500'),(2000,'final')]:
 p=base/f'evaluation_fixed_{sub}_1024';meta=json.loads((p/'capture_metadata.json').read_text());names=meta['body_names'];g=names.index('guitar/guitar');ids=[names.index('human/LH:thumb'+str(s)) for s in (2,3)]
 distances=[];envrows=[]
 for capture in meta['captures']:
  path=p/capture['path'];digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==capture['sha256'];input_pins[str(path)]=digest
  with np.load(path,allow_pickle=False) as arr:body=arr['body_state'].astype(np.float64);time=arr['clock']/240.
  thumb=body[:,ids];world=thumb[:,:,None,:3]+apply(thumb[:,:,None,3:7],samples[None])
  guitar=body[:,g];q=guitar[:,3:7].copy();q[:,:3]*=-1
  local=apply(q[:,None,None],world-guitar[:,None,None,:3]);T=local.shape[0]
  gap=local@plane[:3]+plane[3]
  squared=np.full(local.shape[:-1],np.inf)
  for tri in triangles:squared=np.minimum(squared,triangle_distance2(local,tri))
  squared=np.where(valid[None],squared,np.inf)
  distance=np.sqrt(squared.min(axis=(1,2)))
  rearonly=np.sqrt(np.where(gap>=-.001,squared,np.inf).min(axis=(1,2)))
  # Cross-check quaternion transform with SciPy for a whole segment.
  expected=Rotation.from_quat(guitar[:,3:7]).inv().apply(world[:,1,0]-guitar[:,:3]);assert np.max(abs(expected-local[:,1,0]))<1e-12
  mask=time>=10-1e-10;distances.append(distance[mask]);envrows.append({'env_id':capture['env_id'],'initial_min_sample_distance_m':float(distance[0]),'post10_median_m':float(np.median(distance[mask])),'post10_within_3mm_fraction':float(np.mean(distance[mask]<=.003)),'post10_within_10mm_fraction':float(np.mean(distance[mask]<=.01)),'post10_backside_sample_within3mm_fraction':float(np.mean(rearonly[mask]<=.003))})
 d=np.concatenate(distances);rows.append({'updates':label,'envs':len(envrows),'post10_endpoint_count':len(d),'distance_median_m':float(np.median(d)),'distance_min_m':float(d.min()),'distance_max_m':float(d.max()),'within3mm_fraction':float(np.mean(d<=.003)),'within10mm_fraction':float(np.mean(d<=.01)),'envs_detail':envrows})
result={'schema':'v8_thumb_rear_source_surface_analysis.v1','completed':True,'geometry':'min Euclidean distance of existing source thumb2/3 support vertices to finite rear facets (normal Gz < -.5) of two physical source neck convex hulls; not actual contact/pressure. Back-side sample check permits up to1mm plane penetration.','rear_plane_G':plane.tolist(),'rear_triangles':triangles.tolist(),'thumb_surface_sample_count':int(valid.sum()),'samples':'8 predeclared safe envs per checkpoint,60Hz endpoints t>=10s,1370 each. No240Hz contact forces/partners in NPZ.','models':rows,'input_sha256':input_pins}
Path('/tmp/v8_thumb_pose_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for r in rows: print(json.dumps({k:v for k,v in r.items() if k!='envs_detail'}))
print('initial_distances',rows[-1]['envs_detail'])
