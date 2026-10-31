"""Moving IK reference tracking via bounded joint goals, never direct torque."""
import numpy as np


class PreparationJointTracking:
    def __init__(self, lower, upper):
        self.lower, self.upper = np.asarray(lower,dtype=float), np.asarray(upper,dtype=float)
        if self.lower.shape!=(12,) or self.upper.shape!=(12,) or not np.isfinite(np.r_[self.lower,self.upper]).all() or (self.lower>self.upper).any():
            raise ValueError('finite ordered 12-joint bounds required')
        self.integral=np.zeros(12)

    def update(self, reference, actual, previous, dt):
        reference,actual,previous=[np.asarray(v,dtype=float) for v in (reference,actual,previous)]
        if any(v.shape!=(12,) for v in (reference,actual,previous)) or not np.isfinite(np.r_[reference,actual,previous,dt]).all() or dt<=0:
            raise ValueError('finite 12-joint values and positive dt required')
        reference=np.clip(reference,self.lower,self.upper);error=reference-actual
        proposed=self.integral+error*dt
        def limited(integral):
            residual=.7*error+.5*integral
            raw=reference+residual
            bounded=np.clip(reference+np.clip(residual,-.15,.15),self.lower,self.upper)
            return raw,np.clip(bounded,previous-.8*dt,previous+.8*dt)
        raw,target=limited(proposed)
        blocked=error*(raw-target)>1e-12
        self.integral=np.where(blocked,self.integral,proposed)
        raw,target=limited(self.integral)
        return target,{'reference_rad':reference.tolist(),'error_rad':error.tolist(),
            'integral_rad_s':self.integral.tolist(),'blocked':blocked.tolist(),
            'applied_residual_rad':(target-reference).tolist()}
