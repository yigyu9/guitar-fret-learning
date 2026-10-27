"""Explicit diagnostic CLI. Isaac Gym must load before NumPy/Torch."""
import argparse


def parser():
    value = argparse.ArgumentParser(description='Fresh single-note fixed-guitar diagnostic; production defaults unchanged')
    sub = value.add_subparsers(dest='command', required=True)
    train = sub.add_parser('train')
    train.add_argument('--teacher', required=True)
    train.add_argument('--mode', choices=('incremental', 'position'), required=True)
    train.add_argument('--initial-std', type=float, required=True, help='predeclared mode-specific latent exploration std')
    train.add_argument('--song', default='05_BN2-131-B_solo')
    train.add_argument('--size', choices=('small', 'medium', 'large'), default='large')
    train.add_argument('--num-envs', type=int, default=128)
    train.add_argument('--horizon', type=int, default=32)
    train.add_argument('--updates', type=int, default=300)
    train.add_argument('--save-every', type=int, default=50)
    train.add_argument('--seed', type=int, default=7)
    train.add_argument('--out', required=True)
    evaluate = sub.add_parser('evaluate')
    evaluate.add_argument('--checkpoint', required=True)
    evaluate.add_argument('--episodes', type=int, default=16)
    evaluate.add_argument('--control', choices=('policy', 'zero', 'random', 'reference'), default='policy')
    evaluate.add_argument('--reference', help='sealed selected4 reference JSON; evaluation-only')
    evaluate.add_argument('--out', required=True)
    return value


def main():
    args = parser().parse_args()
    if args.command == 'evaluate':
        if args.episodes < 1:
            raise ValueError('Positive evaluation attempt count required')
        if (args.control == 'reference') != bool(args.reference):
            raise ValueError('--reference is required exactly for --control reference')
    import isaacgym
    from .runner import run
    run(args)


if __name__ == '__main__':
    main()
