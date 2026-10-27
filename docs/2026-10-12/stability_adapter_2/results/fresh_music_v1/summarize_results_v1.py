"""Read completed native runs and verify the exported actual-state trajectories."""
import hashlib
import json
import statistics
from pathlib import Path

import torch

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.open()]


def save(name, value):
    with (BASE / name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)


names = ('pilot_b16_v4', 'baseline_b_v4', 'eval_b16_v4', 'baseline_d_v4')
inputs = [Path(__file__)]
for name in names:
    inputs += [BASE / name / n for n in ('report.json', 'attempt.json', 'transitions.jsonl', 'initial_state.json', 'capture.json')
               if (BASE / name / n).exists()]
inputs += list((BASE / 'pilot_b16_v4').glob('checkpoint_*.pt'))
inputs += [BASE / 'pilot_b16_v4/metrics.jsonl']
for name in names[1:]:
    inputs += [BASE / ('motion_' + name) / n for n in ('manifest.json', 'motion.jsonl')]
before = {str(path): sha(path) for path in inputs}
save('analysis_inputs_before.json', before)
result = {}
for name in names:
    run = BASE / name
    report = read(run / 'report.json')
    assert report['completed'] and not report['changed_inputs'] and not report['process_counters']['forbidden_calls']
    history = rows(run / 'transitions.jsonl')
    assert len(history) == report['process_counters']['valid_controls']
    final = history[-1]['info']
    audible = [f['distance_m'] for row in history for f in row['info']['fret_rows'] if f['audible_hold_required']]
    entry = dict(completed=True, controls=len(history), training_cumulative=report['cumulative'],
                 performed_updates=report['performed_updates'], reward_sum=sum(r['reward'] for r in history),
                 cost_sum=sum(r['cost'] for r in history),
                 audible_fret_marker_distance_mean_mm=1000 * statistics.mean(audible) if audible else None,
                 final_physics_time_s=final['clock']['physics_time_s'],
                 final_press_hold_release=final['press_hold_release'],
                 final_press_hold_release_candidate_complete=final['press_hold_release_candidate_complete'],
                 final_matched_string_targets=final['matched_string_targets'],
                 final_total_string_targets=final['total_string_targets'],
                 max_position_outside_m=max(max(r['info']['position_outside_m']) for r in history),
                 max_rotation_feasible_upper_rad=max(r['info']['rotation_envelope']['upper_rad'] for r in history))
    if name != 'pilot_b16_v4':
        capture = read(run / 'capture.json')['frames']
        assert capture[0]['physics_step'] == 0 and capture[-1]['physics_step'] == final['clock']['physics_step']
        assert all(f['render_preserves_states'] for f in capture)
        for video in report['videos'].values():
            assert sha(Path(video['path'])) == video['sha256']
            assert int(video['stream']['nb_read_frames']) == len(capture)
        motion_dir = BASE / ('motion_' + name)
        manifest = read(motion_dir / 'manifest.json')
        motion = rows(motion_dir / 'motion.jsonl')
        assert len(motion) == len(history) + 1 == manifest['frames']
        assert sha(motion_dir / 'motion.jsonl') == manifest['motion_sha256']
        initial = read(run / 'initial_state.json')
        assert motion[0]['q81_rad'] == [r['pos'] for r in initial['human_dof_states']]
        assert motion[0]['qdot81_rad_s'] == [r['vel'] for r in initial['human_dof_states']]
        assert motion[0]['guitar_root_body_state'] == initial['guitar_body_states'][0]
        for frame, row in zip(motion[1:], history):
            assert all(frame[k] == row['info']['native_motion'][k] for k in ('q81_rad', 'qdot81_rad_s', 'guitar_root_body_state'))
            assert frame['physics_time_s'] == row['info']['clock']['physics_time_s']
        assert all(sha(run / n) == digest for n, digest in manifest['source_input_sha256'].items())
        entry.update(video_frames_per_view=len(capture), motion_frames=len(motion), motion_exact_roundtrip=True)
    result[name] = entry

initial = torch.load(BASE / 'pilot_b16_v4/checkpoint_0000.pt', map_location='cpu', weights_only=False)
trained = torch.load(BASE / 'pilot_b16_v4/checkpoint_0016.pt', map_location='cpu', weights_only=False)
assert initial['updates'] == 0 and trained['updates'] == 16
assert torch.equal(initial['model']['log_std'], torch.full((54,), -3.))
assert all(torch.count_nonzero(t) == 0 for k, t in initial['model'].items() if k.startswith('actor_heads'))
delta = {k: float((v - initial['model'][k]).abs().max()) for k, v in trained['model'].items()}
assert all(torch.isfinite(v).all() for v in trained['model'].values())
metrics = rows(BASE / 'pilot_b16_v4/metrics.jsonl')
evaluation = read(BASE / 'eval_b16_v4/attempt.json')
checkpoint = BASE / 'pilot_b16_v4/checkpoint_0016.pt'
assert evaluation['arguments']['checkpoint'] == str(checkpoint)
assert evaluation['input_sha256'][str(checkpoint)] == sha(checkpoint)
result['learning_audit'] = dict(initial_actor_heads_zero=True, initial_log_std=-3.,
    parameter_max_abs_changes=delta, learned_log_std_min=float(trained['model']['log_std'].min()),
    learned_log_std_max=float(trained['model']['log_std'].max()),
    approx_kl_min=min(r['losses']['approx_kl'] for r in metrics),
    approx_kl_max=max(r['losses']['approx_kl'] for r in metrics),
    target_kl=.03, target_kl_scope='post-epoch stop criterion, not a hard bound',
    eval_exact_checkpoint=True, evaluation_scope='same B event, single deterministic evaluation; no held-out task claim')
assert all(sha(Path(path)) == digest for path, digest in before.items())
result['analysis_inputs_unchanged'] = True
save('analysis_v1.json', result)
print(json.dumps(result, ensure_ascii=False, indent=2))
