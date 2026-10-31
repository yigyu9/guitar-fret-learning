"""Minimize necessary radius over all detector-allowed depths, independently of a path."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha,pose
from .elbow_wrist_strike_source_v1 import A,B,P,INITIAL,string_segments,ROOT


def main():
    paths=[Path(__file__).resolve(),INITIAL,B/'native_upper50_v13_static/media/physics_endpoint_contacts.json',P/'radial_bound_v1.json',ROOT/'tab2body/strike_cfg.py']+list(A.glob('*.py'))
    inputs={str(f):sha(f) for f in paths};save(P/'depth_bound_before_v1.json',inputs)
    from tab2body.strike_cfg import STRIKE
    b=read(INITIAL);state=b['native_initial_state'];h=dict(zip(b['human_body_names'],state['human_body_states']));start,end=string_segments(b)
    radius=read(P/'radial_bound_v1.json')['maximum_fixed_elbow_pick_radius_m'];lane=STRIKE['zone']['phrase_lane_y_m'];u=(lane-start[:,1])/(end[:,1]-start[:,1]);points=start+u[:,None]*(end-start)
    ep=read(paths[2])['rows'];rows=[]
    for step in (0,480,1200):
        g=state['guitar_body_states'][0] if step==0 else ep[step-1]['guitar_body_states']['guitar'];elbow=h['R_Elbow'] if step==0 else ep[step-1]['human_body_states']['R_Elbow'];gp,gr=pose(g);axis=gr.inv().apply(pose(elbow)[0]-gp)
        for label,depth in [('detector_minimum',STRIKE['detector']['min_depth_m']),('default_trajectory_depth',STRIKE['trajectory']['crossing_depth_m'])]:
            closest=points.copy();closest[:,2]=np.minimum(axis[2],points[:,2]-depth)
            lower=np.maximum(np.linalg.norm(closest-axis,axis=1)-radius,0)
            rows.append({'physics_step':step,'time_s':step/240,'depth_condition':label,'minimum_depth_m':depth,'elbow_axis_G_m':axis.tolist(),'closest_allowed_pick_positions_G_m':closest.tolist(),'minimum_possible_error_each_string_m':lower.tolist()})
    assert all(sha(f)==h for f,h in inputs.items());save(P/'depth_bound_v1.json',{'passed':True,'input_sha256':inputs,'lane_G_y_m':lane,'radius_m':radius,'rows':rows,'scope':'necessary bound minimized over pickZ<=stringZ-minDepth, no upper depth limit assumed; fixed elbow axis and reference finger posture; no joint/collision/whole-task success certificate; actual finger compliance unbounded'})
    print([(r['time_s'],r['depth_condition'],[round(x*1000,3) for x in r['minimum_possible_error_each_string_m']]) for r in rows])


if __name__=='__main__':main()
