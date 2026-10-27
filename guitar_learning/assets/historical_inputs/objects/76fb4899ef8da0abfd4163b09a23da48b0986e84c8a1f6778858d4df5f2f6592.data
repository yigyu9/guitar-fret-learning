"""CPU-only contract for the unified task training entry point."""
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body import train  # noqa: E402


def main():
    assert train.resolve_task([]) == "fret"
    assert train.resolve_task(
        ["--task", "fret", "--iterations", "5"]) == "fret"
    assert train.resolve_task(
        ["--task", "strike", "--timing-tolerance-ms", "50"]) == "strike"
    assert train.resolve_task(["--task=strike", "--smoke"]) == "strike"
    assert train.resolve_task(
        ["--task", "full", "--fret-checkpoint", "f.pt",
         "--strike-checkpoint", "s.pt"]) == "full"
    assert train.runner_argv(
        ["--task", "strike", "--iterations", "5"]
    ) == ["--iterations", "5"]
    assert train.runner_argv(
        ["--task=strike", "--smoke"]
    ) == ["--smoke"]
    assert train.runner_argv(
        ["--task", "full", "--fret-checkpoint", "f.pt"]
    ) == ["--fret-checkpoint", "f.pt"]
    fake_runner = SimpleNamespace(
        build_parser=lambda: None,
        main=lambda _argv=None: None,
    )
    with patch.object(train.importlib, "import_module",
                      return_value=fake_runner) as importer:
        assert train.load_runner("strike") is fake_runner
        importer.assert_called_once_with("tab2body.train_strike")

    print("PASS: unified train.py task dispatch")


if __name__ == "__main__":
    main()
