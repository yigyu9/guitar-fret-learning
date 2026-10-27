"""Audit a bounded recovery pilot, preserving both successes and rejections."""
import argparse
import json
from pathlib import Path
import torch
from .audit_pilot_v1 import BASE, ROOT, sha, read, inspect_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evaluation', required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    args = parser.parse_args()
    run = BASE/'recovery64_v1'
    report = read(run/'report.json')
    attempt = read(run/'attempt.json')
    rows = [json.loads(line) for line in (run/'rollouts.jsonl').open()]
    accepted = {r['rollout_id'] for r in rows if r['status']=='accepted'}
    rejected = {r['rollout_id'] for r in rows if r['status']=='rejected'}
    counts = {}
    for line in (run/'transitions.jsonl').open():
        row = json.loads(line)
        counts[row['rollout_id']] = counts.get(row['rollout_id'],0)+1
    c = report['counters']
    baseline = inspect_run('heldout_baseline_v5')
    evaluation = inspect_run(args.evaluation)
    source = inspect_run('pilot64_v5')
    start = torch.load(BASE/'pilot64_v5/checkpoint_0000.pt',map_location='cpu',weights_only=False)
    final = torch.load(args.checkpoint,map_location='cpu',weights_only=False)
    component_changes = {}
    for prefix in ('encoder','actor_heads.0','actor_heads.1','actor_heads.2','reward_critic','cost_critic'):
        component_changes[prefix] = max(float((final['model'][key]-value).abs().max()) for key,value in start['model'].items() if key.startswith(prefix+'.'))
    hashes = attempt['input_sha256']
    changes = [name for name,digest in hashes.items() if not Path(name).is_file() or sha(name)!=digest]
    copies = []
    for name,digest in hashes.items():
        p = Path(name)
        if p.suffix in ('.py','.sh') and ROOT in p.parents:
            cp = run/'source_before'/p.relative_to(ROOT)
            copies.append(cp.is_file() and sha(cp)==digest)
    commands = [json.loads(line) for line in (run/'commands.jsonl').open()]
    loaded = set(report['loaded_project_python_modules'].values())
    checks = dict(
        recovery_reached_requested_budget=report['completed'] and report['final_updates']==64,
        source_completed27=source['completed_updates']==27,
        accepted_rollouts_have256_steps=all(counts.get(i)==256 for i in accepted),
        rejected_rollouts_never_update=all(not r['ppo_updated'] for r in rows if r['status']=='rejected'),
        accounting_matches=(sum(counts.values())==c['valid_controls'] and sum(counts.get(i,0) for i in accepted)==c['accepted_ppo_steps'] and sum(counts.get(i,0) for i in rejected)==c['discarded_controls'] and c['valid_controls']==c['accepted_ppo_steps']+c['discarded_controls']+c['pending_valid_controls']),
        update_counts_match=len(accepted)==report['performed_updates']==report['final_updates']-27,
        command_attempts_contiguous=[r['control_attempt'] for r in commands]==list(range(1,c['attempted_controls']+1)),
        rejection_and_attempt_limits=c['total_rejected_rollouts']<=8 and c['attempted_controls']<=11264,
        recovery_no_forbidden_calls=not c['forbidden_calls'],
        recovery_source_snapshots_exact=all(copies),
        recovery_loaded_sources_and_data_unchanged=not [p for p in changes if p in loaded or Path(p).suffix!='.py'],
        paired_ABI=baseline['environment_ABI']==evaluation['environment_ABI']==read(run/'config.json')['identity']['environment'],
        paired_seed=baseline['seed']==evaluation['seed']==9002,
        paired_complete=all(r['original_report_completed'] and r['collected_control_steps']==300 for r in (baseline,evaluation)),
        paired_source_and_action_checks=all(r['source_before_all_exact'] and r['kept27_targets_exact'] and r['effort_targets_agree'] and r['finite_transition_values'] and not r['forbidden_calls'] and not r['changed_loaded_python_modules'] and not r['changed_non_python_inputs'] for r in (baseline,evaluation)),
        policy_and_critics_changed=all(v>0 for v in component_changes.values()),
        final_checkpoint_matches_report=final['updates']==report['final_updates'],
    )
    for r in (source,baseline,evaluation):
        del r['environment_ABI']
    result=dict(checks=checks, source=source, baseline=baseline,evaluation=evaluation,
        recovery_report=report,recovery_current_changed_inputs=changes,recovery_source_copy_count=len(copies),
        rollouts=rows,component_max_abs_change=component_changes,
        audit_source_sha256=sha(__file__),final_checkpoint_sha256=sha(args.checkpoint),
        scope='Selection-biased bounded training pilot. One paired validation goal; no music, human-likeness, or general safety evidence.')
    with (BASE/'recovery_v1_analysis.json').open('x') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps(checks,ensure_ascii=False))


if __name__=='__main__':
    main()
