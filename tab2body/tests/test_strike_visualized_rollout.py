"""CPU-only contracts for additive strike zone/pick diagnostic videos."""
from pathlib import Path
import json
import tempfile
import sys

import numpy as np
from PIL import Image


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
for path in (str(PACKAGE_ROOT), str(PROJECT_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from tools.record_strike_visualized_rollout import (
    configure_full_song_diagnostic_replay,
    resolve_visualized_report_path,
    resolve_visualized_video_paths,
    restored_environment_spec,
    validate_full_song_capture,
)
from tools.strike_visualization import (
    CameraSpec,
    VISUAL_STRING_RIBBON_HALF_WIDTH_M,
    build_strike_overlay_geometry,
    draw_strike_zone_pick_overlay,
    project_world_points,
)


ALLOWED = (-0.385, -0.255)
PREFERRED = (-0.355, -0.295)


def string_fixture():
    x = np.linspace(-0.030, 0.030, 6)
    starts = np.stack([
        x, np.full(6, -0.205), np.full(6, 0.012)
    ], axis=-1)
    ends = np.stack([
        x + 0.003, np.full(6, -0.410), np.full(6, 0.012)
    ], axis=-1)
    return starts, ends


class FakeStrikeEnv:
    allowed_y = ALLOWED
    preferred_y = PREFERRED
    lane_allowed_half_width = 0.0125
    lane_core_half_width = 0.006
    target_lane_y = np.array([-0.325], dtype=np.float64)

    def __init__(self):
        self.starts, self.ends = string_fixture()

    def string_segments_g(self):
        return self.starts[None], self.ends[None]

    def _current_target_string(self):
        return np.array([2])

    def guitar_frame(self):
        return (
            np.array([[0.0, 0.0, 0.0]]),
            np.array([[0.0, 0.0, 0.0, 1.0]]),
        )

    def hbody_pos(self, name):
        assert name == "RH:pick"
        return np.array([[0.003, -0.325, 0.035]])


def main():
    class ReplayEnv:
        evaluation_full_song = True
        wrong_crossing_termination_enabled = True

    replay = ReplayEnv()
    assert configure_full_song_diagnostic_replay(replay)
    assert not replay.wrong_crossing_termination_enabled
    replay.evaluation_full_song = False
    replay.wrong_crossing_termination_enabled = True
    assert not configure_full_song_diagnostic_replay(replay)
    assert replay.wrong_crossing_termination_enabled

    full_song_contract = {"minimum_original_song_steps": 10}
    validate_full_song_capture({
        "captured_original_song_duration": True,
        "completed_full_timeline": True,
        "ended_before_original_song_end": False,
    }, full_song_contract)
    for incomplete in (
            {
                "captured_original_song_duration": True,
                "completed_full_timeline": False,
                "ended_before_original_song_end": False,
            },
            {
                "captured_original_song_duration": False,
                "completed_full_timeline": False,
                "ended_before_original_song_end": True,
            }):
        try:
            validate_full_song_capture(incomplete, full_song_contract)
        except RuntimeError as exc:
            assert "original song timeline" in str(exc)
        else:
            raise AssertionError("incomplete full-song capture must fail")

    class Generation:
        @staticmethod
        def numel():
            return 4

    assert restored_environment_spec({"environment_state": {
        "schema": "tab2body.strike_environment_state.v13",
        "reset_generation": Generation(),
        "random_start": True,
    }}) == (4, True)
    assert restored_environment_spec({"environment_state": {
        "schema": "tab2body.strike_environment_state.v14",
        "reset_generation": Generation(),
        "random_start": False,
    }}) == (4, False)
    try:
        restored_environment_spec({"environment_state": {
            "schema": "tab2body.strike_environment_state.v12",
            "reset_generation": Generation(),
            "random_start": True,
        }})
    except ValueError as exc:
        assert "base recorder" in str(exc)
    else:
        raise AssertionError("visualized exact replay must reject legacy v12")

    checkpoint = Path(
        "/tmp/strike_visual_contract/checkpoints/strike_005000.pt")
    paths = resolve_visualized_video_paths(checkpoint)
    assert paths["remembered"].name == (
        "strike_005000_rollout_remembered_zone_pick.mp4")
    assert paths["current"].name == (
        "strike_005000_rollout_current_zone_pick.mp4")
    report = resolve_visualized_report_path(
        checkpoint, paths["remembered"])
    assert report.name == "strike_005000_rollout_zone_pick.json"
    assert len({paths["remembered"], paths["current"], report}) == 3

    starts, ends = string_fixture()
    geometry = build_strike_overlay_geometry(
        starts,
        ends,
        allowed_y=ALLOWED,
        preferred_y=PREFERRED,
        target_lane_y=-0.325,
        lane_outer_half_width_m=0.0125,
        lane_core_half_width_m=0.006,
        target_string=2,
    )


    build_strike_overlay_geometry(
        starts,
        ends,
        allowed_y=ALLOWED,
        preferred_y=PREFERRED,
        target_lane_y=float(np.float32(PREFERRED[1])),
        lane_outer_half_width_m=0.0125,
        lane_core_half_width_m=0.006,
        target_string=2,
    )
    recovery_geometry = build_strike_overlay_geometry(
        starts,
        ends,
        allowed_y=ALLOWED,
        preferred_y=PREFERRED,

        target_lane_y=-0.2919691205024719,
        lane_outer_half_width_m=0.0125,
        lane_core_half_width_m=0.006,
        target_string=2,
    )
    assert recovery_geometry["target_lane_within_preferred"] is False
    assert geometry["target_string_number"] == 3
    assert geometry["ribbon_half_width_m"] == (
        VISUAL_STRING_RIBBON_HALF_WIDTH_M)
    for item in geometry["strings"]:
        assert item["allowed"] is not None
        assert item["preferred"] is not None
        allowed_y = np.sort(item["allowed"]["centerline"][:, 1])
        preferred_y = np.sort(item["preferred"]["centerline"][:, 1])
        np.testing.assert_allclose(allowed_y, ALLOWED, atol=1e-12)
        np.testing.assert_allclose(preferred_y, PREFERRED, atol=1e-12)
        assert item["allowed"]["polygon"].shape == (4, 3)
        assert item["preferred"]["polygon"].shape == (4, 3)

    spec = CameraSpec(
        eye=(0.32, 0.22, 0.38),
        target=(0.0, -0.325, 0.01),
        width=640,
        height=360,
        horizontal_fov_deg=42.0,
    )
    projected, depth = project_world_points(
        np.array([[0.0, -0.325, 0.012]]), spec)
    assert projected.shape == (1, 2)
    assert depth[0] > 0.0

    with tempfile.TemporaryDirectory() as directory:
        image = Path(directory) / "frame.png"
        Image.new("RGB", (640, 360), (110, 110, 110)).save(image)
        before = np.asarray(Image.open(image)).copy()
        state = draw_strike_zone_pick_overlay(
            image,
            FakeStrikeEnv(),
            spec,
            pick_trail_world=(
                (0.001, -0.321, 0.040),
                (0.002, -0.323, 0.038),
            ),
        )
        with Image.open(image) as rendered:
            assert rendered.size == (640, 360)
            after = np.asarray(rendered)
        assert np.count_nonzero(after != before) > 500
        assert state["diagnostic_only"] is True
        assert state["adds_physics_geometry"] is False
        assert state["target_string_number"] == 3
        assert state["pick_trail_sample_count"] == 2
        json.dumps(state)

    print("PASS: additive strike zone/pick visualization contracts")


if __name__ == "__main__":
    main()
