"""Small native-GPU command probe; root runs this only after source freeze.

No policy/PPO, gain changes, joint-state injection or safety suppression.
Positive/negative mean native generalized-coordinate direction, not anatomy.
"""
import argparse
import faulthandler
import hashlib
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from guitar_learning.training import json_io

AMPLITUDES = (.1, -.1, .2, -.2)
PUSH, HOLD, REVERSE = 30, 10, 30


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json_io.dump(value, stream, allow_nan=False, indent=2)
        stream.write('\n')


def command_batches(count):
    require(type(count) is int and 1 <= count <= 8, 'num-envs must be1..8')
    return [tuple(AMPLITUDES[(start+i) % 4] for i in range(count))
            for start in range(0, 4, count)]


def command_at(tick, amplitude):
    require(0 <= tick < PUSH+HOLD+REVERSE, 'Invalid trial tick')
    return amplitude if tick < PUSH else 0. if tick < PUSH+HOLD else -amplitude


def mapping(contract):
    codec = contract['action_codec']
    require(contract['schema'] == 'guitar_learning.gpu_finite_control.v3' and
            codec['schema'] == 'guitar_learning.gpu_left_incremental_fingers.v1' and
            codec['velocity_scale_rad_s'] == 4. and codec['control_hz'] == 60 and
            contract['physics_hz'] == 240, 'Wrong incremental control contract')
    names, order = contract['joint_names'], contract['action_order']
    joints, actions = codec['incremental_joint_names'], codec['incremental_action_indices']
    require(len(names) == len(set(names)) == 105 and len(order) == len(set(order)) == 39,
            'Expected unique native105/action39')
    require(len(joints) == len(set(joints)) == len(actions) == 21, 'Expected21 unique finger axes')
    require(all(type(a) is int and 0 <= a < 39 and order[a] == n for n,a in zip(joints, actions)),
            'Finger/action name mismatch')
    native = [names.index(n) for n in joints]
    require(all(i in contract['position_indices'] and contract['rate_rad_s'][i] == 4. and
                contract['smoothing_alpha'][a] == 1. for i,a in zip(native, actions)),
            'Finger POSITION/rate/smoothing mismatch')
    return native, actions


def audit_trace(arrays, contract, tested_joint, amplitude):
    """Independent CPU recurrence; actual motion is measured, never inferred."""
    import numpy as np
    native, actions = mapping(contract)
    frames = len(arrays['clock'])
    require(1 <= frames <= PUSH+HOLD+REVERSE+1, 'Invalid frame count')
    shapes = dict(q=(frames,105), qd=(frames,105), target=(frames,105),
                  action=(frames,39), body_state=(frames,106,13), clock=(frames,),
                  global_physics_step=(frames,))
    for key, shape in shapes.items():
        require(arrays[key].shape == shape and bool(np.isfinite(arrays[key]).all()), 'Invalid '+key)
    require(bool((arrays['action'][0] == 0).all()), 'Initial command sentinel must be zero')
    require(np.array_equal(arrays['clock'], np.arange(frames)*4) and
            np.array_equal(np.diff(arrays['global_physics_step']), np.full(frames-1,4)), 'Physics clock mismatch')
    require(np.max(np.abs(np.linalg.norm(arrays['body_state'][...,3:7],axis=-1)-1)) < 1e-3,
            'Invalid body quaternion')
    lo = np.array(contract['action_lower_rad'])[actions]
    hi = np.array(contract['action_upper_rad'])[actions]
    targets = arrays['target'][:,native]
    expected = targets[0].astype(np.float64).copy()
    error = 0.
    tested = contract['action_codec']['incremental_joint_names'].index(tested_joint)
    require(np.allclose(targets[0], np.array(contract['reference105_rad'])[native], rtol=0,atol=3e-6),
            'Initial finger target was not prepared reset')
    for t in range(1,frames):
        prescribed = np.zeros(39)
        prescribed[actions[tested]] = command_at(t-1,amplitude)
        require(np.allclose(arrays['action'][t],prescribed,rtol=0,atol=1e-7), 'Applied command differs')
        expected = np.clip(expected+prescribed[actions]*(4./60),lo,hi)
        error = max(error,float(np.max(np.abs(expected-targets[t]))))
    require(error <= 4e-6, 'Incremental target recurrence failed: '+str(error))
    q = arrays['q'][:,native[tested]]
    target = targets[:,tested]
    sign = 1 if amplitude > 0 else -1
    bound = hi[tested] if sign > 0 else lo[tested]
    # Only observed saturation/reversal can certify absence of latent windup.
    saturated = sum(abs(float(target[t])-bound) <= 2e-6 for t in range(1,min(frames,PUSH+1)))
    reversal = frames > PUSH+HOLD+1
    reverse_delta = float(target[PUSH+HOLD+1]-target[PUSH+HOLD]) if reversal else None
    no_windup = saturated >= 2 and reversal and reverse_delta*sign < -1e-7
    end_push, end_hold = min(PUSH,frames-1), min(PUSH+HOLD,frames-1)
    return dict(control_contract_passed=True, control_ticks=frames-1,
        complete_schedule=frames == PUSH+HOLD+REVERSE+1, max_target_recurrence_error_rad=error,
        target_push_delta_rad=float(target[end_push]-target[0]),
        target_hold_delta_rad=float(target[end_hold]-target[end_push]),
        target_reverse_delta_rad=float(target[-1]-target[end_hold]) if reversal else None,
        first_reverse_target_delta_rad=reverse_delta, observed_saturated_push_endpoints=saturated,
        no_windup_observed=no_windup,
        actual_push_delta_rad=float(q[end_push]-q[0]),
        actual_hold_delta_rad=float(q[end_hold]-q[end_push]),
        actual_reverse_delta_rad=float(q[-1]-q[end_hold]) if reversal else None,
        actual_range_rad=float(np.ptp(q)), actual_motion_observed=bool(np.ptp(q)>1e-4),
        endpoint_tracking_rms_rad=float(np.sqrt(np.mean((q[1:]-target[1:])**2))) if frames>1 else None)


