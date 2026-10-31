"""24-arm target PI with rate/bound saturation anti-windup; no simulator writes."""
import numpy as np


class BoundedArmHold:
    def __init__(self, reference, lower, upper):
        self.reference = np.asarray(reference, dtype=float).copy()
        self.low = np.maximum(lower, self.reference-.3)
        self.high = np.minimum(upper, self.reference+.3)
        if self.reference.shape != (24,) or not np.isfinite([self.reference,self.low,self.high]).all() or not ((self.low<=self.reference)&(self.reference<=self.high)).all():
            raise ValueError('finite 24-joint reference inside bounds required')
        self.integral = np.zeros(24)
        self.previous = self.reference.copy()

    def update(self, actual, dt):
        actual = np.asarray(actual, dtype=float)
        if actual.shape != (24,) or not np.isfinite(actual).all() or not np.isfinite(dt) or dt<=0:
            raise ValueError('finite actual 24-vector and positive dt required')
        error = self.reference-actual
        proposed_integral = self.integral+error*dt
        def limited(integral):
            raw = error+2*integral
            bounded = np.clip(self.reference+raw,self.low,self.high)
            return raw, np.clip(bounded,self.previous-.8*dt,self.previous+.8*dt)
        raw, target = limited(proposed_integral)
        blocked = error*(raw-(target-self.reference))>1e-12
        self.integral = np.where(blocked,self.integral,proposed_integral)
        raw, target = limited(self.integral)
        step = target-self.previous
        self.previous = target.copy()
        return target, {'error_at_update_rad':error.tolist(),'integral_rad_s':self.integral.tolist(),
            'raw_delta_rad':raw.tolist(),'applied_delta_rad':(target-self.reference).tolist(),
            'integral_blocked':blocked.tolist(),'saturated':(abs(raw-(target-self.reference))>1e-10).tolist(),
            'max_nominal_target_step_rad':float(max(abs(step)))}
