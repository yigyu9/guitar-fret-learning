"""Read-only cross-check of the two existing quality training logs."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1'


def audit(name):
    run = SOURCE / name
    with gzip.open(run / 'transitions.jsonl.gz', 'rt') as stream:
        rows = [json.loads(line) for line in stream]
    report = json.loads((run / 'report.json').read_text())
    quality_report = json.loads((run / 'musical_quality_report.json').read_text())
    terms, episodes, quality_episodes = Counter(), [], []
    errors, reward_errors, cost, logged = [], [], 0., 0
    for tick, row in enumerate(rows):
        for worker, info in enumerate(row['infos']):
            logged += 1
            terms.update(info['reward_terms'])
            cost += info['cost']
            reward_errors.append(abs(row['reward'][worker] - sum(info['reward_terms'].values())))
            if info['timing'] != info['specialist']['timing']:
                errors.append(['nested_timing', tick, worker])
            if abs(info['task_time_s'] - (tick + 1) / 60.) > 1e-9:
                errors.append(['clock', tick, worker])
            if info['musical_quality']['strike']['previous_actual_step'] != (tick + 1) * 4:
                errors.append(['physics_step', tick, worker])
            if 'episode' in info:
                episode = info['episode']
                episodes.append(episode)
                quality_episodes.append(info['musical_quality'])
                if episode['musical_quality'] != info['musical_quality']:
                    errors.append(['nested_quality', tick, worker])
    if logged != report['transitions']:
        errors.append(['committed_count', logged, report['transitions']])
    if quality_episodes != quality_report['episodes']:
        errors.append(['quality_episode_summary'])
    reward_delta = abs(sum(terms.values()) - sum(e['reward'] for e in episodes))
    cost_delta = abs(cost - sum(e['cost'] for e in episodes))
    summary_delta = max(abs(value - quality_report['reward_terms'][key]) for key, value in terms.items())
    if max(reward_errors + [reward_delta, cost_delta, summary_delta]) > 1e-6:
        errors.append(['numeric_accounting'])
    pins = json.loads((run / 'inputs_before.json').read_text())
    paths = ['parallel.py', 'train_parallel.py', 'ppo.py', 'train_musical_quality.py',
             'musical_quality.py', 'musical_quality_environment.py', 'safety.py']
    source_parity = {filename: hashlib.sha256((ROOT / 'guitar_learning' / filename).read_bytes()).hexdigest()
                     == pins.get(str(ROOT / 'guitar_learning' / filename)) for filename in paths}
    if not all(source_parity.values()):
        errors.append(['current_source_parity'])
    last = rows[-1]['infos'][0]
    q = last['musical_quality']
    update = report['updates'][0]
    return dict(path=str(run), errors=errors, passed=not errors,
        sampled_workers_per_tick=len(rows[0]['infos']), logged_control_ticks=len(rows),
        logged_worker_transitions=logged, committed_transitions=report['transitions'],
        maximum_float32_reward_difference=max(reward_errors),
        episode_reward_difference=reward_delta, episode_cost_difference=cost_delta,
        quality_reward_summary_difference=summary_delta, current_source_matches_inputs=source_parity,
        role=q['role'], run_completed=report['completed'],
        completed_episode_reasons=[e['reason'] for e in episodes],
        quality_successes=sum(e['musical_quality']['stage_success'] for e in episodes),
        timing_only_successes=sum(e['timing']['timing_only_stage_success'] for e in episodes),
        clean_audible_fraction=q['clean_audible_fraction'], release_complete=q['release_complete'],
        release_late_s=q['release_late_s'], missing_press_s=q['missing_press_s'],
        accepted_crossings=q['strike']['counts']['accepted'], extra_crossings=q['strike']['counts']['extra'],
        timing_wrong_crossings=last['timing']['wrong_crossings'],
        legacy_joint_wrong_crossings=last['music']['wrong_crossings'],
        recovered=q['strike']['recovered'], analytic_kl=update['analytic_kl'],
        max_attempted_kl=update['max_attempted_kl'], kl_retries=update['kl_retries'],
        actor_lr=update['actor_lr'], actor_grad_norm=update['actor_grad_norm'],
        update_keys=list(update), reward_terms=dict(terms),
        transition_top_level_keys=list(rows[0]), info_keys=list(rows[0]['infos'][0]))


if __name__ == '__main__':
    result = dict(schema='guitar_learning.logging_metric_audit.v1',
        scope='existing one-update single-worker runs; no new physics or training',
        runs={name: audit(name) for name in ('left_native_train_v2', 'right_native_train_v1')})
    result['passed'] = all(run['passed'] for run in result['runs'].values())
    destination = Path(__file__).with_name('metrics_audit_v1.json')
    if destination.exists():
        raise FileExistsError('Preserve the previous audit; choose a new output version')
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(dict(passed=result['passed'], path=str(destination))))
