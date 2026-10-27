"""Palm facet point and bounded target-space feedback for the blue neck side."""
from pathlib import Path
from .audit_palm_side_target import PHASE as SOURCE_PHASE
from .search_palm_neck_side import REFERENCE
from .finger_grip_probe import SUPPORT_PHASE
from .environment import ROOT,np,quaternion,vector
from .build_fixed_lower_asset import read,pose
from scipy.spatial.transform import Rotation

PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1'
SETTINGS=ROOT/'stability_adapter_2/trials/palm_neck_side_v1/facet_distal/facet_50um_twist_0mrad_distal_40.json'


def context():
    search=read(SOURCE_PHASE/'facet_distal_search/search.json')
    seed=read(SOURCE_PHASE/'facet_native_short/probe.json')['states'][0]
    audit=read(SOURCE_PHASE/'initial_audit_v2/audit.json')
    reference=read(REFERENCE/'report.json')
    q0=np.array([d['pos'] for d in seed['human_dof_states']])
    indices=np.array(reference['arm_indices'][:12])
    low=np.maximum(reference['diagnostic_lower_rad'][:12],q0[indices]-.15)
    high=np.minimum(reference['diagnostic_upper_rad'][:12],q0[indices]+.15)
    pp,pq=pose(seed['human_body_states'][reference['human_body_names'].index('LH:palm')])
    gp,gq=pose(seed['guitar_body_states'][0]);gr=Rotation.from_quat(gq)
    return {'seed':seed,'reference':reference,'q0':q0,'indices':indices,'lower':low,'upper':high,
        'local_point':np.array(search['palmar_facet_point_local_m']),
        'goal_point_G':gr.inv().apply(np.array(audit['target_center_W_m'])+np.array(audit['target_outward_normal_W'])*.00005-gp),
        'relative_rotation':gr.inv()*Rotation.from_quat(pq),
        'shift':read(SUPPORT_PHASE/'search_near_touch.json')['guitar_initial_translation_m']}


def observation(env,ctx):
    body=env.bodies(env.human)[env.human_bodies.index('LH:palm')]['pose']
    rotation=Rotation.from_quat(quaternion(body['r']))
    return vector(body['p'])+rotation.apply(ctx['local_point']),rotation


def task_error(env,ctx):
    point,rotation=observation(env,ctx)
    guitar=env.bodies(env.guitar)[0]['pose']
    gr=Rotation.from_quat(quaternion(guitar['r']))
    desired=vector(guitar['p'])+gr.apply(ctx['goal_point_G'])
    orientation=gr*ctx['relative_rotation']
    return np.r_[desired-point,.08*(orientation*rotation.inv()).as_rotvec()]


def input_paths():
    return [Path(__file__).resolve(),SETTINGS,REFERENCE/'report.json',SUPPORT_PHASE/'search_near_touch.json',
        SOURCE_PHASE/'facet_distal_search/search.json',SOURCE_PHASE/'facet_native_short/probe.json',
        SOURCE_PHASE/'initial_audit_v2/audit.json',SOURCE_PHASE/'artifact_inventory.json']
