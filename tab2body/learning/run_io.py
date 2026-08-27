"""Task-neutral I/O and resource guards for fret/strike training runs.

The helpers stay independent of either Isaac task, so runners can validate
resources and update run records without importing the simulator here.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Mapping

from .run_layout import RunLayout, layout_for


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
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _append_session(layout: RunLayout, row: Mapping[str, object]) -> None:
    with layout.sessions.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(
            dict(row), ensure_ascii=False, allow_nan=False) + "\n")


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
    "available_ram_bytes",
    "nearest_existing_parent",
    "record_artifact_error",
    "record_artifact_result",
    "record_run_metadata",
    "training_resource_preflight",
    "utc_now_iso",
]
