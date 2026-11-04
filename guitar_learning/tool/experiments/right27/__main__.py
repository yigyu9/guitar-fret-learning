"""오른손27 타현 학습과 실제 GPU 관절 응답 검사를 실행한다."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('train', 'probe'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--song', default=None)
    parser.add_argument('--updates', type=int, default=100)
    parser.add_argument('--num-envs', type=int, default=64)
    parser.add_argument('--horizon', type=int, default=32)
    parser.add_argument('--size', choices=('small', 'medium', 'large'), default='medium')
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    if args.command == 'probe' and args.resume is not None:
        parser.error('probe does not load a checkpoint')
    if args.out.exists():
        parser.error('새 출력 디렉토리를 지정해야 합니다')
    import isaacgym  # Torch보다 native Gym을 먼저 로드한다.
    from .runtime import settings_for, train
    settings = settings_for(args)
    if args.command == 'probe':
        from .probe import probe
        result = probe(settings, args.out)
    else:
        result = train(settings, args.out, args.resume)
    print(json.dumps(dict(completed=result.get('completed'), out=str(args.out.resolve())),
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
