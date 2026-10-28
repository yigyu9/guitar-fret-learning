"""CPU comparison after root confirms four-stage launcher completion."""
import copy
import csv
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DIAG = BASE.parents[1]
ROOT = DIAG.parents[2]
OLD = DIAG/'03_short_learning/other_finger_precheck_v3'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prior = load(OLD/'analysis/analyze.py', 'prior_otherfinger_analysis')
read, sha = prior.read, prior.sha


def main():
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment

    assert not any((HERE/n).exists() for n in ('comparison.json', 'validation.json', 'performance.csv', 'comparison.png'))
    torch.set_num_threads(1)
    reuse = load(BASE/'run_probe.py', 'gain_reused_orchestrator')
    old = reuse.reused()
    hashes, current, checks, rows, details, series = {}, {}, [], [], {}, {}
    def remember(p):
        hashes[str(p)] = sha(p)
    def stat(x):
        return dict(min=np.min(x, axis=0).tolist(), median=np.median(x, axis=0).tolist(), max=np.max(x, axis=0).tolist())
    launcher = read(BASE/'01_launcher.json')
    assert launcher['returncode'] == 0 and read(BASE/'runs/report.json')['completed']
    assert read(OLD/'01_launcher.json')['returncode'] == 0 and read(OLD/'runs/report.json')['completed']
    for root, jobs in ((OLD, old.jobs()), (BASE, reuse.jobs())):
        assert len(read(root/'runs/report.json')['stages']) == len(jobs)
        for job in jobs:
            old.validate(job)
            p = Path(job['out'])
            before = read(p/'inputs_before.json')
            for path, value in before.items():
                if path not in current: current[path] = sha(path)
                assert current[path] == value
            checks.append(dict(stage=str(p), completed=True, closed=True, input_pins=len(before)))
            for n in ('report.json', 'inputs_before.json', 'inputs_after.json', 'gpu_scene_final.json'):
                remember(p/n)
        for p in (root/'01_launcher.json', root/'runs/report.json', root/'preparation_seal.json'):
            remember(p)
    seal = read(BASE/'preparation_seal.json')
    assert all(sha(p) == h for p, h in seal['input_sha256'].items())
    original_model = torch.load(OLD/'runs/index_initial/initial.pt', map_location='cpu', weights_only=False)
    new_model = torch.load(BASE/'runs/index_initial/initial.pt', map_location='cpu', weights_only=False)
    assert original_model['updates'] == new_model['updates'] == 0
    assert len(original_model['model']) == len(new_model['model']) == 73
    assert all(torch.equal(v, new_model['model'][k]) for k, v in original_model['model'].items())
    initial_audit = read(BASE/'runs/actual_initial_verification.json')
    assert initial_audit['same_tensors'] == 73
    for p in (OLD/'runs/index_initial/initial.pt', BASE/'runs/index_initial/initial.pt', BASE/'runs/actual_initial_verification.json'):
        remember(p)
    old_settings = read(OLD/'runs/index_initial/settings.json')
    new_settings = read(BASE/'runs/index_initial/settings.json')
    original_control = old_settings['song']['short_learning']['wrist_control']
    actual_control = new_settings['song']['short_learning']['wrist_control']
    assert sorted(k for k in original_control if original_control[k] != actual_control[k]) == [
        'correction_rate_bound_rad_s', 'correction_step_rad', 'schema']
    assert abs(actual_control['correction_step_rad']-np.deg2rad(.1)) < 1e-15
    assert actual_control['correction_rate_bound_rad_s'] == actual_control['correction_step_rad']*60
    assert original_model['metadata']['settings'] == old_settings and new_model['metadata']['settings'] == new_settings
    normalized = copy.deepcopy(new_settings)
    normalized['song']['short_learning']['wrist_control'] = old_settings['song']['short_learning']['wrist_control']
    assert normalized == old_settings
    old_contract = read(OLD/'runs/index_initial/training_contract.json')
    new_contract = read(BASE/'runs/index_initial/training_contract.json')
    normalized = copy.deepcopy(new_contract)
    for spec in (normalized['task']['short_learning'], normalized['task']['song']['short_learning']):
        spec['wrist_control'] = old_settings['song']['short_learning']['wrist_control']
    assert normalized == old_contract
    metadata, _ = fixture(1)
    for label, root in (('original_0p5', OLD), ('new_0p1', BASE)):
        details[label], series[label] = {}, {}
        for control in ('reference', 'zero', 'random'):
            folder = root/'runs'/('index_'+control)
            settings, meta = read(folder/'settings.json'), read(folder/'trace_metadata.json')
            assert settings == (old_settings if label == 'original_0p5' else new_settings)
            result = read(folder/'evaluation.json')
            assert result['condition'] == control and not result['policy_performance']
            episodes = result['episodes']
            summary = dict(episodes=4, achieved_fraction=sum(e['achieved'] for e in episodes)/4,
                mean_clean_fraction=sum(e['clean_fraction'] for e in episodes)/4,
                mean_audible_wrong_fraction=sum(e['audible_wrong_fraction'] for e in episodes)/4,
                physical_failure_fraction=sum(e['termination']['physical_failure'] for e in episodes)/4,
                wrist_failure_fraction=sum(e['termination']['wrist_failure'] for e in episodes)/4,
                any_failure_fraction=sum(e['reason'] == 'terminal_failure' for e in episodes)/4)
            assert all(abs(result['summary'][k]-v) < 1e-12 for k, v in summary.items())
            rows.append(dict(condition=label, control=control, achieved=round(summary['achieved_fraction']*4), **summary))
            t = np.load(folder/'trace_env0_episode0.npz')
            assert meta['joint_names'] == metadata['joint_names'] and meta['body_names'] == metadata['body_names']
            spec = settings['song']['short_learning']; view = spec['view']
            arm_names = old_contract['action']['names'][:12]
            arm = [meta['joint_names'].index(n) for n in arm_names]
            selected = [meta['joint_names'].index(n) for n in spec['learned_action_names']]
            torso_names = [n for n in meta['joint_names'] if n.startswith(('Torso_', 'Spine_', 'Chest_'))]
            torso = [meta['joint_names'].index(n) for n in torso_names]
            g, w, distal, thumb = [meta['body_names'].index(n) for n in ('guitar/guitar', 'human/L_Wrist', 'human/LH:index3', 'human/LH:thumb3')]
            gr = Rotation.from_quat(t['body_state'][:, g, 3:7])
            wrist_G = gr.inv().apply(t['body_state'][:, w, :3]-t['body_state'][:, g, :3])
            actual_R = gr.inv()*Rotation.from_quat(t['body_state'][:, w, 3:7])
            pe = np.linalg.norm(t['wrist_goal_G_m']-wrist_G, axis=1)*1000
            re = np.rad2deg((Rotation.from_quat(t['wrist_goal_G_xyzw']).inv()*actual_R).magnitude())
            request, target, q = t['wrist_requested_arm_rad'], t['target'][:, arm], t['q'][:, arm]
            base = np.array([spec['teacher']['arm_targets_rad'][n] for n in arm_names])
            delta_cap = spec['wrist_control']['correction_step_rad']
            assert abs(t['wrist_requested_delta_rad']).max() <= delta_cap+1e-7
            alpha = np.array(old_contract['action']['target_contract']['smoothing_alpha'][:12])
            alpha_residual = float(abs(target[1:]-(target[:-1]+alpha*(request[1:]-target[:-1]))).max())
            assert alpha_residual < 1e-6
            arrays = dict(position_error_mm=pe, rotation_error_deg=re,
                request_submitted_max_gap_deg=np.rad2deg(abs(request-target)).max(1),
                submitted_actual_max_gap_deg=np.rad2deg(abs(target-q)).max(1),
                request_actual_max_gap_deg=np.rad2deg(abs(request-q)).max(1),
                nearest_pad_distance_mm=t['surface_distance_m']*1000,
                distal_resultant_N=np.linalg.norm(t['net_body_force_n'][:, distal], axis=1),
                thumb_resultant_N=np.linalg.norm(t['net_body_force_n'][:, thumb], axis=1))
            env = ShortEnvironment(metadata, bundle=settings['song_training']['bundle'], song=settings['song'], skill=settings['finger_skill'], device='cpu')
            def snapshot(i):
                return dict(q=torch.tensor(t['q'][i:i+1]), qd=torch.zeros(1, 105), target=torch.tensor(t['target'][i:i+1]),
                    body_state=torch.tensor(t['body_state'][i:i+1]), contact_force=torch.tensor(t['net_body_force_n'][i:i+1]))
            env.reset([0], snapshot(0)); j = env.selected_index
            gates, rear, rear_valid, rear_signed = [], [], [], []
            unit = env.thumb_support_plane[:3].numpy(); unit = unit/np.linalg.norm(unit)
            thumb_force_G = gr.inv().apply(t['net_body_force_n'][:, thumb])
            for i, now in enumerate(t['time_s']):
                env.clock[0] = round(now*240); env._snapshot(snapshot(i))
                assert bool(env.candidate[0, j]) == t['candidate'][i] and bool(env.wrong[0, j]) == t['wrong'][i]
                assert abs(float(env.surface_distance[0, j])-t['surface_distance_m'][i]) < 1e-6
                gates.append([bool(v[0, j]) for v in (env.surface_body_loaded, env.contact_geometry, env.contact_facing, env.contact_loaded_target, env.candidate, env.wrong)])
                rear.append(float(env.thumb_support['normal_load'][0])); rear_valid.append(bool(env.thumb_support['normal_load_valid'][0]))
                rear_signed.append(float(thumb_force_G[i]@unit))
            arrays.update(thumb_rear_normal_load_N=np.array(rear), thumb_signed_rear_force_N=np.array(rear_signed))
            phases = dict(before=t['time_s'] < 3-1e-9,
                audible=(t['time_s'] >= 3-1e-9) & (t['time_s'] <= view['local_end_s']+1e-9),
                after=t['time_s'] > view['local_end_s']+1e-9,
                tracking_2_to_3p67=(t['time_s'] >= 2-1e-9) & (t['time_s'] <= 3.67))
            phase_rows = {}
            for phase, mask in phases.items():
                phase_rows[phase] = dict(endpoint_count=int(mask.sum()), scalar_stats={k:stat(v[mask]) for k, v in arrays.items()},
                    gate_counts=dict(zip(('loaded', 'any_position', 'any_position_facing', 'positive', 'candidate', 'wrong'), np.array(gates)[mask].sum(0).tolist())),
                    selected_actual_deg=stat(np.rad2deg(t['q'][mask][:, selected])), selected_target_deg=stat(np.rad2deg(t['target'][mask][:, selected])),
                    arm_request_minus_target_deg=stat(np.rad2deg(request[mask]-target[mask])),
                    arm_target_minus_actual_deg=stat(np.rad2deg(target[mask]-q[mask])),
                    torso_actual_deg=stat(np.rad2deg(t['q'][mask][:, torso])), thumb_rear_load_valid_count=int(np.array(rear_valid)[mask].sum()))
            mask = phases['tracking_2_to_3p67']
            lo = np.array(old_contract['action']['target_contract']['action_lower_rad'][:12])
            hi = np.array(old_contract['action']['target_contract']['action_upper_rad'][:12])
            bounds = {key:dict(lower_counts=(abs(value[mask]-lo) <= 1e-6).sum(0).tolist(),
                upper_counts=(abs(value[mask]-hi) <= 1e-6).sum(0).tolist())
                for key, value in (('request', request), ('submitted_target', target))}
            details[label][control] = dict(phases=phase_rows, arm_names=arm_names, torso_names=torso_names,
                arm_action_bound_counts_2_to_3p67=bounds,
                bounded_correction_reconstructed_deg=stat(np.rad2deg(request[mask]-base)),
                bounded_correction_start_end_deg=np.rad2deg((request[mask]-base)[[0, -1]]).tolist(),
                final_arm_deg=dict(request=np.rad2deg(request[-1]).tolist(), submitted_target=np.rad2deg(target[-1]).tolist(), actual=np.rad2deg(q[-1]).tolist()),
                alpha_reconstruction_max_residual_rad=alpha_residual, original_note_view=view,
                native_episode_notes=[dict(env_id=e['env_id'], achieved=e['achieved'], note=e['note'], termination=e['termination']) for e in episodes])
            series[label][control] = dict(time=t['time_s'], **arrays)
            for n in ('evaluation.json', 'trace_env0_episode0.npz', 'trace_metadata.json', 'settings.json', 'training_contract.json'):
                remember(folder/n)
    assert len(checks) == 16 and not torch.cuda.is_initialized()
    data = dict(summary=rows, env0=details, scope='24 assigned attempts, original240Hz musical ledger; env0 trace60Hz only; no trained-policy claim or additional gain search',
        force_scope='distal/thumb net body resultants; rear signed component uses source rear normal, helper normal_load is rectified and selected-valid gated; no pair pressure/string force or causal contribution',
        correction_scope='reconstructed request minus fixed feedforward after2s, not independently saved memory; logged delta is post-step-cap and pre-request-bound/rate clipping')
    validation = dict(completed=True, stage_checks=checks, all16_scenes_closed=True, new_launcher_returncode=0,
        new_outer_wall_s=launcher['wall_s'], all_initial_tensors_exact=73, settings_and_contract_only_three_control_fields=True,
        current_input_paths=len(current), preparation_pins=len(seal['input_sha256']), input_sha256=hashes,
        script_sha256=sha(Path(__file__)), GPU_executed=False, CUDA_initialized=False)
    for name, value in (('comparison.json', data), ('validation.json', validation)):
        with (HERE/name).open('x') as f: json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')
    with (HERE/'performance.csv').open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    plt.rcParams['font.family'] = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
    for label in details:
        s = series[label]['reference']; use = (s['time'] >= 2-1e-9) & (s['time'] <= 3.67)
        for ax, key, title in zip(axes.flat, ('position_error_mm', 'rotation_error_deg', 'request_submitted_max_gap_deg', 'submitted_actual_max_gap_deg'),
                ('손목 위치 오차 (mm)', '손목 회전 오차 (도)', '요청→제출 target 최대차 (도)', '제출 target→actual 최대차 (도)')):
            ax.plot(s['time'][use], s[key][use], label=label); ax.set_title(title); ax.grid(alpha=.2); ax.axvline(3, color='gray', ls='--', lw=.8)
    axes[0, 0].legend(fontsize=8)
    for ax in axes[1]: ax.set_xlabel('로컬 시간 (초)')
    fig.suptitle('검지 reference · env0 60Hz · 원래0.5도 vs고정0.1도/tick')
    fig.tight_layout(); fig.savefig(HERE/'comparison.png', dpi=140); plt.close(fig)
    print(json.dumps(dict(completed=True, rows=rows, current_paths=len(current), CUDA_initialized=False)))


if __name__ == '__main__':
    main()
