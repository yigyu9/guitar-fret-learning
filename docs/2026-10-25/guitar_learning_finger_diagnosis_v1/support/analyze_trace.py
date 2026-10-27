"""Analyze bounded actual240Hz observer copies, auditing original episode summaries."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

PHASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_existing import temporal, FINGERS


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_stats(mask, clock):
    """Exactly count contiguous completed240Hz endpoint samples."""
    edge = np.diff(np.r_[False, mask, False].astype(int))
    a, b = np.where(edge == 1)[0], np.where(edge == -1)[0]
    duration = (b-a)/240
    return dict(count=len(a), total_s=float(duration.sum()), max_s=float(duration.max()) if len(a) else 0.,
        median_s=float(np.median(duration)) if len(a) else 0.,
        thresholds={str(t): dict(count=int(np.sum(duration >= t)),
            total_s=float(duration[duration >= t].sum()),
            eligible_time_fraction=float(duration[duration >= t].sum()/duration.sum()) if duration.sum() else 0.)
            for t in (.25, .5, 1.)},
        intervals=[dict(first_endpoint_s=float(clock[x]/240), last_endpoint_s=float(clock[y-1]/240),
            sampled_duration_s=float((y-x)/240)) for x, y in zip(a, b)])


def reward_integrals(gate, quality, tracking_quality, reason, approach):
    """Preserve whole failed control tick suppression, with no later-episode samples."""
    tick_ok = np.ones(len(gate), bool)
    if reason != 'timeline_complete':
        tick_ok[-4:] = False
    raw = .0025*np.sum(gate*quality, axis=0)/240
    weighted = .0025*np.sum(gate*quality*tick_ok[:, None], axis=0)/240*approach
    tracking = float(np.sum(.5*tracking_quality.sum(1)/240*tick_ok)*approach)
    return raw, weighted, tracking


def condition_masks(angles, valid, gate, idle, pressing, tracking, time, final_end):
    pattern = (angles[:, 1] <= 10) & (angles[:, 2] >= 60)
    masks = dict(all=np.ones(len(time), bool), actual_standby=gate > 0,
        full_actual_standby=gate == 1, pressing=pressing, tracking=tracking,
        standby_and_tracking=(gate > 0) & tracking,
        standby_no_tracking=(gate > 0) & ~tracking,
        pattern_and_tracking=pattern & tracking,
        pattern_and_pressing=pattern & pressing,
        pattern_and_standby=pattern & (gate > 0),
        release_no_tracking_or_press=~tracking & ~pressing,
        final_full_idle_tail=time > final_end+.15,
        time_idle_but_vetoed=(idle > 0) & (gate == 0))
    return {k:mask & valid for k,mask in masks.items()}


def require_first_episode(clock, steps):
    if len(clock) != steps*4 or not np.array_equal(clock, np.arange(1, len(clock)+1)):
        raise ValueError('Trace must be the exact first ended episode prefix, without reset samples')


def main():
    report_path = PHASE/'trace_observed_report.json'
    observer = json.loads(report_path.read_text())
    evaluation = PHASE/observer['evaluation']
    with (evaluation/'first_episodes.jsonl').open() as stream:
        episodes = {r['env_id']:r for r in map(json.loads, stream)}
    targets = json.loads((evaluation/'targets.json').read_text())
    assert len(episodes) == 1024 and len(targets) == 67
    result = dict(schema='guitar_learning.actual_gate_trace_analysis.v1',
        scope='Unchanged deterministic final v19, repeated1024firstepisodes, actual240Hz observer copies for predeclared env0..7; no PPO/reward/control changes.',
        limitations=['Completed endpoint runs are sampled durations, not continuous-time proof.',
            'Joint pattern PIP<=10deg and DIP>=60deg is a diagnostic threshold, not reward.',
            'Per-condition reward integrals are raw before approach stage and failed-tick suppression; integral_checks apply both.',
            'Overlapping exclusion flags and concurrent reward opportunities do not establish causal reward competition.',
            'Repeat GPU inference may differ numerically; original and observer results are distinguished.'],
        inputs_sha256={str(report_path):sha(report_path), str(Path(__file__).resolve()):sha(Path(__file__).resolve()),
            str(evaluation/'first_episodes.jsonl'):sha(evaluation/'first_episodes.jsonl'),
            str(evaluation/'targets.json'):sha(evaluation/'targets.json'),
            str(PHASE/'support/analyze_existing.py'):sha(PHASE/'support/analyze_existing.py')},
        cohort=dict(episodes=1024, safe=sum(e['reason']=='timeline_complete' for e in episodes.values())), captures={})
    saved = None
    original = PHASE.parent/'guitar_learning_long_training_v19_3000/evaluation_video1_final_1024'
    for capture in observer['captures']:
        env_id = capture['env_id']
        path = PHASE/'physics_observed'/capture['path']
        assert sha(path) == capture['sha256']
        result['inputs_sha256'][str(path)] = sha(path)
        ep = episodes[env_id]
        diag = ep['left_episode_diagnostics']
        with np.load(path) as z:
            clock = z['clock']; time = clock/240
            require_first_episode(clock, ep['steps'])
            gate, quality, idle = z['gate'], z['quality'], z['idle_weight']
            angles = np.degrees(z['angles'].astype(float))
            valid = z['valid'].all(-1)
            pressing, tracking = z['pressing'], z['tracking_valid']
            temporal_b = temporal(time, targets, .35, .15)
            observation_idle = temporal(time, targets, 2., .25)
            np.testing.assert_allclose(idle, temporal_b, atol=3e-7, rtol=0)
            approach = ep['left_curriculum']['weights']['approach']
            raw_b, weighted_b, tracking_reward = reward_integrals(gate, quality,
                z['tracking_quality'], ep['reason'], approach)
            np.testing.assert_allclose(raw_b, diag['standby']['raw_standby_reward'], atol=1e-10, rtol=1e-9)
            checks = dict(raw_b_max_abs_error=float(np.max(np.abs(raw_b-diag['standby']['raw_standby_reward']))))
            for key, value in dict(eligible_s=(gate > 0).sum(0)/240,
                gate_weighted_s=gate.sum(0)/240,
                time_blocked_s=(idle == 0).sum(0)/240,
                contact_excluded_s=z['contact_veto'].sum(0)/240,
                proximity_excluded_s=z['near_veto'].sum(0)/240,
                nonfinite_distance_excluded_s=z['nonfinite_veto'].sum(0)/240).items():
                np.testing.assert_allclose(value, diag['standby'][key], atol=2e-9, rtol=1e-9)
                checks[key+'_max_abs_error'] = float(np.max(np.abs(value-diag['standby'][key])))
            np.testing.assert_allclose(weighted_b, diag['standby']['weighted_standby_reward'], atol=1e-9, rtol=1e-8)
            np.testing.assert_allclose(tracking_reward, ep['reward_components']['song_finger_tracking'], atol=2e-4, rtol=1e-5)
            checks['tracking_reward_reconstructed'] = float(tracking_reward)
            checks['tracking_reward_reported'] = ep['reward_components']['song_finger_tracking']
            checks['standby_reward_reconstructed'] = float(weighted_b.sum())
            checks['standby_reward_reported'] = ep['reward_components']['song_finger_standby']
            np.testing.assert_allclose(weighted_b.sum(), ep['reward_components']['song_finger_standby'], atol=2e-6, rtol=2e-5)
            row = dict(reason=ep['reason'], steps=ep['steps'], left_success_count=ep['song']['left_success_count'],
                integral_checks=checks, fingers={})
            for f, name in enumerate(FINGERS):
                pattern = (angles[:, f, 1] <= 10) & (angles[:, f, 2] >= 60)
                strict = pattern & (angles[:, f, 0] <= 15)
                final_end = max(t['end_s'] for t in targets if t['finger'] == f+1)
                masks = condition_masks(angles[:,f], valid[:,f], gate[:,f], idle[:,f],
                    pressing[:,f], tracking[:,f], time, final_end)
                first_press = min(t['press_s'] for t in targets if t['finger'] == f+1)
                masks['initial_unrelated_idle'] = (time < first_press-2.) & valid[:,f]
                conditions = {}
                motion_inds = [ep['left_finger_motion']['joint_names'].index('LH:'+name+s) for s in ('1_x','2','3')]
                for label, mask in masks.items():
                    mask &= valid[:, f]
                    selected = z['tracking_indices'][mask, f]
                    selected_valid = z['tracking_valid'][mask, f]
                    sample = np.where(mask)[0][selected_valid]
                    selected = selected[selected_valid]
                    distance = z['distance'][sample, selected]
                    hist = {str(int(i)):int(n) for i,n in zip(*np.unique(selected, return_counts=True))}
                    conditions[label] = dict(samples=int(mask.sum()), sampled_s=float(mask.sum()/240),
                        pattern_fraction=float(pattern[mask].mean()) if mask.any() else None,
                        mcp_also_straight_fraction=float(strict[mask].mean()) if mask.any() else None,
                        mean_angles_degrees=angles[mask, f].mean(0).tolist() if mask.any() else None,
                        tracking_target_histogram=hist,
                        selected_distance_mean_m=float(distance.mean()) if len(distance) else None,
                        selected_candidate_fraction=float(z['candidate'][sample, selected].mean()) if len(sample) else None,
                        tracking_raw_integral=float(.5*z['tracking_quality'][mask, f].sum()/240),
                        standby_raw_integral=float(.0025*np.sum(gate[mask, f]*quality[mask, f])/240),
                        action_mean=z['action'][mask][:,motion_inds].mean(0).tolist() if mask.any() else None)
                joint_summaries = {}
                for condition, weight in (('idle', gate[:, f]), ('press', pressing[:, f].astype(float))):
                    denominator = (weight[:, None]*z['valid'][:, f]).sum(0)/240
                    avg = (angles[:, f]*weight[:, None]*z['valid'][:, f]).sum(0)/240/denominator
                    np.testing.assert_allclose(denominator, diag[condition+'_angles']['valid_weighted_s'][f], atol=2e-9, rtol=1e-9)
                    np.testing.assert_allclose(avg, np.degrees(diag[condition+'_angles']['mean_rad'][f]), atol=1e-8, rtol=1e-8)
                    joint_summaries[condition] = avg.tolist()
                row['fingers'][name] = dict(conditions=conditions, verified_mean_angles_degrees=joint_summaries,
                    actual_gate_positive_runs=run_stats(gate[:, f] > 0, clock),
                    full_gate_runs=run_stats(gate[:, f] == 1, clock),
                    actual_gate_observation_idle_zero_s=float(np.sum((gate[:,f] > 0) & (observation_idle[:,f] == 0))/240),
                    actual_gate_weighted_pattern_fraction=float(np.sum(gate[:,f]*pattern)/gate[:,f].sum()),
                    eligible_quality=float(np.sum(gate[:,f]*quality[:,f])/gate[:,f].sum()))
                for label in ('initial_unrelated_idle', 'final_full_idle_tail'):
                    mask = masks[label]
                    if mask.any():
                        assert (gate[mask,f] == 1).all() and not tracking[mask,f].any()
                        row['fingers'][name]['conditions'][label].update(
                            first_angles_degrees=angles[mask,f][0].tolist(),
                            last_angles_degrees=angles[mask,f][-1].tolist(),
                            first_b_quality=float(quality[mask,f][0]),
                            last_b_quality=float(quality[mask,f][-1]),
                            first_action=z['action'][mask][:,motion_inds][0].tolist(),
                            last_action=z['action'][mask][:,motion_inds][-1].tolist())
            result['captures'][str(env_id)] = row
            if env_id == 0:
                saved = (time, angles, gate, pressing, tracking)
        # Comparison uses actual60Hz captures from original/repeated cohorts, never reconstruction.
        oldpose, newpose = original/('poses_env%04d.npz'%env_id), evaluation/('poses_env%04d.npz'%env_id)
        result['inputs_sha256'].update({str(p):sha(p) for p in (oldpose,newpose)})
        with np.load(oldpose) as a, np.load(newpose) as b:
            repeat = dict(equal_length=len(a['clock'])==len(b['clock']))
            for key in ('q','target','action','body_state'):
                count = min(len(a[key]),len(b[key]))
                delta = a[key][:count].astype(float)-b[key][:count].astype(float)
                repeat[key+'_max_abs_difference'] = float(np.max(np.abs(delta)))
                repeat[key+'_rms_difference'] = float(np.sqrt(np.mean(delta**2)))
            count = min(len(a['clock']),len(b['clock']))
            old_body, new_body = a['body_state'][:count].astype(float), b['body_state'][:count].astype(float)
            repeat['body_position_max_abs_difference_m'] = float(np.max(np.abs(old_body[...,:3]-new_body[...,:3])))
            old_quat, new_quat = old_body[...,3:7], new_body[...,3:7]
            cosine = np.sum(old_quat*new_quat, axis=-1)/(np.linalg.norm(old_quat,axis=-1)*np.linalg.norm(new_quat,axis=-1))
            repeat['body_orientation_max_angle_degrees'] = float(np.degrees(2*np.arccos(np.clip(np.abs(cosine),0,1))).max())
            row['repeatability_to_original'] = repeat
    (PHASE/'trace_analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    time, angles, gate, pressing, tracking = saved
    fig, axes = plt.subplots(4, 1, figsize=(13, 10), sharex=True)
    for f, ax in enumerate(axes):
        for j, label in enumerate(('MCP','PIP','DIP')):
            ax.plot(time, angles[:,f,j], label=label, lw=.9)
        ax.fill_between(time, -45, 105, where=gate[:,f] > 0, color='green', alpha=.12, label='Actual B gate>0')
        ax.plot(time, -43+8*tracking[:,f], color='black', lw=.5, label='Tracking active')
        ax.set(ylabel=FINGERS[f]+' (deg)', ylim=(-45,105)); ax.grid(alpha=.2)
    axes[0].legend(ncol=5, loc='upper right')
    axes[-1].set_xlabel('Song clock (s), actual240Hz completed physics endpoints')
    fig.suptitle('Observer final v19 env0: actual angles, actual B eligibility and tracking')
    fig.tight_layout(); fig.savefig(PHASE/'trace_angles.png', dpi=150); plt.close(fig)
    print(json.dumps(dict(cohort=result['cohort'], env0=result['captures']['0']), indent=2))


if __name__ == '__main__':
    main()
