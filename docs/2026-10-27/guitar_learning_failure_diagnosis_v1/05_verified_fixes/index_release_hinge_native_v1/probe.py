"""현재 Jv3에서 원3음 참고 동작과 해제 두 관절 후보를 비교한다."""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent/'index_release_clearance_v1/runs/reference'
EXPLORATION = HERE.parents[1]/'04_ablation/prefix_release_alignment_v1/exploration/results_v1/comparison.json'
MODES = ('baseline', 'candidate', 'noisy_candidate')
SCHEMA = 'diagnostic.release_hinge_native.v1'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def save_rows(path, rows):
    """실패 전까지 수집한 완전한 행을 원출력과 구분하여 보존한다."""
    if not rows:
        return
    import numpy as np
    assert all(set(row) == set(rows[0]) for row in rows)
    with Path(path).open('xb') as f:
        np.savez_compressed(f, **{k: np.asarray([r[k] for r in rows]) for k in rows[0]})


def support():
    if 'release_hinge_support' not in sys.modules:
        spec = importlib.util.spec_from_file_location('release_hinge_support', HERE/'support.py')
        value = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = value
        spec.loader.exec_module(value)
    return sys.modules['release_hinge_support']


def changed_pins(pins):
    return [p for p, h in pins.items() if not Path(p).is_file() or sha(p) != h]


def acceptance(rows):
    assert len(rows) == 128 and sorted(r['env_id'] for r in rows) == list(range(128))
    assert all(r['selected_target_count'] == len(r['notes']) == 3 for r in rows)
    assert all(bool(r['achieved']) == all(n['achieved'] for n in r['notes']) for r in rows)
    per = []
    for col, index in enumerate((4, 7, 8)):
        notes = [r['notes'][col] for r in rows]
        assert all(n['source_index'] == index for n in notes)
        achieved = sum(n['achieved'] for n in notes)/128
        clean = sum(n['clean_fraction'] for n in notes)/128
        wrong = sum(n['audible_wrong_fraction'] for n in notes)/128
        per.append(dict(source_index=index, achieved_fraction=achieved, mean_clean_fraction=clean,
                        mean_wrong_fraction=wrong, passed=achieved >= .9 and clean >= .9 and wrong <= .1))
    all3 = sum(r['achieved'] for r in rows)/128
    physical = sum(r['termination']['physical_failure'] for r in rows)
    wrist = sum(r['termination']['wrist_failure'] for r in rows)
    released = sum(r['notes'][0]['released'] for r in rows)/128
    music = all(n['passed'] for n in per) and all3 >= .9 and physical == wrist == 0
    return dict(attempts=128, note_opportunities=384, per_note=per, all3_achieved_fraction=all3,
                physical_failures=physical, wrist_failures=wrist, A_released_fraction=released,
                music_passed=music, release_passed=released >= .9, stage_ready=music and released >= .9)


def baseline_matches_original(evaluation):
    """후보 실행 전 과거 기준의 음별 품질까지 확인한다. 물리 궤적 동일성은 별도다."""
    old = acceptance(read(BASE/'evaluation.json')['episodes'])
    new = evaluation['acceptance']
    if new['all3_achieved_fraction'] != old['all3_achieved_fraction'] or new['A_released_fraction'] != old['A_released_fraction']:
        return False
    if new['physical_failures'] != old['physical_failures'] or new['wrist_failures'] != old['wrist_failures']:
        return False
    for previous, actual in zip(old['per_note'], new['per_note']):
        if previous['achieved_fraction'] != actual['achieved_fraction']:
            return False
        for key in ('mean_clean_fraction', 'mean_wrong_fraction'):
            if abs(previous[key]-actual[key]) > 1e-5:
                return False
    return True


