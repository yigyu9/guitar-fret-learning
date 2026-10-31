"""Finite neck faces and selected source hand facets; not cooked contact points."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read, pose

ROOT = Path(__file__).resolve().parents[1]
FACETS = ROOT/'docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/search.json'


def left_indices(names):
    result = np.array([i for i, n in enumerate(names)
                       if n.startswith(('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist', 'LH:'))])
    assert len(result) == 33
    return result


def width(y):
    return .027908-.01631590413943356*(y+.241803)


def face_measurements(poses, gp, gr, station, front_z, facets):
    rows = {}
    offsets = {'LH:index3': .024, 'LH:middle3': .008,
               'LH:ring3': -.008, 'LH:pinky3': -.024}
    for name, facet in facets.items():
        p, r = poses[name]
        point = gr.inv().apply(p+r.apply(facet['point_local_m'])-gp)
        direction = gr.inv().apply(r.apply(facet['normal_local']))
        palm, thumb = name == 'LH:palm', name == 'LH:thumb3'
        y = float(np.clip(point[1], station-.04, station+.04)) if palm or thumb else station+offsets[name]
        w = width(y)
        normal = np.array([1., .01631590413943356, 0.]) if palm else np.array([0., 0., -1. if thumb else 1.])
        normal /= np.linalg.norm(normal)
        surface = (np.array([w, y, .00065]) if palm else
                   np.array([np.clip(point[0], -w+.002, w-.002), y, -.008 if thumb else front_z]))
        gap = .005 if palm or thumb else .008
        target = surface+gap*normal
        rows[name] = {'face': 'underside' if palm else 'back' if thumb else 'strings_front',
                      'point_G_m': point.tolist(), 'surface_G_m': surface.tolist(),
                      'target_G_m': target.tolist(), 'outward_normal_G': normal.tolist(),
                      'facet_normal_G': direction.tolist(), 'target_gap_m': gap,
                      'facet_signed_plane_gap_m': float((point-surface)@normal),
                      'point_target_error_m': float(np.linalg.norm(point-target)),
                      'alignment_dot': float(direction@-normal),
                      'facet_scope': 'selected active collision facet; anatomical pad identity unverified'}
    rows['LH:palm']['normal_up_W'] = float(poses['LH:palm'][1].apply(facets['LH:palm']['normal_local'])[2])
    return rows


def native_faces(env, state, candidate):
    poses = {n: pose(s) for n, s in zip(env.human_bodies, state['human_body_states'])}
    gp, gr = pose(state['guitar_body_states'][0])
    return face_measurements(poses, gp, gr, candidate['left_neck_near']['station_G_m'],
                             candidate['left_neck_near']['front_z_G_m'], read(FACETS)['facets'])
