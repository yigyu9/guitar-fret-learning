"""Necessary radial reach bounds at actual saved proximal poses, not a success certificate."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha,pose
from .elbow_wrist_strike_source_v1 import A,B,P,INITIAL,string_segments


def main():
    paths=[Path(__file__).resolve(),A/'ELBOW_WRIST_STRIKE_PLAN_V2.md',INITIAL,B/'native_upper50_v13_static/media/physics_endpoint_contacts.json',A/'elbow_wrist_strike_source_v1.py',A/'initial_pose_noise_v1.py',A/'upper_arm_static_geometry_v1.py']
    inputs={str(f):sha(f) for f in paths};save(P/'radial_bound_before_v1.json',inputs)
    b=read(INITIAL);state=b['native_initial_state'];hp=dict(zip(b['human_body_names'],state['human_body_states']));gp,gr=pose(state['guitar_body_states'][0])
    elbow=pose(hp['R_Elbow'])[0];wrist=pose(hp['R_Wrist'])[0];pick=pose(hp['RH:pick'])[0]
    forearm=float(np.linalg.norm(wrist-elbow));wrist_pick=float(np.linalg.norm(pick-wrist));maximum=forearm+wrist_pick
    start,end=string_segments(b);endpoint=read(paths[3])['rows'];rows=[]
    for step in (0,480,1200):
        if step:
            row=endpoint[step-1];gp,gr=pose(row['guitar_body_states']['guitar']);elbow=pose(row['human_body_states']['R_Elbow'])[0]
        for lane in np.linspace(-.385,-.255,27):
            u=(lane-start[:,1])/(end[:,1]-start[:,1]);points=start+u[:,None]*(end-start);points[:,2]-=.004
            distances=np.linalg.norm(gp+gr.apply(points)-elbow,axis=1)
            rows.append({'physics_step':step,'time_s':step/240,'lane_G_y_m':float(lane),'distance_elbow_to_each_string_m':distances.tolist(),'unavoidable_position_error_lower_bound_each_string_m':np.maximum(distances-maximum,0).tolist(),'all_six_inside_radial_bound':bool(np.all(distances<=maximum))})
    assert all(sha(f)==h for f,h in inputs.items());save(P/'radial_bound_v1.json',{'passed':True,'input_sha256':inputs,'forearm_length_m':forearm,'held_finger_wrist_to_pick_length_m':wrist_pick,'maximum_fixed_elbow_pick_radius_m':maximum,'rows':rows,'scope':'triangle inequality gives a necessary position bound only; inside sphere does not certify limits/orientation/collision/strike; t=2/5 actual proximal/guitar poses from static reference; wrist-pick length holds the reference finger posture, actual finger compliance not bounded here'})
    for row in rows:
        if abs(row['lane_G_y_m']+.325)<1e-8:print('time',row['time_s'],'central lane lowerbound mm',[round(x*1000,2) for x in row['unavoidable_position_error_lower_bound_each_string_m']])


if __name__=='__main__':main()
