"""Strict fresh incremental-finger initial/final GPU evaluation and actual pose capture.

No PPO updates/curriculum advancement; same prepared whole-song contract.
"""
import argparse
import copy
import faulthandler
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent
NUM_ENVS = 1024
CAPTURE_ENVS = tuple(range(8))
sys.path.insert(0, str(ROOT))
from guitar_learning.training import json_io


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json_io.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def select_video_env(episodes):
    """Predeclared selection: lowest safe ID, else longest; no score selection."""
    rows = {e['env_id']: e for e in episodes if e['env_id'] in CAPTURE_ENVS}
    require(set(rows) == set(CAPTURE_ENVS), 'All eight predeclared first episodes required')
    safe = [i for i, e in rows.items() if e['reason'] == 'timeline_complete' and e['left_curriculum']['full_safe']]
    return min(safe) if safe else min(rows, key=lambda i: (-rows[i]['task_time_s'], i))


def validate_capture(arrays, body_count, episode):
    import numpy as np
    frames = episode['steps']+1
    shapes = dict(body_state=(frames, body_count, 13), q=(frames, 105), qd=(frames, 105),
        target=(frames, 105), action=(frames, 39), clock=(frames,),
        left_count=(frames,), near_count=(frames,), contact_count=(frames,), candidate_count=(frames,))
    require(set(arrays) == set(shapes), 'Unexpected pose capture fields')
    for key, shape in shapes.items():
        require(arrays[key].shape == shape and np.isfinite(arrays[key]).all(), 'Invalid capture: '+key)
    require(np.array_equal(arrays['clock'], np.arange(frames)*4), 'First-song physics clock not continuous')
    require(abs(arrays['clock'][-1]/240.-episode['task_time_s']) < 1e-9, 'Capture endpoint differs from episode')
    require(int(arrays['left_count'][-1]) == episode['song']['left_success_count'], 'Capture/ledger success count differs')
    require(np.max(np.abs(np.linalg.norm(arrays['body_state'][..., 3:7], axis=-1)-1)) < 1e-3,
            'Recorded body quaternion not near unit length')


def per_note_summary(episodes, targets):
    result = []
    for j, target in enumerate(targets):
        row = copy.deepcopy(target)
        for group, selected in (('all_first', episodes), ('full_safe_first',
                [e for e in episodes if e['left_curriculum']['full_safe']])):
            n = len(selected)
            values = [e['left_note_ledger']['values'] for e in selected]
            row[group] = dict(episodes=n, left_success_count=sum(v['left'][j] for v in values))
            for field in ('left', 'near_done', 'contact_done'):
                row[group][field+'_fraction'] = sum(v[field][j] for v in values)/n if n else None
            for field in ('clean', 'wrong', 'missing', 'contact_time', 'near_time'):
                row[group]['mean_'+field+'_s'] = sum(v[field][j] for v in values)/n if n else None
        result.append(row)
    return result


