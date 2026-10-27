"""Measure existing humanoid and build a private concert-shaped rigid guitar."""
from pathlib import Path
import hashlib,json,os,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import ConvexHull
import trimesh
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'stability_adapter_2/assets/realistic_guitar_v1'
RESULT=ROOT/'docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1'
SOURCE=ROOT/'tab2body/assets/guitar_asset.xml'
HUMAN=ROOT/'tab2body/assets/smpl_mpl_hands_body.xml'
UPPER=np.array([[0,.03],[.04,.085],[.1,.125],[.18,.148],[.25,.151],[.33,.139],[.41,.113],[.44,.101]])
LOWER=np.array([[.44,.101],[.5,.134],[.6,.173],[.72,.188],[.8,.182],[.9,.14],[.97,.075],[1,.006]])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    with Path(p).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False)
def human_measurement():
    import mujoco
    root=ET.parse(HUMAN).getroot();root.find('compiler').set('meshdir',str((HUMAN.parent/'mesh').resolve()));relaxed=[]
    for j in root.iter('joint'):
        if j.get('range'):
            lo,hi=map(float,j.get('range').split())
            if lo==hi:j.set('limited','false');relaxed.append(j.get('name'))
    m=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'));d=mujoco.MjData(m);mujoco.mj_forward(m,d);bounds=[]
    for i in range(m.ngeom):
        typ=int(m.geom_type[i]);r=d.geom_xmat[i].reshape(3,3);p=d.geom_xpos[i];size=m.geom_size[i]
        if typ==mujoco.mjtGeom.mjGEOM_PLANE:continue
        if typ==mujoco.mjtGeom.mjGEOM_MESH:
            mid=m.geom_dataid[i];adr=m.mesh_vertadr[mid];v=m.mesh_vert[adr:adr+m.mesh_vertnum[mid]]@r.T+p;bounds.extend([v.min(0),v.max(0)]);continue
        if typ==mujoco.mjtGeom.mjGEOM_CAPSULE:extent=abs(r[:,2]*size[1])+size[0]
        elif typ==mujoco.mjtGeom.mjGEOM_SPHERE:extent=np.full(3,size[0])
        elif typ==mujoco.mjtGeom.mjGEOM_ELLIPSOID:extent=np.sqrt((r*r*size*size).sum(1))
        elif typ==mujoco.mjtGeom.mjGEOM_BOX:extent=abs(r)@size
        else:raise ValueError('unexpected human geometry type '+str(typ))
        bounds.extend([p-extent,p+extent])
    b=np.array(bounds);positions={n:d.xpos[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,n)].tolist() for n in ('Pelvis','Head','L_Shoulder','R_Shoulder','L_Wrist','R_Wrist')}
    return {'neutral_source_height_m':float(np.ptp(b,axis=0)[2]),'neutral_source_bounds_m':[b.min(0).tolist(),b.max(0).tolist()],'body_origin_positions_m':positions,'shoulder_body_origin_separation_m':float(np.linalg.norm(np.array(positions['L_Shoulder'])-positions['R_Shoulder'])),'read_only_zero_range_limit_relaxations':relaxed,'scope':'neutral source geometry at q0; not seated native height or measured human anthropometry'}
def hull_mesh(points,path):
    hull=ConvexHull(points);faces=hull.simplices.copy()
    for i,(face,equation) in enumerate(zip(faces,hull.equations)):
        a,b,c=points[face]
        if np.dot(np.cross(b-a,c-a),equation[:3])<0:faces[i]=face[[0,2,1]]
    mesh=trimesh.Trimesh(points,faces,process=True);assert mesh.is_volume and mesh.is_watertight and mesh.volume>0
    with path.open('x') as f:f.write(mesh.export(file_type='obj'))
    return {'path':str(path),'sha256':sha(path),'bounds_m':mesh.bounds.tolist(),'volume_m3':float(mesh.volume),'convex':bool(mesh.is_convex),'watertight':bool(mesh.is_watertight),'vertex_count':len(mesh.vertices),'face_count':len(mesh.faces)}
