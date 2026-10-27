"""Regression: changing the logged arm policy must not change geometry-owned R9 goals."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np


def branch(path):
    tree=ast.parse(path.read_text())
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.BoolOp)
              and any(isinstance(x,ast.Name) and x.id=='waiting_priority' for x in n.test.values))
    return compile(ast.fix_missing_locations(ast.Module(body=node.orelse,type_ignores=[])),str(path),'exec')


def evaluate(code,policy,previous,correction):
    actual=np.linspace(-.25,.25,9)
    namespace={'np':np,'actual':actual,'controlled_arm':np.arange(9),'correction':correction.copy(),
        'ready_integral':np.linspace(-.06,.06,9),'policy':np.full(9,policy),
        'args':SimpleNamespace(right_rate=3.2),'env':SimpleNamespace(lower=np.full(9,-1.57),
        upper=np.full(9,1.57),target=previous.copy()),'desired':np.zeros(9)}
    exec(code,namespace)
    return tuple(namespace[n].copy() for n in ('desired','ready_integral','blocked','raw_goal'))


def main():
    root=Path(__file__).resolve().parents[1]
    phase=root/'docs/2026-10-12/stability_adapter_2/results/strike_effort_geometry_pi_v1'
    current=root/'stability_adapter_2/run_strike_effort_geometry_pi.py'
    prior=phase/'source_before_pre_review_fix/run_strike_effort_geometry_pi.py'
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__).resolve(),current,prior)}
    actual=np.linspace(-.25,.25,9);cases=[(actual,np.linspace(-.02,.02,9)),
        (actual-.3,np.full(9,.15)),(actual+.3,np.full(9,-.15))]
    results=[]
    for label,path in (('before_fix',prior),('current',current)):
        code=branch(path);checks=[]
        for previous,correction in cases:
            a=evaluate(code,.8,previous,correction);b=evaluate(code,-.8,previous,correction)
            checks.append(all(np.array_equal(x,y) for x,y in zip(a,b)))
        results.append({'source':label,'policy_perturbation_invariant_cases':checks})
    assert results[0]['policy_perturbation_invariant_cases']==[False]*3
    assert results[1]['policy_perturbation_invariant_cases']==[True]*3
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
    (phase/'numerical_goal_owner_check.json').write_text(json.dumps({'input_sha256':hashes,
        'inputs_unchanged':True,'results':results,'scope':'pure extracted PI branch regression; no Gym import/physics or full controller certification'},indent=2)+'\n')
    print('Old submitted-policy bug reproduced in3cases; current goal/integral/preview policy-invariant in3cases')


if __name__=='__main__':main()
