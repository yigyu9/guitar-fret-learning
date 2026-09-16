"""Run every Action Residual contract test without a pytest dependency."""
from __future__ import annotations

from pathlib import Path
import runpy


TEST_DIR = Path(__file__).resolve().parent
TEST_FILES = (
    "test_contract.py",
    "test_goal_encoder.py",
    "test_context_encoding.py",
    "test_source_intent.py",
    "test_source_projection.py",
    "test_action_safety.py",
)


def main() -> None:
    for filename in TEST_FILES:
        path = TEST_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        print(f"\n=== {filename} ===")
        runpy.run_path(str(path), run_name="__main__")
    print(f"\nPASS all {len(TEST_FILES)} Action Residual test modules")


if __name__ == "__main__":
    main()

