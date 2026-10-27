"""Saved-native numerical contract checks; no live simulator or contact claims."""
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace, ModuleType
import numpy as np
from scipy.spatial.transform import Rotation as R
from .underneck_initial_search import ROOT, BASE, read, pose


def main():
    data = ROOT/'docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/ON/data'
    initial = read(data/'initial_values.json'); state = initial['native_initial_state']; audit = read(data/'initial_audit.json')
    stub = ModuleType('stability_adapter_2.underneck_pose_trial_v5')
    stub.initial_audit = lambda *args:audit
    sys.modules[stub.__name__] = stub
    from .palm_thumb_support_v1 import PalmThumbSupport
    env = SimpleNamespace(names=initial['joint_names'],human_bodies=read(BASE)['human_body_names'],
        initial_q=np.array(initial['initial_angles_rad']),lower=np.array(initial['native_lower_rad']),
        upper=np.array(initial['native_upper_rad']),candidate={})
    ctl = PalmThumbSupport(env,state); before = copy.deepcopy(state)
    final,row = ctl.update(state,env.initial_q,env.initial_q,1/60)
    checks = dict(left17_partition=len(ctl.indices)==17,
        state_readonly=state==before,FK_saved_native=row['fk_position_error_m']<1e-8,
        first_rate_limit=bool(np.max(abs(final-env.initial_q[ctl.indices]))<=.3/60+1e-10),
        initial_bounds=bool(np.all((final>=ctl.lower)&(final<=ctl.upper))))
    changed = copy.deepcopy(state); gp,gr = pose(state['guitar_body_states'][0]); gp += [.01,0,0]
    changed['guitar_body_states'][0]['pose']['p'] = dict(zip('xyz',gp.tolist()))
    ctl2 = PalmThumbSupport(env,state); _,row2 = ctl2.update(changed,env.initial_q,env.initial_q,1/60)
    checks['current_G_target_translation'] = bool(np.allclose(np.array(row2['contact_point_targets_W_m'])-
        row['contact_point_targets_W_m'],[.01,0,0],atol=1e-12))
    # A common virtual world transform leaves the numerical support command invariant.
    rotated = copy.deepcopy(state); world = R.from_rotvec([.02,-.01,.03]); offset = np.array([.04,-.02,.01])
    for body in rotated['human_body_states']+rotated['guitar_body_states']:
        p,r = pose(body); body['pose'] = dict(p=dict(zip('xyz',(offset+world.apply(p)).tolist())),
            r=dict(zip('xyzw',(world*r).as_quat().tolist())))
    ctl3 = PalmThumbSupport(env,state); final3,row3 = ctl3.update(rotated,env.initial_q,env.initial_q,1/60)
    checks['world_frame_equivariance'] = bool(np.max(abs(final-final3))<1e-7 and row3['fk_position_error_m']<1e-8)
    broken = copy.deepcopy(state); broken['human_body_states'][env.human_bodies.index('LH:palm')]['pose']['p']['x'] += .01
    try: ctl.update(broken,env.initial_q,env.initial_q,1/60)
    except ValueError: checks['FK_mismatch_rejected'] = True
    else: checks['FK_mismatch_rejected'] = False
    previous = env.initial_q.copy()
    for _ in range(150):
        values,_ = ctl2.update(changed,env.initial_q,previous,1/60)
        assert np.max(abs(values-previous[ctl2.indices]))<=.3/60+1e-10
        previous[ctl2.indices] = values
    checks['long_target_envelope'] = bool(np.all(abs(previous[ctl2.indices]-ctl2.initial)<=ctl2.cap+1e-10))
    # Saturated total targets stop support integration instead of accumulating hidden motion.
    ctl4 = PalmThumbSupport(env,state); ctl4.upper = ctl4.initial.copy(); ctl4.lower = ctl4.initial.copy()
    values,row4 = ctl4.update(changed,env.initial_q,env.initial_q,1/60)
    checks['saturation_antiwindup'] = bool(np.array_equal(values,ctl4.initial) and np.array_equal(ctl4.delta,np.zeros(17)))
    assert all(checks.values()),checks
    print(json.dumps(dict(checks=checks,live_native_initializations=0,physics_steps=0),indent=2))


if __name__=='__main__':main()