def main():
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--num-envs',type=int,default=4)
    parser.add_argument('--joint',action='append',help='Exact LH joint name; default all21')
    args = parser.parse_args()
    batches = command_batches(args.num_envs)
    # Native SDK import MUST precede NumPy/Torch or any settings/control import.
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.core.control import LEFT_HAND_NAMES, ACTIVE_NAMES
    from guitar_learning.training.start import settings_document
    from guitar_learning.training.gpu_pool import GpuPool
    from guitar_learning.training.recording import project_source_paths
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.lower_body_release_v1.common import pin
    joints = list(LEFT_HAND_NAMES) if args.joint is None else args.joint
    require(bool(joints) and len(set(joints)) == len(joints) and all(n in LEFT_HAND_NAMES for n in joints),
            'Unique supported LH joints required')
    out = args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    settings = settings_document('left',num_envs=args.num_envs,size='large',updates=1,
                                 horizon=32,device='cuda:0',physics='gpu',seed=7)
    write(out/'settings.json',settings)
    sources = {p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    sources.update((ROOT/'guitar_learning/assets').rglob('*.json'))
    sources.update((ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*.xml'))
    sources.update(p for p in Path(settings['song_training']['bundle']).rglob('*') if p.is_file())
    sources.update(prepared_input_paths())
    sources.update((out/'settings.json',Path(__file__).resolve()))
    pins = pin(BASELINE_CONFIG,extra=sources)
    write(out/'inputs_before.json',pins)
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    pool, failure, cleanup_errors, trials = None, None, [], []
    ticks, stage = 0, 'creating_pool'
    started = time.perf_counter()
    def lifecycle(value):
        nonlocal stage
        stage = value
        path = out/'lifecycle.json'
        path.with_suffix('.tmp').write_text(json_io.dumps(dict(stage=stage,control_ticks=ticks,
            wall_s=time.perf_counter()-started),allow_nan=False)+'\n')
        path.with_suffix('.tmp').replace(path)
    try:
        lifecycle('creating_pool')
        pool = GpuPool(settings,out)
        contract = pool.controller.contract
        native, actions = mapping(contract)
        require(contract['action_order'] == list(ACTIVE_NAMES) and
                contract['action_codec']['incremental_joint_names'] == list(LEFT_HAND_NAMES), 'Canonical mapping mismatch')
        write(out/'control_contract.json',contract)
        write(out/'visual_initial.json',pool.scene.contract['initial'])
        write(out/'capture_metadata.json',dict(schema='guitar_learning.gpu_finger_probe_capture.v1',
            body_names=pool.scene.body_names,joint_names=pool.scene.names,physics_hz=240,capture_hz=60,
            body_frame='Native environment-local world',initial_frame='Prepared reset; frame0 action sentinel',
            clock='Per-trial physics clock0,4,...; global_physics_step never resets',
            action='Frame k>0 is the command applied over preceding4 native physics steps',
            axes=[dict(joint=n,body=pool.controller.bodies[int(pool.controller.joint_bodies[i].item())],
                       source_body_local_axis=pool.controller.axes[i].cpu().tolist()) for n,i in zip(LEFT_HAND_NAMES,native)],
            direction='Native joint-coordinate sign, not an anatomical flexion/extension claim',
            amplitudes=AMPLITUDES,push_ticks=PUSH,hold_ticks=HOLD,reverse_ticks=REVERSE,
            selection='All requested joints and all four commands; duplicate rows are not independent trials'))
        lifecycle('probing')
        for joint in joints:
            for amplitudes in batches:
                pool.reset()
                frames, episodes, terminal_ids = [], [], set()
                def capture(action):
                    sample = pool.scene.snapshot()
                    row = {key:sample[key].detach().cpu().numpy().copy() for key in ('body_state','q','qd','target')}
                    row.update(action=action.detach().cpu().numpy().copy(),
                        clock=pool.environment.clock.cpu().numpy().copy(),
                        global_physics_step=np.full(args.num_envs,pool.scene.physics_steps,dtype=np.int64))
                    frames.append(row)
                action = torch.zeros(args.num_envs,39,device=pool.scene.device)
                capture(action)
                batch_error = None
                try:
                    for t in range(PUSH+HOLD+REVERSE):
                        action.zero_()
                        a = actions[list(LEFT_HAND_NAMES).index(joint)]
                        action[:,a] = torch.tensor([command_at(t,v) for v in amplitudes],device=pool.scene.device)
                        result = pool.step(action)
                        ticks += 1
                        capture(action)
                        if result[5]:
                            episodes.extend(result[5])
                        if bool((result[3]|result[4]).any()):
                            terminal_ids.update((result[3]|result[4]).nonzero().flatten().cpu().tolist())
                            break  # Keep terminal state; never step a failed row or hide it by reset.
                except BaseException as error:
                    batch_error = dict(type=type(error).__name__,message=str(error))
                    raise
                finally:
                    # Persist completed snapshots even if the next native operation raises.
                    for env_id, amplitude in enumerate(amplitudes):
                        arrays = {key:np.stack([f[key][env_id] for f in frames]) for key in frames[0]}
                        filename = 'trial_%04d.npz' % len(trials)
                        np.savez_compressed(str(out/filename),**arrays)
                        row = dict(path=filename,sha256=sha(out/filename),joint=joint,env_id=env_id,
                            amplitude=amplitude,batch_error=batch_error,terminal=env_id in terminal_ids,
                            episodes=[e for e in episodes if e['env_id']==env_id])
                        trials.append(row)
                        row['audit'] = audit_trace(arrays,contract,joint,amplitude)
                    write(out/('batch_%04d.json'%len(trials)),trials[-args.num_envs:])
                lifecycle('probing')
        lifecycle('steps_complete')
        torch.cuda.synchronize()
    except BaseException as error:
        failure = dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc(),stage=stage)
        write(out/'python_exception.json',failure)
        traceback.print_exc()
    finally:
        if pool is not None:
            try:
                lifecycle('closing')
                torch.cuda.synchronize()
            except BaseException as error:
                cleanup_errors.append(dict(component='preclose_sync',message=repr(error)))
            try:
                pool.close()
            except BaseException as error:
                cleanup_errors.append(dict(component='pool.close',message=repr(error)))
        changed = [p for p,h in pins.items() if not Path(p).is_file() or sha(p)!=h]
        missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        scene = pool.scene.diagnostics if pool is not None and pool.scene is not None else None
        native_ok = bool(scene and scene['closed'] and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and
                         scene['simulator_count']==1 and scene['environment_count']==args.num_envs and
                         all(str(v).startswith('cuda:') for v in scene['tensor_devices'].values()) and
                         scene['physics_steps']==4*ticks)
        complete = failure is None and not(cleanup_errors or changed or missing) and native_ok
        physical_failures = sum(row['terminal'] for row in trials)
        observed = sum(row.get('audit',{}).get('no_windup_observed',False) for row in trials)
        motion = sum(row.get('audit',{}).get('actual_motion_observed',False) for row in trials)
        report = dict(schema='guitar_learning.gpu_finger_probe.v1',completed=complete,
            passed=complete and not physical_failures and all(row['audit']['complete_schedule'] for row in trials),
            failure=failure,cleanup_errors=cleanup_errors,changed_inputs=changed,missing_import_pins=missing,
            gpu_scene=scene,control_ticks=ticks,wall_s=time.perf_counter()-started,
            physical_terminal_rows=physical_failures,no_windup_observed_trials=observed,
            actual_motion_observed_trials=motion,actual_motion_observed_all=motion==len(trials) and bool(trials),
            no_windup_coverage='Only reported observed trials; other native limits were not reached/tested',trials=trials,
            scope='Command recurrence validation and measured physical response; uncovered saturation is not certified; no pressure/song-learning claim')
        write(out/'report.json',report)
        lifecycle('report_written')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
