"""CPU-only checkpoint/trace audit; does not import or modify the active package."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root = args.output.resolve()
    assert read(root / 'comparison_completed.json')['completed']
    spec = read(root / 'train/settings.json')['song']['short_learning']
    names = spec['learned_action_names']
    std_slice = slice((spec['finger'] - 1) * 4, spec['finger'] * 4)
    results = []
    pins = {}
    for update in (0, 50, 100, 150, 200, 250, 300):
        checkpoint = root / 'train' / ('initial.pt' if update == 0 else
                     'final.pt' if update == 300 else 'evaluation_%06d.pt' % update)
        pins[str(checkpoint)] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        saved = torch.load(checkpoint, map_location='cpu', weights_only=False)
        raw_logstd = saved['model']['finger_log_std'][std_slice].double().numpy()
        actual_logstd = np.clip(raw_logstd, -5., 2.)
        folder = root / ('evaluation_initial_policy' if update == 0 else 'evaluation_%06d' % update)
        evaluation = read(folder / 'evaluation.json')
        meta = read(folder / 'trace_metadata.json')
        trace = np.load(folder / 'trace_env0_episode0.npz')
        action = trace['policy_action'][:, meta['learned_action_indices']]
        selected_q = [meta['joint_names'].index(name) for name in names]
        q = np.degrees(trace['q'][:, selected_q])
        target = np.degrees(trace['target'][:, selected_q])
        onset, end = spec['view']['local_onset_s'], spec['view']['local_end_s']
        # Each action controls [t_end-dt, t_end); q is sampled at t_end.
        action_start = trace['time_s'] - 1. / 60.
        masks = dict(preparation=action_start < onset,
                     audible_overlap=(action_start < end) & (trace['time_s'] > onset),
                     after_note=action_start >= end)
        action_summary = {key: dict(samples=int(mask.sum()), mean=action[mask].mean(0).tolist(),
                          rms=np.sqrt(np.mean(action[mask] ** 2, axis=0)).tolist())
                          for key, mask in masks.items()}
        episode_names = evaluation['episodes'][0]['angles']['joint_names']
        selected_lh = [episode_names.index(name) for name in names]
        angles = {}
        for key in ('actual_range_rad', 'target_range_rad', 'tracking_error_rms_rad',
                    'tracking_error_max_abs_rad', 'actual_native_limit_fraction',
                    'target_native_limit_fraction'):
            values = np.asarray([e['angles']['values'][key] for e in evaluation['episodes']])[:, selected_lh]
            if key.endswith('_rad'):
                values = np.degrees(values)
            angles[key.replace('_rad', '_deg')] = dict(mean=values.mean(0).tolist(),
                 median=np.median(values, axis=0).tolist(), p95=np.quantile(values, .95, axis=0).tolist(),
                 maximum=values.max(0).tolist(), attempts=len(values))
        rewards = {key: float(np.mean([e['reward_components'][key] for e in evaluation['episodes']]))
                   for key in evaluation['episodes'][0]['reward_components']}
        results.append(dict(update=update, summary=evaluation['summary'], raw_logstd=raw_logstd.tolist(),
            effective_logstd=actual_logstd.tolist(), effective_std=np.exp(actual_logstd).tolist(),
            env0_post_tanh_deterministic_action=action_summary,
            env0_actual_deg_at_first_sample=q[0].tolist(), env0_actual_deg_at_last_sample=q[-1].tolist(),
            env0_target_deg_at_last_sample=target[-1].tolist(), selected_angles_all128=angles,
            mean_episode_reward_terms=rewards,
            mean_episode_total_reward=float(np.mean([e['reward'] for e in evaluation['episodes']]))))
        for filename in ('evaluation.json', 'trace_metadata.json', 'trace_env0_episode0.npz'):
            path = folder / filename
            pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = dict(schema='short_policy_drift.v1', selected_joint_names=names,
        scope='fixed guitar/one middle-finger target/teacher arm/other-finger B/seed7',
        action_scope='post-tanh deterministic mean output, env0 first attempt only; not 128-attempt mean',
        std_scope='latent Gaussian std before tanh; effective clamp[-5,2], not joint displacement std',
        angle_scope='all128 first attempts; 60Hz endpoint samples; native limit tolerance comes from runner',
        checkpoints=results, input_sha256=pins)
    out = root / 'analysis/policy_drift.json'
    with out.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(out)


if __name__ == '__main__':
    main()
