"""Locate native upper-arm contacts in the declared shoulder-side/upper-bout region."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parent;R=P.parents[4]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vec(v):return np.array([v[k]for k in 'xyz'])
def pose(s):return vec(s['pose']['p']),Rotation.from_quat([s['pose']['r'][k]for k in 'xyzw'])
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 asset=R/'tab2body/assets/smpl_mpl_hands_body.xml';geom=next(b for b in ET.parse(asset).iter('body')if b.get('name')=='R_Shoulder').find('geom');a,b=np.fromstring(geom.get('fromto'),sep=' ').reshape(2,3);axis=b-a;radius=float(geom.get('size'));inputs={str(Path(__file__).resolve()):sha(Path(__file__).resolve()),str(asset):sha(asset)};cases={}
 folders=sorted(P.glob('native_v*/*/report.json'))
 baseline=R/'docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/native_v2/right4_close_support_upper_press'
 for folder in [baseline]+[f.parent for f in folders]:
  path=folder/'media/physics_endpoint_contacts.json';inputs[str(path)]=sha(path);endpoints=read(path)['rows'];assert len(endpoints)==1200;rows=[];samples=positive=0;pair_errors=[];surface_errors=[];example=None
  for ep in endpoints:
   hp,hr=pose(ep['human_body_states']['R_Shoulder']);bp,br=pose(ep['guitar_body_states']['G:body']);gp,gr=pose(ep['guitar_body_states']['guitar']);contacts=[]
   for c in ep['right_upper_arm_body_contacts']:
    h='0'if c['body0_name']=='human/R_Shoulder'else'1';g='1'if h=='0'else'0';assert c['body'+g+'_name']=='guitar/G:body';hl=vec(c['localPos'+h])+vec(c['offset'+h]);gl=vec(c['localPos'+g])+vec(c['offset'+g]);hw=hp+hr.apply(hl);gw=bp+br.apply(gl);pair=float(np.linalg.norm(hw-gw));t=float((hl-a)@axis/(axis@axis));clipped=float(np.clip(t,0,1));surface=float(abs(np.linalg.norm(hl-(a+clipped*axis))-radius));G=gr.inv().apply(gw-gp);quality=pair<=.003 and surface<=.003;prox=clipped<=.35;upper=G[0]<-.17 and -.55<=G[1]<=-.43;qualified=quality and prox and upper
    item={'human_segment_fraction_raw':t,'human_segment_fraction_clipped':clipped,'guitar_feature_G_m':G.tolist(),'contact_feature_W_m':gw.tolist(),'feature_pair_distance_m':pair,'capsule_radius_difference_m':surface,'frame_geometry_consistent':quality,'shoulder_side35':prox,'upper_bulge_region':bool(upper),'declared_region_contact':bool(qualified),'positive_raw_lambda':bool(c['lambda']>0)};contacts.append(item);pair_errors.append(pair);surface_errors.append(surface)
    if qualified and c['lambda']>0 and example is None:example={'physics_step':ep['physics_step'],'time_s':ep['physics_step']/240,'contact':item}
   samples+=any(c['declared_region_contact']for c in contacts);positive+=any(c['declared_region_contact']and c['positive_raw_lambda']for c in contacts);rows.append({'physics_step':ep['physics_step'],'time_s':ep['physics_step']/240,'contacts':contacts})
  assert all(c['frame_geometry_consistent']for row in rows for c in row['contacts']), 'native contact frame/surface consistency failed; do not certify region'
  cases[folder.name]={'folder':str(folder),'total_samples':1200,'upper_arm_any_contact_samples':sum(bool(ep['right_upper_arm_body_contacts'])for ep in endpoints),'declared_region_contact_samples':int(samples),'declared_region_positive_raw_lambda_samples':int(positive),'max_feature_pair_distance_m':max(pair_errors,default=0),'max_capsule_radius_difference_m':max(surface_errors,default=0),'first_qualified_positive_example':example,'rows':rows}
 assert all(sha(Path(p))==h for p,h in inputs.items())
 save(P/'contact_region_v2.json',{'input_sha256':inputs,'capsule_fromto_local_m':[a.tolist(),b.tolist()],'capsule_radius_m':radius,'region_definition':{'human_segment_clipped_max':.35,'guitar_G_x_max_m':-.17,'guitar_G_y_range_m':[-.55,-.43],'native_frame_consistency_tolerance_m':.003},'cases':cases,'scope':'native contact feature/offset location projected to source capsule; pairs and radius cross-checked. Does not measure force/support share or certify anatomical armpit tissue/continuous solver contacts.'})
 print(json.dumps({k:{n:v[n]for n in ['upper_arm_any_contact_samples','declared_region_contact_samples','declared_region_positive_raw_lambda_samples','max_feature_pair_distance_m','max_capsule_radius_difference_m']}for k,v in cases.items()},indent=2))
if __name__=='__main__':main()
