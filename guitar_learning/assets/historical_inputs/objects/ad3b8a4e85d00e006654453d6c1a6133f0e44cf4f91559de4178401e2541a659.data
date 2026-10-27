"""fret/strike 공용 tab2body 학습 진입점.

태스크 구현을 여기서 import하지 않는다. ``--task``만 먼저 읽은 뒤
``train_fret``, ``train_strike`` 또는 G0 assembly runner의 동일한 인터페이스를
불러온다. 따라서 왼손 환경이 오른손 학습의 선행 의존성이 되지 않는다.

예:
  python -m tab2body.train --task fret --iterations 5000
  python -m tab2body.train --task strike --iterations 5000
  python -m tab2body.train --task full --fret-checkpoint ... --strike-checkpoint ...
"""
from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


TASK_RUNNER_MODULES = {
    "fret": "tab2body.train_fret",
    "strike": "tab2body.train_strike",
    "full": "tab2body.train_full",
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="tab2body skill training and G0 full-player assembly",
        add_help=False,
    )
    parser.add_argument(
        "--task",
        choices=tuple(TASK_RUNNER_MODULES),
        default="fret",
        help="학습할 손 태스크 또는 full G0 assembly 선택",
    )
    return parser


def resolve_task(argv=None):
    """Resolve one task while leaving its runner-specific options untouched."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    selected, _unknown = build_parser().parse_known_args(arguments)
    return selected.task


def runner_argv(argv=None):
    """Remove the public ``--task`` selector before runner parsing."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    result = []
    index = 0
    while index < len(arguments):
        value = arguments[index]
        if value == "--task":
            if index + 1 >= len(arguments):
                raise SystemExit(
                    "--task requires fret, strike, or full")
            index += 2
            continue
        if value.startswith("--task="):
            index += 1
            continue
        result.append(value)
        index += 1
    return result


def load_runner(task):
    """Load and validate a task runner through the shared interface."""
    try:
        module_name = TASK_RUNNER_MODULES[task]
    except KeyError as exc:
        raise ValueError(f"unknown training task: {task!r}") from exc
    runner = importlib.import_module(module_name)
    for member in ("build_parser", "main"):
        if not callable(getattr(runner, member, None)):
            raise RuntimeError(
                f"training runner {module_name} lacks callable {member}()")
    return runner


def main(argv=None):
    task = resolve_task(argv)
    runner = load_runner(task)
    return runner.main(runner_argv(argv))


if __name__ == "__main__":
    main()
