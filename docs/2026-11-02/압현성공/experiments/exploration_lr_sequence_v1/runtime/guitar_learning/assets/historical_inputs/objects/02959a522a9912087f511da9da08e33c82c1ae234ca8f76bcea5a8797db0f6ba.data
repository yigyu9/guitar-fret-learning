"""Deterministic native evaluation of one explicit policy pre-roll timing stage."""
import argparse
import copy
import json
from pathlib import Path


def evaluate(settings, args):
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.imitation.imitation_io import CONFIG, BUNDLE, pin_inputs, verify_inputs
    from guitar_learning.training.recording import write
    from guitar_learning.training.parallel import FIELDS
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.training.ppo import PPOConfig, PPOTrainer
    from guitar_learning.timing.timing_curriculum import TimingConfig
    from guitar_learning.timing.timing_environment import build_environment
    from guitar_learning.timing.timing_transfer import apply_actor_initialization
    from guitar_learning.tool.training.train_timing import timing_compact
    if type(args.episodes) is not int or args.episodes < 1:
        raise ValueError('positive native evaluation episode count required')
    torch.set_num_threads(1); torch.backends.cuda.matmul.allow_tf32 = False
    role = settings['specialist']['role']
    checkpoint = args.initialization.resolve() if args.initialization else args.run.resolve()/'final.pt'
    if args.initialization and checkpoint != Path(settings['actor_initialization']).resolve():
        raise ValueError('evaluation initialization must match pinned settings')
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    pinned = pin_inputs([checkpoint, args.settings.resolve()]); write(out/'inputs_before.json', pinned)
    write(out/'settings.json', settings)
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    arch = (payload.get('architecture') if settings['actor_initialization_kind'] == 'bc'
            else payload.get('identity', {}).get('architecture')) if args.initialization else payload.get('identity', {}).get('architecture')
    if not isinstance(arch, dict) or arch.get('role') != role:
        raise ValueError('checkpoint hand role mismatch')
    env = build_environment(CONFIG, out/'environment', role=role,
        timing=TimingConfig(**settings['timing']), bundle=BUNDLE)
    episodes, rows = [], []
    try:
        for episode in range(args.episodes):
            observation, reset = env.reset(); write(out/('reset_%02d.json'%episode), reset)
            if episode == 0:
                model = SpecialistPolicy(observation['state'].shape[-1], size=settings['size'],
                    role=role, frozen_partner=False, contract=env.contract).to(settings['device'])
                if args.initialization:
                    transfer = apply_actor_initialization(model, checkpoint,
                        kind=settings['actor_initialization_kind'])
                    write(out/'timing_initialization.json', transfer)
                else:
                    trainer = PPOTrainer(model, PPOConfig(**payload['identity']['config']))
                    trainer.load(checkpoint)
                model.eval()
            if env.contract != model.architecture['contract']:
                raise RuntimeError('timing policy/evaluation contract mismatch')
            horizon = env.task.duration_s*60
            if abs(horizon-round(horizon)) > 1e-9:
                raise ValueError('complete control-tick evaluation horizon required')
            for tick in range(round(horizon)):
                before = {key: np.array(observation[key], copy=True) for key in FIELDS}
                inputs = [torch.as_tensor(before[key], device=settings['device']).unsqueeze(0) for key in FIELDS]
                with torch.no_grad():
                    action = model.act(*inputs, deterministic=True)['action'][0].cpu().numpy()
                observation, reward, terminated, truncated, info = env.step(action)
                rows.append(dict(episode=episode, tick=tick, observation=before, action=action,
                    reward=reward, info=timing_compact(env, info, action),
                    physics_measurements=info['physics_measurements'],
                    native_physics_samples240=info['native_control']['physics_samples240']))
                if terminated or truncated:
                    episodes.append(copy.deepcopy(info['episode']))
                    print('[timing evaluate] role=%s episode=%d success=%s reason=%s' %
                        (role, episode, info['timing']['stage_success'], info['episode']['reason']), flush=True)
                    break
        write(out/'transitions.json.gz', rows, compressed=True)
        source_unchanged = verify_inputs(pinned)
        result = dict(schema='guitar_learning.timing_evaluation.v1',
            completed=len(episodes) == args.episodes, role=role, config=settings['timing'],
            kind='actor_migration' if args.initialization else 'strict_PPO', checkpoint=str(checkpoint),
            requested_episodes=args.episodes, episodes=episodes,
            successful_episodes=sum(row['timing']['stage_success'] for row in episodes),
            source_unchanged=source_unchanged,
            scope='same prepared start, fixed relaxed timing window; original music remains separate; no pressure/sound or generalization claim')
        write(out/'result.json', result)
        return result
    finally:
        env.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--run', type=Path)
    source.add_argument('--initialization', type=Path)
    parser.add_argument('--settings', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--episodes', type=int, default=2)
    args = parser.parse_args()
    if args.settings is None:
        if args.run is None: parser.error('--initialization requires --settings')
        args.settings = args.run/'settings.json'
    import os
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    from guitar_learning.tool.training.train_timing import settings_document
    settings = settings_document(json.loads(args.settings.read_text()))
    evaluate(settings, args)


if __name__ == '__main__': main()
