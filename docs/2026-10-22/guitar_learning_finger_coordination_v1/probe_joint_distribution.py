"""Root-only N4 fixed-command posture comparison; no policy, learning or state injection."""
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
sys.path.insert(0, str(ROOT))
from guitar_learning.training import json_io

FINGERS = ('index', 'middle', 'ring', 'pinky')
JOINTS = tuple('LH:'+f+s for f in FINGERS for s in ('1_x', '1_z', '2', '3'))
CASES = (('distal_only', (0, 0, 0, 90)), ('distributed', (40, 0, 55, 35)),
         ('standby', (30, 0, 30, 15)), ('straight', (0, 0, 0, 0)))
TICKS = 180


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json_io.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def goals_rad():
    """Four rows by four fingers by native1_x/1_z/2/3; radians."""
    import numpy as np
    return np.deg2rad(np.array([list(angles)*4 for _, angles in CASES], dtype=np.float64))


def command_actions(current, goals, low, high):
    """Only incremental16 actions; no target/state writes. NumPy CPU fixture API."""
    import numpy as np
    require(current.shape == goals.shape == (4, 16) and low.shape == high.shape == (16,), 'N4 by16 goal arrays required')
    require(all(np.isfinite(v).all() for v in (current, goals, low, high)) and
            (goals >= low-1e-6).all() and (goals <= high+1e-6).all(), 'Goal outside finite native bounds')
    return np.clip((goals-current)*60/4, -1, 1)


