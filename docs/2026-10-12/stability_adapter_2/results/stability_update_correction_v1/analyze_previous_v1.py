"""Offline diagnosis only: seal input bytes and distinguish censored episodes."""
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
OLD = HERE.parent/'stability_priority_training_v1'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(path, data):
    with Path(path).open('x') as stream: json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)


inputs = {str(Path(__file__).resolve()): sha(__file__)}
result = {}
for mode in ('on', 'off'):
    run = OLD/('long_'+mode+'_v1')
    paths = [run/'training.jsonl', OLD/('long_'+mode+'_v1.exit.json')]
    evaluations, cps = [], []
    for label in ('initial_000000', 'update_000001'):
        ep = run/'evaluations'/label/'native/episode_0001'
        cp = run/'checkpoints'/(label+'.pt')
        paths += [cp]+[ep/n for n in ('initial_values.json', 'controls.json', 'report.json', 'trace.json')]
        rows = read(ep/'controls.json'); report = read(ep/'report.json')
        payload = torch.load(cp, map_location='cpu', weights_only=True)
        groups = np.array(payload['abi']['groups'])
        delta = np.array(rows[0]['requested81_rad'])-np.array(rows[0]['nominal81_rad'])
        evaluations.append({'label': label, 'actual_seconds': report['physics_seconds'],
            'full_horizon': report['full_horizon_completed'], 'safety': report['safety_violation'],
            'joint_success_events': report['joint_success_events'], 'accepted_crossings': report['accepted_crossings'],
            'position_outside_fraction': float(np.mean([max(r['position_outside_m']) > 0 for r in rows])),
            'maximum_position_outside_norm_m': float(max(np.linalg.norm(r['position_outside_m']) for r in rows)),
            'initial_max_requested_residual_rad_by_group': {g: float(np.abs(delta[groups == g]).max()) for g in ('body','head','arm','finger')},
            'initial_native_state': read(ep/'initial_values.json')['native_initial_state'],
            'first_nominal': rows[0]['nominal81_rad'], 'first_action': rows[0]['policy_action81']})
        cps.append(payload)
    for p in paths: inputs[str(p.resolve())] = sha(p)
    logs = [json.loads(s) for s in (run/'training.jsonl').read_text().splitlines()]
    episodes = logs[-1]['completed_episodes']
    e0, e1 = evaluations
    assert e0['initial_native_state'] == e1['initial_native_state']
    assert e0['first_nominal'] == e1['first_nominal']
    mu0, mu1 = [np.arctanh(e['first_action']) for e in evaluations]
    s0, s1 = [np.exp(c['model']['log_std'].double().numpy()) for c in cps]
    kl = np.log(s1/s0)+(s0*s0+(mu0-mu1)**2)/(2*s1*s1)-.5
    for e in evaluations:
        for key in ('initial_native_state', 'first_nominal', 'first_action'): del e[key]
    result[mode] = {'updates': logs[-1]['update'], 'transitions': logs[-1]['transitions'],
        'completed_episodes': len(episodes), 'finite_velocity_safety_episodes': sum(e['stop_reason']=='finite_joint_velocity_safety' for e in episodes),
        'full_horizon_episodes': sum(e['full_horizon_completed'] for e in episodes),
        'joint_success_events': sum(e['joint_success_events'] for e in episodes),
        'every_update_one_step_then_KL_stop': all(e['ppo']['optimizer_steps']==1 and e['ppo']['early_kl_stop'] for e in logs),
        'initial_native_state_and_nominal_exact': True,
        't0_analytic_Gaussian_KL_initial_to_update1': float(kl.sum()),
        't0_max_mean_shift_old_std_units': float(np.abs((mu1-mu0)/s0).max()),
        'evaluations': evaluations, 'exit': read(OLD/('long_'+mode+'_v1.exit.json'))}
write(HERE/'previous_analysis_v1.json', {'input_sha256': inputs, 'results': result,
    'scope': 'offline saved data; t0 KL combines actor and RMS changes, not rollout average or attribution; ON/OFF policy histories differ',
    'inputs_unchanged': all(sha(p)==h for p,h in inputs.items())})
print(json.dumps(result, ensure_ascii=False, indent=2))
