"""Read-only diagnostic rear surfaces; the native collision asset is unchanged."""
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation


CONDITIONS=('current_all_vertices','face_only_playing_neck1')
BASE=Path(__file__).resolve().parents[1]
DIAG=BASE.parents[2]


def validate_freeze():
    path=BASE/'frozen_sources.json'
    pins=json.loads(path.read_text())['source_pins']
    if any(not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in pins.items()):
        raise ValueError('Prepared native comparison source seal changed')
    return dict(pins,**{str(path):hashlib.sha256(path.read_bytes()).hexdigest()})


def source_paths():
    audit=json.loads((BASE.parent/'geometry_summary.json').read_text())
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in audit['input_pins'].items()):
        raise ValueError('Reviewed source audit inputs changed')
    return [*map(Path,audit['input_pins']),*sorted((BASE/'support').glob('*.py')),BASE.parent/'README.md',BASE.parent/'geometry_summary.json',
        DIAG/'01_control/support/run_thumb_deeper.py',
        DIAG.parents[2]/'guitar_learning/tool/validation/thumb_contact_probe.py']


def load_surfaces():
    from guitar_learning.gpu.thumb_support import load_thumb_support
    from guitar_learning.gpu.rigid_guitar import _ASSET_DIR
    current=load_thumb_support()
    asset=_ASSET_DIR/'guitar_compound.xml';root=ET.parse(asset).getroot()
    mesh=next(x for x in root.findall('./asset/mesh') if x.get('name')=='guitar_neck1')
    geom=next(x for x in root.findall('./worldbody/body/geom') if x.get('mesh')=='guitar_neck1'
        and not(x.get('contype')=='0' and x.get('conaffinity')=='0'))
    path=(asset.parent/root.find('compiler').get('meshdir','.')/mesh.get('file')).resolve()
    rows=path.read_text().splitlines()
    vertices=np.array([[float(x) for x in row.split()[1:4]] for row in rows if row.startswith('v ')])
    faces=np.array([[int(x.split('/')[0])-1 for x in row.split()[1:]] for row in rows if row.startswith('f ')])
    vertices=vertices[np.unique(faces)]*np.fromstring(mesh.get('scale','1 1 1'),sep=' ')
    q=np.fromstring(geom.get('quat','1 0 0 0'),sep=' ')
    vertices=Rotation.from_quat(np.r_[q[1:],q[:1]]).apply(vertices)+np.fromstring(geom.get('pos','0 0 0'),sep=' ')
    hull=ConvexHull(vertices);rear=hull.equations[:,2]<-.5;planes=hull.equations[rear]
    if not np.allclose(planes,planes[0],atol=1e-10,rtol=0):raise ValueError('One physical playing-neck rear plane required')
    corners=np.unique(vertices[hull.simplices[rear]].reshape(-1,3),axis=0)
    levels=np.unique(corners[:,1])
    if len(corners)!=4 or len(levels)!=2:raise ValueError('Finite four-corner rear trapezoid required')
    low,high=corners[corners[:,1]==levels[0]],corners[corners[:,1]==levels[1]]
    ordered=np.stack((low[low[:,0].argmin()],low[low[:,0].argmax()],high[high[:,0].argmax()],high[high[:,0].argmin()]))
    face=copy.deepcopy(current);face.update(rear_vertices=ordered,plane=planes[0])
    face['contract'].update(schema='diagnostic.thumb_face_only_neck1.v1',
        diagnostic_only=True,physical_asset_unchanged=True,
        region='face-referenced physical playing-neck1 rear; central half width and centerGy+/-40mm clipped to actual neck1 bounds',
        rear_vertices_guitar_m=ordered.tolist(),rear_plane_guitar=planes[0].tolist(),
        predicate_scope='same thresholds/formula; changed diagnostic geometry, not original training performance')
    for p in source_paths():
        face['contract']['source_sha256'][str(p.resolve())]=hashlib.sha256(p.read_bytes()).hexdigest()
    return dict(zip(CONDITIONS,(current,face)))


def dual_geometry(original, surfaces, points, normals, valid, center_y, rear, plane, net_force_guitar=None):
    """Primary selection is untouched; evaluate both surfaces at that same point."""
    import torch
    primary=original(points,normals,valid,center_y,rear,plane,net_force_guitar=net_force_guitar)
    if len(points)!=1:raise ValueError('One predeclared diagnostic environment required')
    index=primary['sample_index'].clamp_min(0)[:,None,None].expand(-1,1,3)
    selected=points.gather(1,index)
    facing=normals.gather(1,index)
    point_valid=primary['valid'].reshape(1)
    for name,surface in surfaces.items():
        extra=original(selected,facing,point_valid,center_y,
            torch.as_tensor(surface['rear_vertices'],device=points.device,dtype=points.dtype),
            torch.as_tensor(surface['plane'],device=points.device,dtype=points.dtype),net_force_guitar=net_force_guitar)
        for key in ('signed_gap','region_excess','normal_cos','normal_load','contact_candidate','quality'):
            primary['comparison_'+name+'_'+key]=extra[key]
    return primary
