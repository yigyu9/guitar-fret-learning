"""CPU audit of role masks, expert transfer, native stability and strict resume."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path('/home/ajou/yigyu/3')
sys.path.insert(0, str(ROOT))
from guitar_learning.specialist_policy import SpecialistPolicy

PHASE = Path(__file__).resolve().parent
FIELDS = ('state', 'events', 'mask', 'priority_events', 'priority_mask')


def same(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and np.array_equal(a, b)
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return type(a) is type(b) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def branch_equal(a, b, hand):
    keys = [k for k in a if k.startswith(('actor_encoders.'+hand+'.', 'actor_heads.'+hand+'.'))]
    selection = SpecialistPolicy.role_slices[hand]
    return bool(keys) and all(torch.equal(a[k], b[k]) for k in keys) and torch.equal(a['log_std'][selection], b['log_std'][selection])


def load(path):
    return torch.load(path, map_location='cpu', weights_only=False)


def model(payload):
    architecture = payload['identity']['architecture']
    result = SpecialistPolicy(architecture['state_dim'], size=architecture['size'],
        contract=architecture['contract'], role=architecture['role'], frozen_partner=architecture['frozen_partner'])
    result.load_state_dict(payload['model'], strict=True)
    result.eval()
    return result


def main():
    torch.set_num_threads(1)
    names = ('left', 'right', 'right_with_left', 'joint', 'left_resume')
    sources = {hand: load(PHASE / ('native_'+hand+'_v1') / 'final.pt') for hand in ('left', 'right')}
    results = []
    for name in names:
        folder = PHASE / ('native_'+name+'_v1')
        report = json.loads((folder/'report.json').read_text())
        summary = json.loads((folder/'specialist_report.json').read_text())
        initial, final = load(folder/'initial.pt'), load(folder/'final.pt')
        rollout = load(folder/'rollout_first.pt')
        role = report['settings']['specialist']['role']
        expected_transitions = report['settings']['horizon']*report['settings']['num_envs']
        checks = dict(report_completed=report['completed'], persistent_audit=report['persistent_audit']['completed'],
            transition_counts=report['transitions'] == summary['logged_transitions'] == expected_transitions,
            one_update=final['updates']-initial['updates'] == 1,
            finite_model=all(torch.isfinite(v).all().item() for v in final['model'].values()),
            kl_guard=all(u['analytic_kl'] <= report['settings']['ppo']['target_kl'] for u in report['updates']),
            no_input_or_physical_errors=not any(report[k] for k in ('changed_inputs','missing_import_pins',
                'original_source_parity_errors','missing_worker_audits','worker_audit_read_errors','guard_violations',
                'worker_failures','physical_flags_errors','cleanup_errors')))
        inactive = None if role == 'joint' else ('right' if role == 'left' else 'left')
        if inactive:
            checks['inactive_branch_and_std_unchanged'] = branch_equal(initial['model'], final['model'], inactive)
        if name in ('right_with_left', 'joint'):
            checks['both_expert_actors_and_std_transferred'] = all(
                branch_equal(initial['model'], sources[hand]['model'], hand) for hand in ('left', 'right'))
            if name == 'right_with_left':
                inputs = [rollout[k].flatten(0,1) for k in FIELDS]
                with torch.no_grad():
                    teacher = model(sources['left']).act(*inputs, deterministic=True)['action'][:, :33]
                    adapted = model(final).act(*inputs, deterministic=True)['action'][:, :33]
                checks['frozen_partner_outputs_match_teacher_on_all_rollout_states'] = torch.equal(teacher, adapted)
        if name == 'left_resume':
            checks['strict_resume_exact'] = all(same(initial[k], sources['left'][k]) for k in (
                'identity','model','actor_optimizer','value_optimizer','cost_weight','updates',
                'torch_rng','numpy_rng','python_rng','cuda_rng'))
        stability = dict(samples=0, any_support_samples=0, triple_support_samples=0, both_feet_samples=0,
                         guitar_displacement_max_m=0., guitar_rotation_max_rad=0., foot_displacement_max_m=0.)
        actions = []
        with gzip.open(folder/'transitions.jsonl.gz', 'rt') as stream:
            for line in stream:
                for info in json.loads(line)['infos']:
                    action = np.asarray(info['debug']['action'])
                    actions.append(action)
                    s = info['stability']; flags = np.asarray(s['flags'])
                    stability['samples'] += 1
                    stability['any_support_samples'] += int(flags[:3].any())
                    stability['triple_support_samples'] += int(flags[:3].all())
                    stability['both_feet_samples'] += int(flags[-2:].all())
                    stability['guitar_displacement_max_m'] = max(stability['guitar_displacement_max_m'], float(np.linalg.norm(s['guitar_delta_m'])))
                    stability['guitar_rotation_max_rad'] = max(stability['guitar_rotation_max_rad'], float(np.linalg.norm(s['guitar_rotation_vector_rad'])))
                    stability['foot_displacement_max_m'] = max(stability['foot_displacement_max_m'], float(np.linalg.norm(s['foot_delta_m'], axis=1).max()))
        actual = np.asarray(actions)
        expected = rollout['latent'].tanh().numpy().reshape(-1,39)
        checks['logged_actions_match_sampled_rollout'] = bool(np.allclose(actual, expected, atol=1e-7, rtol=0))
        if name in ('left', 'right', 'left_resume'):
            checks['inactive_actions_exact_zero'] = bool((actual[:, SpecialistPolicy.role_slices[inactive]] == 0).all())
        checks['no_physical_failure_episodes'] = summary['physical_failure_episodes'] == 0
        results.append(dict(name=name, passed=all(checks.values()), checks=checks, wall_s=report['wall_s'],
            transitions=report['transitions'], physics_policy_samples=4*report['transitions'],
            updates_initial=initial['updates'], updates_final=final['updates'],
            completed_episodes=summary['completed_episodes'], stage_success_episodes=summary['successful_episodes'],
            physical_failure_episodes=summary['physical_failure_episodes'], stability_endpoint60Hz=stability,
            report_path=str(folder/'report.json'), report_sha256=hashlib.sha256((folder/'report.json').read_bytes()).hexdigest()))
    result = dict(completed=all(r['passed'] for r in results), runs=results,
        transitions=sum(r['transitions'] for r in results), physics_policy_samples=sum(r['physics_policy_samples'] for r in results),
        completed_episodes=sum(r['completed_episodes'] for r in results),
        stage_success_episodes=sum(r['stage_success_episodes'] for r in results),
        physical_failure_episodes=sum(r['physical_failure_episodes'] for r in results),
        scope='bounded wiring and safety regression; not trained skill, reachability or long-run convergence certification')
    target = PHASE/'native_verification_v1.json'
    with target.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(dict(completed=result['completed'], transitions=result['transitions'],
        physics_policy_samples=result['physics_policy_samples'], completed_episodes=result['completed_episodes'],
        stage_success_episodes=result['stage_success_episodes'], physical_failure_episodes=result['physical_failure_episodes'])))
    if not result['completed']:
        raise SystemExit('native verification failed')


if __name__ == '__main__':
    main()
