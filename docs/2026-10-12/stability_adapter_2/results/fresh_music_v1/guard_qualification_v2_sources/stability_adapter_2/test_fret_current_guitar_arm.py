"""FK agreement and executable target optimization on preserved native states."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from .fret_current_guitar_arm import CurrentGuitarArm
from .underneck_initial_search import pose, BASE, read, ROOT


def main():
    base=ROOT/'docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data'
    initial=read(base/'initial_values.json'); handoff=read(base/'handoff_values.json')
    env=SimpleNamespace(names=initial['joint_names'],human_bodies=read(BASE)['human_body_names'],
        lower=np.array(initial['native_lower_rad']),upper=np.array(initial['native_upper_rad']),
        initial_q=np.array(initial['initial_angles_rad']))
    previous=np.array(handoff['prepared_left_targets_rad'])
    controller=CurrentGuitarArm(env,handoff['native_state'],previous)
    checks={}; rows=[]
    # Native saved states check that the calibrated expmap model remains accurate.
    for tm in (2,4,8):
        row=min(read(base/'trace.json'),key=lambda r:abs(r['time_s']-tm)); state=row['native_state']
        gp,gr=pose(state['guitar_body_states'][0]); wp,wr=pose(state['human_body_states'][controller.wrist_index])
        goal=gr.inv().apply(wp-gp)+np.array([.01,0,0])
        target,d=controller.solve(state,goal,previous,1/60)
        checks['native_fk_'+str(tm)]=d['fk_position_error_m']<.002 and d['fk_rotation_error_rad']<.01
        checks['rate_'+str(tm)]=bool(np.max(abs(target-previous))<=.8/60+1e-9)
        checks['envelope_'+str(tm)]=bool(np.all(target>=controller.low) and np.all(target<=controller.high))
        rows.append(dict(time_s=tm,**d))
    # A coherent FK state at the submitted target isolates direction from PD lag.
    state=copy.deepcopy(handoff['native_state'])
    q=np.array([r['pos'] for r in state['human_dof_states']]); q[controller.indices]=previous
    poses=controller.fk(q)
    for n,body in zip(env.human_bodies,state['human_body_states']):
        p,r=poses[n]; body['pose']={'p':dict(zip('xyz',p.tolist())),'r':dict(zip('xyzw',r.as_quat().tolist()))}
    for v,body in zip(q,state['human_dof_states']):body['pos']=float(v)
    gp,gr=pose(state['guitar_body_states'][0]); wp,wr=pose(state['human_body_states'][controller.wrist_index])
    c=CurrentGuitarArm(env,state,previous)
    before=copy.deepcopy(state)
    target,d=c.solve(state,gr.inv().apply(wp-gp)+np.array([.01,0,0]),previous,1/60)
    checks['coherent_10mm_position_reduced']=d['predicted_error_m']<d['wrist_error_m']
    checks['state_readonly']=state==before
    assert all(checks.values()), checks
    print(json.dumps(dict(checks=checks,rows=rows,coherent=d),indent=2))


if __name__=='__main__':main()
