"""CPU-only checks for organized fret-training output paths."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.run_layout import (  # noqa: E402
    default_evaluation_path,
    default_plot_path,
    default_run_dir,
    default_video_path,
    has_training_history,
    infer_run_dir_from_checkpoint,
    layout_for,
    resolve_run_dir,
    timestamp_run_name,
)


def expect_error(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def main():
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        run = default_run_dir(workspace, "song_a", "pilot_01")
        assert run == workspace.resolve() / "fret/training/runs/pilot_01"
        moment = datetime(2026, 7, 22, 14, 5, 9,
                          tzinfo=timezone(timedelta(hours=9)))
        assert timestamp_run_name(moment) == "20260722_1405"
        assert default_run_dir(workspace, "song_a", moment=moment) == (
            workspace.resolve() / "fret/training/runs/20260722_1405_song_a")
        assert default_run_dir(
            workspace, "02_Jazz1-200-B_solo", moment=moment) == (
            workspace.resolve()
            / "fret/training/runs/20260722_1405_02_Jazz1-200-B_solo")
        layout = layout_for(run, create=True)
        for path in (layout.checkpoints, layout.logs, layout.evaluations,
                     layout.videos, layout.plots):
            assert path.is_dir()
        assert not has_training_history(layout)

        checkpoint = layout.checkpoints / "fret_000100.pt"
        checkpoint.touch()
        assert has_training_history(layout)
        assert infer_run_dir_from_checkpoint(checkpoint) == layout.root
        assert resolve_run_dir(
            workspace, "ignored", checkpoint=checkpoint) == layout.root
        assert default_evaluation_path(checkpoint) == (
            layout.evaluations / "fret_000100.eval.json")
        assert default_video_path(checkpoint) == (
            layout.videos / "fret_000100_rollout.mp4")
        assert default_plot_path(layout.metrics) == (
            layout.plots / "training_curves.png")
        assert layout.training_log == layout.logs / "training.log"
        assert layout.artifact_log == layout.logs / "artifacts.log"

        expect_error(lambda: default_run_dir(workspace, "song_a", "bad/name"))
        expect_error(lambda: resolve_run_dir(
            workspace, "song_a", explicit=workspace / "x", run_name="x"))

    print("run layout checks passed")


if __name__ == "__main__":
    main()
