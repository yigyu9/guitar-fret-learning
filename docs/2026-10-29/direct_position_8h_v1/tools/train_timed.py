"""기존 J 실행기에 시간 예산을 전달하는 이번 실행 전용 진입점."""
import argparse
from pathlib import Path
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--updates', type=int, required=True)
    parser.add_argument('--seconds', type=float, required=True)
    parser.add_argument('--checkpoint-every', type=int, default=250)
    args = parser.parse_args()
    import isaacgym
    from guitar_learning.training.launch import settings_document, run
    settings = settings_document(size='large', num_envs=1024, horizon=32,
        updates=args.updates, seed=7, checkpoint_every=args.checkpoint_every)
    settings['max_wall_seconds'] = args.seconds
    result = run(settings, SimpleNamespace(out=args.out, resume=None))
    if result['failure'] is not None or not result['stages']:
        raise RuntimeError('학습 실패: report.json 참조')
    stage = result['stages'][-1]['report']
    if not stage['completed'] or result['stopped'] not in ('wall_budget', 'updates_complete'):
        raise RuntimeError('정상 종료/봉인 검증 실패: report.json 참조')


if __name__ == '__main__':
    main()