def prepare():
    assert 'isaacgym' not in sys.modules
    inputs = HERE/'cpu_inputs'
    inputs.mkdir(exist_ok=False)
    sys.path.insert(0, str(ROOT))
    import torch
    from guitar_learning.training.launch import build_settings
    from guitar_learning.song.task import make_task
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_teacher
    from guitar_learning.training.finger_skill_runner import _pins
    assert not torch.cuda.is_initialized() and not torch.cuda.is_available()
    source = read(BASE/'settings.json')
    old = source['song']['short_learning']
    historical = []
    evidence = {BASE/'settings.json', Path(old['teacher']['input_path'])}
    for filename, expected in old['teacher']['source_evidence'].items():
        path = Path(filename)
        if not path.is_file() or sha(path) != expected:
            path = ROOT/'guitar_learning/assets/historical_inputs/objects'/(expected+'.data')
        assert path.is_file() and sha(path) == expected
        evidence.add(path)
        historical.append(dict(original_path=filename, sha256=expected, verified_bytes_path=str(path)))
    write(inputs/'historical_verification.json', dict(originals_untouched=True, records=historical,
        description='Historical bytes verified at original path or immutable CAS; current implementation is separately pinned. No old checkpoint/source identity is rewritten.'))
    teacher = copy.deepcopy(old['teacher'])
    for key in ('input_path', 'input_sha256'):
        teacher.pop(key, None)
    teacher['source_evidence'] = {str(p): sha(p) for p in evidence | {inputs/'historical_verification.json'}}
    teacher['derivation'] = 'Same recorded arm/wrist numerical targets, reissued for fresh Jv3 noNN runtime; old teacher preserved'
    write(inputs/'teacher.json', teacher)
    teacher = read_teacher(inputs/'teacher.json')
    settings = build_settings('left', learning_family='finger-skill', physics='gpu', device='cuda:0',
        song='05_BN2-131-B_solo', size='large', seed=7, num_envs=128, horizon=32, updates=300,
        checkpoint_every=50)
    current_skill = copy.deepcopy(settings['finger_skill'])
    settings['song'] = copy.deepcopy(source['song'])
    short = settings['song']['short_learning']
    short.update(schema=SCHEMA, teacher=teacher,
        policy_scope='No neural network, checkpoint, optimizer, fit, or PPO; scripted normalized goals only',
        result_scope='Conditional fixed-guitar128 noNN first attempts; Jv3 557 observation. Original3note music/release gates, not free-guitar learning.')
    short.pop('ablation', None)
    short['view'], _ = support().view_and_catalog(make_task(settings['song_training']['bundle']))
    # The current compiler's provenance contains consolidated source paths.
    # All target values and timing must remain exact; record only these new fingerprints.
    changed_view = {k: dict(old=old['view'].get(k), current=short['view'].get(k))
                    for k in set(old['view']) | set(short['view']) if old['view'].get(k) != short['view'].get(k)}
    assert set(changed_view) <= {'catalog_sha256', 'source_sha256'}
    write(inputs/'view_derivation.json', dict(changes=changed_view, target_and_timing_exact=True,
        explanation='Current compiler provenance and catalogue identity are declared anew; original fingerprints are preserved.'))
    assert settings['finger_skill'] == current_skill
    settings['initial_std'] = source['initial_std']
    settings['simple_start']['initialization'] = 'fresh noNN diagnostic; no checkpoint or policy construction'
    for mode in MODES:
        value = copy.deepcopy(settings)
        value['song']['short_learning']['execution_mode'] = mode
        if mode != 'baseline':
            import math
            value['song']['short_learning']['reference_release_schedule']['negative_selected_rad'][2:] = [math.radians(40), math.radians(10)]
        write(inputs/(mode+'.json'), value)
    # _pins expects settings.json, which is a current baseline settings document.
    write(inputs/'settings.json', settings)
    check_spec = importlib.util.spec_from_file_location('release_hinge_CPU', HERE/'cpu_checks.py')
    checks = importlib.util.module_from_spec(check_spec)
    check_spec.loader.exec_module(checks)
    cpu = checks.check()
    write(HERE/'cpu_verification.json', cpu)
    extra = evidence | set(support().SOURCES.values()) | set(inputs.glob('*.json'))
    extra.update((HERE/'PLAN.md', HERE/'support.py', HERE/'cpu_checks.py', Path(__file__),
                  HERE/'restoration.json', HERE/'cpu_verification.json', EXPLORATION,
                  HERE.parent/'index_release_clearance_v1/surface.py'))
    extra.update(BASE/n for n in ('trace_env0_episode0.npz', 'observations4.npz', 'goal_codec_env0.npz',
                                'training_contract.json', 'evaluation.json', 'surface_static.npz'))
    pins = _pins(settings, inputs, extra)
    write(HERE/'preparation_seal.json', dict(schema=SCHEMA, independent_review='pending', input_pins=pins))
    print(json.dumps(dict(CPU_prepared=True, native_runs=0, pins=len(pins))))


