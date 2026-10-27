from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from stability_adapter_2.initial_pose_noise_v1 import read,pose
from stability_adapter_2.environment_contract_v1 import EnvironmentContract
from stability_adapter_2.upper_arm_static_geometry_v1 import ROOT,calibrated_upper_fk,capsule_witness


def context():
    d=read(ROOT/'docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/bank_build_v1/proposal_00/native_audit.json');c=EnvironmentContract();fk,parents=calibrated_upper_fk(c.names,d['human_body_names'],d['actual'],c.q_ref);return d,c,fk

def test_full_zero_fk_matches_all_native_bodies():
    d,c,fk=context();poses=fk(c.q_ref)
    for n,s in zip(d['human_body_names'],d['actual']['human_body_states']):
        p,r=pose(s);pp,rr=poses[n];assert np.linalg.norm(pp-p)<1e-12;assert (r.inv()*rr).magnitude()<1e-12

def test_three_degree_whole_chest_lean_preserves_fixed_root_lower():
    d,c,fk=context();p0=fk(c.q_ref);axis=np.array([-1.,0,0]);target=Rotation.from_rotvec(axis*np.deg2rad(3))*p0['Chest'][1]
    def res(v):
        q=c.q_ref.copy();q[c.body]=v;return (target.inv()*fk(q)['Chest'][1]).as_rotvec()
    fit=least_squares(res,c.q_ref[c.body],bounds=(c.q_ref[c.body]-.087,c.q_ref[c.body]+.087));q=c.q_ref.copy();q[c.body]=fit.x;p=fk(q)
    assert np.rad2deg((target.inv()*p['Chest'][1]).magnitude())<1e-4
    for n in ('Pelvis','R_Hip','R_Knee','L_Hip','L_Knee'):assert np.array_equal(p[n][0],p0[n][0]) and (p[n][1].inv()*p0[n][1]).magnitude()<1e-12
    other=np.array([i for i in range(81) if i not in c.body]);assert np.array_equal(q[other],c.q_ref[other])

def test_capsule_support_point_stays_below_upper_arm():
    _,c,fk=context();poses=fk(c.q_ref);w=capsule_witness(poses,np.array([0,0,1.]));assert w[2]<poses['R_Shoulder'][0][2]
