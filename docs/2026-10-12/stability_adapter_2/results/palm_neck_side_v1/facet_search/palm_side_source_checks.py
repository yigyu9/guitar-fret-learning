"""Conservative source-only intersections with face-used neck hulls."""
from .face_referenced_geometry import face_geometry
from .thigh_palm_support import intersection


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
