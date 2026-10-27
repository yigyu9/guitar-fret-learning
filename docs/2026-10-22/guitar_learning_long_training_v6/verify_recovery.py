"""CPU streaming audit of saved1300 + newly resumed700 v6 updates.

Historical files keep their original pins. Only manifest-proved relocation is
allowed; old1300 prefix never implies normal native close or whole gzip EOF.
"""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import math
from pathlib import Path
import struct
import verify_training as base
from verify_training import (ROOT, ENVS, HORIZON, REWARD_KEYS, RIGHT_KEYS, require,
    read, digest, encoded, finite, journal, verify_codec, verify_architecture,
    verify_rate_components, verify_episode, summary_close, component_sum,
    raw_rows, lines, torch, np, json_io)


def relocation_manifest(path, old_run):
    value = read(path)
    require(value['schema'] == 'guitar_learning.relocated_run_copy.v1' and
            value['completed'] is True and isinstance(value['errors'],list), 'Relocation copy incomplete')
    source, destination = Path(value['source']), Path(value['destination'])
    require(source.is_absolute() and destination.is_absolute() and destination.resolve() == old_run.resolve(),
            'Explicit absolute relocation roots differ')
    require({str(p.relative_to(destination)) for p in destination.rglob('*') if p.is_file()} == set(value['files']),
            'Relocated exact file set differs')
    require(value['bytes'] == sum(row['bytes'] for row in value['files'].values()), 'Relocation byte total differs')
    for name, row in value['files'].items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe relocation relative path')
        target = destination/relative
        require(target.stat().st_size == row['bytes'] and digest(target) == row['sha256'],
                'Relocated file byte/SHA mismatch: '+str(target))
    return value


def verify_pin(name, expected, relocation):
    path = Path(name)
    if relocation is not None:
        try:
            relative = path.relative_to(Path(relocation['source']))
        except ValueError:
            relative = None
        if relative is not None:
            row = relocation['files'].get(str(relative))
            require(row is not None and row['sha256'] == expected, 'Original pin not proved by copy manifest: '+name)
            target = Path(relocation['destination'])/relative
            require(target.stat().st_size == row['bytes'] and digest(target) == expected, 'Relocated pin bytes/SHA mismatch: '+name)
            return
    require(digest(path) == expected, 'Input SHA mismatch: '+name)


def same(a, b):
    """Exact CPU state/RNG equality, including floating-point signed-zero bits."""
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape and a.numpy().tobytes() == b.numpy().tobytes()
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(v, b[k]) for k,v in a.items())
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(same(x,y) for x,y in zip(a,b))
    if isinstance(a, float):
        return struct.pack('!d',a) == struct.pack('!d',b)
    return a == b


def verify_restore(saved, initial):
    previous, resumed = (torch.load(p,map_location='cpu',weights_only=False) for p in (saved,initial))
    finite(previous);finite(resumed)
    require(previous['updates'] == resumed['updates'] == 1300, 'Saved/resumed optimizer1300 boundary')
    require(same({k:v for k,v in previous.items() if k!='metadata'},
                 {k:v for k,v in resumed.items() if k!='metadata'}), 'Exact nonmetadata model/optimizers/RNG/curriculum restore')
    return dict(optimizer_updates=1300, exact_nonmetadata=True,
                saved_sha256=digest(saved), initial_sha256=digest(initial),
                scope='Metadata alone may differ; physical state/clock are new prepared episodes, not restored')


