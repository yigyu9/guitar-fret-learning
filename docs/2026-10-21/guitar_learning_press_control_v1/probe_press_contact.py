"""Record native240Hz load and press targets under zero39 commands in N4.

No policy, PPO, pose injection or controller/physics changes. Root executes the
native probe after source freeze; physical failures/no contact remain results.
"""
import argparse
import faulthandler
from pathlib import Path
import sys
import time
import traceback

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PHASE))
from evaluate_checkpoints import json_io, require, sha, write


def allocate(samples, targets):
    import numpy as np
    specs = dict(native_contact_force=((11, 3), np.float32),
        surface_sample=((targets,), np.int32), selected_body=((targets,), np.int16),
        surface_delta=((targets, 3), np.float32), surface_distance=((targets,), np.float32),
        selected_surface_G=((targets, 3), np.float32), candidate=((targets,), np.bool_),
        contact_geometry=((targets,), np.bool_), body_loaded=((targets,), np.bool_),
        q_left21=((21,), np.float32), target_left21=((21,), np.float32),
        string_starts_G=((6, 3), np.float32), string_ends_G=((6, 3), np.float32),
        clock=((), np.int64), global_physics_step=((), np.int64))
    return {name: np.empty((4, samples)+shape, dtype=dtype) for name, (shape, dtype) in specs.items()}


