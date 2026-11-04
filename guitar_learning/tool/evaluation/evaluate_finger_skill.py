"""현행 V5 압현 저장본의 정책·물리 계약을 엄격히 검증하여 독립 평가한다."""
import argparse
from pathlib import Path


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument('checkpoint', type=Path)
    value.add_argument('--out', type=Path, required=True)
    value.add_argument('--num-envs', type=int, default=None)
    value.add_argument('--scope', choices=('full_song', 'phrases'), default='full_song')
    return value


def main():
    args = parser().parse_args()
    import isaacgym
    from guitar_learning.tool.experiments.compact_press_v5 import evaluate
    report, _ = evaluate(args.checkpoint, args.out, num_envs=args.num_envs, scope=args.scope)
    print('episodes=%d scope=%s completed=%s' % (report['episodes'], report['scope'], report['completed']))


if __name__ == '__main__':
    main()
