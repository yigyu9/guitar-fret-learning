"""Build a grey OM outer envelope and bounded convex collision pieces."""
from pathlib import Path
import hashlib,json,os,xml.etree.ElementTree as ET
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.spatial import ConvexHull
import trimesh

R=Path(__file__).resolve().parents[1]
BASE=R/'stability_adapter_2/assets/realistic_guitar_v1'
SOURCE=R/'docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1/outline_v2.json'
P=R/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1'
OUT=R/'stability_adapter_2/assets/om_body_geometry_v3'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    outline=json.loads(SOURCE.read_text());depth=json.loads((P/'depth_v1.json').read_text())
    inputs={str(f):sha(f) for f in [SOURCE,P/'depth_v1.json',Path(__file__).resolve(),R/'stability_adapter_2/OM_BODY_GEOMETRY_PLAN_V1.md',BASE/'guitar_asset.xml',BASE/'manifest.json']}
    inputs.update(depth['input_sha256'])
    xy=np.array(outline['outline_body_xy_m']);length=outline['body_length_m'];width=outline['body_width_m']
    levels=np.unique(xy[:,1]);widths=np.array([abs(xy[np.isclose(xy[:,1],y,atol=1e-12,rtol=0),0]).max() for y in levels])
    half=PchipInterpolator(levels,widths);y0,y1=float(levels[0]),float(levels[-1])
    f,b=depth['arcs']['front'],depth['arcs']['back']
    fc,bc=np.array(f['center_DXF_mm'][:2])/1000,np.array(b['center_DXF_mm'][:2])/1000
    rf,rb=f['radius_mm']/1000,b['radius_mm']/1000
    sx0,sx1=np.array(depth['side_axis_interval_mm'])/1000
    front_anchor=.02-(fc[1]+rf)
    def surfaces(x,y):
        sx=sx0+(sx1-sx0)*(y-y0)/(y1-y0)
        front=front_anchor+fc[1]+np.sqrt(rf*rf-(sx-fc[0])**2-x*x)
        back=front_anchor+bc[1]-np.sqrt(rb*rb-(sx-bc[0])**2-x*x)
        return front,back
    def cloud(ys,fractions):
        xs=np.array([half(y)*fractions for y in ys]);yy=np.broadcast_to(np.array(ys)[:,None],xs.shape)
        front,back=surfaces(xs,yy)
        return np.r_[np.c_[xs.ravel(),yy.ravel(),front.ravel()],np.c_[xs.ravel(),yy.ravel(),back.ravel()]]
    ys=np.unique(np.r_[np.linspace(y0,y1,247),levels]);fractions=np.linspace(-1,1,21)
    vertices=cloud(ys,fractions);n,m=len(ys),len(fractions);offset=n*m;faces=[]
    for i in range(n-1):
        for j in range(m-1):
            a=i*m+j;c=(i+1)*m+j
            faces.extend([[a,a+1,c+1],[a,c+1,c],[a+offset,c+1+offset,a+1+offset],[a+offset,c+offset,c+1+offset]])
        for j,side in [(0,'left'),(m-1,'right')]:
            a=i*m+j;c=(i+1)*m+j
            faces.extend([[a,c,c+offset],[a,c+offset,a+offset]] if side=='left' else [[a,a+offset,c+offset],[a,c+offset,c]])
    for i in [0,n-1]:
        for j in range(m-1):
            a=i*m+j
            tris=[[a,a+offset,a+1+offset],[a,a+1+offset,a+1]]
            faces.extend(tris if i==0 else [t[::-1] for t in tris])
    visual=trimesh.Trimesh(vertices,faces,process=True)
    visual.update_faces(visual.nondegenerate_faces());visual.update_faces(visual.unique_faces());visual.remove_unreferenced_vertices();trimesh.repair.fix_normals(visual)
    assert visual.is_watertight and visual.is_volume and visual.volume>0
    visual_path=OUT/'body_visual.obj';visual_path.write_text(visual.export(file_type='obj'))
    meshes=[];errors=[]
    def piece(a,b):
        points=cloud(np.linspace(a,b,9),np.linspace(-1,1,9));h=ConvexHull(points[:len(points)//2,:2])
        test_y=np.linspace(a,b,101);eq=h.equations;positive=eq[:,0]>1e-12
        envelope=np.min((-eq[positive,1,None]*test_y[None,:]-eq[positive,2,None])/eq[positive,0,None],axis=0)
        outside=float(np.maximum(envelope-half(test_y),0).max())
        inside=float(np.maximum(half(test_y)-envelope,0).max())
        if max(outside,inside)>.0005 and b-a>.001:
            mid=(a+b)/2;piece(a,mid);piece(mid,b);return
        hull=ConvexHull(points);tris=hull.simplices.copy()
        for i,(face,equation) in enumerate(zip(tris,hull.equations)):
            p,q,r=points[face]
            if np.dot(np.cross(q-p,r-p),equation[:3])<0:tris[i]=face[[0,2,1]]
        mesh=trimesh.Trimesh(points,tris,process=True);assert mesh.is_volume and mesh.is_watertight and mesh.is_convex
        file=OUT/f'body_collision_{len(meshes):02d}.obj';file.write_text(mesh.export(file_type='obj'))
        meshes.append({'path':str(file),'sha256':sha(file),'vertex_count':len(mesh.vertices),'volume_m3':float(mesh.volume),'bounds_m':mesh.bounds.tolist()})
        errors.append({'body_y_interval_m':[a,b],'XY_outside_error_m':outside,'XY_inside_error_m':inside,'test_points':101})
    for a,b in zip(np.linspace(y0,y1,25)[:-1],np.linspace(y0,y1,25)[1:]):piece(float(a),float(b))
    tree=ET.parse(BASE/'guitar_asset.xml');root=tree.getroot();old=ET.parse(BASE/'guitar_asset.xml').getroot();asset=root.find('asset')
    for mesh in asset.findall('mesh'):
        path=(BASE/mesh.get('file')).resolve();inputs[str(path)]=sha(path);mesh.set('file',os.path.relpath(path,OUT))
    root.find('default').find('./default/geom').set('rgba','.65 .65 .65 1')
    bodies={body.get('name'):body for body in root.findall('./worldbody//body')};body=bodies['G:body']
    for geom in list(body.findall('geom')):body.remove(geom)
    for i,entry in enumerate(meshes):
        name=f'om_collision_{i:02d}';ET.SubElement(asset,'mesh',name=name,file=Path(entry['path']).name)
        ET.SubElement(body,'geom',type='mesh',mesh=name,density='1000',rgba='0 0 0 0')
    ET.SubElement(asset,'mesh',name='om_visual_body',file=visual_path.name)
    ET.SubElement(body,'geom',type='mesh',mesh='om_visual_body',contype='0',conaffinity='0',density='0',group='1',rgba='.65 .65 .65 1')
    for node in root.findall('./worldbody//body'):
        if node is body:continue
        for geom in node.findall('geom'):
            if geom.get('rgba')!='0 0 0 0':geom.set('rgba','.65 .65 .65 1')
    for original in list(bodies['guitar'].findall('geom')):
        if original.get('type')=='mesh':
            ET.SubElement(bodies['guitar'],'geom',type='mesh',mesh=original.get('mesh'),contype='0',conaffinity='0',density='0',group='1',rgba='.65 .65 .65 1')
    xml=OUT/'guitar_asset.xml';tree.write(xml,encoding='unicode')
    clean=lambda g:{k:v for k,v in g.attrib.items() if k!='rgba'}
    checks={'body_frames_order_exact':[e.attrib for e in old.findall('./worldbody//body')]==[e.attrib for e in root.findall('./worldbody//body')],
        'all_nonbody_physics_exact':all([clean(g) for g in e.findall('geom')]==[clean(g) for g in bodies[e.get('name')].findall('geom')[:len(e.findall('geom'))]] for e in old.findall('./worldbody//body') if e.get('name')!='G:body'),
        'added_neck_visual_geoms_nonphysical':all(g.get('contype')==g.get('conaffinity')=='0' and g.get('density')=='0' for g in bodies['guitar'].findall('geom')[len(old.find('./worldbody/body').findall('geom')):]),
        'visual_closed_positive':bool(visual.is_volume and visual.is_watertight),
        'collision_XY_errors_below_0_5mm':all(max(e['XY_outside_error_m'],e['XY_inside_error_m'])<=.0005 for e in errors),
        'collision_hulls_under_256_vertices':all(e['vertex_count']<=256 for e in meshes),
        'source_inputs_unchanged':all(sha(path)==value for path,value in inputs.items())}
    assert all(checks.values()),checks
    base=json.loads((BASE/'manifest.json').read_text());profile_t=np.linspace(0,1,401);profile=np.c_[profile_t,half(y1-profile_t*length)]
    tail=-.4-length/2;front,back=surfaces(-float(half(-.2243+.4)), -.2243+.4)
    buttons=[[-float(half(-.2243+.4))-.002,-.2243,float((front+back)/2-.0217)],[0,tail-.002,float(sum(surfaces(0,y0))/2-.0217)]]
    attribution=OUT/'ATTRIBUTION.md'
    attribution.write_text('''# OM 바디 메시 출처와 이용 조건

원본: Acoustic guitar — Orchestra Model (OM), version1.1, Christophe Grellier, 2007/2008.
출처: https://www.grellier.fr/fr/telechargements
원본DXF: https://www.grellier.fr/static/data/plans/OM_acoustic_guitar/OM_acoustic_guitar.dxf
원본표기: 페이지CC BY-NC-SA2.0 France; DXF언어별표제2.0 France/3.0 Unported 링크보존.
원본라이선스: https://creativecommons.org/licenses/by-nc-sa/2.0/fr/ 및 https://creativecommons.org/licenses/by-nc-sa/3.0/
이바디파생메시의기여분: CC BY-NC-SA3.0 Unported https://creativecommons.org/licenses/by-nc-sa/3.0/
변경: 도면바디rim추출, 외부측면곡률로무채색3D외곽생성, 측면/평면0.957431mm길이차이를정규화축으로정렬, 근사convex충돌mesh생성. 내부구조/목재재료/음향은생성하지않음.
BY-NC-SA표기는새 body_visual.obj/body_collision_*.obj의도면기반형상에대한것이다. 기존넥/프렛/현/코드/휴머노이드의라이선스를이문서로변경하지않는다. 원저작자의후원/승인을뜻하지않는다.
비상업연구범위로사용한다. 기업상용화/유료제품등다른용도는원저작자조건에맞게별도확인한다. 파생메시를공개할때출처/변경이력/라이선스표시를유지한다.
''')
    base.update(checks=checks,input_sha256=inputs,asset=str(xml),asset_sha256=sha(xml),
        new_body_length_m=length,new_body_max_width_m=width,new_body_depth_range_m=[.085,depth['maximum_centerline_depth_mm']/1000],
        half_width_profile_t_m=profile.tolist(),strap_buttons_G_m=buttons,
        meshes=meshes+[{'path':str(visual_path),'sha256':sha(visual_path)},{'path':str(attribution),'sha256':sha(attribution)}],
        visual_only=False,collision_piece_count=len(meshes),collision_XY_error_checks=errors,
        body_surface_rule=depth['surface_rule'],body_surface_geometry=depth,visual_bounds_body_m=visual.bounds.tolist(),
        mass_rule='preserve prior native per-body masses; use new imported COM and inertia scaled by old/imported mass',
        scope='OM exterior shape/depth reconstruction with documented spherical/axis alignment choices; no internal structure, measured wood mass or native clearance certification')
    base['reference']={'model':'Grellier OM exterior construction plan','url':'https://www.grellier.fr/fr/telechargements','source_outline':str(SOURCE),'source_depth':str(P/'depth_v1.json'),'author':'Christophe Grellier','adapter_license':'CC BY-NC-SA 3.0 Unported'}
    base.pop('dimension_scale_ratio',None);base.pop('body_front_plane_G_z_m',None)
    base['body_geometry_scale_rule']='plan XY 1:1; only side-profile normalized-axis alignment 491/491.957431'
    base['body_front_max_G_z_m']=float(visual.bounds[1,2]-.0217)
    base['body_envelope_center_G_m']=(visual.bounds.mean(0)+np.array([0,-.4,-.0217])).tolist()
    base['body_length_to_humanoid_neutral_height_ratio']=length/base['humanoid']['neutral_source_height_m']
    head=np.array([[float(x) for x in line.split()[1:4]] for line in (BASE/'headstock.obj').read_text().splitlines() if line.startswith('v ')])
    base['total_length_m']=float(head[:,1].max()-tail)
    (OUT/'manifest.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n');(P/'build_v3.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'checks':checks,'convex_pieces':len(meshes),'visual_bounds_m':visual.bounds.tolist(),'max_XY_error_m':max(max(e['XY_outside_error_m'],e['XY_inside_error_m']) for e in errors)}))


if __name__=='__main__':main()
