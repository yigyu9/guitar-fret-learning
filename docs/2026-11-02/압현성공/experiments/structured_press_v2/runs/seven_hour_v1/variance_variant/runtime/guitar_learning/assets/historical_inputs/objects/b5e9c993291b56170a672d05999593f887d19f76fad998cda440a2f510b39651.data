"""Separate actual pick tracking errors from saved-q calibrated FK errors."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import calibrated_upper_fk
from .search_elbow_wrist_ready_pose_v1 import P,A


def main():
    folders=[P/'native_strike_v1',P/'native_velocity_v1'];paths=[Path(__file__).resolve()]+list(A.glob('*.py'))+[f for n in folders for f in n.rglob('*') if f.is_file()]
    inputs={str(f):sha(f) for f in paths};save(P/'tracking_diagnostic_before_v1.json',inputs);cases={}
    for n in folders:
        b=read(n/'initial_values.json');state=b['native_initial_state'];fk,_=calibrated_upper_fk(b['joint_names'],b['human_body_names'],state,np.array(b['q_ref_rad']));trace=read(n/'trace.json');ends=read(n/'media/physics_endpoint_contacts.json')['rows'];targets=read(n/'media/six_joint_target_rows.json')['rows'];rows=[]
        for k,r in enumerate(trace[1:]):
            ep=ends[r['physics_step']-1];gp,gr=pose(ep['guitar_body_states']['guitar']);actual=pose(ep['human_body_states']['RH:pick'])[0];predicted=fk(np.array(r['q_rad']))['RH:pick'][0];goal=gp+gr.apply(targets[k]['desired_pick_G_m'])
            rows.append({'physics_step':r['physics_step'],'FK_minus_actual_G_m':gr.inv().apply(predicted-actual).tolist(),'FK_error_m':float(np.linalg.norm(predicted-actual)),'desired_minus_actual_G_m':gr.inv().apply(goal-actual).tolist()})
        cases[n.name]={'max_FK_error_mm':max(r['FK_error_m'] for r in rows)*1000,'rows':rows}
        print(n.name,'maxFk_actual_mm',cases[n.name]['max_FK_error_mm'],flush=True)
    assert all(sha(f)==h for f,h in inputs.items());save(P/'tracking_diagnostic_v1.json',{'input_sha256':inputs,'cases':cases,'scope':'same-q measured native pick vs source FK; desired point is preceding control goal, not next tick goal'})


if __name__=='__main__':main()