def gate():
    seal = read(HERE/'preparation_seal.json')
    assert not changed_pins(seal['input_pins'])
    review = read(HERE/'review.json')
    assert seal['independent_review'] == 'PASS' and review['verdict'] == 'PASS'
    assert not review['findings'] and not changed_pins(review['reviewed_sha256'])
    assert seal['input_pins'][str(HERE/'review.json')] == sha(HERE/'review.json')
    return seal['input_pins']


def geometry_function():
    # Reuse the exact source128 measurement, importing its current merged primitives only.
    import torch
    import numpy as np
    from guitar_learning.gpu.contact import pad_target_geometry, project_press_strings
    source = HERE.parent/'index_release_clearance_v1/surface.py'
    node = next(n for n in ast.parse(source.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'geometry')
    scope = dict(torch=torch, np=np, pad_target_geometry=pad_target_geometry, project_press_strings=project_press_strings)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), scope)
    return scope['geometry']


def capture_surface(pool, first, start_clock, geometry):
    import numpy as np
    import torch
    from guitar_learning.gpu.control import apply, conjugate
    env = pool.environment
    ids = (first[:4] & (env.clock[:4] >= 692) & (env.clock[:4] <= 920)).nonzero().flatten()
    if not len(ids):
        return []
    body = env.body[ids][:, env.pad_indices]
    guitar = env.guitar_body[ids]
    points = apply(conjugate(guitar[:, None, None, 3:7]),
        body[:, :, None, :3] + apply(body[:, :, None, 3:7], env.pad_local[None]) - guitar[:, None, None, :3])
    normals = apply(conjugate(guitar[:, None, None, 3:7]), apply(body[:, :, None, 3:7], env.pad_normals[None]))
    rows = []
    for j, i in enumerate(ids.tolist()):
        valid = bool(not env.snapshot['reset_body_snapshot'][i] and torch.isfinite(body[j]).all() and torch.isfinite(guitar[j]).all())
        row = dict(env_id=i, start_clock=int(start_clock[i]), clock=int(env.clock[i]), valid_snapshot=valid,
            post_failure=bool(env.failure[i].any() | env.wrist_failure[i] | env.wrist_severe_failure[i]))
        values = dict(q105=pool.scene.q[i], target105=pool.scene.target[i], distal_pose=body[j, 0, :7],
            index1_pose=env.body[i, env.body_names.index('human/LH:index1'), :7], guitar_pose=guitar[j, :7],
            points_G=points[j, 0], normals_G=normals[j, 0], body_loaded=env.loaded[i, env.pad_indices[0]],
            body_force_n=env.snapshot['contact_force'][i, env.pad_indices[0]], candidate=env.candidate[i, 4],
            released=env.note['released'][i, 4], release_s=env.note['release_s'][i, 4])
        if valid:
            sample, aggregate, residual = geometry(points[j:j+1], normals[j:j+1], env.pad_valid,
                env.starts[i:i+1], env.ends[i:i+1], env.frets[i:i+1], env.loaded[i:i+1][:, env.pad_indices], env.press_plane, 2, 4)
            values.update({'point_'+k: v[0] for k, v in sample.items()})
            values.update({'aggregate_'+k: v[0] for k, v in aggregate.items()})
            values['aggregate_distance_residual_m'] = residual[0]
        else:
            for key in ('distance', 'normal_cos', 'signed_height', 'lateral'):
                values['point_'+key] = torch.full((128,), float('nan'))
            for key in ('position_geometry', 'facing_geometry', 'positive', 'in_cell'):
                values['point_'+key] = torch.zeros(128, dtype=torch.bool)
            for key in ('distance', 'normal_cos', 'signed_height'):
                values['aggregate_'+key] = torch.tensor(float('nan'))
            for key in ('position_geometry', 'facing_geometry', 'positive'):
                values['aggregate_'+key] = torch.tensor(False)
            values['aggregate_sample_index'] = torch.tensor(-1)
            values['aggregate_distance_residual_m'] = torch.tensor(float('nan'))
        row.update({k: v.detach().cpu().numpy().copy() for k, v in values.items()})
        rows.append(row)
    return rows


