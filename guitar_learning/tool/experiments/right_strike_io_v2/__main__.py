"""Replay the sealed v1 task with NumPy-safe snapshot output only."""
import argparse
import json
import os
from pathlib import Path
from unittest.mock import patch

from . import verify_manifest, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('probe', 'queue-probe'))
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--queue-out', type=Path)
    args = parser.parse_args()
    verify_manifest(args.manifest)
    if args.command == 'queue-probe':
        if args.queue_out is None:
            parser.error('--queue-out required for queue-probe')
        from .queue import queue_probe
        result = queue_probe(args.manifest, args.out, args.queue_out)
    else:
        from guitar_learning.tool.experiments.right_strike.runtime import GPU_UUID
        os.environ['CUDA_VISIBLE_DEVICES'] = GPU_UUID
        for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
            os.environ[key] = '1'
        from guitar_learning.tool.experiments.right_strike import native_probe
        with patch.object(native_probe, 'write', write):
            result = native_probe.run(args.manifest, args.out)
    print(json.dumps({k: v for k, v in result.items() if k in ('completed', 'status', 'outcome')}))


if __name__ == '__main__':
    main()
