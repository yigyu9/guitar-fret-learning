"""CPU-only contracts for task-neutral fret/strike run bookkeeping."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.learning import run_io  # noqa: E402
from tab2body.learning.run_layout import layout_for  # noqa: E402


def expect_error(error_type, fragment, callback):
    try:
        callback()
    except error_type as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError(
            f"expected {error_type.__name__} containing {fragment!r}")


class FakeCuda:
    @staticmethod
    def is_available():
        return True

    @staticmethod
    def mem_get_info(_device):
        gib = 1024 ** 3
        return 12 * gib, 16 * gib

    @staticmethod
    def get_device_properties(_device):
        return SimpleNamespace(name="fake-gpu")


class FakeTorch:
    cuda = FakeCuda()

    @staticmethod
    def device(value):
        return SimpleNamespace(type=str(value).split(":", 1)[0])


def main():
    with tempfile.TemporaryDirectory() as directory:
        layout = layout_for(Path(directory) / "run", create=True)
        manifest = {
            "checkpoint_contract_sha256": "a" * 64,
            "artifacts": {},
        }
        run_io.record_run_metadata(
            layout, manifest, {"mode": "training"})
        run_io.record_run_metadata(
            layout, manifest, {"mode": "evaluation"})
        sessions = [
            json.loads(line)
            for line in layout.sessions.read_text(encoding="utf-8").splitlines()
        ]
        assert [row["mode"] for row in sessions] == [
            "training", "evaluation"]

        changed = dict(manifest, checkpoint_contract_sha256="b" * 64)
        expect_error(
            RuntimeError, "checkpoint contract differs",
            lambda: run_io.record_run_metadata(
                layout, changed, {"mode": "resume"}))

        legacy = layout_for(Path(directory) / "legacy", create=True)
        legacy.manifest.write_text(
            json.dumps({"artifacts": {}}), encoding="utf-8")
        expect_error(
            RuntimeError, "checkpoint contract differs",
            lambda: run_io.record_run_metadata(
                legacy, manifest, {"mode": "resume"}))

        run_io.record_artifact_result(layout, {"checkpoint": "model.pt"})
        error = RuntimeError("renderer unavailable")
        record = run_io.record_artifact_error(layout, "video", error)
        assert record["type"] == "RuntimeError"
        saved = json.loads(layout.manifest.read_text(encoding="utf-8"))
        assert saved["artifacts"]["checkpoint"] == "model.pt"
        assert saved["artifact_errors"]["video"]["message"] == str(error)
        run_io.record_artifact_result(layout, {"video": "video.mp4"})
        saved = json.loads(layout.manifest.read_text(encoding="utf-8"))
        assert "artifact_errors" not in saved
        assert not list(layout.root.glob(".run_manifest.json.*.tmp"))

        gib = 1024 ** 3
        limits = {
            "max_num_envs": 1024,
            "min_free_vram_gib": 8.0,
            "min_available_ram_gib": 8.0,
            "min_free_disk_gib": 10.0,
        }
        with patch.object(
                run_io, "available_ram_bytes", return_value=20 * gib):
            with patch.object(
                    run_io.shutil, "disk_usage",
                    return_value=SimpleNamespace(free=20 * gib)):
                snapshot = run_io.training_resource_preflight(
                    FakeTorch, "cuda:0", layout.root, 512, limits,
                    task_name="strike")
                assert snapshot["gpu_name"] == "fake-gpu"
                assert snapshot["num_envs"] == 512
                expect_error(
                    ValueError, "positive integer",
                    lambda: run_io.training_resource_preflight(
                        FakeTorch, "cuda:0", layout.root, True, limits))
                expect_error(
                    ValueError, "requires CUDA",
                    lambda: run_io.training_resource_preflight(
                        FakeTorch, "cpu", layout.root, 1, limits))

    print("PASS: task-neutral run metadata, artifact and resource contracts")


if __name__ == "__main__":
    main()
