"""Face-used source neck hulls; does not assert correspondence to PhysX cooking."""
from .environment import np
from .initial_overlap import mujoco
from .plot_neck_palm import geometry


def face_geometry(model,data,shape):
    if shape['actor']!='guitar' or shape['body']!='guitar':
        return geometry(model,data,shape)
    import trimesh
    geom=shape['geom_id']
    if model.geom_type[geom]!=mujoco.mjtGeom.mjGEOM_MESH:
        raise ValueError('neck source shape must be a mesh')
    mesh_id=model.geom_dataid[geom]
    start,count=model.mesh_vertadr[mesh_id],model.mesh_vertnum[mesh_id]
    first,number=model.mesh_faceadr[mesh_id],model.mesh_facenum[mesh_id]
    indices=np.unique(model.mesh_face[first:first+number])
    if len(indices)<4 or indices.min()<0 or indices.max()>=count:
        raise ValueError('source faces must index this mesh vertex block')
    mesh=trimesh.convex.convex_hull(model.mesh_vert[start+indices])
    transform=np.eye(4)
    transform[:3,:3],transform[:3,3]=data.geom_xmat[geom].reshape(3,3),data.geom_xpos[geom]
    mesh.apply_transform(transform)
    return mesh