def run(mode):
    pins = gate()  # stdlib-only before loading Isaac Gym.
    if mode != 'baseline':
        baseline = read(HERE/'runs/baseline/evaluation.json')
        assert read(HERE/'runs/baseline/report.json')['completed'] and baseline['acceptance']['stage_ready']
        assert baseline['acceptance']['all3_achieved_fraction'] == baseline['acceptance']['A_released_fraction'] == 1.
        assert baseline_matches_original(baseline), 'Fresh baseline differs from historical music/release quality'
    if mode == 'noisy_candidate':
        assert read(HERE/'runs/candidate/report.json')['completed']
        assert read(HERE/'runs/candidate/evaluation.json')['acceptance']['stage_ready']
    import isaacgym
    import numpy as np
    import torch
    import random
    sys.path.insert(0, str(ROOT))
    from guitar_learning.training.training_log_io import project_source_paths
    out = HERE/'runs'/mode
    out.mkdir(parents=True, exist_ok=False)
    config = read(HERE/'cpu_inputs'/(mode+'.json'))
    write(out/'settings.json', config)
    pool = None
    failure = None
    completed = False
    cleanup = []
    started = time.monotonic()
    episodes, trace, surface, noise_rows = [], [], [], []
    counts = [0]*128
    noise_hash = hashlib.sha256()
    try:
        torch.set_num_threads(1)
        torch.backends.cuda.matmul.allow_tf32 = False
        random.seed(7); np.random.seed(7); torch.manual_seed(7)
        pool = support().Pool(config, out)
        pool.environment.set_evaluation(True, full_song=False)
        write(out/'training_contract.json', pool.contract)
        write(out/'native_effort_readback.json', pool.effort_readback)
        # Match the original noisy-reference seed boundary after pool construction.
        random.seed(7); np.random.seed(7); torch.manual_seed(7)
        measure = geometry_function()
        for tick in range(pool.spec['view']['duration_ticks']):
            first = pool.first.clone()
            start_clock = pool.environment.clock.clone()
            raw = support().reference_raw(pool)
            if mode == 'noisy_candidate':
                ids = pool.spec['learned_action_indices']
                sigma = raw.new_tensor(read(EXPLORATION)['candidate_sigma4']).log().clamp(-5, 2).exp()
                assert bool((raw[:, ids].abs() < 1).all())
                noise = torch.distributions.Normal(torch.zeros_like(raw[:, ids]), sigma.expand_as(raw[:, ids])).sample()
                noise_hash.update(noise.detach().cpu().numpy().tobytes())
                before = raw[:, ids].clone()
                raw[:, ids] = (before.atanh()+noise).tanh()
                for i in range(4):
                    if bool(first[i]):
                        noise_rows.append(dict(env_id=i, start_clock=int(start_clock[i]),
                            raw_reference=before[i].cpu().numpy().copy(), scaled_noise=noise[i].cpu().numpy().copy(),
                            raw_noisy_goal=raw[i, ids].cpu().numpy().copy()))
            action, goal = support().convert(pool, raw)
            observation, reward, cost, terminated, truncated, finished = pool.step(action)
            assert bool(torch.isfinite(reward).all() & torch.isfinite(cost).all())
            surface.extend(capture_surface(pool, first, start_clock, measure))
            if counts[0] == 0:
                env = pool.environment
                record = dict(time_s=float(env._local_time()[0]), source_time_s=float(env._score_time()[0]))
                values = dict(raw_goal_normalized=raw[0, 17:21], decoded_goal_rad=goal[0],
                    policy_action=pool.last_policy_action[0], executed_action=pool.last_executed_action[0],
                    q=pool.scene.q[0], target=pool.scene.target[0], body_state=pool.scene.body_state[0],
                    net_body_force_n=pool.scene.snapshot()['contact_force'][0], candidate=env.candidate[0, [4,7,8]],
                    wrong=env.wrong[0, [4,7,8]], surface_distance_m=env.surface_distance[0, [4,7,8]],
                    surface_height_m=env.surface_height[0, [4,7,8]], released=env.note['released'][0, [4,7,8]],
                    release_s=env.note['release_s'][0, [4,7,8]])
                values.update({'wrist_'+k: v[0] for k, v in pool.last_wrist_feedback.items()})
                record.update({k: v.detach().cpu().numpy().copy() for k, v in values.items()})
                trace.append(record)
            for row in finished:
                i = row['env_id']
                if counts[i] == 0:
                    episodes.append(support().compact_episode(row, pool.spec)); counts[i] = 1
            if tick % 60 == 0:
                print(json.dumps(dict(mode=mode, ticks=tick+1, completed_attempts=sum(counts))), flush=True)
            if counts == [1]*128:
                break
            done = (terminated | truncated).nonzero().flatten()
            if done.numel():
                pool.reset(done)
        assert counts == [1]*128
        result = acceptance(episodes)
        write(out/'evaluation.json', dict(schema=SCHEMA, condition=mode, policy_performance=False,
            assigned_quotas=[1]*128, episodes=episodes, acceptance=result))
        for filename, rows in (('trace_env0_episode0.npz', trace), ('release_clearance4.npz', surface),
                               ('reference_noise4.npz', noise_rows), ('current_goal_DIP60.npz', pool.guard_rows)):
            save_rows(out/filename, rows)
        write(out/'trace_metadata.json', dict(joint_names=pool.scene.names, body_names=pool.scene.metadata['body_names'],
            source_indices=[4,7,8], sampling_Hz=60, env0_first_attempt=True,
            surface_env_ids=[0,1,2,3], surface_clock_window=[692,920], surface_only_original_distal128=True,
            noNN=True, checkpoints_loaded=0, PPO_updates=0, noise_draw_shape=[128,4] if noise_rows else None,
            noise_stream_sha256=noise_hash.hexdigest() if noise_rows else None))
        with (out/'surface_static.npz').open('xb') as f:
            np.savez_compressed(f, local_points=pool.environment.pad_local[0].cpu().numpy(),
                local_normals=pool.environment.pad_normals[0].cpu().numpy(),
                source_valid=pool.environment.pad_valid.cpu().numpy(), plane=pool.environment.press_plane.cpu().numpy())
        completed = True
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        if failure is not None:
            try:
                write(out/'partial_evaluation.json', dict(assigned_quotas=[1]*128,
                    completed_attempts=sum(counts), episodes=episodes, complete=False, failure=failure))
                for name, rows in (('trace_env0_episode0', trace), ('release_clearance4', surface),
                                   ('reference_noise4', noise_rows),
                                   ('current_goal_DIP60', [] if pool is None else pool.guard_rows)):
                    save_rows(out/('partial_'+name+'.npz'), rows)
                if pool is not None and pool.pending is not None:
                    save_rows(out/'aborted_control.npz', [{k: v.detach().cpu().numpy().copy()
                        for k, v in pool.pending.items()}])
            except BaseException as error:
                cleanup.append(dict(stage='partial_artifact_preservation', type=type(error).__name__, message=str(error)))
        if pool is not None:
            try:
                pool.close()
            except BaseException as error:
                cleanup.append(dict(type=type(error).__name__, message=str(error)))
        changed = changed_pins(pins)
        missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        write(out/'inputs_after.json', dict(verified=not changed and not missing,
            changed_paths=changed, unpinned_project_sources=missing, input_pins=pins))
        write(out/'report.json', dict(schema=SCHEMA, condition=mode, completed=completed and not changed and not missing and not cleanup,
            failure=failure, cleanup_errors=cleanup, changed_inputs=changed, unpinned_project_sources=missing,
            closed=pool is not None and pool.closed, wall_s=time.monotonic()-started,
            completed_attempts=sum(counts), NN_constructors=0, checkpoint_loads=0, PPO_updates=0, fit_steps=0))
        if failure is None and (changed or missing or cleanup):
            raise RuntimeError('Fresh diagnostic input/lifecycle audit failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', action='store_true')
    group.add_argument('--gate-check', action='store_true')
    group.add_argument('--execute', choices=MODES)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.execute:
        run(args.execute)
    else:
        assert not any(n in sys.modules for n in ('torch', 'numpy', 'isaacgym'))
        gate()
        print(json.dumps(dict(stdlib_only=True, ready=True)))
