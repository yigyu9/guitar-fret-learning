"""기존 오른손 song 학습의 CPU·GPU 실행 진입점. 왼손 압현은 guitar_learning.train(V5)을 사용한다."""
import argparse
import copy
from functools import partial
import os
from pathlib import Path
import sys
from unittest.mock import patch


from guitar_learning.training.launch import DEFAULT_SONG
from guitar_learning.training.launch import build_settings as build_settings


def settings_document(hand, *, learning_family='song', **options):
    if learning_family != 'song':
        raise ValueError('Current finger-skill training uses python -m guitar_learning.train')
    return build_settings(hand, learning_family=learning_family, **options)


def run(settings, args):
    """오른손 진단용 공용 수집기·PPO를 이 실행 동안만 연결한다."""
    if settings.get('specialist', {}).get('role') != 'right':
        raise ValueError('구형 왼손 학습은 제거했습니다. V5: python -m guitar_learning.train --out NEW')
    # Isaac Gym must precede imports of torch in the runner and policy.
    import isaacgym
    if 'physics_backend' in settings:
        from guitar_learning.tool.training.legacy_gpu_runner import run as run_gpu
        return run_gpu(settings, args)
    from guitar_learning.training import runner as train_parallel
    from guitar_learning.training import parallel, policy
    from guitar_learning.training.parallel import finalize_persistent_run
    from guitar_learning.training.policy import SpecialistPolicy
    from guitar_learning.song.runtime import native_environment, summarize_run
    hand = settings['specialist']['role']
    if hand not in ('left', 'right') or any(
            settings['specialist'].get(name+'_checkpoint') is not None for name in ('left', 'right')):
        raise ValueError('single hand without expert checkpoints required')
    base_pool = parallel.Pool

    class HandPool(base_pool):
        def __init__(self, specs, **kwargs):
            specs = copy.deepcopy(specs)
            for spec in specs:
                spec.update(specialist=copy.deepcopy(settings['specialist']),
                    song=copy.deepcopy(settings['song']))
            super().__init__(specs, worker_factory=native_environment, **kwargs)

    out = args.out.resolve()
    argv = [sys.argv[0], '--settings', str(out/'settings.json'), '--out', str(out)]
    if args.resume is not None:
        argv += ['--resume', str(args.resume)]
    existed = out.exists()
    summary = None
    try:
        with patch.object(parallel, 'Pool', HandPool), \
             patch.object(policy, 'Policy', partial(SpecialistPolicy, role=hand, frozen_partner=False)), \
             patch.object(sys, 'argv', argv):
            train_parallel.main(settings=settings)
    finally:
        original_error = sys.exc_info()[1]
        if not existed:
            try:
                passed = finalize_persistent_run(out)
                if (out/'report.json').is_file():
                    summary = summarize_run(out)
                if passed is False and original_error is None:
                    raise RuntimeError('persistent lifecycle audit failed; see report.json')
            except BaseException as audit_error:
                if original_error is None:
                    raise
                print('[training] secondary summary/audit error: '+str(audit_error),
                    file=sys.stderr, flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hand', choices=('right',), required=True,
                        help='오른손 전용. 왼손 압현은 python -m guitar_learning.train(V5) 사용')
    parser.add_argument('--song', default=DEFAULT_SONG,
                        help='reviewed song identifier under data/song_bundles')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--updates', type=int, default=100)
    parser.add_argument('--num-envs', type=int, help='GPU default128; CPU default2')
    parser.add_argument('--device', choices=('auto', 'cpu', 'cuda:0'), default='cuda:0')
    parser.add_argument('--physics', choices=('auto', 'cpu', 'gpu'), default='auto',
                        help='auto uses GPU physics with CUDA, CPU physics with CPU policy')
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--horizon', type=int,
                        help='GPU default32, CPU default whole song; cuts continue the song clock')
    parser.add_argument('--size', choices=('small', 'medium', 'large'), default='medium')
    parser.add_argument('--checkpoint-every', type=int, default=250,
                        help='save an additional checkpoint every N updates (default250)')
    parser.add_argument('--resume', type=Path)
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    settings = settings_document(args.hand, song=args.song, updates=args.updates, num_envs=args.num_envs,
        device=args.device, seed=args.seed, horizon=args.horizon, size=args.size, physics=args.physics,
        checkpoint_every=args.checkpoint_every, learning_family='song')
    return run(settings, args)


if __name__ == '__main__':
    main()
