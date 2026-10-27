"""Small physical rotation margin around the preserved playable Euler region."""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .prepared_strike_start import guitar_in_playable_region


def evaluate_entry_region(position,quaternion,chest_z):
    p,q=np.asarray(position),np.asarray(quaternion)
    strict=guitar_in_playable_region(p,q,chest_z)
    result={'strict_region':strict,'entry_region':strict,'rotation_margin_deg':.1,
            'reference_euler_xyz_deg':None,'reference_distance_deg':0. if strict else None}
    if strict:return result
    if p.shape!=(3,) or q.shape!=(4,) or not np.isfinite(np.r_[p,q,chest_z]).all() or np.linalg.norm(q)<1e-12:return result
    if not ((p>=[-.50,-.15,.65]) & (p<=[-.15,.15,chest_z])).all():return result
    current=Rotation.from_quat(q);e=current.as_euler('xyz',degrees=True)
    lower=np.array([45.,50.,135.]);upper=np.array([90.,100.,180.])
    candidates=[]
    for seed in (e.copy(),np.array([e[0]+180,180-e[1],e[2]+180])):
        seed[[0,2]]%=360
        fit=least_squares(lambda v:(Rotation.from_euler('xyz',v,degrees=True).inv()*current).as_rotvec(),
                          np.clip(seed,lower+1e-8,upper-1e-8),bounds=(lower,upper),max_nfev=80,
                          gtol=1e-12,xtol=1e-12,ftol=1e-12)
        if np.isfinite(fit.x).all() and ((fit.x>=lower)&(fit.x<=upper)).all():
            distance=float(np.degrees((Rotation.from_euler('xyz',fit.x,degrees=True).inv()*current).magnitude()))
            candidates.append((distance,fit.x))
    if candidates:
        distance,reference=min(candidates,key=lambda row:row[0])
        result.update(entry_region=distance<=.1,reference_euler_xyz_deg=reference.tolist(),reference_distance_deg=distance)
    return result
