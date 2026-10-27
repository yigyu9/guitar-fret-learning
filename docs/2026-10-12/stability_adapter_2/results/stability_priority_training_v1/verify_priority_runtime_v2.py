"""Verify completed initial evaluations; ongoing learning is only a snapshot."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

P = Path(__file__).resolve().parent
inputs = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    inputs[str(path)] = sha(path)
    return json.loads(Path(path).read_text())


def huber(value):
    value = np.abs(value)
    return np.where(value <= 1., .5*value*value, value-.5)


checks = {}; summaries = {}
for mode in ('on', 'off'):
    base = P/f'long_{mode}_v1'
    attempt = read(base/'attempt.json')
    checks[mode+'_closure_unchanged'] = all(sha(p) == h for p, h in attempt['input_sha256'].items())
    transfer = read(base/'transfer_policy.json')
    source_path = Path(transfer['checkpoint']); initial_cp = base/'checkpoints/initial_000000.pt'
    inputs[str(source_path)] = sha(source_path); inputs[str(initial_cp)] = sha(initial_cp)
    source = torch.load(source_path, map_location='cpu', weights_only=True)
    new = torch.load(initial_cp, map_location='cpu', weights_only=True)
    checks[mode+'_actor_RMS_exact'] = all(torch.equal(value, new['model'][key])
        for key, value in source['model'].items() if not key.startswith('critic.'))
    checks[mode+'_new_reward_fresh_optimizer'] = not new['optimizer']['state'] and new['updates'] == 0 \
        and new['transitions'] == 0 and new['abi']['profile']['name'] == 'stability_priority_pilot_v1'
    evaluation = read(base/'evaluations/initial_000000/report.json')
    report = evaluation['native_report']
    native = base/'evaluations/initial_000000/native/episode_0001'
    rows = read(native/'controls.json')
    error = 0.
    for row in rows:
        ledger = row['raw_component_ledger']
        expected_position = -8.*float(huber(np.array(row['position_outside_m'])/.05).sum())/60
        expected_rotation = -4.*float(huber(row['rotation']['upper_rad']/.15))/60
        error = max(error, abs(ledger['position']-expected_position),
                    abs(ledger['rotation_upper_proxy']-expected_rotation),
                    abs(sum(ledger.values())-row['unfloored_raw_reward']))
    checks[mode+'_measured_weighted_ledger'] = error < 1e-12
    checks[mode+'_raw_scaled_total'] = np.isclose(sum(row['scaled_reward'] for row in rows), report['return']) \
        and np.isclose(sum(row['raw_reward'] for row in rows), report['raw_return'])
    checks[mode+'_native_eval_completed'] = evaluation['completed'] and evaluation['inputs_unchanged'] \
        and report['baseline_weights_unchanged'] and not report['forbidden_calls']
    checks[mode+'_strap_physical_calls'] = report['strap_force_calls'] == (13*report['physics_steps'] if mode == 'on' else 0)
    checks[mode+'_videos_unchanged'] = all(sha(value['path']) == value['sha256'] for value in report['videos'].values())
    outside = [bool(np.any(np.asarray(row['position_outside_m']) > 0)) for row in rows]
    summaries[mode] = {'source_updates': transfer['source_updates'],
        'initial_eval_actual_seconds': report['physics_seconds'],
        'full_horizon_completed': report['full_horizon_completed'], 'stop_reason': report['stop_reason'],
        'position_outside_percent_control_endpoints': 100*float(np.mean(outside)),
        'joint_success_events': report['joint_success_events'], 'settled_events': report['settled_events'],
        'weighted_ledger_max_absolute_error': error, 'safety_violation': report['safety_violation'],
        'videos': report['videos']}
    # Snapshot rather than a frozen hash of a log that is still being appended.
    rows_live = (base/'training.jsonl').read_text().splitlines()
    last = json.loads(rows_live[-1]) if rows_live else {}
    summaries[mode]['learning_snapshot'] = {k: last.get(k) for k in ('update', 'transitions', 'utc')}
    summaries[mode]['latest_accepted_optimizer_steps'] = last.get('ppo', {}).get('optimizer_steps', 0)
    checks[mode+'_actual_new_learning'] = bool(rows_live) and summaries[mode]['latest_accepted_optimizer_steps'] > 0
checks['audit_inputs_unchanged'] = all(sha(p) == h for p, h in inputs.items())
checks = {key: bool(value) for key, value in checks.items()}
result = {'utc': datetime.now(timezone.utc).isoformat(), 'checks_passed': all(checks.values()),
    'checks': checks, 'conditions': summaries, 'input_sha256': inputs, 'producer_sha256': sha(__file__),
    'scope': 'completed initial evaluations and transfer; new learning progress snapshot; long-run completion excluded',
    'production_reward_certified': False, 'stability_success_claimed': False}
(P/'runtime_verification_v2.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'checks_passed': result['checks_passed'], 'checks': checks}))
if not result['checks_passed']:
    raise SystemExit('Runtime verification failed; inspect preserved results.')
