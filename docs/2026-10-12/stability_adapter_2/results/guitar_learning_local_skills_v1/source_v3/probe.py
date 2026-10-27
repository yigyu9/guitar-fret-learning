"""Measure bounded local actions using the original563 task and safety gates."""
import argparse
import copy
import gzip
import json
import os
from pathlib import Path
import sys
import time


def available_gib():
    return next(int(line.split()[1])*1024/2**30 for line in Path('/proc/meminfo').read_text().splitlines()
                if line.startswith('MemAvailable:'))


def successful_episode(episode, *, ticks):
    return bool(episode and ticks == 420 and episode.get('valid') is True
        and episode.get('reason') == 'timeline_complete'
        and abs(episode.get('task_time_s', -1)-7.) < 1e-9
        and episode.get('musical_quality', {}).get('stage_success') is True)


def run(settings, args):
    import isaacgym
    import numpy as np
    import torch
    from ..imitation_io import CONFIG, BUNDLE, pin_inputs
    from ..imitation_v2 import canonical_contract
    from ..parallel import FIELDS
    from ..recording import digest, write, project_source_paths
    from ..specialist_policy import SpecialistPolicy
    from ..musical_quality_environment import build_environment
    from ..timing_curriculum import TimingConfig
    from .controls import Controller, candidate_configs, normalize_target

    role = settings['specialist']['role']
    candidates = args.candidates or ['policy', 'zero'] + [x['name'] for x in candidate_configs(role)]
    allowed = {'policy', 'zero'} | {x['name'] for x in candidate_configs(role)}
    if not candidates or len(set(candidates)) != len(candidates) or set(candidates)-allowed:
        raise ValueError('explicit unique known candidates for the configured hand required')
    if args.device not in ('cpu', 'cuda:0'):
        raise ValueError('explicit cpu or cuda:0 policy device required')
    if available_gib() < 8:
        raise RuntimeError('at least8 GiB MemAvailable required before one native probe')
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    checkpoint = args.checkpoint.resolve()
    torch.set_num_threads(1); torch.backends.cuda.matmul.allow_tf32 = False
    torch.manual_seed(settings['seed']); np.random.seed(settings['seed'])
    pins = pin_inputs([checkpoint, args.settings.resolve(), Path(__file__).resolve()])
    # Concurrent additions for BC/dispatch are not imported by this native probe.
    pins = {p:h for p,h in pins.items() if '/tests/' not in p and
        ('/guitar_learning/local_skills/' not in p or Path(p).name in ('__init__.py','controls.py','probe.py'))}
    write(out/'inputs_before.json', pins)
    write(out/'settings.json', settings)
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    arch = payload.get('identity', {}).get('architecture')
    if (payload.get('identity', {}).get('schema') != 'guitar_learning_ppo_v1'
            or type(payload.get('updates')) is not int or payload['updates'] < 1
            or not isinstance(arch, dict) or arch.get('state_dim') != 563
            or arch.get('role') != role or arch.get('frozen_partner') is not False):
        raise ValueError('own563 single-hand PPO checkpoint required')
    if not isinstance(payload.get('model'), dict) or any(not isinstance(v, torch.Tensor)
            or not torch.isfinite(v).all() for v in payload['model'].values()):
        raise ValueError('finite own PPO model weights required')
    env = build_environment(CONFIG, out/'environment', role=role, bundle=BUNDLE,
        timing=TimingConfig(**settings['timing']))
    results = []
    started = time.monotonic()
    model = None
    scene = None
    try:
        for candidate in candidates:
            if available_gib() < 8:
                raise RuntimeError('at least8 GiB available before another case')
            case = out/candidate; case.mkdir()
            arrays = {key: [] for key in FIELDS}
            arrays.update(action=[], policy_action=[], intervention=[], task_time_s=[])
            episode = None; failure = None; physical = False; ticks = 0
            controller = None if candidate in ('policy','zero') else Controller(role, candidate)
            try:
                observation, info = env.reset()
                write(case/'reset.json', info)
                scene = env.control.session.scene
                if model is None:
                    model = SpecialistPolicy(563, size=arch['size'], role=role,
                        frozen_partner=False, contract=env.contract).to(args.device)
                    if canonical_contract(model.architecture) != canonical_contract(arch):
                        raise ValueError('checkpoint/native task architecture or control contract mismatch')
                    model.load_state_dict(payload['model'], strict=True); model.eval()
                elif canonical_contract(env.contract) != canonical_contract(model.architecture['contract']):
                    raise RuntimeError('persistent reset changed the source contract')
                codec = env.control.contract
                selection = codec.active_indices
                qref = codec.q_ref[selection]
                last_info = info
                case_start = time.monotonic()
                with gzip.open(case/'trace.jsonl.gz', 'xt', compresslevel=1) as trace:
                    for tick in range(420):
                        if time.monotonic()-case_start > 600:
                            raise TimeoutError('single native case exceeded600 seconds')
                        if tick % 60 == 0:
                            free = available_gib()
                            print('[local probe] role=%s case=%s tick=%d/420 free=%.2f GiB' %
                                  (role,candidate,tick,free), flush=True)
                            if free < 6:
                                raise RuntimeError('native probe memory protection6 GiB')
                        before = {key: np.array(observation[key], copy=True) for key in FIELDS}
                        tensors = [torch.as_tensor(before[key], device=args.device).unsqueeze(0) for key in FIELDS]
                        with torch.no_grad():
                            policy_action = model.act(*tensors, deterministic=True)['action'][0].cpu().numpy()
                        context = dict(time_s=float(tick)/60., task_end_s=env.task.targets[0].end_s,
                            musical_quality_before=last_info['musical_quality'],
                            applied_normalized39=normalize_target(env.control.codec_previous[selection],
                                qref, codec.action_lower, codec.action_upper),
                            reference39=qref.tolist(), lower39=codec.action_lower.tolist(),
                            upper39=codec.action_upper.tolist())
                        if candidate == 'policy': action, intervention = policy_action.copy(), False
                        elif candidate == 'zero': action, intervention = np.zeros(39), False
                        else: action, intervention = controller.action(policy_action, context)
                        action = np.asarray(action, dtype=np.float32)
                        inactive = slice(33,39) if role == 'left' else slice(0,33)
                        if action.shape != (39,) or not np.isfinite(action).all() or np.any(np.abs(action)>1) or np.any(action[inactive] != 0):
                            raise ValueError('bounded39 command and exactly zero inactive hand required')
                        observation, reward, terminated, truncated, info = env.step(action)
                        ticks += 1; last_info = info
                        physical |= bool(info['failure_reasons'])
                        for key in FIELDS: arrays[key].append(before[key])
                        arrays['action'].append(action.copy())
                        arrays['policy_action'].append(policy_action.copy())
                        arrays['intervention'].append(bool(intervention))
                        arrays['task_time_s'].append(tick/60.)
                        row = dict(tick=tick, task_time_before_s=tick/60., action=action.tolist(),
                            policy_action=policy_action.tolist(), intervention=bool(intervention),
                            controller_diagnostic=copy.deepcopy(controller.diagnostic) if controller else {},
                            reward=reward, terminated=terminated, truncated=truncated, info=info)
                        def encode(value):
                            if isinstance(value, np.ndarray): return value.tolist()
                            if isinstance(value, np.generic): return value.item()
                            raise TypeError(type(value).__name__)
                        trace.write(json.dumps(row,default=encode,allow_nan=False)+'\n')
                        if terminated or truncated:
                            episode = copy.deepcopy(info['episode'])
                            break
            except BaseException as error:
                failure = dict(type=type(error).__name__, message=str(error))
                raise
            finally:
                np.savez_compressed(case/'demonstration.npz', **{k:np.asarray(v) for k,v in arrays.items()})
                flags = bool(scene is not None and scene.human_root_fixed is True
                    and scene.guitar_root_fixed is False and scene.guitar_gravity_disabled is False
                    and not scene.forbidden_calls and np.array_equal(scene.pd_properties, env.control.original_properties))
                changed = [path for path,sha in pins.items() if not Path(path).is_file() or digest(path) != sha]
                unchanged = not changed
                missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
                result = dict(schema='guitar_learning.local_skill_probe.v1', role=role, candidate=candidate,
                    source_checkpoint=str(checkpoint), source_checkpoint_sha256=digest(checkpoint),
                    policy_loading='exact full PPO model weights; deterministic execution, no optimizer/RNG resume',
                    policy_device=args.device, completed=ticks==420 and episode is not None and
                        episode.get('reason')=='timeline_complete' and failure is None,
                    success=successful_episode(episode,ticks=ticks) and not physical and flags and unchanged and not missing,
                    ticks=ticks, episode=episode, failure=failure, physical_failure=physical,
                    physical_flags_ok=flags, source_unchanged=unchanged,
                    forbidden_calls=copy.deepcopy(scene.forbidden_calls) if scene is not None else [],
                    missing_import_pins=missing, changed_inputs=changed, intervention_ticks=sum(arrays['intervention']),
                    scope='bounded normalized actions only; teacher-controlled suffix is not learned policy success')
                write(case/'partial_result.json', result); results.append(result)
                print('[local probe result] role=%s case=%s success=%s physical_failure=%s' %
                      (role,candidate,result['success'],physical), flush=True)
    finally:
        primary = sys.exc_info()[1]
        session = env.control.session
        cleanup_error = None
        try:
            env.close()
        except BaseException as error:
            cleanup_error = dict(type=type(error).__name__, message=str(error))
        changed = [path for path,sha in pins.items() if not Path(path).is_file() or digest(path) != sha]
        for result in results:
            result['cleanup_error'] = cleanup_error
            result['source_unchanged'] = not changed
            result['success'] = result['success'] and cleanup_error is None and not changed
            write(out/result['candidate']/'result.json', result)
        write(out/'result.json', dict(schema='guitar_learning.local_skill_search.v1',
            role=role, source_checkpoint=str(checkpoint), elapsed_s=time.monotonic()-started,
            candidates=results, successful_candidates=[x['candidate'] for x in results if x['success']],
            source_unchanged=not changed, changed_inputs=changed, cleanup_error=cleanup_error,
            failure=dict(type=type(primary).__name__,message=str(primary)) if primary else None,
            native_environments_concurrent=1,
            lifecycle=copy.deepcopy(getattr(session,'persistent_reset_diagnostics',None)) if session is not None else None,
            scope='native feasibility/capture, not BC or PPO learning success'))
        if cleanup_error is not None and primary is None:
            raise RuntimeError('native probe cleanup failed: '+repr(cleanup_error))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--candidates', nargs='+')
    parser.add_argument('--device', default='cpu')
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[name]='1'
    import isaacgym
    from ..train_musical_quality import settings_document
    run(settings_document(json.loads(args.settings.read_text())), args)


if __name__ == '__main__': main()