def main():
    OUT.mkdir(parents=True,exist_ok=False);RESULT.mkdir(parents=True,exist_ok=True);tree=ET.parse(SOURCE);root=tree.getroot();old=ET.parse(SOURCE).getroot();inputs={str(SOURCE):sha(SOURCE),str(HUMAN):sha(HUMAN),str(Path(__file__)):sha(__file__)}
    for p in (ROOT/'tab2body/assets/mesh').glob('*'):
        if p.is_file():inputs[str(p)]=sha(p)
    measurements=human_measurement();bodies={b.get('name'):b for b in root.findall('./worldbody//body')};markers={s:{n:np.fromstring(bodies['G:string'+str(s)+n].get('pos'),sep=' ') for n in ('','_end')} for s in range(1,7)}
    lengths=np.array([np.linalg.norm(v['']-v['_end']) for v in markers.values()]);scale=float(lengths.mean()/.634);length=.497*scale;width=.380*scale;depth=np.array([.09,.11])*scale;front_G=-.0017;front_body=.02;body_y=-.4
    profile=np.vstack([UPPER,LOWER[1:]]);profile[:,1]*=width/(2*.188);mesh_info=[]
    for label,base in (('upper',UPPER),('lower',LOWER)):
        t=base[:,0];halfwidth=base[:,1]*width/(2*.188);y=length/2-t*length;back=front_body-(depth[0]+(depth[1]-depth[0])*t);points=np.array([[sign*w,yy,z] for w,yy,zz in zip(halfwidth,y,back) for sign in (-1,1) for z in (front_body,zz)])
        mesh_info.append(hull_mesh(points,OUT/(label+'.obj')))
    root.find('compiler').set('meshdir','.')
    for mesh in root.findall('./asset/mesh'):mesh.set('file',os.path.relpath(SOURCE.parent/'mesh'/mesh.get('file'),OUT))
    for label in ('upper','lower'):ET.SubElement(root.find('asset'),'mesh',name='concert_'+label,file=label+'.obj')
    body=bodies['G:body'];body.remove(body.find('geom'))
    for label in ('upper','lower'):ET.SubElement(body,'geom',type='mesh',mesh='concert_'+label,density='1000',rgba='.65 .38 .17 1')
    # Continue the existing short headstock to the scaled total-length reference.
    tail=body_y-length/2;tip=tail+1.021*scale;start=.254;hw=.041*scale;z0,z1=-.02,-.003
    head=np.array([[sign*w,y,z] for y,w in ((start,hw),(tip,hw*.85)) for sign in (-1,1) for z in (z0,z1)]);mesh_info.append(hull_mesh(head,OUT/'headstock.obj'));ET.SubElement(root.find('asset'),'mesh',name='concert_headstock',file='headstock.obj');ET.SubElement(bodies['guitar'],'geom',type='mesh',mesh='concert_headstock',density='1000',rgba='.35 .21 .1 1')
    asset=OUT/'guitar_asset.xml';tree.write(asset,encoding='unicode');new=ET.parse(asset).getroot();new_bodies={b.get('name'):b for b in new.findall('./worldbody//body')};old_bodies={b.get('name'):b for b in old.findall('./worldbody//body')}
    t=float((body_y+length/2-(-.2243))/length);w=float(np.interp(t,profile[:,0],profile[:,1]));first=[-w-.002,-.2243,front_G-float(depth[0]+(depth[1]-depth[0])*t)/2];second=[0,tail-.002,front_G-depth[1]/2]
    checks={'body_names_order_unchanged':list(new_bodies)==list(old_bodies),'all_body_frames_unchanged':all(b.attrib==new_bodies[n].attrib for n,b in old_bodies.items()),'music_markers_and_nonbody_geoms_unchanged':all([ET.tostring(g) for g in b.findall('geom')]==[ET.tostring(g) for g in new_bodies[n].findall('geom')] for n,b in old_bodies.items() if n not in ('guitar','G:body')),'original_neck_and_string_geoms_unchanged':all(ET.tostring(a)==ET.tostring(b) for a,b in zip(old_bodies['guitar'].findall('geom'),new_bodies['guitar'].findall('geom'))),'two_convex_bouts_keep_waist':len(body.findall('geom'))==2 and all(v['convex'] for v in mesh_info),'positive_watertight_meshes':all(v['watertight'] and v['volume_m3']>0 for v in mesh_info),'scaled_total_length_matches_reference':abs((tip-tail)-1.021*scale)<1e-12,'inputs_preserved':all(sha(p)==h for p,h in inputs.items())};assert all(checks.values()),checks
    result={'checks':checks,'input_sha256':inputs,'humanoid':measurements,'reference':{'model':'Yamaha FS800 concert acoustic','url':'https://shop.sg.yamaha.com/fs800.html','length_m':.497,'width_m':.380,'depth_range_m':[.09,.11],'scale_m':.634,'total_length_m':1.021,'outline':'designed two-convex-bout approximation; not exact product scan'},'existing_string_marker_lengths_m':lengths.tolist(),'dimension_scale_ratio':scale,'new_body_length_m':length,'new_body_max_width_m':width,'new_body_depth_range_m':depth.tolist(),'old_body_dimensions_m':[.34,.30,.04],'total_length_m':tip-tail,'body_length_to_humanoid_neutral_height_ratio':length/measurements['neutral_source_height_m'],'body_front_plane_G_z_m':front_G,'legacy_body_reference_G_m':[0,-.4,-.0217],'body_envelope_center_G_m':[0,-.4,front_G-depth.mean()/2],'half_width_profile_t_m':profile.tolist(),'strap_buttons_G_m':[first,second],'mass_rule':'preserve per-body native reference masses; use new imported COM and imported inertia scaled to those masses before initialization','asset':str(asset),'asset_sha256':sha(asset),'meshes':mesh_info,'scope':'source geometry and coordinate ABI; native mass/cooking/clearance/music performance pending'}
    save(OUT/'manifest.json',result);save(RESULT/'geometry_build_v1.json',result);print(json.dumps({k:v for k,v in result.items() if k in ('checks','humanoid','new_body_length_m','new_body_max_width_m','new_body_depth_range_m','total_length_m')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
