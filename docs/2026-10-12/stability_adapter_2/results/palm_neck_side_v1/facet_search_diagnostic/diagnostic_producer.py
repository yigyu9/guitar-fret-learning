import isaacgym
import scipy.optimize as so
import numpy as np
original=so.linprog
saved=False
def traced(*args,**kwargs):
 global saved
 result=original(*args,**kwargs)
 if not result.success and result.status!=2 and not saved:
  np.savez('/tmp/stability2_lp_failure.npz',matrix=kwargs['A_ub'],rhs=kwargs['b_ub'])
  saved=True
 return result
so.linprog=traced
import sys
sys.argv=['search','--out','docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/facet_search_diagnostic','--settings-dir','stability_adapter_2/trials/palm_neck_side_v1/facet_diagnostic']
from stability_adapter_2.search_palm_contact_facet import main
try:main()
except RuntimeError:pass
f=np.load('/tmp/stability2_lp_failure.npz')
for method,options in [('highs',{'presolve':False}),('highs-ds',{'presolve':False}),('highs-ipm',{}),('interior-point',{'tol':1e-10})]:
 r=original([0,0,0,-1],A_ub=f['matrix'],b_ub=f['rhs'],bounds=[(None,None)]*3+[(0,None)],method=method,options=options)
 print(method,options,r.status,r.message,r.x,flush=True)
 if r.x is not None:print('maxconstraint',np.max(f['matrix']@r.x-f['rhs']))