def audit(arrays, metadata, episode):
    """CPU audit of first-episode clocks, body IDs and press/wire distinction."""
    import numpy as np
    count = len(arrays['clock'])
    require(count > 0 and np.array_equal(arrays['clock'], np.arange(1, count+1)), 'Consecutive actual240Hz episode clocks required')
    require(np.array_equal(np.diff(arrays['global_physics_step']), np.ones(count-1)), 'Native global clock has a gap')
    require(all(np.isfinite(v).all() for v in arrays.values()), 'Nonfinite native capture')
    if episode is not None:
        require(count == 4*episode['steps'], 'First episode end and capture length differ')
    sample = arrays['surface_sample']
    body_offset = sample//metadata['surface_samples_per_body']
    require(bool(((body_offset >= 0) & (body_offset < 10)).all()), 'Selected sample outside finger10')
    expected_body = np.array(metadata['finger_body_indices'])[body_offset]
    require(np.array_equal(expected_body, arrays['selected_body']), 'Selected sample/body mapping differs')
    require(bool((body_offset//2 == np.array(metadata['target_fingers'])[None]).all()), 'Selected sample from wrong designated finger')
    goal = arrays['selected_surface_G']+arrays['surface_delta']
    plane = np.array(metadata['press_surface']['plane_G'])
    plane_error = np.abs(goal@plane[:3]+plane[3])
    require(float(plane_error.max()) < 2e-6, 'Approach goal is not on source press plane')
    require(np.allclose(np.linalg.norm(arrays['surface_delta'], axis=-1), arrays['surface_distance'], rtol=1e-5, atol=2e-7), 'Surface distance/delta differ')
    start = arrays['string_starts_G'][:, metadata['target_strings']]
    line = arrays['string_ends_G'][:, metadata['target_strings']]-start
    wire = start+(goal[..., 1]-start[..., 1])[..., None]/line[..., 1, None]*line
    force = arrays['native_contact_force'][:, :10]
    selected_force = np.linalg.norm(force, axis=-1)[np.arange(count)[:, None], body_offset]
    # Float32 norm reduction may round at the threshold; allow only1e-7N.
    loaded = arrays['body_loaded']; threshold = metadata['force_threshold_n']
    require(bool((selected_force[loaded] >= threshold-1e-7).all()) and
            bool((selected_force[~loaded] <= threshold+1e-7).all()), 'Native selected-body load flag differs')
    return dict(samples=count, capture_hz=240, clock_passed=True, body_mapping_passed=True,
        maximum_press_plane_residual_m=float(plane_error.max()),
        virtual_wire_minus_press_goal_z_range_m=[float((wire[..., 2]-goal[..., 2]).min()), float((wire[..., 2]-goal[..., 2]).max())],
        native_body_max_force_norm_n=np.linalg.norm(arrays['native_contact_force'], axis=-1).max(0).tolist(),
        candidate_frames_per_note=arrays['candidate'].sum(0).tolist(),
        geometry_frames_per_note=arrays['contact_geometry'].sum(0).tolist(),
        selected_body_loaded_frames_per_note=loaded.sum(0).tolist(),
        scope='All recorded first-episode physics samples; frame counts are not timed note achievement or pressure. Net body forces have no contact-pair witness.')


def main():
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    import isaacgym  # Must precede NumPy/Torch/native settings imports.
    import numpy as np
    import torch
    from guitar_learning.core.control import LEFT_HAND_NAMES
    from guitar_learning.gpu.geometry import apply, conjugate
    from guitar_learning.gpu.environment import CONTACT_CONTRACT
    from guitar_learning.training.start import settings_document
    from guitar_learning.training.gpu_pool import GpuPool
    from guitar_learning.training.recording import project_source_paths
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.lower_body_release_v1.common import pin
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    settings = settings_document('left', num_envs=4, size='large', updates=1,
                                 horizon=32, device='cuda:0', physics='gpu', seed=7)
    write(out/'settings.json', settings)
    sources = {p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    sources.update((ROOT/'guitar_learning/assets').rglob('*.json'))
    sources.update((ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*.xml'))
    sources.update(p for p in Path(settings['song_training']['bundle']).rglob('*') if p.is_file())
    sources.update(prepared_input_paths())
    sources.update((out/'settings.json', Path(__file__).resolve(), PHASE/'evaluate_checkpoints.py'))
    pins = pin(BASELINE_CONFIG, extra=sources); write(out/'inputs_before.json', pins)
    torch.set_num_threads(1); torch.backends.cuda.matmul.allow_tf32 = False
    pool, buffers, metadata = None, None, None
    first_end, active, counts, pending = [None]*4, np.ones(4, bool), np.zeros(4, np.int64), []
    ticks, failure, cleanup = 0, None, []
    started = time.perf_counter()
    def status(stage):
        path = out/'lifecycle.json'
        path.with_suffix('.tmp').write_text(json_io.dumps(dict(stage=stage, control_ticks=ticks,
            first_episode_samples=counts.tolist(), wall_s=time.perf_counter()-started), allow_nan=False)+'\n')
        path.with_suffix('.tmp').replace(path)
    try:
        status('creating_pool'); pool = GpuPool(settings, out)
        env = pool.environment
        max_ticks = int(np.ceil(env.task.duration_s*60-1e-9))
        buffers = allocate(max_ticks*4, env.M)
        native_indices = torch.cat((env.finger_indices, torch.tensor([len(pool.scene.human_bodies)], device=env.device)))
        left = torch.tensor([pool.scene.names.index(n) for n in LEFT_HAND_NAMES], device=env.device)
        metadata = dict(schema='guitar_learning.press_contact_probe.v1', num_envs=4,
            capture_hz=240, control_hz=60, maximum_control_ticks=max_ticks,
            allocated_capture_bytes=sum(a.nbytes for a in buffers.values()),
            finger_body_indices=env.finger_indices.cpu().tolist(),
            native_force_body_names=[pool.scene.body_names[i] for i in env.finger_indices.cpu().tolist()]+['guitar/guitar'],
            force_threshold_n=CONTACT_CONTRACT['force_threshold_n'],
            surface_samples_per_body=env.surface_count, target_fingers=env.finger.cpu().tolist(),
            target_strings=env.string.cpu().tolist(), target_ids=[t.target_id for t in env.task.targets],
            left_joint_names=list(LEFT_HAND_NAMES), press_surface=env.press_surface,
            body_frame='Native environment-local; selected surface and string coordinates in moving guitar frame',
            clock='Actual first-episode physics clock1..4*steps; no reset/initial synthetic frame',
            selected_body='Logical body index of designated finger2/3 source surface sample; native human body index is identical',
            native_force='Unmodified native net contact tensor: human finger10 and physical compound guitar root; no pair witness',
            actions='All39 zero every60Hz; incremental left21 holds prepared targets, no policy/PPO',
            scope='First episode only per row; after termination, selective reset plus zero-action filler is unrecorded. Physical failure/no contact are diagnostic results, not silently removed.')
        write(out/'capture_metadata.json', metadata); write(out/'training_contract.json', pool.contract)
        require(not set(metadata['press_surface']['source_sha256'])-set(pins), 'Press source missing from input pins')
        original = env.substep
        def recorded_substep(snapshot):
            original(snapshot)
            chosen = env.surface_sample
            offset = chosen//env.surface_count
            body_id = env.finger_indices[offset]
            body = env.body[torch.arange(4, device=env.device)[:, None], body_id]
            local = env.surface_local.flatten(0, 1)[chosen]
            world = body[..., :3]+apply(body[..., 3:7], local)
            point = apply(conjugate(env.guitar_q[:, None]), world-env.guitar_body[:, None, :3])
            row = dict(native_contact_force=pool.scene._native_contact_force[:, native_indices],
                surface_sample=chosen, selected_body=body_id, surface_delta=env.surface_delta,
                surface_distance=env.surface_distance, selected_surface_G=point,
                candidate=env.candidate, contact_geometry=env.contact_geometry,
                body_loaded=env.surface_body_loaded, q_left21=snapshot['q'][:, left],
                target_left21=snapshot['target'][:, left], string_starts_G=env.starts,
                string_ends_G=env.ends, clock=env.clock)
            values = {key: value.detach().cpu().numpy() for key, value in row.items()}
            for index in np.flatnonzero(active):
                slot = int(counts[index])
                require(slot < max_ticks*4, 'Capture exceeds bounded full-song allocation')
                for key, value in values.items():
                    buffers[key][index, slot] = value[index]
                buffers['global_physics_step'][index, slot] = pool.scene.physics_steps
                counts[index] += 1
        env.substep = recorded_substep
        action = torch.zeros(4, 39, device=env.device)
        status('recording')
        for _ in range(max_ticks):
            if pending:
                pool.reset(pending)
            result = pool.step(action); ticks += 1
            for episode in result[5]:
                index = episode['env_id']
                if active[index]:
                    first_end[index] = episode; active[index] = False
            pending = (result[3]|result[4]).nonzero().flatten().cpu().tolist()
            if ticks%60 == 0:
                status('recording')
            if not active.any():
                break
        require(not active.any(), 'All first episodes must end within the song horizon')
        status('first_episodes_complete')
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        traceback.print_exc()
    finally:
        if pool is not None:
            try:
                pool.close()
            except BaseException as error:
                cleanup.append(repr(error))
    captures = []
    if buffers is not None and metadata is not None:
        for index in range(4):
            arrays = {key: value[index, :counts[index]] for key, value in buffers.items()}
            path = out/('raw_env%04d.npz'%index)
            np.savez_compressed(str(path), **arrays)
            try:
                proof = audit(arrays, metadata, first_end[index])
            except BaseException as error:
                proof = dict(error=repr(error))
                if failure is None:
                    failure = dict(type='CaptureAuditError', message=repr(error))
            captures.append(dict(env_id=index, path=path.name, sha256=sha(path),
                first_episode=first_end[index], audit=proof))
    scene = pool.scene.diagnostics if pool is not None and pool.scene is not None else None
    changed = [name for name, value in pins.items() if not Path(name).is_file() or sha(name) != value]
    missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
    native_ok = bool(scene and scene['closed'] and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and
        scene['simulator_count'] == 1 and scene['environment_count'] == 4 and scene['physics_steps'] == 4*ticks and
        all(device == 'cuda:0' for device in scene['tensor_devices'].values()))
    completed = failure is None and not(cleanup or changed or missing) and native_ok and all(first_end)
    report = dict(completed=completed, failure=failure, cleanup_errors=cleanup, changed_inputs=changed,
        missing_import_pins=missing, gpu_scene=scene, control_ticks=ticks, capture_hz=240,
        recorded_first_episode_samples=counts.tolist(), captures=captures,
        policy_inference_steps=0, PPO_updates=0, actions='zero39', wall_s=time.perf_counter()-started,
        scope='Completed means diagnostic recording/lifecycle/pins passed, not physical safety, note success or pressure certification.')
    write(out/'report.json', report); status('report_written')
    print(json_io.dumps(dict(completed=completed, samples=counts.tolist(),
        outcomes=[e['reason'] if e else None for e in first_end]), allow_nan=False))
    return 0 if completed else 1


if __name__ == '__main__':
    sys.exit(main())
