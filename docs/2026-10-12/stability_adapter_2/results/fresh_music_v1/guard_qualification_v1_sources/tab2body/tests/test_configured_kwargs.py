"""설정 기반 생성자 연결기의 CPU 회귀 검사."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.config import configured_kwargs  # noqa: E402


class Example:
    def __init__(self, required, optional=2):
        self.required = required
        self.optional = optional


def expect_error(error_type, fragment, callback):
    try:
        callback()
    except error_type as exc:
        assert fragment in str(exc)
    else:
        raise AssertionError(f"expected {error_type.__name__}: {fragment}")


def main():
    source = {"required": 1, "optional": 3, "unrelated": 99}
    assert configured_kwargs(Example, source) == {
        "required": 1, "optional": 3}
    assert configured_kwargs(Example, source, optional=4) == {
        "required": 1, "optional": 4}
    expect_error(
        TypeError, "unknown constructor arguments",
        lambda: configured_kwargs(Example, source, typo=4))
    expect_error(
        KeyError, "missing required configuration",
        lambda: configured_kwargs(Example, {}))
    print("PASS: configured constructor arguments")


if __name__ == "__main__":
    main()
