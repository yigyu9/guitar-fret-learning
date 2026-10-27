"""Read-only analysis of the original fixed v19 cohort and eight actual-pose captures."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.gpu.finger_reward import finger_posture_reward

PHASE = Path(__file__).resolve().parents[1]
EVAL = ROOT/'docs/2026-10-25/guitar_learning_long_training_v19_3000/evaluation_video1_final_1024'
FINGERS = ('index', 'middle', 'ring', 'pinky')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runs(mask, dt):
    """Consecutive endpoint samples; approximate durations, not exact boundary intervals."""
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return [(int(a)*dt, int(b)*dt, int(b-a)*dt)
            for a, b in zip(np.where(edges == 1)[0], np.where(edges == -1)[0])]


def temporal(now, targets, preparation, fade):
    press = np.array([t['press_s'] for t in targets])
    end = np.array([t['end_s'] for t in targets])
    finger = np.array([t['finger'] for t in targets])
    busy = np.minimum(np.clip((now[:, None]-(press-preparation-fade))/fade, 0, 1),
                      np.clip((end+fade-now[:, None])/fade, 0, 1))
    busy[(now[:, None] >= press-preparation) & (now[:, None] <= end)] = 1
    return np.stack([1-busy[:, finger == f].max(-1) for f in range(1, 5)], -1)


def aggregate(rows):
    seconds = sum(r['left_episode_diagnostics']['physics_sampled_s'] for r in rows)
    result = dict(episodes=len(rows), total_episode_seconds=seconds, fingers={})
    for f, name in enumerate(FINGERS):
        standby = {k: sum(r['left_episode_diagnostics']['standby'][k][f] for r in rows)
                   for k in rows[0]['left_episode_diagnostics']['standby'] if k != 'eligible_mean_quality'}
        g = standby['gate_weighted_s']
        standby['eligible_mean_quality'] = sum(
            r['left_episode_diagnostics']['standby']['eligible_mean_quality'][f]*
            r['left_episode_diagnostics']['standby']['gate_weighted_s'][f] for r in rows)/g
        standby['mean_gate_weighted_s_per_episode'] = g/len(rows)
        standby['gate_weighted_fraction_of_exposure'] = g/seconds
        angles = {}
        for condition in ('idle', 'press'):
            weight = sum(np.array(r['left_episode_diagnostics'][condition+'_angles']['valid_weighted_s'][f]) for r in rows)
            numerator = sum(np.array(r['left_episode_diagnostics'][condition+'_angles']['mean_rad'][f])*
                            np.array(r['left_episode_diagnostics'][condition+'_angles']['valid_weighted_s'][f]) for r in rows)
            angles[condition] = dict(valid_weighted_s=weight.tolist(), mean_degrees=np.degrees(numerator/weight).tolist())
        motion = {}
        for suffix in ('1_x', '2', '3'):
            joint = 'LH:'+name+suffix
            j = rows[0]['left_finger_motion']['joint_names'].index(joint)
            samples = sum(r['left_finger_motion']['action_samples'] for r in rows)
            values = {}
            for key in ('action_mean', 'action_mean_abs', 'action_positive_fraction',
                        'action_negative_fraction', 'limit_outward_command_fraction'):
                values[key] = sum(r['left_finger_motion']['values'][key][j]*r['left_finger_motion']['action_samples'] for r in rows)/samples
            values['tracking_error_rms_degrees'] = np.degrees(np.sqrt(sum(
                r['left_finger_motion']['values']['tracking_error_rms_rad'][j]**2*r['left_finger_motion']['endpoint_samples'] for r in rows)/samples))
            for sign in ('positive', 'negative'):
                values['episodes_'+sign+'_fraction_ge95pct'] = sum(
                    r['left_finger_motion']['values']['action_'+sign+'_fraction'][j] >= .95 for r in rows)
            values['episode_action_mean_p05_p50_p95'] = np.quantile(
                [r['left_finger_motion']['values']['action_mean'][j] for r in rows], [.05, .5, .95]).tolist()
            pairs = sum(r['left_finger_motion']['action_change_pairs'] for r in rows)
            values['action_opposite_sign_fraction'] = sum(
                r['left_finger_motion']['values']['action_opposite_sign_fraction'][j]*
                r['left_finger_motion']['action_change_pairs'] for r in rows)/pairs
            motion[suffix] = values
        result['fingers'][name] = dict(standby=standby, angles=angles, motion=motion)
    return result


def main():
    torch.set_num_threads(1)
    meta = json.loads((EVAL/'capture_metadata.json').read_text())
    targets = json.loads((EVAL/'targets.json').read_text())
    initial = json.loads((EVAL/'visual_initial.json').read_text())
    with (EVAL/'first_episodes.jsonl').open() as stream:
        rows = [json.loads(line) for line in stream]
    assert len(rows) == 1024 and len({r['env_id'] for r in rows}) == 1024
    assert [sum(t['finger'] == f for t in targets) for f in range(1, 5)] == [25, 18, 12, 12]
    source = ROOT/'guitar_learning/gpu/finger_reward.py'
    assert sha(source) == meta['posture_reconstruction']['source_function_sha256']
    pins = {str(p): sha(p) for p in [Path(__file__).resolve(), source,
        ROOT/'guitar_learning/core/control.py', ROOT/'guitar_learning/gpu/geometry.py',
        EVAL/'first_episodes.jsonl', EVAL/'capture_metadata.json', EVAL/'targets.json', EVAL/'visual_initial.json']}
    safe = [r for r in rows if r['reason'] == 'timeline_complete']
    result = dict(schema='guitar_learning.existing_finger_diagnosis.v1', inputs_sha256=pins,
        scope='Fixed deterministic final v19 cohort; aggregate actual240Hz standby/angles, 60Hz command statistics; saved actual60Hz geometry for8predeclared envs. No new inference, training, control or reward changes.',
        limitations=['Exclusion seconds overlap; do not add them.',
            'Existing240Hz records have no run lengths, contemporaneous tracking reward, or joint-pattern occupancy.',
            'Pose temporal B eligibility omits actual proximity/contact vetoes; never call it actualgate.',
            'Pattern thresholds are diagnostic choices, not reward or anatomical certification.',
            'No reward causal attribution from observational records alone.'],
        all=aggregate(rows), safe=aggregate(safe), env0=aggregate([next(r for r in rows if r['env_id'] == 0)]),
        schedule={}, captures={})
    endtime = max(r['steps'] for r in rows)/60
    time = np.arange(1, int(round(endtime*240))+1)/240
    btime, obs = temporal(time, targets, .35, .15), temporal(time, targets, 2., .25)
    for f, name in enumerate(FINGERS):
        run = runs(btime[:, f] > 0, 1/240)
        durations = np.array([v[2] for v in run])
        result['schedule'][name] = dict(temporal_b_positive_s=float(np.sum(btime[:, f] > 0)/240),
            temporal_b_weighted_s=float(btime[:, f].sum()/240),
            temporal_b_positive_runs_endpoint_approx=run,
            max_positive_run_s=float(durations.max()), median_positive_run_s=float(np.median(durations)),
            runs_lt_half_second=int(np.sum(durations < .5)), runs_ge_one_second=int(np.sum(durations >= 1)),
            observation_idle_positive_s=float(np.sum(obs[:, f] > 0)/240),
            b_positive_observation_busy_s=float(np.sum((btime[:, f] > 0) & (obs[:, f] == 0))/240),
            final_own_end_s=max(t['end_s'] for t in targets if t['finger'] == f+1),
            full_b_tail_start_s=max(t['end_s'] for t in targets if t['finger'] == f+1)+.15)
    series = []
    for capture in meta['captures']:
        path = EVAL/capture['path']
        assert sha(path) == capture['sha256']
        pins[str(path)] = sha(path)
        with np.load(path) as z:
            times = z['clock'][1:]/240
            body = z['body_state'][1:]
            pm = meta['posture_reconstruction']
            measured = finger_posture_reward(torch.tensor(times),
                *[torch.tensor([t[k] for t in targets]) for k in ('onset_s', 'end_s', 'press_s')],
                torch.tensor([t['finger'] for t in targets]),
                torch.tensor(body[:, pm['palm_body_index'], 3:7], dtype=torch.float64),
                torch.tensor(body[:, pm['segment_body_indices'], 3:7], dtype=torch.float64))
            angles = np.degrees(measured['angles'].numpy())
            valid = measured['valid'].numpy().all(-1)
            bt = temporal(times, targets, .35, .15)
            info = dict(reason=capture['reason'], scope='60Hz completed endpoints; time-only idle, not actual standby gate', fingers={})
            for f, name in enumerate(FINGERS):
                press = np.any([(times >= t['press_s']) & (times <= t['end_s']) for t in targets if t['finger'] == f+1], axis=0)
                idle = bt[:, f] > 0
                pattern = (angles[:, f, 1] <= 10) & (angles[:, f, 2] >= 60)
                strict = pattern & (angles[:, f, 0] <= 15)
                conditions = {}
                for label, mask in dict(all=np.ones(len(times), bool), time_idle=idle, press=press, other=~idle & ~press,
                                        final_full_idle_tail=times >= result['schedule'][name]['full_b_tail_start_s']).items():
                    mask = mask & valid[:, f]
                    conditions[label] = dict(samples=int(mask.sum()), seconds=float(mask.sum()/60),
                        mean_angles_degrees=angles[mask, f].mean(0).tolist() if mask.any() else None,
                        pip_le10_dip_ge60_fraction=float(pattern[mask].mean()) if mask.any() else None,
                        mcp_le15_also_fraction=float(strict[mask].mean()) if mask.any() else None)
                ainds = [ACTIVE_NAMES.index('LH:'+name+s) for s in ('1_x', '2', '3')]
                qinds = [initial['joint_names'].index('LH:'+name+s) for s in ('1_x', '2', '3')]
                actions = z['action'][1:, ainds]
                q, target = z['q'][1:, qinds], z['target'][1:, qinds]
                info['fingers'][name] = dict(conditions=conditions,
                    first_angles_degrees=angles[0, f].tolist(), final_angles_degrees=angles[-1, f].tolist(),
                    action_mean=actions.mean(0).tolist(), action_std=actions.std(0).tolist(),
                    action_negative_fraction=(actions < 0).mean(0).tolist(), action_positive_fraction=(actions > 0).mean(0).tolist(),
                    target_tracking_rms_degrees=np.degrees(np.sqrt(np.mean((target-q)**2, axis=0))).tolist(),
                    final_command_degrees=np.degrees(target[-1]).tolist())
            result['captures'][str(capture['env_id'])] = info
            if capture['env_id'] == 0:
                series = [times, angles, bt]
    (PHASE/'existing_analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(4, 1, figsize=(13, 10), sharex=True)
    times, angles, bt = series
    for f, ax in enumerate(axes):
        for j, label in enumerate(('MCP', 'PIP', 'DIP')):
            ax.plot(times, angles[:, f, j], label=label, lw=1)
        ax.fill_between(times, -45, 100, where=bt[:, f] > 0, alpha=.12, color='green', label='Time-only B eligible')
        ax.set(ylabel=FINGERS[f]+' (deg)', ylim=(-45, 105))
        ax.grid(alpha=.2)
    axes[0].legend(ncol=4, loc='upper right')
    axes[-1].set_xlabel('Song clock (s), actual60Hz completed endpoints; green omits proximity/contact veto')
    fig.suptitle('Original final v19 env0: source-body geometric flexion')
    fig.tight_layout()
    fig.savefig(PHASE/'existing_angles.png', dpi=150)
    plt.close(fig)
    print(json.dumps(dict(all_episodes=len(rows), safe_episodes=len(safe),
        standby_quality={k:v['standby']['eligible_mean_quality'] for k,v in result['all']['fingers'].items()},
        env0_index_patterns=result['captures']['0']['fingers']['index']['conditions']), indent=2))


if __name__ == '__main__':
    main()
