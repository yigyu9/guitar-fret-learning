"""CPU source-mesh convex envelope audit, not native cooked-hull readback."""
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from guitar_learning.gpu.fingertip_pad import load_fingertip_pad
from guitar_learning.gpu.thumb_support import load_thumb_support


def main():
    base=Path(__file__).resolve().parents[1]
    patch=load_fingertip_pad();thumb=load_thumb_support();rows=[]
    sources=[(source,patch['points_local'][i],patch['normals_local'][i])
             for i,source in enumerate(patch['contract']['fingers_diagnostics'])]
    sources.append((thumb['contract']['patch_diagnostics'],thumb['points_local'],thumb['normals_local']))
    layout=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attribute','<u2')])
    for source,points,normals in sources:
        path=Path(source['mesh']);payload=path.read_bytes();count=struct.unpack_from('<I',payload,80)[0]
        vertices=np.frombuffer(payload,dtype=layout,count=count,offset=84)['vertices'].reshape(-1,3).astype(float)
        vertices*=np.asarray(source['mesh_scale'])
        quat=source['geom_quaternion_wxyz']
        vertices=Rotation.from_quat(quat[1:]+quat[:1]).apply(vertices)+np.asarray(source['geom_position_m'])
        hull=ConvexHull(vertices);planes=hull.equations
        signed=points@planes[:,:3].T+planes[:,3]
        inner=np.maximum(-signed.max(1),0)
        denominators=normals@planes[:,:3].T
        exit_distance=np.maximum(np.where(denominators>1e-12,-signed/np.maximum(denominators,1e-12),np.inf).min(1),0)
        rows.append(dict(body=source['body'],mesh=str(path),mesh_sha256=hashlib.sha256(payload).hexdigest(),
            samples=len(points),convex_envelope_vertices=len(hull.vertices),
            inward_shortest_plane_distance_mm=dict(minimum=float(inner.min()*1000),median=float(np.median(inner)*1000),maximum=float(inner.max()*1000)),
            source_normal_exit_distance_mm=dict(minimum=float(exit_distance.min()*1000),median=float(np.median(exit_distance)*1000),maximum=float(exit_distance.max()*1000)),
            samples_inward_gt_0_1mm=int((inner>.0001).sum()),samples_inward_gt_1mm=int((inner>.001).sum())))
    report=dict(schema='guitar_learning.source_convex_envelope_pad_audit.v1',rows=rows,
        limitation='CPU convex hull of transformed original STL vertices only; not PhysX cooked mesh, inflation, margin, contact witness or force readback',
        source_sha256=dict(patch['contract']['source_sha256'],**thumb['contract']['source_sha256']))
    (base/'source_hull_audit_with_thumb.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
