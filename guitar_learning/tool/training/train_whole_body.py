"""전신37 지지 정책의 학습·엄격 재개·Actor 전용 평가 진입점."""
import argparse
import json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('train', 'inspect'):
        sub = commands.add_parser(name)
        sub.add_argument('--num-envs', type=int, default=128)
        sub.add_argument('--horizon', type=int, default=32)
        sub.add_argument('--updates', type=int, default=100)
        sub.add_argument('--checkpoint-every', type=int, default=25)
        sub.add_argument('--duration-s', type=float, default=10.)
        sub.add_argument('--seed', type=int, default=7)
        sub.add_argument('--device', default='cuda:0')
        if name == 'train':
            sub.add_argument('--out', required=True)
            sub.add_argument('--resume')
    sub = commands.add_parser('evaluate')
    sub.add_argument('checkpoint')
    sub.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    # Isaac Gym must precede torch; inspect/help intentionally remain CPU-only.
    if args.command != 'inspect':
        import isaacgym  # noqa: F401
    from guitar_learning.training.whole_body_runner import configuration, run, evaluate
    if args.command == 'evaluate':
        return evaluate(args.checkpoint, args.out)
    settings = configuration(**{k: v for k, v in vars(args).items() if k not in ('command', 'out', 'resume')})
    if args.command == 'inspect':
        print(json.dumps(dict(settings=settings, state_dim=484, learned_action_dim=37,
            scope='configuration only; no GPU scene or training'), ensure_ascii=False, indent=2))
        return settings
    return run(settings, args.out, resume=args.resume)


if __name__ == '__main__':
    main()
