"""Compare anatomical-right placement and after-preparation guitar motion."""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .search_right_shift_initial_v1 import ROOT,A,B,P


def main():
    old=B/'native_off_v1';new=P/'native_right10_v1'
    diagnostic=ROOT/'docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/diagnostic_v1/diagnostic.json'
    paths=[Path(__file__).resolve(),diagnostic,P/'strike_analysis_v1.json',P/'face_audit_v1.json',P/'command_audit_v1.json',P/'config_v1/candidate.json']+[f for n in (old,new) for f in n.rglob('*') if f.is_file()]
    inputs={str(p):sha(p) for p in paths};save(P/'comparison_before_v1.json',inputs)
    centre=np.array(read(diagnostic)['guitar_centre_G_m']);result={}
    for n in (old,new):
        initial=read(n/'initial_values.json');endpoints=read(n/'media/physics_endpoint_contacts.json')['rows'];states=[initial['native_initial_state']['guitar_body_states'][0]]+[r['guitar_body_states']['guitar'] for r in endpoints]
        root=np.array([pose(s)[0] for s in states]);rot=Rotation.from_quat([pose(s)[1].as_quat() for s in states]);body=root+rot.apply(centre)
        support={key:sum(bool(row[key]) for row in endpoints) for key in ('right_upper_arm_body_contacts','right_thorax_body_contacts','right_hip_body_contacts','right_forearm_body_contacts','trunk_guitar_contacts')}
        result[n.name]={'body_centre_initial_W_m':body[0].tolist(),'body_centre_final_W_m':body[-1].tolist(),'maximum_body_change_from2s_mm':float(np.linalg.norm(body[480:]-body[480],axis=1).max()*1000),'maximum_SO3_change_from2s_deg':float(np.rad2deg((rot[480].inv()*rot[480:]).magnitude()).max()),'support_contact_steps':support}
    result['initial_body_difference_W_mm']=(np.array(result[new.name]['body_centre_initial_W_m'])-result[old.name]['body_centre_initial_W_m'])*1000
    result['final_body_difference_W_mm']=(np.array(result[new.name]['body_centre_final_W_m'])-result[old.name]['body_centre_final_W_m'])*1000
    for key in ('initial_body_difference_W_mm','final_body_difference_W_mm'):result[key]=result[key].tolist()
    assert all(sha(p)==h for p,h in inputs.items());save(P/'comparison_v1.json',{'passed':True,'input_sha256':inputs,'results':result,'scope':'actual240Hz BB-centre/current quaternion and physics contact-query rows; after2s changes are not passive equilibrium, repeated-trial robustness or learned gameplay'})
    print(result,flush=True)


if __name__=='__main__':main()
