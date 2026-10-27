"""Clarify configured substeps without claiming a native SimParams readback."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2';B=R/'docs/2026-10-12/stability_adapter_2/results';P=B/'finger_contact_map_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not (P/'configuration_clarification.json').exists()
    paths=[Path(__file__).resolve(),P/'analysis.json',B/'fixed_strap_shoulder_response_v1/plus008/initial_values.json']+[A/n for n in ['environment.py','physics_presets.py','fixed_lower_environment.py','self_collision_environment.py','capture_isaac_gym_initial.py']]
    before={str(p):sha(p) for p in paths};initial=json.loads(paths[2].read_text());tree=ast.parse((A/'environment.py').read_text());expected=ast.parse("params.substeps = self.physics_parameters.get('substeps',1)").body[0]
    assignments=[n for n in ast.walk(tree) if isinstance(n,ast.Assign) and ast.dump(n)==ast.dump(expected)]
    preset_tree=ast.parse((A/'physics_presets.py').read_text());presets=ast.literal_eval(next(n.value for n in preset_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRESETS' for t in n.targets)))
    checks=dict(source_hashes_match_consumed_native=all(initial['input_sha256'][str(p)]==sha(p) for p in paths[3:]),source_substeps_assignment_exact=len(assignments)==1,saved_physics_matches_baseline=initial['physics_parameters']==presets['baseline'],source_baseline_configured_substeps1=presets['baseline'].get('substeps',1)==1)
    after={str(p):sha(p) for p in paths};checks['inputs_preserved']=before==after;assert all(checks.values()),checks
    result=dict(checks=checks,input_sha256_before=before,input_sha256_after=after,supersedes_analysis_check='single_substep',configured_substeps_from_consumed_source=1,native_SimParams_readback_performed=False,saved_physics_parameters_contains_substeps='substeps' in initial['physics_parameters'],scope='analysis single_substep field used a default on an absent saved key; source setting verified separately, native readback remains unverified; post-step feature pair numeric agreement is independent evidence',native_initializations=0,physics_steps=0)
    (P/'configuration_clarification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['checks']))
if __name__=='__main__':main()