def main():
    faulthandler.enable(all_threads=True)
    global NUM_ENVS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=PHASE/'train2000')
    parser.add_argument('--expected-updates', type=int, default=2000)
    parser.add_argument('--num-envs', type=int, default=1024)
    parser.add_argument('--tag', default='')
    args = parser.parse_args()
    run, NUM_ENVS = args.run.resolve(), args.num_envs
    require(NUM_ENVS >= len(CAPTURE_ENVS), 'Capture cohort requires at least8 environments')
    settings = json.loads((run/'settings.json').read_text())
    report = json.loads((run/'report.json').read_text())
    training_pins = json.loads((run/'inputs_before.json').read_text())
    require(report['completed'] is True and report['optimizer_updates'] == args.expected_updates and
            report['failure'] is None and not report['cleanup_errors'] and
            not report['changed_inputs'] and not report['missing_import_pins'], 'Training incomplete/integrity failure')
    require(settings['num_envs'] == NUM_ENVS and settings['horizon'] == 32 and
            settings['size'] == 'large' and settings['seed'] == 7 and
            settings['specialist']['role'] == 'left' and settings['song_training']['control_ticks'] == 1969,
            'Expected large/H32/seed7 left whole-song settings')
    require(not [f for f,h in training_pins.items() if sha(f) != h], 'Training inputs changed')
    chain = dict(schema='guitar_learning.fresh_incremental_fingers_run.v1', run=str(run),
        fresh_policy=True, source_optimizer_updates=args.expected_updates,
        run_completed=True, source_manifest=str(PHASE/'training_source_manifest.json'))
    sys.path.insert(0, str(ROOT))
    import isaacgym  # Must precede NumPy/Torch in the native entry point.
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import GpuPool, FIELDS
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.training.ppo import PPOTrainer, PPOConfig
    from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    results = []
    for name, expected_updates in (('initial', 0), ('final', args.expected_updates)):
        out = PHASE/('evaluation_'+(args.tag+'_' if args.tag else '')+name+'_'+str(NUM_ENVS))
        out.mkdir(exist_ok=False)
        checkpoint = run/('initial.pt' if name == 'initial' else 'final.pt')
        write(out/'settings.json', settings)
        pins = dict(training_pins)
        pins.update({str(f): sha(f) for f in (out/'settings.json', checkpoint, run/'initial.pt',
            run/'report.json', run/'training_contract.json', PHASE/'training_source_manifest.json', Path(__file__).resolve())})
        write(out/'inputs_before.json', pins)
        pool, completed, captures, ticks = None, {}, {}, 0
        started = time.perf_counter()
        def lifecycle(stage, **extra):
            status = dict(stage=stage, ticks=ticks, completed_first_episodes=len(completed),
                wall_s=time.perf_counter()-started, checkpoint=str(checkpoint), **extra)
            (out/'lifecycle.json.tmp').write_text(json_io.dumps(status, allow_nan=False)+'\n')
            (out/'lifecycle.json.tmp').replace(out/'lifecycle.json')
        lifecycle('creating_pool')
        try:
            pool = GpuPool(settings, out)
            lifecycle('pool_created')
            policy = SpecialistPolicy(512, size='large', contract=pool.contract, role='left').to(settings['device'])
            coordinator = CurriculumCoordinator(policy, pool)
            trainer = PPOTrainer(policy, PPOConfig(**settings['ppo']))
            trainer.load(checkpoint)
            require(trainer.updates == expected_updates, 'Unexpected restored update count')
            observation = coordinator.restore()
            policy.eval()
            restored_state = policy.left_curriculum_state.clone()
            progress = coordinator.state.progress
            lifecycle('checkpoint_restored')
            targets = copy.deepcopy(pool.environment.task.provenance['song']['schedule'])
            require(len(targets) == pool.environment.M == 67, 'Expected actual67 target schedule')
            ids = [t.target_id for t in pool.environment.task.targets]
            require([t['target_id'] for t in targets] == ids, 'Target schedule/order mismatch')
            for j, target in enumerate(targets):
                target.update(target_index=j, canonical_string_1based=target['string']+1,
                    required_clean_s=float(pool.environment.required[j].item()))
            write(out/'targets.json', targets)
            capture_metadata = None
            if name == 'final':
                write(out/'visual_initial.json', pool.scene.contract['initial'])
                capture_metadata = dict(schema='guitar_learning.gpu_first_song_pose_capture.v1',
                    checkpoint=str(checkpoint), checkpoint_sha256=pins[str(checkpoint)], source_optimizer_updates=args.expected_updates,
                    training_chain=chain,
                    body_names=pool.scene.body_names, joint_names=pool.scene.names,
                    body_frame='Native environment-local world; no environment-origin addition/subtraction',
                    state_layout='body_state[x,y,z,qx,qy,qz,qw,COM_vx,COM_vy,COM_vz,wx,wy,wz]',
                    logical_guitar='39 source markers from the actual GPU one-body rigid-guitar transform',
                    source_physics_hz=240, capture_hz=60, capture_envs=list(CAPTURE_ENVS),
                    initial_frame='Prepared reset t0; action0 is sentinel, not an applied policy decision',
                    action='Frame k>0 stores the policy action applied over preceding four native physics steps',
                    selection='Lowest envID among predeclared0..7 safe whole first songs; if none, longest first episode, then lowest ID',
                    scope='Real final-checkpoint first-episode observations before reset; no synthetic motion or pose interpolation')
                def capture(env_ids, actions):
                    env = pool.environment
                    indices = torch.tensor(env_ids, device=env.device)
                    values = {key: env.snapshot[key][indices].detach().cpu().numpy()
                              for key in ('body_state', 'q', 'qd', 'target')}
                    values.update(action=actions[indices].detach().cpu().numpy(), clock=env.clock[indices].cpu().numpy())
                    for key, field in (('left_count', 'left'), ('near_count', 'near_done'), ('contact_count', 'contact_done')):
                        values[key] = env.note[field][indices].sum(-1).cpu().numpy()
                    values['candidate_count'] = env.candidate[indices].sum(-1).cpu().numpy()
                    for offset, index in enumerate(env_ids):
                        frames = captures.setdefault(index, {key: [] for key in values})
                        for key, value in values.items():
                            frames[key].append(value[offset].copy())
                capture(CAPTURE_ENVS, torch.zeros(NUM_ENVS, 39, device=pool.scene.device))
            with (out/'first_episodes.jsonl').open('x') as episode_stream, torch.no_grad():
                while len(completed) < NUM_ENVS and ticks < 1969:
                    capture_ids = [i for i in CAPTURE_ENVS if i not in completed] if name == 'final' else []
                    action = policy.act(*(observation[k] for k in FIELDS), deterministic=True)['action']
                    observation, reward, cost, terminated, truncated, episodes = pool.step(action)
                    require(bool(torch.isfinite(reward).all()) and bool(torch.isfinite(cost).all()), 'Nonfinite evaluation metrics')
                    require(not bool(truncated.any()), 'Unexpected truncation in whole-song evaluation')
                    if capture_ids:
                        capture(capture_ids, action)
                    for episode in episodes:
                        index = episode['env_id']
                        if index in completed:
                            continue
                        ledger = episode['left_note_ledger']
                        require(ledger['target_ids'] == ids and len(ledger['values']['left']) == 67, 'Native ledger order mismatch')
                        require(sum(ledger['values']['left']) == episode['song']['left_success_count'], 'Native ledger/count mismatch')
                        completed[index] = episode
                        episode_stream.write(json_io.dumps(episode, allow_nan=False)+'\n')
                    episode_stream.flush()
                    ticks += 1
                    if ticks % 60 == 0:
                        lifecycle('stepping')
                    done = (terminated | truncated).nonzero().flatten()
                    if done.numel() and len(completed) < NUM_ENVS and ticks < 1969:
                        observation = pool.reset(done)[0]
            lifecycle('stepping_complete')
            require(set(completed) == set(range(NUM_ENVS)), 'Not all first episodes ended')
            torch.cuda.synchronize(pool.scene.device)
            require(trainer.updates == expected_updates and coordinator.state.progress == progress and
                    torch.equal(policy.left_curriculum_state, restored_state), 'Evaluation changed learning/curriculum state')
            changed = [f for f, h in pins.items() if sha(f) != h]
            lifecycle('input_pins_checked', changed_inputs=changed)
            require(not changed, 'Evaluation inputs/checkpoint changed')
            episodes = [completed[i] for i in range(NUM_ENVS)]
            if capture_metadata is not None:
                capture_metadata['selected_env_id'] = select_video_env(episodes)
                capture_metadata['captures'] = []
                for index in CAPTURE_ENVS:
                    arrays = {key: np.stack(value) for key, value in captures[index].items()}
                    validate_capture(arrays, len(pool.scene.body_names), completed[index])
                    path = out/('poses_env%04d.npz' % index)
                    np.savez_compressed(str(path), **arrays)
                    capture_metadata['captures'].append(dict(env_id=index, path=path.name, sha256=sha(path),
                        frames=len(arrays['clock']), reason=completed[index]['reason'],
                        full_safe=completed[index]['left_curriculum']['full_safe'], duration_s=completed[index]['task_time_s']))
                write(out/'capture_metadata.json', capture_metadata)
                lifecycle('pose_captures_written')
            report = dict(completed=True, checkpoint=str(checkpoint), source_optimizer_updates=expected_updates,
                training_chain=chain,
                deterministic=True, num_envs=NUM_ENVS, ticks=ticks, curriculum_progress=progress,
                first_episodes_path='first_episodes.jsonl', targets_path='targets.json',
                episodes=[{key: value for key, value in e.items() if key != 'left_note_ledger'} for e in episodes],
                per_note=per_note_summary(episodes, targets),
                capture_metadata_path='capture_metadata.json' if capture_metadata is not None else None,
                input_pins_verified=len(pins), wall_s=time.perf_counter()-started,
                scope='All first ended episodes only; reset other ended environments only to keep the original batch stepping. No PPO update or curriculum advance.',
                limitations='Same song/prepared pose and each checkpoint own saved curriculum/observations; not identical-observation weight isolation, independent seeds, generalization, calibrated pressure or sound.')
            lifecycle('result_prepared')
        except BaseException as error:
            write(out/'python_exception.json', dict(error=repr(error), traceback=traceback.format_exc()))
            traceback.print_exc()
            sys.stderr.flush()
            raise
        finally:
            if pool is not None:
                lifecycle('synchronizing_before_close')
                torch.cuda.synchronize(pool.scene.device)
                lifecycle('destroying_simulator')
                pool.close()
                lifecycle('pool_closed')
        report['gpu_scene'] = pool.scene.diagnostics
        require(report['gpu_scene']['closed'] and report['gpu_scene']['physx_use_gpu'] and
                report['gpu_scene']['use_gpu_pipeline'] and report['gpu_scene']['environment_count'] == NUM_ENVS and
                report['gpu_scene']['physics_steps'] == ticks*4, 'Closed nativeGPU batch audit failed')
        write(out/'report.json', report)
        lifecycle('report_written')
        results.append(report)
    write(PHASE/((args.tag+'_' if args.tag else '')+'checkpoint_evaluation.json'), dict(completed=True, training_chain=chain, results=results))
    print(json_io.dumps(dict(completed=True, checkpoint_updates=[0, args.expected_updates], environments=NUM_ENVS)))


if __name__ == '__main__':
    main()
