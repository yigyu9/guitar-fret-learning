"""Same face-plane separation penalty, with proven zero-penalty early return."""
import numpy as np


def separation_penalty(va, pa, vb, pb, clearance):
    direction=vb.mean(axis=0)-va.mean(axis=0)
    for vertices,planes,axis in ((vb,pa,direction),(va,pb,-direction)):
        chosen=np.argsort(-(planes[:,:3] @ axis))[:8]
        gap=float(np.min(vertices @ planes[chosen,:3].T+planes[chosen,3],axis=0).max())
        if gap>=clearance+1e-10:
            return 0.
    gap=max(float(np.min(vb @ pa[:,:3].T+pa[:,3],axis=0).max()),
            float(np.min(va @ pb[:,:3].T+pb[:,3],axis=0).max()))
    return max(0.,clearance-gap)
