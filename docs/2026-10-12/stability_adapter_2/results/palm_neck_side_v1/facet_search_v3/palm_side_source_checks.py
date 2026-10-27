"""Conservative source-only intersections with face-used neck hulls."""
from .face_referenced_geometry import face_geometry
from .environment import np
from scipy.spatial import ConvexHull
from scipy.optimize import linprog


def intersection(a,b):
    if np.any(np.minimum(a.bounds[1],b.bounds[1])-np.maximum(a.bounds[0],b.bounds[0])<=1e-7):
        return 0.
    center=(np.maximum(a.bounds[0],b.bounds[0])+np.minimum(a.bounds[1],b.bounds[1]))/2
    # Millimetres around the overlap box keep near-contact LP tolerances meaningful.
    planes=np.vstack([ConvexHull((mesh.vertices-center)*1000).equations for mesh in (a,b)])
    # Triangulated coplanar faces otherwise give HiGHS many duplicate constraints.
    _,unique=np.unique(np.round(planes,10),axis=0,return_index=True)
    planes=planes[unique]
    matrix=np.column_stack((planes[:,:3],np.ones(len(planes))))
    result=linprog([0,0,0,-1],A_ub=matrix,b_ub=-planes[:,3],bounds=[(None,None)]*3+[(0,None)],method='highs')
    if result.status==2:return 0.
    if not result.success or np.maximum(matrix@result.x+planes[:,3],0).max()>1e-4:
        raise RuntimeError('centered mm source intersection solve failed: '+result.message)
    return float(result.x[3]/1000)


def source_checks(probe):
    model,data,shapes=probe
    meshes={s['geom_id']:face_geometry(model,data,s) for s in shapes}
    overlaps=[];crosshands=[]
    for a in [s for s in shapes if s['actor']=='human']:
        for b in [s for s in shapes if s['actor']=='guitar']:
            radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
            if radius>1e-7:overlaps.append({'human':a['body'],'guitar':b['body'],'common_radius_m':radius})
    for a in [s for s in shapes if s['body'].startswith('LH:') or s['body']=='L_Wrist']:
        for b in [s for s in shapes if s['body'].startswith('RH:') or s['body']=='R_Wrist']:
            radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
            if radius>1e-7:crosshands.append({'left':a['body'],'right':b['body'],'common_radius_m':radius})
    return meshes,overlaps,crosshands
