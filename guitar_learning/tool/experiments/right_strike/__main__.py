"""Explicit entry points; native commands import Gym only after idle admission."""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare')
    prepare.add_argument('--out', type=Path, required=True)
    seal = commands.add_parser('seal')
    seal.add_argument('--bundle', type=Path, required=True)
    seal.add_argument('--out', type=Path, required=True)
    for name in ('probe', 'train', 'evaluate', 'queue-probe'):
        item = commands.add_parser(name)
        item.add_argument('--manifest', type=Path, required=True)
        item.add_argument('--out', type=Path, required=True)
        if name == 'train':
            item.add_argument('--diagnostic-report', type=Path, required=True)
            item.add_argument('--updates', type=int, default=100)
            item.add_argument('--num-envs', type=int, default=64)
            item.add_argument('--horizon', type=int, default=32)
            item.add_argument('--size', choices=('small', 'medium', 'large'), default='medium')
            item.add_argument('--seed', type=int, default=7)
        elif name == 'evaluate':
            item.add_argument('--checkpoint', type=Path, required=True)
        elif name == 'queue-probe':
            item.add_argument('--queue-out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        from .prepare import prepare
        result = prepare(args.out)
    elif args.command == 'seal':
        from .runtime import ROOT, GPU_UUID, SCHEMA, sha, write
        from .prepare import validate_inputs
        from guitar_learning.training.training_log_io import active_source_paths
        from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
        from guitar_learning.native.paths import pin
        bundle = args.bundle.resolve()
        validate_inputs(bundle)
        paths = active_source_paths(ROOT/'guitar_learning') | prepared_input_paths()
        paths.update(p for p in (ROOT/'guitar_learning/assets').rglob('*') if p.is_file())
        paths.update(p for p in bundle.rglob('*') if p.is_file())
        paths.update((ROOT/'guitar_learning/tests').glob('test_right_strike*.py'))
        write(args.out, dict(schema=SCHEMA, sealed=True, condition='single_down_string3_v1',
            gpu_uuid=GPU_UUID, bundle=str(bundle), pins=pin(BASELINE_CONFIG, extra=paths),
            scope='One finite right6 diagnostic; no pressure, sound or learned success inherited'))
        result = dict(manifest=str(args.out.resolve()), sha256=sha(args.out))
    elif args.command == 'queue-probe':
        from .queue import queue_probe
        result = queue_probe(args.manifest, args.out, args.queue_out)
    else:
        from .runtime import GPU_UUID
        os.environ['CUDA_VISIBLE_DEVICES'] = GPU_UUID
        for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
            os.environ[key] = '1'
        if args.command == 'train':
            from .runner import train
            result = train(args.manifest, args.out, updates=args.updates, num_envs=args.num_envs,
                           horizon=args.horizon, size=args.size, seed=args.seed,
                           diagnostic_report=args.diagnostic_report)
        elif args.command == 'evaluate':
            from .evaluate import evaluate
            result = evaluate(args.manifest, args.checkpoint, args.out)
        else:
            from .native_probe import run
            result = run(args.manifest, args.out)
    print(json.dumps({k: v for k, v in result.items() if k in
                     ('completed', 'manifest', 'sha256', 'outcome', 'status')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
