import argparse,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
R=Path('/home/ajou/yigyu/3');B=R/'docs/2026-10-12/stability_adapter_2/results'
parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['palm_patch_priority_initial_v1'],required=True);P=B/parser.parse_args().phase
def read(p):return json.loads(Path(p).read_text())
from stability_adapter_2.environment import np
from stability_adapter_2.initial_overlap import build_probe
from stability_adapter_2.face_referenced_geometry import face_geometry
from stability_adapter_2.build_fixed_lower_asset import ASSET,pose
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
source=R/'stability_adapter_2/search_palm_patch_priority.py'
import ast
node=next(n for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.FunctionDef) and n.name=='palm_projection')
projection_scope={'np':np,'grip':read(P/'proposal.json'),'clearance':.0003}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),projection_scope)
proposal=read(P/'proposal.json');initial=read(B/'three_face_support_loss_v1/native/saved_finger_targets/initial_values.json');bodies=initial['human_body_names'];gn=[r['body'] for r in read(B/'three_face_support_loss_v1/native/saved_finger_targets/shape_properties.json')['actors']['guitar']['body_ranges']]
config=read(R/'stability_adapter_2/config.json');config['humanoid_asset']=str(ASSET);out=[]
from stability_adapter_2.palm_side_source_checks import intersection
from stability_adapter_2.warmstart_targets import compose
checks={}
indices=[initial['human_joint_names'].index(n) for n in read(P/'sensitivity.json')['coordinate_names']]
other=np.setdiff1d(np.arange(81),indices)
main_indices=[initial['human_joint_names'].index(n) for n in initial['main_control_joint_names']]
q0=np.array(proposal['old_initial_angles_rad']);target=np.array(proposal['saved_absolute_targets_rad'],dtype=np.float32)
native_lower=np.array(initial['PD_properties']['lower']);native_upper=np.array(initial['PD_properties']['upper'])
all_rows=proposal['rows']+proposal['rejected']
assert len(indices)==33 and len(all_rows)==proposal['processed_source_candidates'] and 1<=len(all_rows)<=proposal['requested_source_seed_count']
for row in all_rows:
 q=np.array(row['expected_initial_angles_rad']);offs={n:float(target[i])-q[i] for i,n in enumerate(initial['human_joint_names']) if n in proposal['left33_names']}
 assert np.array_equal(q[other],q0[other]) and np.all(q>=native_lower) and np.all(q<=native_upper)
 assert np.all(q[indices]>=row['search_lower_rad']) and np.all(q[indices]<=row['search_upper_rad'])
 assert np.array_equal(compose(q,main_indices,[offs.get(initial['human_joint_names'][i],0.) for i in main_indices],native_lower,native_upper),target)
 assert row['expected_absolute_targets_rad']==proposal['saved_absolute_targets_rad'] and row['absolute_strap_rest_length_m']==initial['absolute_strap_rest_length_m']
 checks[row['label']+'_81target_other48_bounds_LA']=True
xml=ET.parse(ASSET).getroot();parents={c.get('name'):p.get('name') for p in xml.iter('body') for c in p.findall('body')}
def distance(a,b):
 chain=[];current=a
 while current in parents:chain.append(current);current=parents[current]
 chain.append(current);steps=0;current=b
 while current not in chain and current in parents:steps+=1;current=parents[current]
 return steps+chain.index(current) if current in chain else 99
