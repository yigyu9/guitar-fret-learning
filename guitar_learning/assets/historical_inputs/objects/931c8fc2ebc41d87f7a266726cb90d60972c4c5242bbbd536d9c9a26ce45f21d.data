"""CPU-only regression tests for the fixed-guitar canonical event compiler."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.full.events import (  # noqa: E402
    DEFAULT_MAX_DELAY_FRAMES,
    CanonicalEventTimeline,
    SongBundleValidationError,
    UnsupportedCanonicalEventError,
    canonical_content_sha256,
    compile_song_bundle_events,
)


def _bundle(song_id: str) -> Path:
    return PROJECT_ROOT / "data" / "song_bundles" / song_id


def _expect_error(error_type, fragment: str, callback) -> None:
    try:
        callback()
    except error_type as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError(
            f"expected {error_type.__name__} containing {fragment!r}")


def test_strict_jazz_bundle_compile_roundtrip_and_source_identity():
    root = _bundle("02_Jazz1-200-B_solo")
    timeline = compile_song_bundle_events(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    plan = json.loads(
        (root / "training" / "strike_plan.json").read_text(encoding="utf-8"))
    fingering = json.loads(
        (root / "mapping" / "fingering.json").read_text(encoding="utf-8"))

    assert timeline.song_id == root.name
    assert timeline.fps == 60
    assert timeline.timing_mode == "original"
    assert len(timeline.events) == len(plan["events"]) == 42
    # Canonical events follow sparse musical onsets, never 861 dense Fret frames.
    assert len(timeline.events) < len(json.loads(
        (root / "training" / "fret_training.json").read_text(
            encoding="utf-8"))["frames"])

    source_paths = tuple(item.relative_path for item in timeline.source_files)
    assert source_paths == (
        "mapping/fingering.json",
        "training/fret_training.json",
        "training/strike_plan.json",
        "training/strike_training.json",
    )
    for source in timeline.source_files:
        assert source.sha256 == manifest["files"][source.relative_path]["sha256"]

    flattened = tuple(
        source_id for event in timeline.events
        for source_id in event.source_event_ids)
    assert flattened == tuple(range(len(fingering["notes"])))
    assert len(set(flattened)) == len(flattened)
    for event in timeline.events:
        assert tuple(target.source_event_id for target in event.string_targets) == (
            event.source_event_ids)
        assert tuple(dict.fromkeys(
            target.string for target in event.string_targets)) == (
                event.strike.audible_strings)
        for target in event.string_targets:
            source_note = fingering["notes"][target.mapping_note_index]
            assert target.source_string == source_note["string"]
            assert target.string == 5 - source_note["string"]
            assert target.fret == source_note["fret"]
            assert target.fret_event_index is not None
            assert target.press_start_s is not None
            assert target.release_s is not None

    assert timeline.content_sha256 == canonical_content_sha256(timeline)
    restored = CanonicalEventTimeline.from_json(timeline.to_json())
    assert restored == timeline
    assert compile_song_bundle_events(root).content_sha256 == (
        timeline.content_sha256)

    tampered = copy.deepcopy(timeline.to_document())
    tampered["events"][0]["string_targets"][0]["fret"] += 1
    _expect_error(
        SongBundleValidationError, "content hash mismatch",
        lambda: CanonicalEventTimeline.from_document(tampered))


def test_strum_release_boundary_and_deadline_use_first_crossing():
    timeline = compile_song_bundle_events(
        _bundle("00_SS1-68-E_comp"), fail_on_unsupported=False)
    event = next(
        item for item in timeline.events
        if min(item.strike.traversal_offsets_s) < 0.0)
    first_offset = min(event.strike.traversal_offsets_s)
    expected_boundary = event.score_time_s + first_offset

    assert math.isclose(
        event.release_boundary_time_s, expected_boundary, abs_tol=1e-12)
    assert event.release_boundary_time_s < event.score_time_s
    assert event.release_boundary_frame == math.floor(
        expected_boundary * timeline.fps + 0.5)
    # The delay window is relative to first crossing, not the strum centre.
    assert math.isclose(
        event.release_decision_deadline_s,
        event.release_boundary_time_s
        + event.effective_delay_cap_frames / timeline.fps,
        abs_tol=1e-12)
    assert event.release_decision_deadline_frame == (
        event.release_boundary_frame + event.effective_delay_cap_frames)
    assert math.isclose(
        event.traversal_end_time_s,
        event.score_time_s + max(event.strike.traversal_offsets_s),
        abs_tol=1e-12)
    assert event.traversal_end_frame >= event.release_boundary_frame


def test_effective_delay_cap_is_limited_by_outgoing_transition_slack():
    timeline = compile_song_bundle_events(
        _bundle("00_SS1-68-E_comp"), fail_on_unsupported=False)
    for event in timeline.events[:-1]:
        assert event.outgoing_edge_gap_s is not None
        assert event.outgoing_required_gap_s is not None
        slack_frames = math.floor(
            (event.outgoing_edge_gap_s - event.outgoing_required_gap_s)
            * timeline.fps + 1e-9)
        assert event.effective_delay_cap_frames == min(
            DEFAULT_MAX_DELAY_FRAMES, slack_frames)

    assert timeline.events[-1].effective_delay_cap_frames == (
        DEFAULT_MAX_DELAY_FRAMES)
    assert timeline.events[-1].outgoing_edge_gap_s is None
    assert timeline.events[-1].outgoing_required_gap_s is None

    # This reviewed song has a 51 ms edge gap against a 50 ms required gap.
    # At 60 Hz there is not one complete spare frame, so delaying is forbidden.
    tight = timeline.events[82]
    assert math.isclose(tight.outgoing_edge_gap_s, 0.051, abs_tol=1e-12)
    assert math.isclose(tight.outgoing_required_gap_s, 0.05, abs_tol=1e-12)
    assert tight.effective_delay_cap_frames == 0


def test_unsupported_fretted_mapping_fails_closed_but_is_diagnosable():
    root = _bundle("00_SS1-68-E_comp")
    _expect_error(
        UnsupportedCanonicalEventError,
        "missing_or_invalid_fretted_finger",
        lambda: compile_song_bundle_events(root))

    timeline = compile_song_bundle_events(root, fail_on_unsupported=False)
    unsupported = [event for event in timeline.events if not event.supported]
    assert len(unsupported) == 1
    event = unsupported[0]
    assert event.source_event_ids == (128, 129, 130, 131, 132)
    bad_targets = [target for target in event.string_targets if not target.supported]
    assert len(bad_targets) == 1
    assert bad_targets[0].source_event_id == 128
    assert bad_targets[0].finger is None
    assert bad_targets[0].fret_event_index is None
    assert bad_targets[0].unsupported_reasons == (
        "missing_or_invalid_fretted_finger",
        "missing_fret_event_link",
    )


def main():
    test_strict_jazz_bundle_compile_roundtrip_and_source_identity()
    test_strum_release_boundary_and_deadline_use_first_crossing()
    test_effective_delay_cap_is_limited_by_outgoing_transition_slack()
    test_unsupported_fretted_mapping_fails_closed_but_is_diagnosable()
    print("PASS: canonical G0 full-event compiler contracts")


if __name__ == "__main__":
    main()
