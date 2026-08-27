from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body import train_strike


class _CudaStub:
    @staticmethod
    def is_available():
        return False

    @staticmethod
    def manual_seed_all(_seed):
        return None


def main():
    torch_stub = SimpleNamespace(
        manual_seed=lambda _seed: None,
        cuda=_CudaStub(),
    )
    with TemporaryDirectory() as temp:
        run = Path(temp) / "preflight_failure"
        with patch.object(
                train_strike, "_load_strike_support_runtime",
                return_value=torch_stub):
            with patch.object(
                    train_strike, "training_resource_preflight",
                    side_effect=RuntimeError("resource rejected")):
                try:
                    train_strike.main([
                        "--out", str(run),
                        "--iterations", "1",
                    ])
                except RuntimeError as exc:
                    assert str(exc) == "resource rejected"
                else:
                    raise AssertionError("preflight failure must propagate")
        assert not run.exists()

        artifact = Path(temp) / "artifact.json"
        artifact.write_text("{}\n", encoding="utf-8")
        recorded = []
        errors = {}
        with patch.object(
                train_strike, "record_artifact_result",
                side_effect=lambda _layout, values, **_kwargs:
                recorded.append(values)):
            result = train_strike._attempt_artifact(
                None, "artifact",
                lambda: {"artifact": artifact}, errors)
        assert result == {"artifact": str(artifact.resolve())}
        assert recorded == [result]
        assert not errors

        failure = RuntimeError("artifact failed")
        recorded_errors = []

        def fail():
            raise failure

        with patch.object(
                train_strike, "record_artifact_error",
                side_effect=lambda _layout, name, error:
                recorded_errors.append((name, error))):
            result = train_strike._attempt_artifact(
                None, "broken", fail, errors)
        assert result == {}
        assert errors == {"broken": failure}
        assert recorded_errors == [("broken", failure)]
    print("PASS: Strike preflight layout and artifact recording lifecycle")


if __name__ == "__main__":
    main()
