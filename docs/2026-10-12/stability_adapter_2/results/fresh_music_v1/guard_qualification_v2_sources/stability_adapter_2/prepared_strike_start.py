"""Loose diagnostic entry to a frozen Strike policy, not strict readiness."""
import numpy as np
from scipy.spatial.transform import Rotation


def guitar_in_playable_region(position, quaternion, chest_z):
    p,q=np.asarray(position),np.asarray(quaternion)
    if p.shape!=(3,) or q.shape!=(4,) or not np.isfinite(np.r_[p,q,chest_z]).all() or np.linalg.norm(q)<1e-12:
        return False
    if not ((p>=[-.50,-.15,.65]) & (p<=[-.15,.15,chest_z])).all():
        return False
    r=Rotation.from_quat(q).as_matrix();cy=np.hypot(r[0,0],r[1,0])
    if cy<1e-7:
        if -r[2,0]<0: return False
        difference=np.degrees(np.arctan2(r[0,1],r[0,2]))
        return any(-135-1e-6<=difference+k<=-45+1e-6 for k in (-360,0,360))
    x,y,z=np.degrees([np.arctan2(r[2,1],r[2,2]),np.arctan2(-r[2,0],cy),np.arctan2(r[1,0],r[0,0])])
    for a,b,c in ((x,y,z),(x+180,180-y,z+180)):
        a,c=a%360,c%360
        if 45-1e-6<=a<=90+1e-6 and 50-1e-6<=b<=100+1e-6 and 135-1e-6<=c<=180+1e-6:
            return True
    return False


def diagnostic_start_ready(readiness, time_s, region_ok):
    required=('finite','left_finger_neck_contact','left_palm_up',
              'right_front_side','right_grip','right_noncontact')
    return bool(time_s>=2 and region_ok and readiness['pick_to_ready_m']<=.08
                and all(readiness['conditions'][k] for k in required))
