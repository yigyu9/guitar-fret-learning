"""Read-only CPU audit of a completed pair pilot and its native capture."""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch

STUDY = Path(__file__).resolve().parents[1]
MULTI = STUDY.parent
ROOT = next(p for p in STUDY.parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0, str(ROOT))
from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.gpu.finger_reward import finger_target_indices, finger_preparation_gate
from guitar_learning.song.task import make_task

PILOT = MULTI/'학습_인접2지_v1/로그/parallel_v1/pilot_env2/J'
CAPTURE = MULTI/'로그/실제시뮬영상_v1/capture'
BUNDLE = MULTI/'학습_인접2지_v1/입력/song_bundles/index_middle_same'
FINGERS = ('index', 'middle', 'ring', 'pinky')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def document(path):
    return json.loads(Path(path).read_text())


def records(path):
    with (gzip.open if str(path).endswith('.gz') else open)(path, 'rt') as stream:
        return [json.loads(line) for line in stream]


def correlation(a, b):
    return float(np.corrcoef(a, b)[0, 1]) if np.std(a)*np.std(b) > 1e-15 else None


def columns(values):
    x = np.asarray(values, dtype=float)
    return dict(mean=x.mean(0).tolist(), std=x.std(0).tolist(),
                peak_to_peak=(np.max(x, axis=0)-np.min(x, axis=0)).tolist(),
                max_abs=np.abs(x).max(0).tolist())


def temporal(rows, slots):
    # No temporal pair is allowed to cross a reset/episode boundary. One row
    # per completed control tick avoids the four held substeps inflating lag1.
    rows = [r for r in rows if r['substep'] == 4]
    pairs = [(a, b) for a, b in zip(rows, rows[1:])
             if (a['env_id'], a['episode_id']) == (b['env_id'], b['episode_id']) and
             b['control_tick'] == a['control_tick']+1]
    result = columns([np.asarray(r['action'])[slots] for r in rows])
    before = np.asarray([a['action'] for a, _ in pairs])[:, slots]
    after = np.asarray([b['action'] for _, b in pairs])[:, slots]
    result.update(control_samples=len(rows), adjacent_pairs=len(pairs),
        action_lag1=[correlation(before[:, i], after[:, i]) for i in range(len(slots))],
        opposite_sign_fraction=((before*after) < 0).mean(0).tolist())
    return result


def gate_table(task, times):
    now = torch.tensor(times, dtype=torch.float64)
    vectors = {name: torch.tensor([getattr(t, name) for t in task.targets],
        dtype=torch.long if name == 'finger' else torch.float64)
        for name in ('onset_s', 'end_s', 'press_s', 'finger')}
    args = [vectors[n] for n in ('onset_s', 'end_s', 'press_s', 'finger')]
    target = finger_target_indices(now, *args)
    gates = finger_preparation_gate(now, *args,
        torch.zeros(len(times), 4, dtype=torch.bool), torch.full((len(times), 2), .05))
    return [dict(score_time_s=t, targets_exposed=target['valid'][i, :, 0].tolist(),
                 general_events_visible=[bool(n.onset_s <= t+task.lookahead_s and t <= n.end_s+.1)
                                         for n in task.targets],
                 standby_gate=gates['gate'][i].tolist(),
                 approach_tracking_weight=gates['tracking_weight'][i].tolist())
            for i, t in enumerate(times)]


