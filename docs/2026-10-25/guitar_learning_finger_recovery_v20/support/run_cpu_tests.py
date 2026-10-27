"""Run recovery regressions, optionally using staged sources before installation."""
import argparse
import ast
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
import unittest

PHASE = Path(__file__).resolve().parents[1]
ROOT = PHASE.parents[2]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--staged', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    stage = PHASE/'staging'
    if args.staged:
        class Overlay(importlib.abc.MetaPathFinder, importlib.abc.Loader):
            def find_spec(self, fullname, path=None, target=None):
                relative = Path(*fullname.split('.')).with_suffix('.py')
                candidate = stage/relative
                if candidate.is_file():
                    return importlib.util.spec_from_loader(fullname, self, origin=str(ROOT/relative))
            def create_module(self, spec):
                return None
            def exec_module(self, module):
                relative = Path(*module.__name__.split('.')).with_suffix('.py')
                module.__file__ = str(ROOT/relative)
                exec(compile((stage/relative).read_bytes(), module.__file__, 'exec'), module.__dict__)
        sys.meta_path.insert(0, Overlay())
    folders = [ROOT/'guitar_learning/tests']
    if args.staged:
        folders.append(stage/'guitar_learning/tests')
    names = sorted({p.stem for folder in folders for p in folder.glob('test_gpu*.py')} |
                   {'test_press_acquisition', 'test_simple_start'})
    # CPU tensors exercise the GPU implementation without initializing Isaac Gym.
    import torch
    torch.set_num_threads(1)
    suite = unittest.defaultTestLoader.loadTestsFromNames(['guitar_learning.tests.'+n for n in names])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sources = [p for p in (ROOT/'guitar_learning').rglob('*.py')
               if 'archive' not in p.relative_to(ROOT/'guitar_learning').parts]
    for path in sources:
        relative = path.relative_to(ROOT)
        candidate = stage/relative if args.staged and (stage/relative).is_file() else path
        ast.parse(candidate.read_text(), filename=str(path))
    report = dict(verified=result.wasSuccessful(), staged=args.staged, modules=names,
        tests=result.testsRun, errors=len(result.errors), failures=len(result.failures),
        skipped=result.skipped, ast_python_files=len(sources),
        scope='CPU tensor regression; native GPU physics and learning efficacy require separate runs')
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
