"""Read completed pair-isolation outputs only; CPU snapshot analysis, no native launch."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
FIX = HERE.parent
DIAG = FIX.parents[1]
ROOT = DIAG.parents[2]
CONDITIONS = ('baseline', 'refilter')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true')
    args = parser.parse_args()
    if not args.root_completed:
        print('No raw read or result created; root completion handoff required.')
        return
    sys.path.insert(0, str(ROOT))
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    from guitar_learning.gpu.wrong_press import WRONG_PRESS_CONTRACT
    torch.set_num_threads(1)
    out = HERE/'results_v1'
    if out.exists() or out.is_symlink():
        raise FileExistsError(str(out))
    hashes = {}

    def remember(path):
        hashes[str(path)] = sha(path)
        return read(path)

    def stats(x):
        x = np.asarray(x, dtype=np.float64)
        assert np.isfinite(x).all()
        return dict(min=x.min(axis=0).tolist(), p50=np.percentile(x, 50, axis=0).tolist(),
            p95=np.percentile(x, 95, axis=0).tolist(), max=x.max(axis=0).tolist()) if x.size else None

    seal = remember(FIX/'preparation_seal.json')
    assert seal['independent_review'] == 'passed_no_findings'
    assert len(seal['input_pins']) == 677
    assert all(Path(p).is_file() and sha(p) == h for p, h in seal['input_pins'].items())
    launcher = remember(FIX/'01_launcher.json')
    assert launcher['completed'] and launcher['returncode'] == 0
    assert [j['condition'] for j in launcher['jobs']] == list(CONDITIONS)
    metadata, _ = fixture(1)
    results, traces, scenes, contracts, configurations, curves = {}, {}, {}, {}, {}, {}
    rows, force_rows, gate_rows, reward_residuals = [], [], [], []
    for condition in CONDITIONS:
        folder = FIX/'runs'/condition
        child_launcher = remember(FIX/('01_'+condition+'_launcher.json'))
        assert child_launcher['returncode'] == 0
        report, scene, before, after, setting, contract, meta, evaluation, collision = [remember(folder/name)
            for name in ('report.json', 'gpu_scene_final.json', 'inputs_before.json', 'inputs_after.json',
                         'settings.json', 'training_contract.json', 'trace_metadata.json', 'evaluation.json',
                         'collision_condition.json')]
        assert report['completed'] and report['closed'] and report['failure'] is None
        assert report['close_failure'] is None and report['wrapper_calls'] == 1 and report['wrapper_restored']
        assert not report['changed_inputs'] and not report['unpinned_project_sources']
        assert after['verified'] and before == after['input_pins']
        assert not after['changed_paths'] and not after['unpinned_project_sources']
        assert all(Path(p).is_file() and sha(p) == h for p, h in before.items())
        assert before[str(FIX/'preparation_seal.json')] == sha(FIX/'preparation_seal.json')
        assert scene['closed'] and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
        assert scene['environment_count'] == scene['hand_collision_native_readback_environments'] == 4
        assert scene['diagnostic_guitar_mode'] == 'fixed'
        assert collision == remember(FIX/'cpu_inputs'/(condition+'_collision.json'))
        assert scene['hand_collision'] == collision['submitted_contract']
        assert contract['native_backend']['hand_collision'] == collision['submitted_contract']
        assert len(collision['baseline_matrix']) == len(collision['submitted_matrix']) == 1485
        changes = [(a, b) for a, b in zip(collision['baseline_matrix'], collision['submitted_matrix']) if a[-1] != b[-1]]
        assert len(changes) == int(condition == 'refilter')
        for key in ('baseline_matrix', 'submitted_matrix'):
            encoded = json.dumps(collision[key], separators=(',', ':')).encode()
            assert hashlib.sha256(encoded).hexdigest() == collision[key+'_sha256']
        assert collision['external_pair_changes'] == 0 and collision['nonfilter_properties_exact']
        assert collision['submitted_contract']['enabled_distinct_finger_pairs'] == (90 if condition == 'baseline' else 89)
        episodes = evaluation['episodes']
        assert evaluation['condition'] == 'reference' and not evaluation['policy_performance']
        assert evaluation['assigned_quotas'] == [1]*4 and len(episodes) == 4
        assert sorted(e['env_id'] for e in episodes) == list(range(4))
        assert evaluation['summary'] == summary(episodes)
        short = setting['song']['short_learning']; view = short['view']
        assert all(e['target_id'] == short['teacher']['source_target_id'] and e['selected_target_count'] == 1 for e in episodes)
        assert scene['physics_steps'] == 4*max(e['steps'] for e in episodes) <= 4*view['duration_ticks']
        for episode in episodes:
            terms = episode['reward_components']
            assert len(terms) == 9
            residual = sum(terms.values()) - episode['reward']
            tolerance = np.finfo(np.float32).eps*(episode['steps']+1)*max(1., sum(abs(v) for v in terms.values()))
            assert abs(residual) <= tolerance
            reward_residuals.append(dict(condition=condition, env_id=episode['env_id'],
                sum9_minus_reward=residual, float32_accumulation_tolerance=tolerance))
            rows.append(dict(condition=condition, env_id=episode['env_id'], achieved=episode['achieved'],
                clean=episode['clean_fraction'], wrong=episode['audible_wrong_fraction'],
                failure=episode['reason'] == 'terminal_failure', reward=episode['reward']))
        trace_path = folder/'trace_env0_episode0.npz'; hashes[str(trace_path)] = sha(trace_path)
        t = np.load(trace_path, allow_pickle=False)
        assert meta['joint_names'] == metadata['joint_names'] and meta['body_names'] == metadata['body_names']
        local = t['time_s']; n = len(local)
        assert np.allclose(local, np.arange(1, n+1)/60, rtol=0, atol=5e-7)
        assert np.max(abs(t['source_time_s']-local-view['score_offset_s'])) < 1e-9
        e0 = next(e for e in episodes if e['env_id'] == 0)
        assert n == e0['steps']
        safe = np.ones(n, dtype=bool)
        if e0['reason'] == 'terminal_failure':
            safe[-1] = False
        selected = [meta['joint_names'].index(name) for name in short['learned_action_names']]
        arm = list(range(39, 51))
        names = ['human/LH:index'+str(i) for i in (1, 2, 3)] + ['human/LH:middle1']
        body_ids = [meta['body_names'].index(name) for name in names]
        force = t['net_body_force_n'][:, body_ids].astype(np.float64)
        force_path = folder/'pair_forces_env0.npz'; hashes[str(force_path)] = sha(force_path)
        saved = np.load(force_path, allow_pickle=False)
        assert saved['body_names'].tolist() == names and saved['body_indices'].tolist() == body_ids
        assert np.array_equal(saved['time_s'], local) and np.array_equal(saved['force_W_n'], force)
        assert np.array_equal(saved['resultant_n'], np.linalg.norm(force, axis=-1))
        wrist, guitar = [meta['body_names'].index(name) for name in ('human/L_Wrist', 'guitar/guitar')]
        rg = Rotation.from_quat(t['body_state'][:, guitar, 3:7])
        wrist_g = rg.inv().apply(t['body_state'][:, wrist, :3] - t['body_state'][:, guitar, :3])
        wrist_r = rg.inv()*Rotation.from_quat(t['body_state'][:, wrist, 3:7])
        data = dict(resultant_n=np.linalg.norm(force, axis=-1), force_W_n=force,
            actual_selected_deg=np.rad2deg(t['q'][:, selected]), target_selected_deg=np.rad2deg(t['target'][:, selected]),
            target_minus_actual_deg=np.rad2deg((t['target']-t['q'])[:, selected]),
            nearest_distance_mm=t['surface_distance_m']*1000, nearest_height_mm=t['surface_height_m']*1000,
            wrist_position_error_mm=np.linalg.norm(t['wrist_goal_G_m']-wrist_g, axis=1)*1000,
            wrist_rotation_error_deg=np.rad2deg((Rotation.from_quat(t['wrist_goal_G_xyzw']).inv()*wrist_r).magnitude()),
            index1_plus_middle1_norm_n=np.linalg.norm(force[:, 0]+force[:, 3], axis=-1),
            index2_plus_middle1_norm_n=np.linalg.norm(force[:, 1]+force[:, 3], axis=-1))
        # Original predicate reuse at stored endpoints; no music update or fabricated 240Hz replay.
        env = ShortEnvironment(metadata, bundle=setting['song_training']['bundle'], song=setting['song'],
            skill=setting['finger_skill'], device='cpu')
        def snapshot(i):
            return dict(q=torch.tensor(t['q'][i:i+1]), qd=torch.zeros(1, 105), target=torch.tensor(t['target'][i:i+1]),
                body_state=torch.tensor(t['body_state'][i:i+1]), contact_force=torch.tensor(t['net_body_force_n'][i:i+1]))
        env.reset([0], snapshot(0)); gates = []
        for i, now in enumerate(local):
            env.clock[0] = round(now*240); env._snapshot(snapshot(i)); j = env.selected_index
            assert bool(env.candidate[0, j]) == bool(t['candidate'][i])
            assert bool(env.wrong[0, j]) == bool(t['wrong'][i])
            assert abs(float(env.surface_distance[0, j])-t['surface_distance_m'][i]) < 1e-6
            assert abs(float(env.surface_height[0, j])-t['surface_height_m'][i]) < 1e-6
            gates.append(dict(loaded=bool(env.surface_body_loaded[0, j]), position=bool(env.contact_geometry[0, j]),
                position_facing=bool(env.contact_facing[0, j]), positive=bool(env.contact_loaded_target[0, j]),
                candidate=bool(env.candidate[0, j]), wrong=bool(env.wrong[0, j]),
                nearest_cos=float(env.surface_alignment[0, j]), wrong_source_flags=env.wrong_source_flags[0, j].tolist()))
        data['nearest_normal_cos'] = np.array([g['nearest_cos'] for g in gates])
        phases = dict(ramp=local < 2-1e-9, postramp_before=(local >= 2-1e-9) & (local < 3-1e-9),
            audible=(local >= view['local_onset_s']-1e-9) & (local <= view['local_end_s']+1e-9),
            after=local > view['local_end_s']+1e-9)
        phase_stats = {}
        for phase, mask in phases.items():
            valid = mask & safe
            phase_stats[phase] = dict(raw_endpoints=int(mask.sum()), prefailure_endpoints=int(valid.sum()),
                statistics={key: stats(value[valid]) for key, value in data.items()},
                gates={key: sum(gates[i][key] for i in np.flatnonzero(valid))
                    for key in ('loaded', 'position', 'position_facing', 'positive', 'candidate', 'wrong')},
                wrong_provenance_counts=np.asarray([g['wrong_source_flags'] for g in gates], dtype=int)[valid].sum(0).tolist())
            for bi, name in enumerate(names):
                f = np.linalg.norm(force[valid, bi], axis=-1)
                if len(f):
                    force_rows.append(dict(condition=condition, phase=phase, body=name, endpoints=len(f),
                        p50_N=float(np.percentile(f, 50)), p95_N=float(np.percentile(f, 95)), max_N=float(f.max())))
            gate_rows.append(dict(condition=condition, phase=phase, **phase_stats[phase]['gates']))
        results[condition] = dict(summary=evaluation['summary'], episodes=episodes, body_order=names,
            selected_joint_order=short['learned_action_names'], phases=phase_stats,
            reward_component_means={key: sum(e['reward_components'][key] for e in episodes)/4
                for key in episodes[0]['reward_components']},
            wrong_body_order=[meta['body_names'][int(i)] for i in env.finger_indices],
            wrong_cause_order=WRONG_PRESS_CONTRACT['causes'], gate_samples=gates,
            terminal_failure_endpoint_excluded=not bool(safe[-1]))
        traces[condition] = t; scenes[condition] = scene; contracts[condition] = contract; configurations[condition] = setting
        curves[condition] = dict(time_s=local, **data)
    assert len(rows) == 8
    assert configurations['baseline'] == configurations['refilter']
    stripped = [{k: v for k, v in scenes[c].items() if k != 'hand_collision'} for c in CONDITIONS]
    assert stripped[0] == stripped[1]
    cb, cr = [json.loads(json.dumps(contracts[c])) for c in CONDITIONS]
    cb['native_backend'].pop('hand_collision'); cr['native_backend'].pop('hand_collision')
    assert cb == cr
    a, b = traces['baseline'], traces['refilter']
    assert np.array_equal(a['time_s'], b['time_s'])
    selected = [metadata['joint_names'].index(n) for n in configurations['baseline']['song']['short_learning']['learned_action_names']]
    actions = configurations['baseline']['song']['short_learning']['learned_action_indices']
    pair = dict(selected_target_exact=np.array_equal(a['target'][:, selected], b['target'][:, selected]),
        selected_executed_action_exact=np.array_equal(a['executed_action'][:, actions], b['executed_action'][:, actions]),
        actual_q_max_difference_deg=np.rad2deg(abs(a['q'][:, selected]-b['q'][:, selected])).max(axis=0).tolist(),
        arm_target_max_difference_deg=float(np.rad2deg(abs(a['target'][:, 39:51]-b['target'][:, 39:51])).max()),
        arm_request_max_difference_deg=float(np.rad2deg(abs(a['wrist_requested_arm_rad']-b['wrist_requested_arm_rad'])).max()))
    assert pair['selected_target_exact'] and pair['selected_executed_action_exact']
    legacy = DIAG/'05_verified_fixes/wrist_position_candidate_v3/native_precheck/runs/index_reference'
    legacy_meta, legacy_eval, legacy_settings = [remember(legacy/name) for name in ('trace_metadata.json', 'evaluation.json', 'settings.json')]
    old_path = legacy/'trace_env0_episode0.npz'; hashes[str(old_path)] = sha(old_path)
    old = np.load(old_path, allow_pickle=False)
    common = sorted(set(a.files) & set(old.files))
    legacy_comparison = dict(same_settings=legacy_settings == configurations['baseline'],
        same_trace_metadata=legacy_meta == read(FIX/'runs/baseline/trace_metadata.json'),
        same_evaluation=legacy_eval == read(FIX/'runs/baseline/evaluation.json'),
        common_trace_fields=common, field_exact={key: np.array_equal(a[key], old[key]) for key in common},
        scope='Observed separate-run equality, not assumed or a historical strict-checkpoint reload')
    assert 'isaacgym' not in sys.modules and not torch.cuda.is_initialized()
    hashes[str(Path(__file__).resolve())] = sha(__file__); hashes[str(HERE/'PLAN.md')] = sha(HERE/'PLAN.md')
    out.mkdir()
    def write(name, document):
        with (out/name).open('x') as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n')
    write('comparison.json', dict(conditions=results, paired_trace=pair, legacy_baseline=legacy_comparison,
        scope='8 all first attempts; force/posture/gates env0 60Hz only; no pair-pressure or production adoption claim'))
    write('verification.json', dict(completed=True, CPU_only=True, GPU_executed=False, CUDA_initialized=False,
        preparation_pins=677, native_first_attempts=8, native_property_readback='Original pinned setter/get exact assertions; 4env each; no separate full native shape-property dump',
        launcher=launcher, only_contract_change='native_backend.hand_collision', only_scene_change='hand_collision',
        all_saved_predicates_reproduced=True, reward_budget_checks=reward_residuals, input_sha256=hashes))
    for filename, values in [('episodes.csv', rows), ('forces.csv', force_rows), ('gates.csv', gate_rows)]:
        with (out/filename).open('x', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(values[0])); writer.writeheader(); writer.writerows(values)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(12, 6), sharex=True)
    for condition, data in curves.items():
        for j, bi in enumerate((0, 1, 2)):
            axes[0, j].plot(data['time_s'], data['resultant_n'][:, bi], label=condition)
            axes[0, j].set_title(('index1', 'index2', 'index3')[j]+' resultant (N)')
        for ax, key, title in zip(axes[1], ('nearest_distance_mm', 'wrist_position_error_mm', 'wrist_rotation_error_deg'),
                                  ('Nearest pad distance (mm)', 'Wrist position error (mm)', 'Wrist rotation error (deg)')):
            ax.plot(data['time_s'], data[key], label=condition); ax.set_title(title)
    end = configurations['baseline']['song']['short_learning']['view']['local_end_s']
    for ax in axes.flat:
        ax.axvspan(3., end, color='grey', alpha=.18); ax.grid(alpha=.2); ax.set_xlabel('local time (s)')
    axes[0, 0].legend(); fig.suptitle('env0, 60 Hz endpoints; shaded = audible; body resultant is not pair pressure')
    fig.tight_layout(); fig.savefig(out/'comparison.png', dpi=160); plt.close(fig)
    print(json.dumps(dict(completed=True, attempts=8, selected_target_exact=pair['selected_target_exact'],
        legacy_trace_exact=all(legacy_comparison['field_exact'].values()), GPU_executed=False)))


if __name__ == '__main__':
    main()
