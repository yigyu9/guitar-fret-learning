"""Task-neutral I/O and resource guards for fret/strike training runs.

The helpers stay independent of either Isaac task, so runners can validate
resources and update run records without importing the simulator here.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import socket
import tempfile
from typing import Mapping

from .run_layout import RunLayout, layout_for


_PENDING_APPEND_SCHEMA = "tab2body.pending_append.v1"
_PENDING_PREFIX_BYTES = 4096


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"run metadata must be a JSON object: {path}")
    return value


def _write_json_object(path: Path, value: Mapping[str, object]) -> None:
    document = json.dumps(
        dict(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp",
                delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(document)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        _fsync_directory(path.parent)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_json_object_atomic(path, value: Mapping[str, object]) -> Path:
    path = Path(path).resolve()
    if not isinstance(value, Mapping):
        raise TypeError("atomic JSON document must be a mapping")
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json_object(path, value)
    return path


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _pending_append_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.append.pending.json")


def _write_pending_append(
        pending_path: Path, target: Path, offset: int,
        payload: bytes, descriptor: int) -> None:
    stat = os.fstat(descriptor)
    prefix_size = min(offset, _PENDING_PREFIX_BYTES)
    prefix = _read_at(descriptor, prefix_size, offset - prefix_size)
    encoded = base64.b64encode(payload).decode("ascii")
    document = json.dumps({
        "schema": _PENDING_APPEND_SCHEMA,
        "target_name": target.name,
        "target_device": stat.st_dev,
        "target_inode": stat.st_ino,
        "offset": offset,
        "prefix_size": prefix_size,
        "prefix_sha256": hashlib.sha256(prefix).hexdigest(),
        "payload_size": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "payload_base64": encoded,
    }, ensure_ascii=True, allow_nan=False, sort_keys=True)
    document = document.encode("ascii") + b"\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="wb", dir=pending_path.parent,
                prefix=f".{pending_path.name}.", suffix=".tmp",
                delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(document)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, pending_path)
        temporary = None
        _fsync_directory(pending_path.parent)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _read_pending_append(
        pending_path: Path, target: Path) -> tuple[int, bytes, dict]:
    try:
        record = json.loads(pending_path.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"invalid pending log append journal: {pending_path}") from exc
    if not isinstance(record, dict):
        raise ValueError(
            f"pending log append journal must be an object: {pending_path}")
    offset = record.get("offset")
    prefix_size = record.get("prefix_size")
    payload_size = record.get("payload_size")
    target_device = record.get("target_device")
    target_inode = record.get("target_inode")
    if (record.get("schema") != _PENDING_APPEND_SCHEMA
            or record.get("target_name") != target.name
            or isinstance(offset, bool) or not isinstance(offset, int)
            or offset < 0
            or isinstance(prefix_size, bool)
            or not isinstance(prefix_size, int)
            or prefix_size != min(offset, _PENDING_PREFIX_BYTES)
            or isinstance(payload_size, bool)
            or not isinstance(payload_size, int)
            or payload_size < 1
            or isinstance(target_device, bool)
            or not isinstance(target_device, int)
            or isinstance(target_inode, bool)
            or not isinstance(target_inode, int)
            or not isinstance(record.get("prefix_sha256"), str)
            or len(record["prefix_sha256"]) != 64):
        raise ValueError(
            f"invalid pending log append journal fields: {pending_path}")
    try:
        payload = base64.b64decode(
            record.get("payload_base64", ""), validate=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"invalid pending log append payload: {pending_path}") from exc
    digest = hashlib.sha256(payload).hexdigest()
    if (len(payload) != payload_size
            or digest != record.get("payload_sha256")
            or not payload.endswith(b"\n")
            or b"\n" in payload[:-1]
            or b"\r" in payload):
        raise ValueError(
            f"pending log append journal failed integrity checks: "
            f"{pending_path}")
    return offset, payload, {
        "prefix_size": prefix_size,
        "prefix_sha256": record.get("prefix_sha256"),
        "target_device": target_device,
        "target_inode": target_inode,
    }


def _read_at(descriptor: int, size: int, offset: int) -> bytes:
    chunks = []
    remaining = size
    while remaining:
        chunk = os.pread(descriptor, remaining, offset)
        if not chunk:
            raise OSError("unexpected end of file while verifying log append")
        chunks.append(chunk)
        offset += len(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _write_at(descriptor: int, payload: bytes, offset: int) -> None:
    written_total = 0
    while written_total < len(payload):
        written = os.pwrite(
            descriptor, payload[written_total:], offset + written_total)
        if written <= 0:
            raise OSError("failed to write durable log record")
        written_total += written


def _remove_pending_append(pending_path: Path) -> None:
    pending_path.unlink()
    _fsync_directory(pending_path.parent)


def _recover_pending_append_locked(path: Path, descriptor: int) -> bool:
    pending_path = _pending_append_path(path)
    if not pending_path.exists():
        return False
    offset, payload, identity = _read_pending_append(pending_path, path)
    stat = os.fstat(descriptor)
    current_size = stat.st_size
    expected_size = offset + len(payload)
    if (stat.st_dev != identity["target_device"]
            or stat.st_ino != identity["target_inode"]):
        raise ValueError(
            f"pending append target was replaced: {path}")
    if current_size < offset:
        raise ValueError(
            f"log is shorter than its pending append offset: {path}")
    if current_size > expected_size:
        raise ValueError(
            f"pending log append is no longer the final record: {path}")
    if offset and _read_at(descriptor, 1, offset - 1) != b"\n":
        raise ValueError(
            f"pending append offset is not a log record boundary: {path}")
    prefix_size = identity["prefix_size"]
    prefix = _read_at(descriptor, prefix_size, offset - prefix_size)
    if hashlib.sha256(prefix).hexdigest() != identity["prefix_sha256"]:
        raise ValueError(
            f"log prefix changed after its pending append began: {path}")
    observed = _read_at(descriptor, current_size - offset, offset)
    if not payload.startswith(observed):
        raise ValueError(
            f"incomplete final log record does not match its journal: {path}")
    if current_size < expected_size:
        _write_at(descriptor, payload[len(observed):], current_size)
        os.fsync(descriptor)
    if (os.fstat(descriptor).st_size != expected_size
            or _read_at(descriptor, len(payload), offset) != payload):
        raise OSError(f"recovered log record failed verification: {path}")
    _remove_pending_append(pending_path)
    return True


def _append_line_durable(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        _recover_pending_append_locked(path, descriptor)
        offset = os.fstat(descriptor).st_size
        if offset and _read_at(descriptor, 1, offset - 1) != b"\n":
            raise ValueError(
                f"refusing to append after an unterminated log record: {path}")
        pending_path = _pending_append_path(path)
        _write_pending_append(
            pending_path, path, offset, payload, descriptor)
        _write_at(descriptor, payload, offset)
        os.fsync(descriptor)
        expected_size = offset + len(payload)
        if (os.fstat(descriptor).st_size != expected_size
                or _read_at(descriptor, len(payload), offset) != payload):
            raise OSError(f"appended log record failed verification: {path}")
        _remove_pending_append(pending_path)
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)
    return path


def append_text_line_atomic(path, line: str) -> Path:
    path = Path(path).resolve()
    if not isinstance(line, str) or "\n" in line or "\r" in line:
        raise ValueError("atomic log records must be one text line")
    return _append_line_durable(path, (line + "\n").encode("utf-8"))


def append_jsonl_atomic(path, row: Mapping[str, object]) -> Path:
    if not isinstance(row, Mapping):
        raise TypeError("JSONL row must be a mapping")
    document = json.dumps(
        dict(row), ensure_ascii=False, allow_nan=False, sort_keys=True)
    json.loads(document)
    return append_text_line_atomic(path, document)


def _validate_jsonl_locked(path: Path, descriptor: int) -> int:
    stream = os.fdopen(os.dup(descriptor), "rb")
    count = 0
    try:
        for line_number, raw_line in enumerate(stream, 1):
            try:
                line = raw_line.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError(
                    f"malformed UTF-8 JSONL record at "
                    f"{path}:{line_number}") from exc
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"malformed JSONL record at {path}:{line_number}: "
                    f"{exc.msg}") from exc
            if not isinstance(value, dict):
                raise ValueError(
                    f"JSONL record must be an object at "
                    f"{path}:{line_number}")
            count += 1
    finally:
        stream.close()
    return count


def validate_jsonl(path) -> int:
    path = Path(path).resolve()
    if not path.exists():
        if _pending_append_path(path).exists():
            raise ValueError(
                f"pending append journal has no target log: "
                f"{_pending_append_path(path)}")
        return 0
    descriptor = os.open(path, os.O_RDWR)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        _recover_pending_append_locked(path, descriptor)
        return _validate_jsonl_locked(path, descriptor)
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


class RunWriterLease:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.descriptor = os.open(
            self.path, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            fcntl.flock(
                self.descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            owner = os.read(self.descriptor, 4096).decode(
                "utf-8", errors="replace").strip()
            os.close(self.descriptor)
            self.descriptor = None
            detail = f"; current owner={owner}" if owner else ""
            raise RuntimeError(
                f"another trainer owns this run: {self.path}{detail}") from exc
        owner = json.dumps({
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "acquired_at_utc": utc_now_iso(),
        }, ensure_ascii=False, allow_nan=False)
        os.ftruncate(self.descriptor, 0)
        os.write(self.descriptor, (owner + "\n").encode("utf-8"))
        os.fsync(self.descriptor)

    def close(self):
        if self.descriptor is None:
            return
        try:
            fcntl.flock(self.descriptor, fcntl.LOCK_UN)
        finally:
            os.close(self.descriptor)
            self.descriptor = None

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()


def acquire_run_writer(layout: RunLayout) -> RunWriterLease:
    return RunWriterLease(layout.logs / "training.writer.lock")


def _append_session(layout: RunLayout, row: Mapping[str, object]) -> None:
    append_jsonl_atomic(layout.sessions, row)


def record_run_metadata(
        layout, manifest: Mapping[str, object],
        session: Mapping[str, object]) -> RunLayout:
    """Create a stable run manifest once and append one launch session.

    Existing manifests are never overwritten.  A recorded checkpoint contract
    must agree with the live run before another session can be appended.
    A missing saved contract is also a mismatch; this helper never upgrades a
    legacy manifest implicitly.
    """
    layout = layout_for(
        layout.root if isinstance(layout, RunLayout) else layout,
        create=True,
    )
    new_contract = manifest.get("checkpoint_contract_sha256")
    if layout.manifest.exists():
        existing = _read_json_object(layout.manifest)
        old_contract = existing.get("checkpoint_contract_sha256")
        if old_contract != new_contract:
            raise RuntimeError(
                "run_manifest checkpoint contract differs from this runtime: "
                f"{layout.manifest}")
    else:
        _write_json_object(layout.manifest, manifest)
    _append_session(layout, session)
    return layout


def record_artifact_result(
        layout: RunLayout, artifacts: Mapping[str, object], *,
        resolved_errors=()) -> None:
    """Merge successful artifacts into the manifest and append an audit row."""
    manifest = _read_json_object(layout.manifest)
    manifest["artifacts"] = {
        **dict(manifest.get("artifacts", {})),
        **dict(artifacts),
    }
    errors = dict(manifest.get("artifact_errors", {}))
    for name in (*artifacts.keys(), *tuple(resolved_errors)):
        errors.pop(str(name), None)
    if errors:
        manifest["artifact_errors"] = errors
    else:
        manifest.pop("artifact_errors", None)
    _write_json_object(layout.manifest, manifest)
    _append_session(layout, {
        "completed_at_utc": utc_now_iso(),
        "mode": "artifact_generation",
        "artifacts": dict(artifacts),
    })


def record_artifact_error(layout: RunLayout, name, error: BaseException) -> dict:
    """Persist one failed artifact without hiding completed training outputs."""
    manifest = _read_json_object(layout.manifest)
    errors = dict(manifest.get("artifact_errors", {}))
    record = {
        "type": type(error).__name__,
        "message": str(error),
        "recorded_at_utc": utc_now_iso(),
    }
    errors[str(name)] = record
    manifest["artifact_errors"] = errors
    _write_json_object(layout.manifest, manifest)
    _append_session(layout, {
        "completed_at_utc": utc_now_iso(),
        "mode": "artifact_error",
        "artifact": str(name),
        "error": record,
    })
    return record


def nearest_existing_parent(path) -> Path:
    path = Path(path).resolve()
    while not path.exists():
        if path.parent == path:
            raise RuntimeError(f"no existing output parent for {path}")
        path = path.parent
    return path


def available_ram_bytes(meminfo_path="/proc/meminfo") -> int:
    for line in Path(meminfo_path).read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            fields = line.split()
            if len(fields) < 2:
                break
            value = int(fields[1]) * 1024
            if value <= 0:
                break
            return value
    raise RuntimeError(f"cannot read MemAvailable from {meminfo_path}")


def training_resource_preflight(
        torch_module, device, out_dir, num_envs, limits,
        *, task_name="training", min_free_vram_gib=None) -> dict:
    """Fail before Isaac Gym allocation when host capacity is unsafe.

    ``min_free_vram_gib`` is an explicit per-launch override used by tiny smoke
    runs.  RAM, disk, and the validated environment ceiling always remain in
    force.
    """
    if isinstance(num_envs, bool) or not isinstance(num_envs, int) or num_envs < 1:
        raise ValueError("num_envs must be a positive integer")
    max_envs = int(limits["max_num_envs"])
    if num_envs > max_envs:
        raise ValueError(
            f"num_envs {num_envs} exceeds validated {task_name} ceiling "
            f"{max_envs}")
    device = torch_module.device(device)
    if device.type != "cuda":
        raise ValueError(f"{task_name} Isaac Gym training requires CUDA")
    if not torch_module.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; refusing Isaac Gym allocation")

    free_vram, total_vram = torch_module.cuda.mem_get_info(device)
    props = torch_module.cuda.get_device_properties(device)
    ram = available_ram_bytes()
    disk = shutil.disk_usage(nearest_existing_parent(out_dir)).free
    gib = 1024 ** 3
    vram_gib = (
        float(limits["min_free_vram_gib"])
        if min_free_vram_gib is None else float(min_free_vram_gib))
    requirements_gib = {
        "free_vram": vram_gib,
        "available_ram": float(limits["min_available_ram_gib"]),
        "free_disk": float(limits["min_free_disk_gib"]),
    }
    if any(not math.isfinite(value) or value < 0.0
           for value in requirements_gib.values()):
        raise ValueError("resource limits must be finite and non-negative")
    actual = {
        "free_vram": int(free_vram),
        "available_ram": int(ram),
        "free_disk": int(disk),
    }
    required = {
        name: value * gib for name, value in requirements_gib.items()}
    failures = [
        f"{name}={actual[name] / gib:.1f}GiB < {minimum / gib:.1f}GiB"
        for name, minimum in required.items()
        if actual[name] < minimum
    ]
    if failures:
        raise RuntimeError(
            f"insufficient resources before {task_name} allocation: "
            + ", ".join(failures))
    return {
        "gpu_name": props.name,
        "gpu_total_vram_gib": round(int(total_vram) / gib, 2),
        "gpu_free_vram_gib": round(int(free_vram) / gib, 2),
        "available_ram_gib": round(int(ram) / gib, 2),
        "free_disk_gib": round(int(disk) / gib, 2),
        "num_envs": int(num_envs),
    }


__all__ = [
    "RunWriterLease",
    "acquire_run_writer",
    "append_jsonl_atomic",
    "append_text_line_atomic",
    "available_ram_bytes",
    "nearest_existing_parent",
    "record_artifact_error",
    "record_artifact_result",
    "record_run_metadata",
    "training_resource_preflight",
    "utc_now_iso",
    "validate_jsonl",
]
