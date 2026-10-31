"""Summarize the finite v5 pilot and paired native evaluation without editing runs."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def inspect_run(name):
    out = BASE/name
    report, attempt, config = [read(out/n) for n in ('report.json','attempt.json','config.json')]
    kept = config['identity']['environment']['remaining27_indices']
    initial = read(out/'initial_state.json')
    q0 = np.array([v['pos'] for v in initial['human_dof_states']])
    count = active = 0
    reward = cost = squared_error = 0.
    max_displacement = max_rotation = max_velocity_residual = 0.
    targets_preserved = effort_targets_agree = finite = True
    for line in (out/'transitions.jsonl').open():
        row = json.loads(line)
        info = row['info']
        count += 1
        reward += row['reward']
        cost += row['cost']
        max_displacement = max(max_displacement, info['guitar_displacement_m'])
        max_rotation = max(max_rotation, info['guitar_rotation_rad'])
        max_velocity_residual = max(max_velocity_residual, info['effort_control']['velocity_error_m_s'])
        targets = np.array(info['submitted_target81_rad'])
        targets_preserved &= bool(np.array_equal(targets[kept], q0[kept]))
        effort_targets_agree &= info['effort_control']['target81_rad'] == info['submitted_target81_rad']
        finite &= bool(np.isfinite(np.r_[targets, row['reward'], row['cost']]).all())
        if info['clock']['physics_time_s'] > 2.:
            active += 1
            squared_error += info['goal_error_squared_m2']
    metrics = [json.loads(line) for line in (out/'metrics.jsonl').open()]
    episodes = [r for r in metrics if r['kind']=='episode']
    updates = [r for r in metrics if r['kind']=='update']
    hashes = attempt['input_sha256']
    changed = [p for p,h in hashes.items() if not Path(p).is_file() or sha(p)!=h]
    loaded = set(report['loaded_project_python_modules'].values())
    loaded_changes = [p for p in changed if p in loaded]
    non_python_changes = [p for p in changed if Path(p).suffix!='.py']
    copies = []
    for p,h in hashes.items():
        original = Path(p)
        if original.suffix in ('.py','.sh') and ROOT in original.parents:
            copy = out/'source_before'/original.relative_to(ROOT)
            copies.append(copy.is_file() and sha(copy)==h)
    videos = {}
    if report['videos']:
        capture = read(out/'capture.json')
        for view,video in report['videos'].items():
            videos[view] = dict(path=video['path'], frames=int(video['stream']['nb_read_frames']),
                               sha_matches=sha(video['path'])==video['sha256'])
        videos['capture'] = dict(frames=len(capture['frames']),
            initial_physics_step=capture['frames'][0]['physics_step'],
            final_physics_step=capture['frames'][-1]['physics_step'],
            all_render_states_preserved=all(f['render_preserves_states'] for f in capture['frames']),
            all_frame_hashes_match=all(sha(p)==h for f in capture['frames'] for p,h in f['image_sha256'].items()))
    return dict(run=name, original_report_completed=report['completed'], failure=report['failure'],
        collected_control_steps=count, completed_updates=len(updates), completed_episodes=len(episodes),
        terminated_episodes=sum(e['terminated'] for e in episodes), reward_sum=reward, cost_sum=cost,
        active_palm_RMS_mm=1000*math.sqrt(squared_error/active) if active else None,
        max_guitar_actor_root_displacement_mm=1000*max_displacement,
        max_guitar_rotation_deg=math.degrees(max_rotation),
        max_recorded_velocity_validation_error_m_s=max_velocity_residual,
        kept27_targets_exact=targets_preserved, effort_targets_agree=effort_targets_agree,
        finite_transition_values=finite, forbidden_calls=report['forbidden_calls'],
        current_changed_inputs=changed, changed_loaded_python_modules=loaded_changes,
        changed_non_python_inputs=non_python_changes,
        source_before_all_exact=all(copies), source_before_count=len(copies), videos=videos,
        environment_ABI=config['identity']['environment'], seed=attempt['arguments']['seed'])


def main():
    names = ('pilot64_v5','heldout_baseline_v5','heldout_eval_v5')
    inputs = {str(Path(__file__).resolve()):sha(__file__)}
    for name in names:
        for file in (BASE/name).iterdir():
            if file.is_file(): inputs[str(file)] = sha(file)
    result = {name:inspect_run(name) for name in names}
    start = torch.load(BASE/'pilot64_v5/checkpoint_0000.pt',map_location='cpu',weights_only=False)
    final = torch.load(BASE/'pilot64_v5/checkpoint_0064.pt',map_location='cpu',weights_only=False)
    changes = {}
    for prefix in ('encoder','actor_heads.0','actor_heads.1','actor_heads.2','reward_critic','cost_critic'):
        changes[prefix] = max(float((final['model'][k]-v).abs().max()) for k,v in start['model'].items() if k.startswith(prefix+'.'))
    train,baseline,evaluation = [result[name] for name in names]
    checks = dict(
        no_run_exception=all(r['failure'] is None for r in result.values()),
        training_budget_completed=train['completed_updates']==64 and train['collected_control_steps']==16384 and final['updates']==64,
        all_policy_and_value_components_changed=all(v>0 for v in changes.values()),
        paired_evaluation_ABI=train['environment_ABI']==baseline['environment_ABI']==evaluation['environment_ABI'],
        paired_goal_seed=baseline['seed']==evaluation['seed']==9002,
        heldout_goal_seed=not 101<=evaluation['seed']<=101+train['completed_episodes'],
        full_paired_episodes=all(r['collected_control_steps']==300 and r['terminated_episodes']==0 for r in (baseline,evaluation)),
        no_forbidden_API_calls=all(not r['forbidden_calls'] for r in result.values()),
        action_and_values_valid=all(r['kept27_targets_exact'] and r['effort_targets_agree'] and r['finite_transition_values'] for r in result.values()),
        consumed_source_and_data_unchanged=all(not r['changed_loaded_python_modules'] and not r['changed_non_python_inputs'] for r in result.values()),
        source_snapshots_exact=all(r['source_before_all_exact'] for r in result.values()),
    )
    for r in result.values(): del r['environment_ABI']
    unchanged = all(sha(p)==h for p,h in inputs.items())
    output = dict(checks=checks, analysis_inputs_unchanged=unchanged, input_sha256=inputs,
                  runs=result, parameter_max_abs_changes=changes,
                  scope='One Stage-A pilot and one paired held-out goal. No music, human similarity, or general safety claim.')
    with (BASE/'pilot_v5_analysis.json').open('x') as stream:
        json.dump(output,stream,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps(dict(checks=checks,analysis_inputs_unchanged=unchanged),ensure_ascii=False))
    if not all(checks.values()) or not unchanged: raise RuntimeError('pilot verification has unmet checks; inspect preserved analysis')


if __name__=='__main__': main()
