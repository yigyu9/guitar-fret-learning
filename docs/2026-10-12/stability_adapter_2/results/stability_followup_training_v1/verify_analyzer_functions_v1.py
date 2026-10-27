"""Check the offline evaluator against the previously verified CP1 data."""
import ast,hashlib,json
from pathlib import Path
import torch
P=Path(__file__).resolve().parent;source=P/'analyze_checkpoint_v1.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_before=sha(source)
nodes=[]
for node in ast.parse(source.read_text()).body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='parser' for t in node.targets):break
    nodes.append(node)
namespace={'__file__':str(source),'__name__':'offline_function_check'}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),namespace)
Q=P.parent/'stability_support_nominal_v1';cp=Q/'smoke_on_v2/checkpoints/update_000001.pt'
abi=torch.load(cp,map_location='cpu',weights_only=True)['abi']
summary,checks,_=namespace['evaluate'](Q/'smoke_on_v2/evaluations/update_000001',abi)
reference=json.loads((Q/'runtime_verification_v2.json').read_text())['evaluations']['update_000001']
comparison=json.loads((Q/'comparison_v2.json').read_text())['evaluations']['after_one_update']
checks['known_outside_ratio']=summary['outside_percent']==reference['outside_percent']
checks['known_max_distance']=summary['max_position_outside_norm_m']==reference['max_position_outside_norm_m']
checks['known_SO3_rotation']=summary['max_SO3_rotation_from_initial_guitar_deg']==comparison['max_SO3_rotation_from_initial_deg']
checks['longest_two_control_ticks']=namespace['longest']([False,True,True,False,True])==2/60
checks['longest_empty_zero']=namespace['longest']([])==0
checks['source_unchanged']=sha(source)==source_before
inputs=namespace['inputs'];inputs[str(source)]=source_before;inputs[str(Path(__file__).resolve())]=sha(__file__)
for p in [cp,Q/'runtime_verification_v2.json',Q/'comparison_v2.json']:inputs[str(p)]=sha(p)
checks['all_inputs_exact']=all(sha(p)==h for p,h in inputs.items())
with (P/'analyzer_function_verification_v1.json').open('x') as f:json.dump({'checks_passed':all(checks.values()),'checks':checks,
 'input_sha256':inputs,'scope':'saved CP1 function checks only; no new native or learning execution','CP1_summary':summary},f,indent=2)
print('function checks',len(checks),'pass',all(checks.values()))
if not all(checks.values()):raise SystemExit([k for k,v in checks.items() if not v])