def matched_noise(seed=7, count=12000, std=.049787068367863944):
    """Toy first-order response, not a native/PD identification or intervention."""
    rng = np.random.RandomState(seed)
    iid = rng.normal(size=count)
    held = np.repeat(iid[:count//16], 16)
    command = {name: x/x.std()*std for name, x in [('iid_K1', iid), ('held_K16', held)]}
    result = {}
    for tau in (.05, .10, .20):
        alpha = np.exp(-(1/60.)/tau)
        row = {}
        for name, u in command.items():
            state = 0.; response = []
            for target in u:
                state = alpha*state+(1-alpha)*target
                response.append(state)
            row[name] = dict(command_std=float(u.std()), response_std=float(np.std(response[60:])))
        result[str(tau)] = row
    return dict(seed=seed, samples=count, command_std=std, hold_ticks_comparison=[1, 16],
        model='x_next=exp(-dt/tau)*x+(1-exp(-dt/tau))*absolute_command; dt=1/60; no integration',
        scope='mathematical illustration only; tau uncalibrated; not native reachability, reward or policy success',
        response_by_tau_s=result)


def audit(out):
    torch.set_num_threads(1)
    sources = [PILOT/n for n in ('settings.json', 'report.json', 'initial.pt', 'final.pt',
        'learning_metrics.jsonl', 'episodes.jsonl', 'finger_control_trace.jsonl.gz')]
    sources += [CAPTURE/n for n in ('capture_metadata.json', 'poses_env0000.npz',
        'episode_env0000.json', 'scene/finger_control_trace.jsonl.gz')]
    sources += [ROOT/n for n in ('guitar_learning/training/policy.py',
        'guitar_learning/gpu/control.py', 'guitar_learning/gpu/finger_reward.py',
        'guitar_learning/gpu/finger_skill_environment.py', 'guitar_learning/song/task.py',
        'guitar_learning/tests/test_natural_preparation.py')]
    sources += [p for p in BUNDLE.rglob('*') if p.is_file()]
    sources += [Path(__file__).resolve()]
    pins = {str(p): digest(p) for p in sources}
    settings, run = document(PILOT/'settings.json'), document(PILOT/'report.json')
    metrics, episodes = records(PILOT/'learning_metrics.jsonl'), records(PILOT/'episodes.jsonl')
    trace = records(PILOT/'finger_control_trace.jsonl.gz')
    native_trace = records(CAPTURE/'scene/finger_control_trace.jsonl.gz')
    native_episode_id = document(CAPTURE/'episode_env0000.json')['finger_control_diagnostics']['episode_id']
    native_trace_selected = [r for r in native_trace if r['episode_id'] == native_episode_id]
    checkpoints = [torch.load(PILOT/n, map_location='cpu', weights_only=False)
                   for n in ('initial.pt', 'final.pt')]
    head = {}
    for finger in FINGERS:
        prefix = 'finger_heads.'+finger+'.2.'
        w0, b0 = [checkpoints[0]['model'][prefix+k] for k in ('weight', 'bias')]
        w1, b1 = [checkpoints[1]['model'][prefix+k] for k in ('weight', 'bias')]
        head[finger] = dict(initial_max_abs=float(torch.cat((w0.flatten(), b0)).abs().max()),
            final_parameter_max_abs=float(torch.cat((w1.flatten(), b1)).abs().max()),
            parameter_change_l2=float(torch.cat(((w1-w0).flatten(), b1-b0)).norm()),
            latent_absolute_bound_from_hidden_tanh=(w1.abs().sum(-1)+b1.abs()).tolist(),
            bound_scope='all inputs; final head follows bounded tanh128; parameter max is not policy mean')
    total_transitions = sum(m['transitions'] for m in metrics)
    completed_ticks = {i: sum(e['episode']['steps'] for e in episodes if e['episode']['env_id'] == i)
                       for i in range(settings['num_envs'])}
    ppo = dict(updates=len(metrics), accepted_actor_steps=sum(m['diagnostics']['minibatches']['actor_accepted']['steps'] for m in metrics),
        rejected_actor_steps=sum(m['diagnostics']['minibatches']['actor_rejected']['steps'] for m in metrics),
        kl_retries=sum(m['kl_retries'] for m in metrics), analytic_kl_range=[min(m['analytic_kl'] for m in metrics), max(m['analytic_kl'] for m in metrics)],
        preclip_gradient_norm_range=[min(m['actor_grad_norm'] for m in metrics), max(m['actor_grad_norm'] for m in metrics)],
        ppo_settings=settings['ppo'], final_finger_latent_std=checkpoints[1]['model']['finger_log_std'].exp().tolist(),
        heads=head, initial_updates=checkpoints[0]['updates'], final_updates=checkpoints[1]['updates'])
    task = make_task(BUNDLE, pre_roll_s=3., tail_s=.5)
    metadata = document(CAPTURE/'capture_metadata.json')
    native = np.load(CAPTURE/'poses_env0000.npz')
    per_finger = {}
    for finger in FINGERS:
        slots = [i for i, name in enumerate(trace[0]['joint_names']) if name.startswith('LH:'+finger)]
        native_slots = [metadata['joint_names'].index(trace[0]['joint_names'][i]) for i in slots]
        action_slots = [ACTIVE_NAMES.index(trace[0]['joint_names'][i]) for i in slots]
        observed = [t for row in trace for t in row['targets'] if t['finger'] == finger and t['target_present']]
        per_finger[finger] = dict(training_action=temporal(trace, slots),
            training_actual_rad=columns([np.asarray(r['actual_rad'])[slots] for r in trace]),
            training_requested_rad=columns([np.asarray(r['requested_target_rad'])[slots] for r in trace]),
            first_training_target_exposure_s=min((row['score_time_s'] for row in trace
                if any(t['finger'] == finger and t['target_present'] for t in row['targets'])), default=None),
            training_min_target_distance_m=min((t['pad_distance_m'] for t in observed), default=None),
            training_candidate_samples=sum(t['press_candidate'] for t in observed),
            native_deterministic_action=columns(native['action'][:, action_slots]),
            native_deterministic_actual_rad=columns(native['q'][:, native_slots]),
            native_deterministic_target_rad=columns(native['target'][:, native_slots]))
    result = dict(schema='multi_press.learning_signal_audit.v1', cpu_only=True,
        source_pins=pins, completed_run=run['completed'], original_task=[asdict(t) for t in task.targets],
        general_event_lookahead_s=task.lookahead_s,
        budget=dict(num_envs=settings['num_envs'], horizon=settings['horizon'], updates=len(metrics),
            transitions=total_transitions, raw_ticks_per_env=total_transitions//settings['num_envs'],
            physical_seconds_per_env=total_transitions/settings['num_envs']/60.,
            completed_episode_records=len(episodes), completed_ticks_per_env=completed_ticks,
            partial_ticks_per_env={i: total_transitions//settings['num_envs']-v for i, v in completed_ticks.items()},
            wall_s=run['wall_s']), ppo=ppo,
        reward_component_sums={key: sum(m['reward_component_means'][key]*m['transitions'] for m in metrics)
                               for key in metrics[0]['reward_component_means']},
        episode_summary=[dict(env_id=e['episode']['env_id'], stage_success=e['episode']['song']['stage_success'],
            clean=e['episode']['left_note_ledger']['values']['clean'],
            contact=e['episode']['left_note_ledger']['values']['contact_time'],
            surface_min=e['episode']['left_note_ledger']['values']['surface_min']) for e in episodes],
        trace_scope=dict(training_samples_240hz=len(trace), training_env_ids=sorted(set(r['env_id'] for r in trace)),
            training_last_episode=trace[-1]['episode_id'], training_last_score_s=trace[-1]['score_time_s'],
            native_trace_total_samples_240hz=len(native_trace), native_selected_episode_id=native_episode_id,
            native_selected_samples_240hz=len(native_trace_selected), native_control_samples=len(native['q']),
            native_other_episode_samples_excluded=len(native_trace)-len(native_trace_selected),
            native_checkpoint_sha256=metadata['checkpoint_sha256'],
            matches_completed_final_checkpoint=metadata['checkpoint_sha256'] == digest(PILOT/'final.pt'),
            native_capture_training_updates=metadata['training_updates']),
        fingers=per_finger,
        target_and_gate_timeline=gate_table(task, [0., .995, 1., 1.5, 2.5, 2.55, 2.60, 2.65, 3., 3.3, 4.8]),
        mathematical_noise_comparison=matched_noise(),
        limitations=['No causal attribution from a single short pilot.',
            'Training trace is env0 first600 control ticks, not the complete1280 transition set.',
            'Native deterministic action is recorded tanh(mean); no sampled exploration during capture.',
            'Toy time constant is not fitted to native mechanics; held exploration changes the experimental contract.',
            'Completed episodes and partial-episode training transitions are counted separately.'])
    changed = [name for name, expected in pins.items() if digest(name) != expected]
    if changed:
        raise RuntimeError('Read source changed during audit: '+repr(changed))
    out.mkdir(parents=True, exist_ok=False)
    (out/'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    (out/'invocation.json').write_text(json.dumps(dict(command=sys.argv, input_sha256_verified_after=True,
        torch_device='cpu', native_simulation=False), ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(report=str(out/'report.json'), updates=ppo['updates'],
        accepted_actor_steps=ppo['accepted_actor_steps'], completed_episodes=len(episodes)), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=STUDY/'로그/learning_signal')
    audit(parser.parse_args().out)