def verify_segment(run, phase, updates, offset=0, final_mode=False, relocation=None):
    settings, contract = (read(run/name) for name in ('settings.json', 'training_contract.json'))
    expected_updates = 2000 if offset == 0 else 700
    require(settings['updates'] == expected_updates and 0 < updates <= expected_updates, 'Segment budget')
    require(not final_mode or updates == expected_updates, 'Final segment budget incomplete')
    report = read(run/'report.json') if final_mode else None
    control = verify_codec(contract)
    require((settings['size'], settings['num_envs'], settings['horizon'], settings['updates'], settings['seed']) ==
            ('large', ENVS, HORIZON, expected_updates, 7), 'Expected large1024/H32/seed7 segment budget')
    require(settings['checkpoint_every'] == 100, 'Expected checkpoint100 budget')
    require(settings['specialist']['role'] == 'left' and settings['device'] == 'cuda:0' and settings['song']['left_fraction'] == .4, 'Left GPU/song settings')
    require(settings['song_training']['observation_dimension'] == 544, 'Settings left544 inputs')
    if final_mode:
        require(report.get('completed') is True and report['failure'] is None and report['stopped'] == 'updates_complete', 'Training incomplete/failed')
        require(not report['cleanup_errors'] and not report['changed_inputs'] and not report['missing_import_pins'], 'Run integrity errors')
        require(settings == report['settings'], 'Report/settings mismatch')
        require(report['optimizer_updates'] == offset+updates and report['transitions'] == updates*HORIZON*ENVS, 'Update/transition totals')
        journal(report['journal'], updates, True)
        require(report['journal']['compressed_bytes'] == (run/'transitions.jsonl.gz').stat().st_size, 'Gzip byte count')
        scene = read(run/'gpu_scene_final.json')
        require(scene == report['gpu_scene'] and report['lifecycle_verified'] is True and scene['closed'] is True, 'Actual GPU lifecycle')
        require(scene['physx_use_gpu'] is True and scene['use_gpu_pipeline'] is True and scene['simulator_count'] == 1 and
                scene['environment_count'] == scene['num_envs'] == ENVS and scene['physics_steps'] == updates*HORIZON*4, 'GPU physics/batch/steps')
        require(set(scene['tensor_devices']) == {'dof', 'roots', 'bodies', 'contact_force', 'jacobian'} and
                all(v == 'cuda:0' for v in scene['tensor_devices'].values()), 'Actual CUDA tensor devices')
        aggregate = scene['environment_aggregate']
        require((aggregate['max_bodies'], aggregate['max_shapes'], aggregate['self_collisions']) == (68, 145, True), 'Aggregate contract')
    pins, manifest = read(run/'inputs_before.json'), read(phase/'training_source_manifest.json')
    source = manifest['source']
    require(manifest['active_python_count'] == len(source) == 436, 'Frozen436 source count')
    active = {str(p.resolve()) for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    require(active == set(source), 'Active Python source set changed')
    for name, expected in pins.items():
        verify_pin(name, expected, relocation)
    for name, expected in source.items():
        require(pins.get(name) == expected and digest(phase/'source_training'/Path(name).relative_to(ROOT)) == expected, 'Training snapshot/source pin mismatch: '+name)
    schedule = contract['task']['provenance']['song']['schedule']
    require(len(schedule) == 67, 'Expected67-note schedule')
    duration = settings['song_training']['episode_duration_s']
    initial = torch.load(run/'initial.pt', map_location='cpu', weights_only=False)
    finite(initial)
    verify_architecture(initial['identity']['architecture'])
    require(initial['identity']['architecture']['contract'] == contract and initial['identity']['config'] == settings['ppo'],
            'Fresh initial checkpoint contract/config')
    require(initial['updates'] == offset, 'Initial optimizer offset')
    from guitar_learning.song.gpu_left_curriculum import CurriculumState
    counts = [sum(t['finger'] == f for t in schedule) for f in range(1, 5)]
    curriculum = CurriculumState(counts)
    if offset == 0:
        require(not initial['actor_optimizer']['state'] and not initial['value_optimizer']['state'], 'Fresh optimizers')
        require(bool((initial['model']['log_std'][:33] == -3.).all()) and
                bool((initial['model']['actor_heads.left.weight'] == 0).all()) and
                bool((initial['model']['actor_heads.left.bias'] == 0).all()), 'Fresh zero-mean/default-std left actor')
        require(np.array_equal(initial['model']['left_curriculum_state'].numpy(), curriculum.state_vector()), 'Fresh3331 state')
    else:
        require(initial['actor_optimizer']['state'] and initial['value_optimizer']['state'], 'Resumed two optimizer states')
        curriculum.load_state(initial['model']['left_curriculum_state'].numpy())
    if final_mode:
        expected_checkpoints={('checkpoint_%06d.pt'%(i-1)) for i in range(settings['checkpoint_every'],updates,settings['checkpoint_every'])}
        require({p.name for p in run.glob('checkpoint_*.pt')} == expected_checkpoints, 'Checkpoint100 file sequence')
        require(len(report['updates']) == len(list(run.glob('update_*.json'))) == updates, 'Update file/report counts')
    checkpoint = (run/'final.pt' if final_mode else next((path for count, path in sorted(
        [(int(path.stem.split('_')[-1])+1, path) for path in run.glob('checkpoint_*.pt')
         if int(path.stem.split('_')[-1])+1 <= updates], reverse=True)), run/'initial.pt'))
    checkpoint_update = updates if final_mode else (int(checkpoint.stem.split('_')[-1])+1 if checkpoint.name != 'initial.pt' else 0)
    checkpoint_curriculum = curriculum.state_vector().copy() if checkpoint_update == 0 else None
    metrics, logged = iter(lines(run/'learning_metrics.jsonl')), iter(lines(run/'episodes.jsonl'))
    totals = Counter(all=0, physical_failure=0, timeline_complete=0, stage_success=0)
    raw_count = max_episode_error = max_update_error = 0
    raw_status = {}
    with closing(raw_rows(run/'transitions.jsonl.gz', final_mode, raw_status)) as stream:
        for index in range(updates):
            row = read(run/('update_%06d.json' % index))
            finite(row)
            require(row['update_index'] == index and row['optimizer_updates'] == offset+index+1 and row['transitions'] == HORIZON*ENVS and
                    row['physics_steps'] == (index+1)*HORIZON*4, 'Update sequence')
            journal(row['journal'], index+1, False)
            if final_mode:
                require(all(report['updates'][index][key] == row[key] for key in report['updates'][index]), 'Report/update summary')
            require(encoded(next(metrics, None)) == encoded(row), 'Metrics/update correspondence')
            parts = row['reward_component_means']
            require(set(parts) == set(REWARD_KEYS+RIGHT_KEYS) and all(parts[k] == 0 for k in RIGHT_KEYS), 'Update reward fields/right zeros')
            verify_rate_components(parts, 1/60.)
            max_update_error = max(max_update_error, component_sum(parts, row['mean_reward'], 'Update reward'))
            expected_hash, logged_hash, raw_hash = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
            episodes = row['completed_episodes']
            for episode in episodes:
                max_episode_error = max(max_episode_error, verify_episode(episode, schedule, duration, control))
                expected_hash.update(encoded(episode)+b'\n')
                item = next(logged, None)
                require(item is not None and item['update_index'] == index, 'Episode log update/order')
                logged_hash.update(encoded(item['episode'])+b'\n')
                totals['all'] += 1
                totals['physical_failure' if episode['reason'] == 'terminal_failure' else 'timeline_complete'] += 1
                totals['stage_success'] += bool(episode['song']['stage_success'])
            before = curriculum.progress
            summary = curriculum.observe([dict(full_safe=e['reason'] == 'timeline_complete',
                finger_metrics=e['left_curriculum']['finger_metrics']) for e in episodes])
            summary.update(completed_episodes_in_update=len(episodes), progress_before=before,
                           boundary='after committed PPO collection; no scene reset')
            require(summary_close(summary, row['left_curriculum']), 'Full curriculum summary replay')
            if index+1 == checkpoint_update:
                checkpoint_curriculum = curriculum.state_vector().copy()
            reward_sum = cost_sum = raw_episodes = 0
            for tick in range(HORIZON):
                raw = next(stream, None)
                require(raw is not None, 'Missing CRC-verified gzip row')
                finite(raw)
                require(raw['schema'] == 'guitar_learning.gpu_transition.v1' and raw['update_index'] == index and raw['tick_in_update'] == tick, 'Raw transition order')
                require(all(len(raw[k]) == ENVS for k in ('reward', 'cost', 'terminated', 'truncated')), 'Raw batch dimensions')
                require(all(isinstance(v, bool) for k in ('terminated', 'truncated') for v in raw[k]) and not any(raw['truncated']), 'Raw done masks')
                require(all(v >= 0 for v in raw['cost']), 'Negative raw cost')
                ids = [e['env_id'] for e in raw['episodes']]
                require(len(ids) == len(set(ids)) and set(ids) == {i for i, v in enumerate(raw['terminated']) if v}, 'Raw terminal/episode correspondence')
                for episode in raw['episodes']:
                    raw_hash.update(encoded(episode)+b'\n')
                raw_episodes += len(ids)
                reward_sum += math.fsum(raw['reward'])
                cost_sum += math.fsum(raw['cost'])
                raw_count += 1
            require(raw_episodes == len(episodes) and expected_hash.digest() == logged_hash.digest() == raw_hash.digest(), 'Exact episode correspondence across logs')
            require(math.isclose(reward_sum/(HORIZON*ENVS), row['mean_reward'], rel_tol=1e-5, abs_tol=1e-6), 'Raw reward mean')
            require(math.isclose(cost_sum/(HORIZON*ENVS), row['mean_cost'], rel_tol=1e-5, abs_tol=1e-6), 'Raw cost mean')
            if (index+1) % 100 == 0:
                print('Verified updates', index+1, flush=True)
        if final_mode:
            require(next(stream, None) is None and raw_status['complete'], 'Extra gzip data; EOF/CRC verification failed')
    if final_mode:
        require(next(metrics, None) is None and next(logged, None) is None, 'Extra metric/episode log rows')
        require(totals['timeline_complete'] > 0, 'No whole-song timeline completion')
        song = read(run/'song_report.json')
        require(song['completed'] is True and song['partial_trajectories_are_successes'] is False and
                song['completed_episodes'] == report['completed_episodes'] == totals['all'] and
                all(song['episode_counts'][k] == totals[k] for k in ('physical_failure', 'timeline_complete', 'stage_success')), 'Final song counters')
    final = torch.load(checkpoint, map_location='cpu', weights_only=False)
    verify_architecture(final['identity']['architecture'])
    require(final['updates'] == offset+checkpoint_update and final['identity']['architecture']['contract'] == contract and final['identity']['config'] == settings['ppo'], 'Final checkpoint identity/updates')
    require(math.isfinite(final['cost_weight']) and final['cost_weight'] >= 0, 'Checkpoint cost weight')
    tensor_counts = {k: finite(final[k]) for k in ('model', 'actor_optimizer', 'value_optimizer')}
    require(tensor_counts['model'] and (checkpoint_update == 0 or
            (tensor_counts['actor_optimizer'] and tensor_counts['value_optimizer'] and final['actor_optimizer']['state'] and final['value_optimizer']['state'])), 'Checkpoint optimizer/model state')
    saved = final['model']['left_curriculum_state'].numpy()
    require(saved.shape == (3331,) and np.allclose(saved, checkpoint_curriculum, rtol=1e-10, atol=1e-12), 'Final3331 curriculum replay')
    restored = CurriculumState(counts)
    restored.load_state(saved)
    boundaries, reasons = [], Counter()
    for event in lines(run/'events.jsonl', live_tail=not final_mode):
        if not final_mode and event.get('update_index') is not None and event['update_index'] >= updates:
            break
        if event.get('event') == 'cuda_cache_release':
            require(event['after']['free_bytes'] >= 1024**3, 'GPU floor after cache recovery')
            reasons[event['reason']] += 1
            if event['reason'] == 'optimizer_boundary':
                boundaries.append((event['update_index'], event['after']))
    require([i for i, _ in boundaries] == list(range(updates)), 'Cache boundary sequence')
    free = [v['free_bytes'] for _, v in boundaries]
    base = free[0]+boundaries[0][1]['reserved_bytes']
    growth = [base-v['free_bytes']-v['reserved_bytes'] for _, v in boundaries]
    if final_mode:
        require(report['resources']['cuda_free_guard_sample_min_bytes'] >= 1024**3, 'GPU resource floor')
    ram_floor = int(settings['min_available_memory_gib']*1024**3)
    ram_min = None
    for row in lines(run/'resources.jsonl', live_tail=not final_mode):
        if not final_mode and row.get('update_index') is not None and row['update_index'] >= updates:
            break
        require(row['low_memory'] is None and row['available_memory_bytes'] >= ram_floor, 'RAM resource floor')
        ram_min = row['available_memory_bytes'] if ram_min is None else min(ram_min, row['available_memory_bytes'])
    require(ram_min is not None, 'Missing RAM samples')
    return dict(schema='guitar_learning.long_training_v6_verification.v1', run=str(run.resolve()),
                training_contract_sha256=digest(run/'training_contract.json'), source_manifest_sha256=digest(phase/'training_source_manifest.json'), completed=final_mode, prefix_verified=not final_mode, scope=__doc__.strip(), committed_updates=updates,
                committed_transitions=updates*HORIZON*ENVS, raw_rows=raw_count, raw_gzip_CRC_EOF=final_mode, selected_raw_rows_in_CRC_verified_members=True,
                exact_episode_log_correspondence=True, ended_episode_counts=dict(totals), input_pins=len(pins),
                frozen_python_verified=len(source), finite_checkpoint_tensors=tensor_counts,
                curriculum_values=3331, curriculum_replay_max_abs_error=float(np.max(np.abs(saved-checkpoint_curriculum))),
                max_episode_reward_sum_abs_error=max_episode_error, max_update_reward_sum_abs_error=max_update_error,
                reward_sum_tolerance=dict(episode=dict(rel_tol=1e-4, abs_tol=1e-3), update=dict(rel_tol=1e-5, abs_tol=1e-6)),
                PPO_reported_nonfinite_counts_zero=True, GPU_lifecycle_verified=final_mode, incremental_codec_verified=True, observation_dimension=544, priority_slots=8,
                reward_v6_contract_verified=True, new_reward_rate_bounds_verified=True, left_finger_motion_contract_verified=True, left_finger_motion_verified=totals['all']>0,
                left_finger_base_pose_verified=totals['all']>0, motion_episodes_checked=totals['all'],
                memory=dict(post_cache_free_min_GiB=min(free)/1024**3, post_cache_free_final_GiB=free[-1]/1024**3,
                            estimated_nonTorch_growth_final_GiB=growth[-1]/1024**3,
                            estimated_nonTorch_growth_max_GiB=max(growth)/1024**3,
                            estimated_nonTorch_last100_range_GiB=(max(growth[-100:])-min(growth[-100:]))/1024**3,
                            RAM_min_GiB=ram_min/1024**3, cache_release_reasons=dict(reasons)),
                checkpoint_updates=offset+checkpoint_update, local_checkpoint_updates=checkpoint_update, optimizer_offset=offset, final_checkpoint_sha256=digest(checkpoint) if final_mode else None,
                checked_checkpoint_path=str(checkpoint), checked_checkpoint_sha256=digest(checkpoint))


def verify(phase, old_run=None, run=None, copy_manifest=None, prefix=None):
    old_run = (old_run or phase/'recovered_train2000_restart1').resolve()
    run = (run or phase/'train_resume700').resolve()
    copy_manifest = copy_manifest or phase/'recovery_copy_manifest.json'
    limit = 2000 if prefix is None else prefix
    require(type(limit) is int and 1300 <= limit <= 2000, 'Global selected update count1300..2000')
    relocation = relocation_manifest(copy_manifest, old_run)
    old = verify_segment(old_run,phase,1300,relocation=relocation)
    segments = [old]
    restored = None
    if limit > 1300:
        require(read(old_run/'training_contract.json') == read(run/'training_contract.json'), 'Segment contracts differ')
        restored = verify_restore(old_run/'checkpoint_001299.pt',run/'initial.pt')
        segments.append(verify_segment(run,phase,limit-1300,offset=1300,final_mode=prefix is None))
    excluded = sorted(int(p.stem.split('_')[-1]) for p in old_run.glob('update_*.json') if int(p.stem.split('_')[-1]) >= 1300)
    require(sum(s['committed_transitions'] for s in segments) == limit*HORIZON*ENVS, 'Selected chain transitions')
    require(sum(s['raw_rows'] for s in segments) == limit*HORIZON, 'Selected chain raw rows')
    return dict(schema='guitar_learning.long_training_v6_recovery_verification.v1',
        phase=str(phase.resolve()), old_run=str(old_run), run=str(run),
        completed=prefix is None, prefix_verified=prefix is not None, committed_updates=limit,
        committed_transitions=limit*HORIZON*ENVS, raw_rows=limit*HORIZON,
        segments=segments, restore=restored, copy_manifest_sha256=digest(copy_manifest),
        copy_files_verified=len(relocation['files']), copy_bytes_verified=relocation['bytes'],
        copy_errors_history=relocation['errors'],
        source_manifest_sha256=digest(phase/'training_source_manifest.json'),
        checked_checkpoint_path=segments[-1]['checked_checkpoint_path'],
        checked_checkpoint_sha256=segments[-1]['checked_checkpoint_sha256'],
        ended_episode_counts=dict(sum((Counter(s['ended_episode_counts']) for s in segments),Counter())),
        excluded_old_update_indices=excluded, excluded_old_update_file_count=len(excluded),
        excluded_old_update_file_transitions=len(excluded)*HORIZON*ENVS,
        excluded_scope='Files at old local1300+ are excluded from the saved policy path. This does not certify their raw completeness or classify in-flight samples as committed.',
        physical_episode_boundary='New prepared episodes after1300; unfinished old physical trajectories discarded. No continuous2000-update native process is claimed.',
        lifecycle_scope='Historical segment is prefix-only, no full EOF/normal-close claim. Only resumed final segment has full gzip CRC/EOF and actual native close checks.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--old-run',type=Path)
    parser.add_argument('--run',type=Path)
    parser.add_argument('--copy-manifest',type=Path)
    parser.add_argument('--prefix',type=int,help='Global selected count1300..2000;1300 works before the resumed run exists')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();phase=args.phase.resolve()
    out=args.out or phase/('recovery_verification.json' if args.prefix is None else 'recovery_verification_prefix_%06d.json'%args.prefix)
    require(not out.exists(),'Refusing to overwrite verification output')
    torch.set_num_threads(1)
    result=verify(phase,args.old_run,args.run,args.copy_manifest,args.prefix)
    with out.open('x') as stream:json_io.dump(result,stream,indent=2,allow_nan=False)
    print(json_io.dumps(result,indent=2))


if __name__=='__main__':main()
