"""Fixed first-song metrics, with source, journal and resume checks."""
import collections
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from guitar_learning.song.task import make_task

R = Path('/home/ajou/yigyu/3')
P = Path(__file__).resolve().parents[1]
task = make_task(R/'data/song_bundles/05_BN2-131-B_solo', pre_roll_s=3., tail_s=.5)
audible = sum(t.end_s-t.onset_s for t in task.targets)


def load(path):
    return json.loads(path.read_text())


def equal(a, b):
    if torch.is_tensor(a):
        return torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return np.array_equal(a, b)
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def checkpoint(path):
    return torch.load(path, map_location='cpu', weights_only=False)


def aggregate(episodes):
    n = len(episodes)
    fingers = [e['left_curriculum']['finger_metrics'] for e in episodes]
    success = [sum(round(fs[f]['target_count']*fs[f]['success_fraction']) for fs in fingers)
               for f in range(4)]
    assert sum(success) == sum(e['song']['left_success_count'] for e in episodes)
    recovery = []
    for f in range(4):
        rows = [e['left_episode_diagnostics']['recovery']['by_finger'][f] for e in episodes]
        planned = sum(r['planned_s'] for r in rows)
        recovery.append(dict(planned_s=planned, observed_s=sum(r['observed_s'] for r in rows),
            in_band_s=sum(r['in_band_s'] for r in rows),
            fixed_window_occupancy=sum(r['in_band_s'] for r in rows)/planned if planned else None))
    samples = sum(e['left_finger_motion']['endpoint_samples'] for e in episodes)
    motion = {}
    for key in ('actual_native_limit_fraction', 'target_native_limit_fraction',
                'action_mean_abs', 'action_positive_fraction', 'action_negative_fraction'):
        motion[key] = [sum(e['left_finger_motion']['values'][key][j]*
            e['left_finger_motion']['endpoint_samples'] for e in episodes)/samples for j in range(21)]
    thumbs = [e['left_episode_diagnostics']['thumb_support'] for e in episodes]
    return dict(episodes=n, mean_achieved_notes=sum(success)/n,
        safe=sum(e['reason'] == 'timeline_complete' and e['left_curriculum']['full_safe'] for e in episodes),
        failure_reasons=dict(collections.Counter(r for e in episodes for r in e['failure_reasons'])),
        achieved_by_finger=success,
        opportunities_by_finger=[sum(fs[f]['target_count'] for fs in fingers) for f in range(4)],
        clean_fixed_audible_fraction=sum(sum(e['left_note_ledger']['values']['clean']) for e in episodes)/n/audible,
        wrong_fixed_audible_fraction=sum(sum(e['left_note_ledger']['values']['wrong']) for e in episodes)/n/audible,
        missing_fixed_audible_fraction=sum(sum(e['left_note_ledger']['values']['missing']) for e in episodes)/n/audible,
        B_recovery_by_finger=recovery,
        thumb_candidate_fixed_song_fraction=sum(t['contact_candidate_s'] for t in thumbs)/n/task.duration_s,
        joint_names=episodes[0]['left_finger_motion']['joint_names'],
        motion_observed_60hz_endpoints=samples, motion_by_joint=motion)


result = dict(arms={}, limitations=[
    'One seed, fresh100updates each; no long-run convergence or generalization claim.',
    'Same initial networks and PPO noise distribution; physical exploration differs with codec semantics.',
    'Fixed67-note first-song denominator includes failures/unobserved tails; observed joint fractions have a separate denominator.',
    'Source patch/body resultant candidates are not certified contact pairs, pressure or sound.'])
for mode in ('incremental', 'position'):
    run = P/('train_'+mode)
    report, evaluation = load(run/'report.json'), load(P/('eval_'+mode)/'report.json')
    assert report['completed'] and report['lifecycle_verified'] and not report['changed_inputs'] and not report['missing_import_pins']
    journal = report['journal']
    assert all(journal[k] == 409600 for k in ('sampled', 'logged', 'durable', 'committed')) and journal['discarded'] == 0
    assert evaluation['completed'] and evaluation['first_episodes'] == 128
    episodes = [json.loads(line) for line in (P/('eval_'+mode)/'episodes.jsonl').read_text().splitlines()]
    assert sorted(e['env_id'] for e in episodes) == list(range(128))
    arm = aggregate(episodes)
    metrics = [json.loads(line) for line in (run/'learning_metrics.jsonl').read_text().splitlines()]
    arm.update(max_attempted_kl=max(m['max_attempted_kl'] for m in metrics),
        kl_retries=sum(m['kl_retries'] for m in metrics), final_actor_lr=metrics[-1]['actor_lr'],
        final_curriculum=metrics[-1]['left_curriculum'])
    poses = np.load(P/('eval_'+mode)/'poses_env0000.npz')
    capture = load(P/('eval_'+mode)/'capture_metadata.json')
    finger_indices = [capture['joint_names'].index(name) for name in arm['joint_names']]
    arm['env0_last_native_targets_deg'] = np.rad2deg(poses['target'][-1, finger_indices]).tolist()
    result['arms'][mode] = arm

a, b = (checkpoint(P/('train_'+mode)/'initial.pt') for mode in ('incremental', 'position'))
result['same_initial_model'] = equal(a['model'], b['model'])
result['same_initial_optimizers'] = all(equal(a[k], b[k]) for k in ('actor_optimizer', 'value_optimizer'))
result['same_initial_rng'] = all(equal(a[k], b[k]) for k in ('torch_rng', 'numpy_rng', 'python_rng', 'cuda_rng'))
assert result['same_initial_model'] and result['same_initial_optimizers'] and result['same_initial_rng']
a, b = checkpoint(P/'smoke1024/final.pt'), checkpoint(P/'resume1024/initial.pt')
result['resume1024_exact'] = {k: equal(a[k], b[k]) for k in
    ('identity', 'model', 'actor_optimizer', 'value_optimizer', 'cost_weight', 'updates',
     'torch_rng', 'numpy_rng', 'python_rng', 'cuda_rng')}
assert all(result['resume1024_exact'].values())
manifest = load(P/'support/source_manifest.json')
archive = R/'guitar_learning/archive/20261026_before_position_default_rejection_v23'
assert all(hashlib.sha256((archive/Path(r['path']).relative_to(R)).read_bytes()).hexdigest()
           == r['sha256'] for r in manifest)
result['frozen_candidate_python'] = len(manifest)
result['candidate_source_archive'] = str(archive)
result['source_scope'] = 'Candidate sources unchanged during both runs; after evaluation, only default selection/tests/docs changed. Exact candidate bytes verified in archive.'
(P/'comparison.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
for mode, arm in result['arms'].items():
    print(mode, {k: arm[k] for k in ('mean_achieved_notes', 'safe', 'achieved_by_finger',
        'clean_fixed_audible_fraction', 'wrong_fixed_audible_fraction', 'missing_fixed_audible_fraction')})