for row in all_rows:
 state=row['source_state'];scene=SimpleNamespace(config=config,human=0,guitar=1,env=None,gym=SimpleNamespace(get_actor_rigid_body_names=lambda env,actor:bodies if actor==0 else gn),bodies=lambda actor:state['human_body_states'] if actor==0 else state['guitar_body_states'])
 model,data,shapes=build_probe(scene);gp,gq=pose(state['guitar_body_states'][0]);gr=Rotation.from_quat(gq)
 meshes={s['geom_id']:face_geometry(model,data,s) for s in shapes}
 actual=[]
 for h in [s for s in shapes if s['actor']=='human']:
  for g in [s for s in shapes if s['actor']=='guitar']:
   radius=intersection(meshes[h['geom_id']],meshes[g['geom_id']])
   if radius>1e-7:actual.append((h['body'],g['body'],radius))
 expected=[(p['human'],p['guitar'],p['common_radius_m']) for p in row['source_intersections']]
 assert len(actual)==len(expected) and all(a[:2]==e[:2] and abs(a[2]-e[2])<1e-12 for a,e in zip(actual,expected))
 checks[row['label']+'_all_human_guitar_intersections_recomputed']=True
 humans=[s for s in shapes if s['actor']=='human'];hand=[s for s in humans if s['body'].startswith('LH:') or s['body'] in ('L_Wrist','L_Elbow')];self_cross=[]
 for k,h in enumerate(hand):
  for g in hand[k+1:]:
   if distance(h['body'],g['body'])<=2:continue
   radius=intersection(meshes[h['geom_id']],meshes[g['geom_id']])
   if radius>1e-7:self_cross.append((h['body'],g['body'],radius))
 expected=[(v['a'],v['b'],v['common_radius_m']) for v in row['nonadjacent_left_hand_intersections']]
 assert len(self_cross)==len(expected) and all(a[:2]==e[:2] and abs(a[2]-e[2])<1e-12 for a,e in zip(self_cross,expected))
 cross=[]
 for h in [s for s in humans if s['body'].startswith('LH:') or s['body']=='L_Wrist']:
  for g in [s for s in humans if s['body'].startswith('RH:') or s['body']=='R_Wrist']:
   radius=intersection(meshes[h['geom_id']],meshes[g['geom_id']])
   if radius>1e-7:cross.append((h['body'],g['body'],radius))
 expected=[(v['left'],v['right'],v['common_radius_m']) for v in row['cross_hand_intersections']]
 assert len(cross)==len(expected) and all(a[:2]==e[:2] and abs(a[2]-e[2])<1e-12 for a,e in zip(cross,expected))
 checks[row['label']+'_self_and_cross_hands_recomputed']=True
 for body,expected_point in row['front_point_G_m'].items():
  p,r=pose(state['human_body_states'][bodies.index(body)]);facet=row['source_facets'][body];point=gr.inv().apply(p+Rotation.from_quat(r).apply(facet['point_local_m'])-gp)
  assert np.linalg.norm(point-np.array(expected_point))<1e-12
  goal=np.array(row['front_goal_G_m'][body]);assert abs(np.linalg.norm(point-goal)*1000-row['front_goal_error_mm'][body])<1e-9
 checks[row['label']+'_front_points_and_errors_recomputed']=True

 for body,anchor in row['source_anchors'].items():
  p,r=pose(state['human_body_states'][bodies.index(body)]);point=gr.inv().apply(p+Rotation.from_quat(r).apply(anchor['source_point_local_m'])-gp)
  assert np.linalg.norm(point-np.array(row['anchor_G_m'][body]))<1e-12
  assert abs(np.linalg.norm(point-np.array(row['anchor_goal_G_m'][body]))*1000-row['anchor_goal_error_mm'][body])<1e-9
 checks[row['label']+'_anchors_and_errors_recomputed']=True
 for body,gap in row['source_hull_to_finite_patch'].items():
  shape=next(s for s in shapes if s['actor']=='human' and s['body']==body);mesh=face_geometry(model,data,shape);poly=gr.apply(np.array(proposal['regions_G_m']['thumb' if body=='LH:thumb3' else 'palm']))+gp
  a=np.array(gap['palm_witness_world_m']);b=np.array(gap['target_witness_world_m']);center=(mesh.vertices.mean(axis=0)+poly.mean(axis=0))/2;planes=ConvexHull((mesh.vertices-center)*1000).equations
  hull_viol=max(0.,float((planes[:,:3]@((a-center)*1000)+planes[:,3]).max()))
  # Quad triangle membership via nearest barycentric projection, independently of QP weights.
  import trimesh
  tri=np.array([poly[[0,1,2]],poly[[0,2,3]]]);near=trimesh.triangles.closest_point(tri,np.tile(b,(2,1)));poly_error=float(np.linalg.norm(near-b,axis=1).min())
  upper=float(np.linalg.norm(a-b));normal=(a-b)/upper if upper else np.zeros(3);lower=max(0.,float((mesh.vertices@normal).min()-(poly@normal).max()))
  # Verify convex quad membership directly in centred millimetres. Legacy triangle
  # closest-point query has a 2e-11m projection artefact in one distant seed.
  pc=poly.mean(axis=0);quad=(poly-pc)*1000;point=(b-pc)*1000
  normal=np.cross(quad[1]-quad[0],quad[2]-quad[0]);normal/=np.linalg.norm(normal)
  plane_error=abs(float((point-quad[0])@normal))
  edges=np.roll(quad,-1,axis=0)-quad;inward=np.cross(normal,edges);inward/=np.linalg.norm(inward,axis=1)[:,None]
  inward*=np.where(np.einsum('ij,ij->i',inward,quad.mean(axis=0)-quad)>0,1.,-1.)[:,None]
  edge_violation=max(0.,float(-np.einsum('ij,ij->i',inward,point-quad).min()))
  assert hull_viol<1e-9 and plane_error<1e-9 and edge_violation<1e-9 and abs(upper-gap['distance_m'])<1e-12 and abs(lower-gap['distance_lower_bound_m'])<1e-12
  out.append(dict(label=row['label'],body=body,hull_plane_violation_mm=hull_viol,legacy_nearest_triangle_error_m=poly_error,polygon_plane_error_mm=plane_error,polygon_edge_violation_mm=edge_violation,upper_bound_m=upper,lower_bound_m=lower,solver_success_recorded=gap['optimizer_success']))
for row in all_rows:
 expected_goal=projection_scope['palm_projection'](np.array(row['anchor_G_m']['LH:palm']))
 assert np.linalg.norm(expected_goal-np.array(row['anchor_goal_G_m']['LH:palm']))<1e-12
checks['current_palm_finite_patch_goal_recomputed']=True
checks['all_saved_distance_witness_intervals_recomputed']=len(out)==2*len(all_rows)
result={'checks':checks,'measurements':out,'native_initializations':0,'physics_steps':0,'scope':'read-only source meshes reconstructed from saved source body poses; no cooked/actual grip certification','audit_source':Path(__file__).read_text()}
assert not (P/'interval_data_verification.json').exists();(P/'interval_data_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'verified':len(out),'max_hull_plane_violation_mm':max(r['hull_plane_violation_mm'] for r in out),'max_polygon_plane_error_mm':max(r['polygon_plane_error_mm'] for r in out),'max_polygon_edge_violation_mm':max(r['polygon_edge_violation_mm'] for r in out),'recorded_solver_false':sum(not r['solver_success_recorded'] for r in out)},indent=2))
