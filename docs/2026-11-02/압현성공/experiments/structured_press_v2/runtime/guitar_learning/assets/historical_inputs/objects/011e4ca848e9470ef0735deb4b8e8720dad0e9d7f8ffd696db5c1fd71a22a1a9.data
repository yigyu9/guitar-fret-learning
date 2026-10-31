"""Normal-only palm orientation task evaluated from measured native poses."""
import numpy as np
from scipy.spatial.transform import Rotation
from .palm_side_feedback import SOURCE_PHASE
from .build_fixed_lower_asset import read,pose


def prepare(ctx):
    facet=read(SOURCE_PHASE/'facet_distal_search/search.json')
    audit=read(SOURCE_PHASE/'initial_audit_v2/audit.json')
    _,q=pose(ctx['seed']['guitar_body_states'][0])
    ctx=dict(ctx)
    ctx['normal_H']=np.array(facet['palmar_facet_normal_local'])
    ctx['normal_G']=Rotation.from_quat(q).inv().apply(audit['target_outward_normal_W'])
    ctx['palm_index']=ctx['reference']['human_body_names'].index('LH:palm')
    return ctx


def normal_rotation(actual,desired):
    actual=np.asarray(actual)/np.linalg.norm(actual);desired=np.asarray(desired)/np.linalg.norm(desired)
    cross=np.cross(actual,desired);s=float(np.linalg.norm(cross));c=float(np.clip(actual@desired,-1,1))
    if s<1e-12:
        if c<0:raise ValueError('antipodal normal orientation has no unique shortest rotation')
        return cross
    return cross*(np.arctan2(s,c)/s)


def error_from_state(state,ctx):
    pp,pq=pose(state['human_body_states'][ctx['palm_index']]);gp,gq=pose(state['guitar_body_states'][0])
    pr,gr=Rotation.from_quat(pq),Rotation.from_quat(gq)
    point=pp+pr.apply(ctx['local_point']);desired=gp+gr.apply(ctx['goal_point_G'])
    orientation=normal_rotation(pr.apply(ctx['normal_H']),-gr.apply(ctx['normal_G']))
    return np.r_[desired-point,.08*orientation]
