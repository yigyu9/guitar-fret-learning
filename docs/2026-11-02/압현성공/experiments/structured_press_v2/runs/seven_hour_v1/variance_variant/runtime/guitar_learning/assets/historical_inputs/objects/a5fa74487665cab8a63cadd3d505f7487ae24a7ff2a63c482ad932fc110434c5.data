"""Count actual chest and support contacts in the new read-only replay."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1'
N=P/'native_v1'
B=ROOT/'docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/native_v2'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
    paths=[Path(__file__).resolve(),N/'attempt.json',N/'report.json',N/'media/chest_contact_query.json',N/'trace.json',B/'trace.json',N/'initial_values.json',B/'initial_values.json',B.parent/'artifact_inventory_v1.json',P/'main_PLAN_append_proof_v1.json',P/'execution_source_v1/main_PLAN_execution_prefix.md',ROOT/'stability_adapter_2/PLAN.md']
    pins={str(p):sha(p) for p in paths};save(P/'analysis_before_v2.json',pins)
    current_plan=ROOT/'stability_adapter_2/PLAN.md';save_plan=P/'analysis_PLAN_before_v2.md';assert not save_plan.exists();save_plan.write_bytes(current_plan.read_bytes());assert sha(save_plan)==pins[str(current_plan)]
    baseline_inventory=read(B.parent/'artifact_inventory_v1.json')['files']
    assert all(sha(p)==baseline_inventory[str(p)] for p in (B/'trace.json',B/'initial_values.json'))
    report=read(N/'report.json');rows=read(N/'media/chest_contact_query.json')['rows'];assert [r['physics_step'] for r in rows]==list(range(1,3841))
    results={}
    for name in rows[0]['contacts_by_human_body']:
        hit=[r for r in rows if r['contacts_by_human_body'][name]];positive=[r for r in hit if any(c['lambda']>0 for c in r['contacts_by_human_body'][name])]
        results[name]={'contact_steps':len(hit),'positive_lambda_steps':len(positive),'total_steps':len(rows),
            'first_contact_s':hit[0]['time_s'] if hit else None,'last_contact_s':hit[-1]['time_s'] if hit else None,
            'body_pairs':sorted({tuple(sorted([c['body0_name'],c['body1_name']])) for r in hit for c in r['contacts_by_human_body'][name]})}
    before=read(N/'attempt.json')['input_sha256'];changed={p:{'before_sha256':h,'observed_after_sha256':sha(p)} for p,h in before.items() if sha(p)!=h}
    allowed={str(ROOT/'stability_adapter_2/fresh_music_v1'/name) for name in ('events.py','run.py','test_events.py','test_runner.py')}
    proof=read(P/'main_PLAN_append_proof_v1.json');plan_before=Path(proof['before_copy']).read_bytes()
    plan_preserved=sha(proof['before_copy'])==before[proof['source']] and Path(proof['source']).read_bytes().startswith(plan_before)
    checks={'physical_loop_complete':report['failure'] is None and report['physics_steps']==3840 and report['control_steps']==960 and report['stop_reason']=='sixteen_second_left_cycle_observation','duration16s':report['physics_seconds']==16,'actual_and_shared_inputs_preserved':all(p in allowed or (p==proof['source'] and plan_preserved) for p in changed),'main_PLAN_before_prefix_preserved':plan_preserved,'forbidden_calls_zero':not report['forbidden_calls'],
        'same_initial_state':read(N/'initial_values.json')==read(B/'initial_values.json'),'full_trace_exact':read(N/'trace.json')==read(B/'trace.json'),'analysis_inputs_unchanged':all(sha(p)==h for p,h in pins.items())}
    save(P/'analysis_v2.json',{'input_sha256':pins,'checks':checks,'actual_native_contacts':results,
        'global_native_report_completed':report['completed'],'global_native_inputs_unchanged':report['inputs_unchanged'],'global_input_mismatches':changed,'scoped_audit_exact_exclusions':sorted(allowed),'native_main_PLAN_prefix_proof':proof,'analysis_PLAN_before_copy':str(save_plan.resolve()),
        'scope_limitation':'Full wildcard guard failed because four unrelated concurrently edited fresh_music files changed; main PLAN gained an authorized append, its exact original bytes are separately verified by matching the captured native-before SHA to the current prefix. Original failed report preserved. Scoped audit does not certify their preservation; all remaining before-pinned sources/assets/config exact; main PLAN preserved as exact byte prefix; initial/full native trace matches prior run.',
        'scope':'new16s identical-controller replay; actual240Hz postphysics queries, not historical missing fields; raw lambda positive is not calibrated force N; no touching at unobserved initial0s claimed'})
    assert all(checks.values());print(results,flush=True)
if __name__=='__main__':main()
