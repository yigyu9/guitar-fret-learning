"""Six-scalar finite pick IK retained from the validated runtime."""
import numpy as np
from scipy.optimize import least_squares

def solve_pick(fk,qbase,indices,lower,upper,qref,goal,start):
    lo=np.maximum(lower[indices]+1e-6,qref[indices]-1.);hi=np.minimum(upper[indices]-1e-6,qref[indices]+1.)
    def residual(v):
        q=qbase.copy();q[indices]=v
        return np.r_[1000*(fk(q)['RH:pick'][0]-goal),.1*(v-qref[indices]),1000*np.maximum(np.linalg.norm(v.reshape(2,3),axis=1)-np.deg2rad(158),0)]
    fit=least_squares(residual,np.clip(start,lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=60,ftol=1e-8,xtol=1e-8,gtol=1e-8)
    q=qbase.copy();q[indices]=fit.x
    return q,float(np.linalg.norm(fk(q)['RH:pick'][0]-goal)),fit.nfev

