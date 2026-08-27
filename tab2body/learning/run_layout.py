"""Human-readable directory layout for one task-specific training run."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RunLayout:
    root: Path
    checkpoints: Path
    logs: Path
    evaluations: Path
    videos: Path
    plots: Path
    manifest: Path
    metrics: Path
    training_log: Path
    artifact_log: Path
    sessions: Path


def _safe_name(value, label):
    value = str(value)
    if not value or value in (".", "..") or Path(value).name != value:
        raise ValueError(f"{label} must be one directory name, got {value!r}")
    return value


def layout_for(root, create=False):
    root = Path(root).resolve()
    layout = RunLayout(
        root=root,
        checkpoints=root / "checkpoints",
        logs=root / "logs",
        evaluations=root / "evaluations",
        videos=root / "videos",
        plots=root / "plots",
        manifest=root / "run_manifest.json",
        metrics=root / "logs" / "metrics.jsonl",
        training_log=root / "logs" / "training.log",
        artifact_log=root / "logs" / "artifacts.log",
        sessions=root / "logs" / "sessions.jsonl",
    )
    if create:
        for path in (layout.root, layout.checkpoints, layout.logs,
                     layout.evaluations, layout.videos, layout.plots):
            path.mkdir(parents=True, exist_ok=True)
    return layout


def timestamp_run_name(moment=None):
    """Return a local-time run name: YYYYMMDD_HHMM."""
    moment = datetime.now().astimezone() if moment is None else moment
    return moment.strftime("%Y%m%d_%H%M")


def default_run_dir(workspace_root, song_id, run_name=None, moment=None,
                    task_name="fret"):
    song_id = _safe_name(song_id, "song_id")
    task_name = _safe_name(task_name, "task_name")
    default_name = f"{timestamp_run_name(moment)}_{song_id}"
    name = _safe_name(
        run_name if run_name is not None else default_name,
        "run_name",
    )
    return (Path(workspace_root).resolve() / task_name / "training" / "runs"
            / name)


def infer_run_dir_from_checkpoint(checkpoint):
    """Return the run root for the organized layout, with legacy fallback."""
    checkpoint = Path(checkpoint).resolve()
    if checkpoint.parent.name == "checkpoints":
        return checkpoint.parent.parent
    return checkpoint.parent


def resolve_run_dir(workspace_root, song_id, explicit=None, run_name=None,
                    checkpoint=None, task_name="fret"):
    if explicit is not None and run_name is not None:
        raise ValueError("--out and --run-name cannot be used together")
    if explicit is not None:
        return Path(explicit).resolve()
    if checkpoint is not None and run_name is None:
        return infer_run_dir_from_checkpoint(checkpoint)
    return default_run_dir(
        workspace_root, song_id, run_name=run_name, task_name=task_name)


def has_training_history(layout, task_name="fret"):
    """Detect both the organized layout and the former flat run layout."""
    layout = layout if isinstance(layout, RunLayout) else layout_for(layout)
    task_name = _safe_name(task_name, "task_name")
    organized = (layout.metrics.exists()
                 or any(layout.checkpoints.glob(f"{task_name}_*.pt")))
    legacy = ((layout.root / "metrics.jsonl").exists()
              or any(layout.root.glob(f"{task_name}_*.pt")))
    return organized or legacy


def default_evaluation_path(checkpoint):
    checkpoint = Path(checkpoint).resolve()
    root = infer_run_dir_from_checkpoint(checkpoint)
    if checkpoint.parent.name == "checkpoints":
        return root / "evaluations" / f"{checkpoint.stem}.eval.json"
    return checkpoint.with_suffix(".eval.json")


def default_video_path(checkpoint):
    checkpoint = Path(checkpoint).resolve()
    root = infer_run_dir_from_checkpoint(checkpoint)
    if checkpoint.parent.name == "checkpoints":
        return root / "videos" / f"{checkpoint.stem}_rollout.mp4"
    return checkpoint.with_name(f"{checkpoint.stem}_rollout.mp4")


def default_strike_video_paths(checkpoint):
    """Return the frozen remembered/current output names for one strike policy."""
    checkpoint = Path(checkpoint).resolve()
    root = infer_run_dir_from_checkpoint(checkpoint)
    parent = root / "videos" if checkpoint.parent.name == "checkpoints" else checkpoint.parent
    return {
        view: parent / f"{checkpoint.stem}_rollout_{view}.mp4"
        for view in ("remembered", "current")
    }


def default_plot_path(metrics):
    metrics = Path(metrics).resolve()
    if metrics.parent.name == "logs":
        return metrics.parent.parent / "plots" / "training_curves.png"
    return metrics.with_name("training_curves.png")
