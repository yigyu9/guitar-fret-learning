"""Run the frozen refinement pipeline with checked, round-trip JSON numbers."""
import argparse
import json
import os
from pathlib import Path
import sys


def source_paths():
    folder = Path(__file__).parent
    return sorted([*folder.glob('*.py'), folder/'fpu_state.c', folder/'fpu_state.so'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('eval', 'train'))
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--episodes', type=int, default=1)
    args = parser.parse_args()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    audit_path = args.out.parent/(args.out.name+'_runtime_json_audit.json')
    if args.out.exists() or audit_path.exists():
        raise FileExistsError('new execution and runtime audit paths required')
    import isaacgym
    from unittest.mock import patch
    from guitar_learning.tool.experiments.transition_refinement_runtime_v2.activation import activated
    from guitar_learning.tool.experiments.transition_refinement_runtime_v2.observer import Observer
    from guitar_learning.tool.experiments.transition_refinement_runtime_v2.audit import publish
    from guitar_learning.tool.experiments.transition_refinement_runtime_v2.evidence import validate_gates, validate_workers
    from guitar_learning.tool.experiments.transition_refinement_runtime_v2 import worker
    observer = Observer()
    completed = False
    worker_audits = {}
    try:
        with activated(observer):
            from guitar_learning.tool.experiments.transition_refinement import run, evidence, worker as original_worker
            original_sources = evidence.source_paths
            original_validator = evidence.initialization_evidence
            base_factory = original_worker.native_environment
            def sources():
                return sorted(set(original_sources()+source_paths()))
            def validator(settings, *, require_gate=False):
                proof = original_validator(settings, require_gate=require_gate)
                return validate_gates(proof, settings) if require_gate else proof
            with patch.object(evidence, 'source_paths', sources), \
                    patch.object(evidence, 'initialization_evidence', validator), \
                    patch.object(original_worker, 'native_environment', worker.native_environment), \
                    patch.object(worker, '_base_factory', base_factory):
                settings = json.loads(args.settings.read_text())
                result = run.run(settings, args)
                if args.mode == 'train':
                    worker_audits = validate_workers(args.out, settings)
                completed = isinstance(result, dict) and result.get('completed') is True
    finally:
        if observer is not None:
            publish(observer, audit_path, completed=completed, mode=args.mode,
                out=args.out, primary=sys.exc_info()[1], worker_audits=worker_audits)


if __name__ == '__main__':
    main()
