"""Replay a previously verified teacher in the exact BC/PPO profile."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--teacher', type=Path, required=True)
    parser.add_argument('--role', choices=('left', 'right'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    import os
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    import isaacgym
    import numpy as np
    from guitar_learning.imitation.imitation_environment import build_environment
    from guitar_learning.imitation.imitation import load_dataset
    from guitar_learning.imitation.imitation_io import pin_inputs, verify_inputs, CONFIG, BUNDLE
    from guitar_learning.training.recording import write
    from guitar_learning.training.parallel import FIELDS
    data = load_dataset(args.teacher, args.role)
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    pinned = pin_inputs(data['manifest'])
    write(out/'inputs_before.json', pinned)
    env = build_environment(CONFIG, out/'environment', role=args.role,
        skill='hold' if args.role == 'left' else 'cross', bundle=BUNDLE)
    arrays = {key: [] for key in FIELDS}; arrays['action'] = []
    rows = []
    try:
        observation, reset = env.reset(); write(out/'reset.json', reset)
        for tick, action in enumerate(data['action']):
            for key in FIELDS:
                arrays[key].append(observation[key].copy())
            arrays['action'].append(action.copy())
            observation, reward, terminated, truncated, info = env.step(action)
            rows.append(dict(tick=tick, action=action, reward=reward, cost=info['cost'],
                specialist=info['specialist'], music=info['music'],
                samples240=info['native_control']['physics_samples240'],
                measurements=info['physics_measurements']))
            if terminated or truncated:
                break
        np.savez_compressed(out/'demonstration.npz', **{k: np.stack(v) for k, v in arrays.items()})
        write(out/'trace.json.gz', rows, compressed=True)
        write(out/'result.json', dict(role=args.role, ticks=len(rows),
            success=bool(info['specialist']['stage_success']),
            observation_dimension=len(arrays['state'][0]), episode=info.get('episode'),
            teacher=data['manifest'], source_unchanged=verify_inputs(pinned),
            scope='scripted real native replay in the exact initialization/PPO profile, not a learned policy'))
    finally:
        env.close()


if __name__ == '__main__': main()
