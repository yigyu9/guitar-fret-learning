"""Bounded deterministic joint execution; safety proof is separate from music success."""
import argparse
import copy
import gzip
import json
import os
from pathlib import Path
import random
import sys
import time


def evaluate(settings, args):
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.imitation.imitation_io import CONFIG, BUNDLE, pin_inputs_with_evidence, verify_inputs
    from guitar_learning.training.recording import write, digest
    from guitar_learning.training.parallel import FIELDS
    from guitar_learning.training.ppo import PPOConfig, PPOTrainer
    from guitar_learning.timing.timing_curriculum import TimingConfig
    from guitar_learning.runtime.persistent_session import PersistentHeadlessPreparedSession
    from guitar_learning.training.monitoring import available_memory_bytes, LowMemoryError
    from guitar_learning.tool.experiments.local_skills.learning import contract_digest
    from guitar_learning.tool.experiments.joint.environment import build_environment
    from guitar_learning.tool.experiments.joint.policy import JointPolicy
    from guitar_learning.tool.experiments.joint.transfer import validate_experts, apply_experts
    from guitar_learning.tool.experiments.joint.worker import compact
    from guitar_learning.tool.experiments.joint.proofs import EVALUATION_SCHEMA, PREFLIGHT_SCHEMA, full_safe_episode
    if type(args.episodes) is not int or not 1 <= args.episodes <= 4:
        raise ValueError('bounded1..4 joint evaluation episodes required')
    experts = validate_experts(settings)
    checkpoint = args.run.resolve()/'final.pt' if args.run else None
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic(); case_started = started
    env = None; failure = None; cleanup_error = None; primary = None
    episodes = []; forbidden = []; flags_ok = True; unchanged = False; contract = None
    pinned = pin_inputs_with_evidence([args.settings.resolve(), *([checkpoint] if checkpoint else [])], experts['source_pins'])
    write(out/'inputs_before.json', pinned); write(out/'settings.json', settings)
    def guard(start=False):
        threshold = 8. if start else 6.
        if available_memory_bytes() < threshold*1024**3:
            raise LowMemoryError('joint evaluation available memory below %.1f GiB'%threshold)
        now = time.monotonic()
        if now-started > 3000 or now-case_started > 600:
            raise TimeoutError('joint evaluation case/total wall guard')
    def encode(value):
        if isinstance(value, np.ndarray): return value.tolist()
        if isinstance(value, np.generic): return value.item()
        raise TypeError(type(value).__name__)
    try:
        guard(start=True)
        random.seed(settings['seed']); np.random.seed(settings['seed']); torch.manual_seed(settings['seed'])
        torch.set_num_threads(1); torch.backends.cuda.matmul.allow_tf32 = False
        env = build_environment(CONFIG, out/'environment', bundle=BUNDLE,
            timing=TimingConfig(**settings['timing']), stage=settings['stage'],
            start_event_index=settings['start_event_index'], phrase_events=settings['phrase_events'],
            tempo_scale=settings['tempo_scale'], seed=settings['seed'], music=settings['music'],
            session_factory=PersistentHeadlessPreparedSession)
        with gzip.open(out/'transitions.jsonl.gz', 'xt', compresslevel=1) as trace:
            for episode_index in range(args.episodes):
                case_started = time.monotonic(); guard()
                observation, reset = env.reset(); write(out/('reset_%02d.json'%episode_index), reset)
                if episode_index == 0:
                    contract = copy.deepcopy(env.contract); write(out/'training_contract.json', contract)
                    model = JointPolicy(observation['state'].shape[-1], size=settings['size'], contract=contract).to(settings['device'])
                    if checkpoint:
                        trainer = PPOTrainer(model, PPOConfig(**settings['ppo']))
                        trainer.load(checkpoint)
                        initialization = dict(mode='strict_resume', checkpoint=str(checkpoint),
                            checkpoint_sha256=digest(checkpoint), optimizer_updates=trainer.updates)
                    else:
                        initialization = apply_experts(model, settings)
                    write(out/'initialization.json', initialization); model.eval()
                if env.contract != model.architecture['contract']:
                    raise RuntimeError('joint policy/evaluation contract mismatch')
                if env.task.duration_s != 7.: raise ValueError('original full7s joint horizon required')
                for tick in range(420):
                    if tick % 60 == 0: guard()
                    before = {key: np.array(observation[key], copy=True) for key in FIELDS}
                    inputs = [torch.as_tensor(before[key], device=settings['device']).unsqueeze(0) for key in FIELDS]
                    with torch.no_grad(): action = model.act(*inputs, deterministic=True)['action'][0].cpu().numpy()
                    observation, reward, terminated, truncated, info = env.step(action)
                    row = dict(episode=episode_index, tick=tick, observation=before, action=action,
                        reward=reward, info=compact(env, info, action),
                        physics_measurements=info['physics_measurements'],
                        native_last_sample=info['native_control']['physics_samples240'][-1]['native'])
                    trace.write(json.dumps(row, allow_nan=False, default=encode)+'\n')
                    if (tick+1) % 60 == 0:
                        print('[joint evaluate] episode=%d tick=%d/420 coupled=%d left=%s right=%s'%(
                            episode_index, tick+1, info['joint']['coupled_hit_count'],
                            info['musical_quality']['left']['provisional_success'],
                            info['musical_quality']['right']['provisional_success']), flush=True)
                    if terminated or truncated:
                        episodes.append(copy.deepcopy(info['episode'])); break
                scene = env.control.session.scene
                flags_ok = bool(flags_ok and scene.human_root_fixed and not scene.guitar_root_fixed
                    and not scene.guitar_gravity_disabled
                    and np.array_equal(scene.pd_properties, env.control.original_properties))
                forbidden.extend(copy.deepcopy(scene.forbidden_calls)); guard()
                print('[joint evaluate] episode=%d reason=%s joint_success=%s'%(episode_index,
                    episodes[-1]['reason'] if episodes else 'incomplete',
                    info['musical_quality']['stage_success']), flush=True)
    except BaseException as error:
        primary = error; failure = dict(type=type(error).__name__, message=str(error))
    finally:
        if env is not None:
            try:
                session = env.control.session
                if session is None:
                    flags_ok = False  # Reset may already have cleaned up after failure.
                else:
                    scene = session.scene
                    forbidden.extend(copy.deepcopy(scene.forbidden_calls))
                    flags_ok = bool(flags_ok and scene.human_root_fixed and not scene.guitar_root_fixed
                        and not scene.guitar_gravity_disabled
                        and np.array_equal(scene.pd_properties, env.control.original_properties))
            except BaseException as error:
                cleanup_error = dict(type=type(error).__name__, message=str(error))
                if primary is None: primary = error
            try: env.close()
            except BaseException as error:
                cleanup_error = dict(type=type(error).__name__, message=str(error))
                if primary is None: primary = error
        try: unchanged = verify_inputs(pinned)
        except BaseException as error:
            if failure is None: failure = dict(type=type(error).__name__, message=str(error))
            if primary is None: primary = error
    result = dict(schema=EVALUATION_SCHEMA, kind='strict_PPO' if checkpoint else 'fixed_experts',
        completed=(len(episodes) == args.episodes and failure is None and cleanup_error is None),
        requested_episodes=args.episodes, episodes=episodes, source_unchanged=unchanged,
        physical_flags_ok=bool(flags_ok and env is not None), forbidden_calls=forbidden,
        physical_failure_episodes=sum(e['reason'] == 'terminal_failure' for e in episodes),
        joint_successful_episodes=sum(e['musical_quality']['stage_success'] for e in episodes),
        left_successful_episodes=sum(e['musical_quality']['left']['stage_success'] for e in episodes),
        right_successful_episodes=sum(e['musical_quality']['right']['stage_success'] for e in episodes),
        failure=failure, cleanup_error=cleanup_error,
        contract_sha256=contract_digest(contract) if contract else None,
        checkpoint=str(checkpoint) if checkpoint else None, elapsed_wall_s=time.monotonic()-started,
        trace=dict(path=str(out/'transitions.jsonl.gz'),control_hz=60,measurement_hz=240,
            native_pose_hz=60,native_pose_scope='last real physics sample per control tick; no interpolation'),
        scope='same prepared start and first target only; joint clean-crossing, role quality, original50/100ms music and safety remain separate')
    write(out/'result.json', result)
    files = {name:out/(name+'.json') for name in ('result', 'inputs_before', 'initialization', 'training_contract')}
    if not checkpoint and all(path.is_file() for path in files.values()):
        gate = dict(schema=PREFLIGHT_SCHEMA, passed=bool(result['completed'] and unchanged and flags_ok
            and not forbidden and all(full_safe_episode(e) for e in episodes)),
            expert_pins=experts['source_pins'], contract_sha256=result['contract_sha256'],
            artifacts={key:dict(path=str(path),sha256=digest(path)) for key,path in files.items()},
            scope='safe complete joint execution permits fresh coordination learning; music success is not inherited')
        write(out/'preflight_gate.json', gate)
    if primary is not None: raise primary
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--run', type=Path)
    parser.add_argument('--episodes', type=int, default=1)
    args = parser.parse_args()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'): os.environ[key] = '1'
    import isaacgym
    from guitar_learning.tool.experiments.joint.settings import settings_document
    evaluate(settings_document(json.loads(args.settings.read_text())), args)


if __name__ == '__main__': main()
