"""Execute a BC actor or its PPO refinement deterministically in native physics."""
import argparse
import copy
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--initialization', type=Path)
    source.add_argument('--run', type=Path)
    parser.add_argument('--role', choices=('left', 'right'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--episodes', type=int, default=2)
    args = parser.parse_args()
    if args.episodes < 1:
        raise ValueError('positive evaluation episode count required')
    import os
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    import isaacgym
    import torch
    import numpy as np
    from guitar_learning.imitation.imitation_environment import build_environment
    from guitar_learning.imitation.imitation_v2 import apply_actor_initialization
    from guitar_learning.imitation.imitation_io import CONFIG, BUNDLE, pin_inputs, verify_inputs
    from guitar_learning.training.recording import write
    from guitar_learning.training.parallel import FIELDS
    from guitar_learning.skills.specialist_parallel import specialist_compact
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.training.ppo import PPOTrainer, PPOConfig
    torch.set_num_threads(1); torch.backends.cuda.matmul.allow_tf32 = False
    checkpoint = args.initialization.resolve() if args.initialization else args.run.resolve()/'final.pt'
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    arch = payload['architecture'] if args.initialization else payload['identity']['architecture']
    if arch['role'] != args.role:
        raise ValueError('checkpoint hand role mismatch')
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    pinned = pin_inputs([checkpoint]); write(out/'inputs_before.json', pinned)
    env = build_environment(CONFIG, out/'environment', role=args.role,
        skill='hold' if args.role == 'left' else 'cross', bundle=BUNDLE)
    episodes, rows = [], []
    try:
        for episode in range(args.episodes):
            observation, reset = env.reset(); write(out/('reset_%02d.json'%episode), reset)
            if episode == 0:
                model = SpecialistPolicy(505, size=arch['size'], role=args.role,
                    frozen_partner=False, contract=env.contract).to('cuda:0')
                if args.initialization:
                    transfer = apply_actor_initialization(model, checkpoint)
                    write(out/'actor_initialization.json', transfer)
                else:
                    trainer = PPOTrainer(model, PPOConfig(**payload['identity']['config']))
                    trainer.load(checkpoint)
                model.eval()
            if env.contract != model.architecture['contract']:
                raise RuntimeError('policy/evaluation contract mismatch')
            for tick in range(240):
                before = {k: np.array(observation[k], copy=True) for k in FIELDS}
                inputs = [torch.as_tensor(before[k], device='cuda:0').unsqueeze(0) for k in FIELDS]
                with torch.no_grad():
                    action = model.act(*inputs, deterministic=True)['action'][0].cpu().numpy()
                observation, reward, terminated, truncated, info = env.step(action)
                rows.append(dict(episode=episode, tick=tick, observation=before, action=action,
                    reward=reward, info=specialist_compact(env, info, action),
                    physics_measurements=info['physics_measurements']))
                if terminated or truncated:
                    episodes.append(copy.deepcopy(info['episode']))
                    print('[evaluate] role=%s episode=%d success=%s reason=%s' %
                        (args.role, episode, info['specialist']['stage_success'], info['episode']['reason']), flush=True)
                    break
        write(out/'transitions.json.gz', rows, compressed=True)
        write(out/'result.json', dict(completed=len(episodes)==args.episodes,
            role=args.role, kind='BC' if args.initialization else 'PPO', checkpoint=str(checkpoint),
            episodes=episodes, source_unchanged=verify_inputs(pinned),
            scope='deterministic native single target, repeated same prepared start; contact/cross are not audio or musical timing success'))
    finally:
        env.close()


if __name__ == '__main__': main()
