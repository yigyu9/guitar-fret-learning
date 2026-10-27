"""Audit the completed guarded smoke run; no native simulation or modification."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

P = Path(__file__).resolve().parent
RUN = P/'smoke_on_v1'
inputs = {}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    inputs[str(path)] = sha(path)
    return json.loads(Path(path).read_text())
def checkpoint(path):
    inputs[str(path)] = sha(path)
    return torch.load(path, map_location='cpu', weights_only=True)
def huber(value):
    value = np.abs(value)
    return np.where(value <= 1, .5*value*value, value-.5)


inputs[str(Path(__file__).resolve())] = sha(__file__)
report = read(RUN/'report.json'); attempt = read(RUN/'attempt.json')
checks = {'complete_smoke': report['completed'] and report['updates'] == 3 and report['transitions'] == 768,
          'closure_unchanged': all(sha(p) == h for p, h in attempt['input_sha256'].items()),
          'native_CUDA_profile': report['learning_device']=='cuda' and report['physical_backend']=='CPU PhysX'
              and report['profile']=='stability_guarded_update_pilot_v1',
          'exact_exit_zero': read(P/'smoke_on_v1.exit.json')['returncode'] == 0}
init_record = read(RUN/'initialize_rms.json')
source = checkpoint(Path(init_record['checkpoint']))
cps = {label: checkpoint(RUN/'checkpoints'/(label+'.pt'))
       for label in ('initial_000000', 'update_000001', 'update_000003')}
c0 = cps['initial_000000']
rms_keys = [k for k in c0['model'] if k.startswith('obs_rms.')]
checks['RMS_source_and_every_saved_checkpoint_exact'] = all(torch.equal(cp['model'][k], source['model'][k])
    for cp in cps.values() for k in rms_keys)
checks['initial_neutral_mean_fresh_Adam'] = not c0['optimizer']['state'] and c0['updates']==0 \
    and not torch.count_nonzero(c0['model']['actor.4.weight']) and not torch.count_nonzero(c0['model']['actor.4.bias'])
checks['actual_actor_and_critic_updated'] = all(any(not torch.equal(cps['update_000003']['model'][k], v)
    for k, v in c0['model'].items() if k.startswith(prefix)) for prefix in ('actor.', 'critic.'))
inputs[str(RUN/'training.jsonl')] = sha(RUN/'training.jsonl')
logs = [json.loads(s) for s in (RUN/'training.jsonl').read_text().splitlines()]
checks['every_update_accepted_and_KL_guarded'] = len(logs)==3 and all(e['ppo']['optimizer_steps']>0
    and not e['ppo']['RMS_updated'] and 0 <= e['ppo']['final_analytic_kl'] <= .02
    and all(0 <= s['kl'] <= .02 for s in e['ppo']['minibatches']) for e in logs)
groups = c0['abi']['groups']; caps = np.array([c0['abi']['residual_caps_rad'][g] for g in groups])
lo, hi, rates = [np.array(c0['abi'][k]) for k in ('lower', 'upper', 'rates')]
summaries = {}
old_init = read(P.parent/'stability_priority_training_v1/long_on_v1/evaluations/initial_000000/native/episode_0001/initial_values.json')
for label in cps:
    base = RUN/'evaluations'/label; native = base/'native/episode_0001'
    evaluation = read(base/'report.json'); nr = read(native/'report.json'); rows = read(native/'controls.json')
    initial = read(native/'initial_values.json'); capture = read(native/'media/capture.json')
    checks[label+'_initial_exact'] = initial['native_initial_state']==old_init['native_initial_state']
    checks[label+'_native_completion_baseline_guard'] = evaluation['completed'] and nr['baseline_weights_unchanged'] and not nr['forbidden_calls']
    checks[label+'_strap_calls'] = nr['strap_force_calls']==13*nr['physics_steps']
    requested = np.array([r['requested81_rad'] for r in rows]); nominal = np.array([r['nominal81_rad'] for r in rows])
    final = np.array([r['final81_rad'] for r in rows])
    previous = np.vstack([initial['q_ref_rad'], final[:-1]])
    checks[label+'_caps_bounds_rates'] = bool(np.all(np.abs(requested-nominal)<=caps+1e-10)
        and np.all(final>=lo-1e-8) and np.all(final<=hi+1e-8) and np.all(np.abs(final-previous)<=rates/60+1e-7))
    checks[label+'_native_frames_endpoint'] = capture['frames'][0]['physics_step']==0 \
        and capture['frames'][-1]['physics_step']==nr['physics_steps'] and all(f['render_preserves_states'] for f in capture['frames'])
    checks[label+'_videos_exact'] = all(sha(v['path'])==v['sha256'] for v in nr['videos'].values())
    for v in nr['videos'].values(): inputs[v['path']]=v['sha256']
    error = 0.
    for r in rows:
        ledger = r['raw_component_ledger']
        error = max(error, abs(ledger['position']+8*float(huber(np.array(r['position_outside_m'])/.05).sum())/60),
                    abs(ledger['rotation_upper_proxy']+4*float(huber(r['rotation']['upper_rad']/.15))/60),
                    abs(sum(ledger.values())-r['unfloored_raw_reward']))
    checks[label+'_weighted_ledger'] = error < 1e-12
    summaries[label] = {'physics_seconds': nr['physics_seconds'], 'full_horizon_completed': nr['full_horizon_completed'],
        'stop_reason': nr['stop_reason'], 'safety_violation': nr['safety_violation'],
        'outside_percent': 100*float(np.mean(np.max(np.array([r['position_outside_m'] for r in rows]),axis=1)>0)),
        'max_position_outside_norm_m': float(max(np.linalg.norm(r['position_outside_m']) for r in rows)),
        'joint_success_events': nr['joint_success_events'], 'accepted_crossings': nr['accepted_crossings'],
        'frames': len(capture['frames']), 'videos': nr['videos'],
        'max_requested_residual_rad_by_group': {g: float(np.max(np.abs(requested-nominal)[:,np.array(groups)==g])) for g in set(groups)}}
checks['initial_evaluation_actions_zero'] = all(not max(abs(a) for a in r['policy_action81'])
    for r in read(RUN/'evaluations/initial_000000/native/episode_0001/controls.json'))
checks['audit_inputs_unchanged'] = all(sha(p)==h for p,h in inputs.items())
checks = {k: bool(v) for k,v in checks.items()}
result = {'utc': datetime.now(timezone.utc).isoformat(), 'checks_passed': all(checks.values()),
          'checks': checks, 'evaluations': summaries, 'input_sha256': inputs,
          'updates': [{k: e[k] for k in ('update','transitions','ppo')} for e in logs],
          'scope': 'completed CUDA3-update smoke and actual full evaluations; quality/repeatability/production reward not certified'}
with (P/'runtime_verification_v1.json').open('x') as stream: json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
print(json.dumps({'checks_passed': result['checks_passed'], 'checks': checks, 'evaluations': summaries},ensure_ascii=False))
if not result['checks_passed']: raise SystemExit('Inspect preserved failing runtime checks')
