"""Diagnostic outer joint hold: bounded target correction, no native state writes."""
import numpy as np


class JointHoldResidual:
    def __init__(self, reference, lower, upper):
        self.reference = np.asarray(reference,dtype=float).copy()
        self.lower,self.upper = np.asarray(lower,dtype=float),np.asarray(upper,dtype=float)
        if self.reference.shape!=(24,) or self.lower.shape!=(24,) or self.upper.shape!=(24,):
            raise ValueError('expected 24 arm joints')
        if not np.isfinite([self.reference,self.lower,self.upper]).all() or not ((self.lower<=self.reference)&(self.reference<=self.upper)).all():
            raise ValueError('reference must be finite and inside diagnostic bounds')
        self.integral = np.zeros(24)

    def update(self, actual, dt):
        actual = np.asarray(actual,dtype=float)
        if actual.shape!=(24,) or not np.isfinite(actual).all() or not np.isfinite(dt) or dt<=0:
            raise ValueError('finite actual 24-vector and positive dt required')
        error = self.reference-actual
        proposed = self.integral+error*dt
        raw = error+2*proposed
        target = np.clip(self.reference+np.clip(raw,-.15,.15),self.lower,self.upper)
        blocked = error*(raw-(target-self.reference))>1e-12
        self.integral = np.where(blocked,self.integral,proposed)
        raw = error+2*self.integral
        target = np.clip(self.reference+np.clip(raw,-.15,.15),self.lower,self.upper)
        return target, {'error_at_update_rad':error.tolist(),'integral_rad_s':self.integral.tolist(),
            'raw_delta_rad':raw.tolist(),'applied_delta_rad':(target-self.reference).tolist(),
            'integral_blocked':blocked.tolist(),'saturated':(np.abs(raw-(target-self.reference))>1e-10).tolist()}
