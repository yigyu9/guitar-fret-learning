"""CPU-only contracts for task-neutral fret/strike run bookkeeping."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import threading
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

        concurrent_log = layout.logs / "concurrent.jsonl"
        workers = []
        worker_errors = []
        for worker_id in range(4):
            def write_records(identifier=worker_id):
                try:
                    for record in range(100):
                        run_io.append_jsonl_atomic(
                            concurrent_log,
                            {"worker": identifier, "record": record})
                except Exception as exc:
                    worker_errors.append(exc)

            worker = threading.Thread(
                target=write_records)
            worker.start()
            workers.append(worker)
        for worker in workers:
            worker.join()
        assert not worker_errors, worker_errors
        assert run_io.validate_jsonl(concurrent_log) == 400
        concurrent_rows = {
            (row["worker"], row["record"])
            for row in (
                json.loads(line) for line in concurrent_log.read_text(
                    encoding="utf-8").splitlines())
        }
        assert concurrent_rows == {
            (worker, record)
            for worker in range(4) for record in range(100)
        }

        interrupted_log = layout.logs / "interrupted.jsonl"
        real_pwrite = run_io.os.pwrite
        pwrite_calls = {"count": 0}

        def interrupt_after_prefix(descriptor, payload, offset):
            pwrite_calls["count"] += 1
            if pwrite_calls["count"] == 1:
                prefix_size = max(1, len(payload) // 2)
                return real_pwrite(
                    descriptor, payload[:prefix_size], offset)
            raise OSError("simulated power loss")

        with patch.object(
                run_io.os, "pwrite", side_effect=interrupt_after_prefix):
            expect_error(
                OSError, "simulated power loss",
                lambda: run_io.append_jsonl_atomic(
                    interrupted_log, {"iteration": 1, "valid": True}))
        pending = interrupted_log.with_name(
            f".{interrupted_log.name}.append.pending.json")
        assert pending.exists()
        assert not interrupted_log.read_bytes().endswith(b"\n")
        assert run_io.validate_jsonl(interrupted_log) == 1
        assert not pending.exists()
        run_io.append_jsonl_atomic(
            interrupted_log, {"iteration": 2, "valid": True})
        recovered_rows = [
            json.loads(line) for line in interrupted_log.read_text(
                encoding="utf-8").splitlines()
        ]
        assert [row["iteration"] for row in recovered_rows] == [1, 2]

        mismatched_log = layout.logs / "mismatched.jsonl"
        run_io.append_jsonl_atomic(
            mismatched_log, {"iteration": 1, "valid": True})
        committed_size = mismatched_log.stat().st_size
        pwrite_calls["count"] = 0
        with patch.object(
                run_io.os, "pwrite", side_effect=interrupt_after_prefix):
            expect_error(
                OSError, "simulated power loss",
                lambda: run_io.append_jsonl_atomic(
                    mismatched_log, {"iteration": 2, "valid": True}))
        with mismatched_log.open("r+b") as stream:
            stream.seek(committed_size)
            stream.write(b"X")
            stream.flush()
        before_validation = mismatched_log.read_bytes()
        expect_error(
            ValueError, "does not match its journal",
            lambda: run_io.validate_jsonl(mismatched_log))
        assert mismatched_log.read_bytes() == before_validation
        assert mismatched_log.with_name(
            f".{mismatched_log.name}.append.pending.json").exists()

        replaced_log = layout.logs / "replaced.jsonl"
        pwrite_calls["count"] = 0
        with patch.object(
                run_io.os, "pwrite", side_effect=interrupt_after_prefix):
            expect_error(
                OSError, "simulated power loss",
                lambda: run_io.append_jsonl_atomic(
                    replaced_log, {"iteration": 1, "valid": True}))
        replacement = layout.logs / "replacement.tmp"
        replacement.write_bytes(replaced_log.read_bytes())
        replacement.replace(replaced_log)
        replaced_before = replaced_log.read_bytes()
        expect_error(
            ValueError, "target was replaced",
            lambda: run_io.validate_jsonl(replaced_log))
        assert replaced_log.read_bytes() == replaced_before

        lease = run_io.acquire_run_writer(layout)
        expect_error(
            RuntimeError, "another trainer owns this run",
            lambda: run_io.acquire_run_writer(layout))
        lease.close()
        with run_io.acquire_run_writer(layout):
            pass

        malformed = layout.logs / "malformed.jsonl"
        malformed.write_text(
            '{"valid": true}\n{"broken":\n{"valid": true}\n',
            encoding="utf-8")
        malformed_before = malformed.read_bytes()
        expect_error(
            ValueError, ":2:", lambda: run_io.validate_jsonl(malformed))
        assert malformed.read_bytes() == malformed_before

        unterminated = layout.logs / "unterminated.jsonl"
        unterminated.write_text('{"valid": true}', encoding="utf-8")
        assert run_io.validate_jsonl(unterminated) == 1
        expect_error(
            ValueError, "unterminated log record",
            lambda: run_io.append_jsonl_atomic(
                unterminated, {"valid": True}))
        assert unterminated.read_text(encoding="utf-8") == '{"valid": true}'

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