def main():
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    settings_path, out = args.settings.resolve(), args.out.resolve()
    settings = json.loads(settings_path.read_text())
    require(settings['specialist']['role'] == 'left' and settings['device'] == 'cuda:0' and
            settings['size'] == 'large' and settings['horizon'] == 32, 'Large GPU left/H32 settings required')
    settings = copy.deepcopy(settings)
    settings['num_envs'] = 4
    # No Torch/NumPy import occurs before the native SDK boundary.
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import GpuPool
    from guitar_learning.training.recording import project_source_paths
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.lower_body_release_v1.common import pin
    from guitar_learning.gpu.finger_reward import finger_posture_reward, FINGER_COORDINATION_CONTRACT, source_finger_frame_contract
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', settings)
    sources = {p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    sources.update((ROOT/'guitar_learning/assets').rglob('*.json'))
    sources.update((ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*.xml'))
    sources.update(p for p in Path(settings['song_training']['bundle']).rglob('*') if p.is_file())
    sources.update(prepared_input_paths())
    sources.update((settings_path, out/'settings.json', Path(__file__).resolve()))
    pins = pin(BASELINE_CONFIG, extra=sources)
    require(all(sha(p) == h for p,h in pins.items()), 'Input pin mismatch before native pool')
    write(out/'inputs_before.json', pins)
    frame_contract = source_finger_frame_contract()
    pool, metadata, error = None, None, None
    cleanup, frames, ended = [], [], []
    ticks = 0
    started = time.perf_counter()
    recurrence_error = 0.

    def status(stage):
        temp = out/'lifecycle.tmp'
        temp.write_text(json_io.dumps(dict(stage=stage, ticks=ticks, wall_s=time.perf_counter()-started), allow_nan=False)+'\n')
        temp.replace(out/'lifecycle.json')

    def capture(action):
        env = pool.environment
        snapshot = env.snapshot
        row = {k:snapshot[k].detach().cpu().numpy().copy() for k in ('body_state','q','qd','target')}
        row.update(action=action.detach().cpu().numpy().copy(), clock=env.clock.cpu().numpy().copy())
        now = env.clock.to(env.onset.dtype)/240.
        common = (env.body[:,env.finger_palm_index,3:7], env.body[:,env.finger_segment_indices,3:7])
        actual = finger_posture_reward(now, env.onset, env.end, env.press, env.finger, *common)
        empty = env.onset[:0]
        idle = finger_posture_reward(now, empty, empty, empty, env.finger[:0], *common)
        for prefix, values in (('actual_song',actual), ('all_idle_counterfactual',idle)):
            for key,value in values.items():
                row[prefix+'_'+key] = value.detach().cpu().numpy().copy()
        frames.append(row)

    try:
        status('creating_pool')
        pool = GpuPool(settings, out)
        scene, ctl = pool.scene, pool.controller
        require(pool.contract['reward']['schema'].endswith('.v5'), 'Current posture rewardv5 required')
        ids = torch.tensor([scene.names.index(n) for n in JOINTS], device=scene.device)
        action_ids = torch.tensor([ctl.contract['action_order'].index(n) for n in JOINTS], device=scene.device)
        low, high = ctl.action_low[action_ids], ctl.action_high[action_ids]
        goals = torch.tensor(goals_rad(), device=scene.device, dtype=scene.q.dtype)
        command_actions(ctl.target[:,ids].cpu().numpy(), goals.cpu().numpy(), low.cpu().numpy(), high.cpu().numpy())
        initial = pool.environment.snapshot
        initial_spread = {k:float((initial[k]-initial[k][0:1]).abs().max().item()) for k in ('q','body_state')}
        require(max(initial_spread.values()) <= 1e-6, 'All4 prepared035 rows must match before first command')
        metadata = dict(schema='guitar_learning.joint_distribution_fixed_probe.v1', cases=[dict(env_id=i,name=name,goal_per_finger_degrees=list(a)) for i,(name,a) in enumerate(CASES)],
            joint_names=scene.names, body_names=scene.body_names, tested_joint_names=list(JOINTS),
            tested_native_indices=ids.cpu().tolist(), tested_action_indices=action_ids.cpu().tolist(),
            native_lower_rad=low.cpu().tolist(), native_upper_rad=high.cpu().tolist(), goals_rad=goals.cpu().tolist(),
            initial_row_spread=initial_spread, frame_contract=frame_contract, posture_contract=FINGER_COORDINATION_CONTRACT,
            schedule=dict(maximum_ticks=TICKS,control_hz=60,physics_hz=240),
            action_scope='Only16 finger commands are submitted; thumb/arms/all other23 actions remain0. Absolute channels follow their normal reference codec.',
            diagnostics='60Hz actual endpoint full-quaternion geometric angles. actual_song uses current song clock; all_idle_counterfactual passes an empty score. Both are raw helper rates before curriculum/failure masks, not integrated or earned task rewards.',
            scope='Fixed commands, not a learned policy comparison. First native episode end stops all4; surviving rows right-censored. No reset after initial035, target/state injection or force manipulation.')
        write(out/'training_contract.json', pool.contract)
        write(out/'visual_initial.json', scene.contract['initial'])
        zero = torch.zeros(4,39, device=scene.device)
        with torch.no_grad():
            capture(zero)
            for tick in range(TICKS):
                action = zero.clone()
                before = ctl.target[:,ids].clone()
                action[:,action_ids] = ((goals-before)*60/4).clamp(-1,1)
                _, reward, cost, terminated, truncated, episodes = pool.step(action)
                ticks += 1
                capture(action)
                expected = (before+action[:,action_ids]*(4./60)).clamp(low,high)
                recurrence_error = max(recurrence_error,float((ctl.target[:,ids]-expected).abs().max().item()))
                require(bool(torch.isfinite(reward).all() and torch.isfinite(cost).all()), 'Nonfinite transition')
                if bool((terminated|truncated).any()):
                    ended = episodes
                    break
                if ticks%60 == 0:
                    status('stepping')
        require(recurrence_error <= 4e-6, 'Native incremental target recurrence differs')
    except BaseException as exc:
        error = dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
        write(out/'python_exception.json',error)
        traceback.print_exc();sys.stderr.flush()
    finally:
        if pool is not None:
            status('synchronizing_before_close')
            try:
                torch.cuda.synchronize(pool.scene.device)
            except BaseException as exc:
                cleanup.append('synchronize: '+repr(exc))
            try:
                status('closing_pool');pool.close()
            except BaseException as exc:
                cleanup.append('close: '+repr(exc))
    audit, summaries = None, []
    if frames:
        arrays = {key:np.stack([r[key] for r in frames]) for key in frames[0]}
        finite = all(np.isfinite(v).all() for v in arrays.values())
        clock_exact = np.array_equal(arrays['clock'],np.repeat((np.arange(len(frames))*4)[:,None],4,axis=1))
        shape_ok = arrays['body_state'].shape == (ticks+1,4,106,13)
        path = out/'poses.npz';np.savez_compressed(str(path),**arrays)
        audit = dict(finite=finite,clock_exact=bool(clock_exact),body_shape_exact=shape_ok,path=path.name,sha256=sha(path),frames=len(frames))
        if not(finite and clock_exact and shape_ok) and error is None:
            error = dict(type='CaptureAuditError',message='Raw capture retained; finite/clock/body-shape audit failed')
        if metadata is not None:
            metadata['capture'] = audit
            write(out/'capture_metadata.json',metadata)
        first = max(1,len(frames)-30)
        for env_id in (range(4) if ticks and finite and clock_exact and shape_ok else ()):
            summary = dict(env_id=env_id,name=CASES[env_id][0],tail_endpoint_samples=len(frames)-first,
                tail_coverage_s=(len(frames)-first)/60.,tail_start_s=first/60.,tail_end_s=ticks/60.,
                final_goal_target_max_error_rad=float(np.max(np.abs(arrays['target'][-1,env_id,ids.cpu().numpy()]-goals[env_id].cpu().numpy()))))
            for prefix in ('actual_song','all_idle_counterfactual'):
                summary[prefix] = {key:arrays[prefix+'_'+key][first:,env_id].mean(0).tolist() for key in
                    ('angles','coordination_quality','standby_quality','idle_weight','coordination_rate','standby_rate')}
                summary[prefix]['valid_fraction'] = arrays[prefix+'_valid'][first:,env_id].mean(0).tolist()
            summaries.append(summary)
    changed = [p for p,h in pins.items() if not Path(p).is_file() or sha(p)!=h]
    missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
    diagnostics = pool.scene.diagnostics if pool is not None and pool.scene is not None else None
    native_ok = bool(diagnostics and diagnostics['closed'] and diagnostics['physx_use_gpu'] and diagnostics['use_gpu_pipeline'] and diagnostics['num_envs']==4 and diagnostics['simulator_count']==1 and diagnostics['physics_steps']==ticks*4)
    result = dict(completed=error is None and not(cleanup or changed or missing) and native_ok,
        schedule_completed=ticks==TICKS,actual_control_ticks=ticks,actual_physics_steps=ticks*4,
        first_ended_episodes=ended,failure=error,cleanup_errors=cleanup,changed_inputs=changed,missing_import_pins=missing,
        gpu_scene=diagnostics,capture_audit=audit,tail_summaries=summaries,recurrence_max_error_rad=recurrence_error,
        source_python_count=sum('/guitar_learning/' in p and p.endswith('.py') for p in pins),
        model_loaded=False,PPO_updates=0,wall_s=time.perf_counter()-started,
        scope='Actual fixed-command posture probe; schedule completion is not song success or training improvement. Both posture rates are unmasked endpoint diagnostics; counterfactual all-idle values are not actual task rewards.')
    write(out/'report.json',result);status('report_written')
    print(json_io.dumps(dict(completed=result['completed'],schedule_completed=result['schedule_completed'],ticks=ticks)))
    return 0 if result['completed'] else 1


if __name__ == '__main__':
    sys.exit(main())
