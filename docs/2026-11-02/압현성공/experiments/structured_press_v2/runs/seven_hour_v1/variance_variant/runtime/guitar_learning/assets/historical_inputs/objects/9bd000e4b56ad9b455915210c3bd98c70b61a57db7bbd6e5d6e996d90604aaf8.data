"""Current-guitar finite-face placement; near faces without imposed attachment."""
import numpy as np
from .left_neck_near_geometry_v1 import face_measurements, width

OFFSETS={'LH:index3':.030,'LH:middle3':.010,'LH:ring3':-.010,'LH:pinky3':-.030}


def measurements(poses,gp,gr,station,front_z,facets):
    rows=face_measurements(poses,gp,gr,station,front_z,facets)
    for name,m in rows.items():
        point=np.array(m['point_G_m']);surface=np.array(m['surface_G_m'])
        if name in OFFSETS:
            surface[1]=station+OFFSETS[name];w=width(surface[1])
            surface[0]=np.clip(point[0],-w+.002,w-.002)
        gap=.010 if name=='LH:palm' else .008
        m['surface_G_m']=surface.tolist();m['target_gap_m']=gap
        m['target_G_m']=(surface+gap*np.array(m['outward_normal_G'])).tolist()
        m['point_target_error_m']=float(np.linalg.norm(point-m['target_G_m']))
        m['facet_signed_plane_gap_m']=float((point-surface)@np.array(m['outward_normal_G']))
    return rows


def placement_pass(rows):
    return bool(all(m['point_target_error_m']<.012 and .002<m['facet_signed_plane_gap_m']<.016 and m['alignment_dot']>.3
                    for m in rows.values()) and rows['LH:palm']['normal_up_W']>0)
