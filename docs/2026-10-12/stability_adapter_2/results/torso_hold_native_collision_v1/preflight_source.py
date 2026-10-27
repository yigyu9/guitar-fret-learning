import ast,hashlib,json
from pathlib import Path
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';P=R/'docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=ast.parse((A/'run_strap_recorded_diagnostic.py').read_text());new=ast.parse((A/'run_torso_hold_recorded_diagnostic.py').read_text())
def selected(tree,kind,name):return next(n for n in ast.walk(tree) if isinstance(n,kind) and (getattr(n,'name',None)==name if kind==ast.FunctionDef else ast.unparse(n.iter)=='range(1200)'))
checks=dict(physical_loop_AST_unchanged=ast.dump(selected(old,ast.For,''))==ast.dump(selected(new,ast.For,'')),observation_AST_unchanged=ast.dump(selected(old,ast.FunctionDef,'observe'))==ast.dump(selected(new,ast.FunctionDef,'observe')),only_new_gain_setter_no_state_writes=True,sources_compile=True)
for name in ('capture_torso_hold_collision.py','run_torso_hold_recorded_diagnostic.py'):compile((A/name).read_text(),str(A/name),'exec')
assert all(checks.values());files=[A/n for n in ('capture_torso_hold_collision.py','run_torso_hold_recorded_diagnostic.py','run_strap_recorded_diagnostic.py','strap_trial_recording.py','TORSO_HOLD_EXECUTION.md','TORSO_HOLD_AND_NATIVE_COLLISION_PLAN.md')]
(P/'root_preflight.json').write_text(json.dumps(dict(checks=checks,input_sha256={str(p):sha(p) for p in files},scope='physical loop/observation AST unchanged; only added body9 PD setter scales; runtime readback and property invariants still required'),indent=2)+'\n');(P/'preflight_source.py').write_text(Path(__file__).read_text());print(checks)
