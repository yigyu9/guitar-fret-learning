"""공유본 v4 계획의 주법·줄 개수·중심 시각 frame 검증. CPU 전용이다."""
from copy import deepcopy
import json
import math
from pathlib import Path
import sys
import tempfile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from env.strike_goal_compiler import (  # noqa: E402
    compile_strike_events,
    compiled_strike_goal_from_plan_document,
    strike_plan_document,
)
from env.strike_goals import StrikeGoalSequence  # noqa: E402


def plan(strings, times=None, fps=60):
    times = times or [.5 + i*.003 for i in range(len(strings))]
    events = [dict(time=time, frame=int(math.floor(time*fps+.5)), string=string)
              for time, string in zip(times, strings)]
    compiled = compile_strike_events(events, fps=fps, rearm_min_frames=2,
        follow_through_min_frames=1, initial_timing_tolerance_ms=100)
    return compiled, strike_plan_document(compiled, fps=fps)


def expect_error(fragment, document):
    try:
        compiled_strike_goal_from_plan_document(document)
    except ValueError as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError("malformed strike plan was accepted: " + fragment)


def main():
    cases = ((2,), (5, 4), (5, 0), (5, 4, 3, 2, 1, 0), (2, 2), (5, 3, 5))
    for strings in cases:
        compiled, document = plan(strings)
        restored = compiled_strike_goal_from_plan_document(document)
        assert restored.events == compiled.events
        assert restored.original_times_s == compiled.original_times_s
        assert restored.easy_times_s == compiled.easy_times_s
    # 두 발음 줄 사이의 보호 줄 네 개를 통과하는 정상 스트럼을 유지한다.
    _, gapped = plan((5, 0))
    gapped_event = compiled_strike_goal_from_plan_document(gapped).events[0]
    assert gapped_event.gesture == "strum"
    assert gapped_event.audible_strings == (5, 0)
    assert gapped_event.traversal_strings == (5, 4, 3, 2, 1, 0)
    assert gapped_event.protected_strings == (4, 3, 2, 1)
    # alternate 묶음도 여러 종류 줄과 보호 줄을 포함할 수 있다.
    _, alternate = plan((5, 3, 5))
    alternate_event = compiled_strike_goal_from_plan_document(alternate).events[0]
    assert alternate_event.gesture == "alternate_restrike"
    assert alternate_event.audible_strings == (5, 3)
    assert alternate_event.traversal_strings == (5, 4, 3)

    for strings, gesture in (((5, 0), "single_pick"), ((2,), "strum"),
                             ((5, 0), "alternate_restrike"), ((5, 3, 5), "strum")):
        _, document = plan(strings)
        document["events"][0]["gesture"] = gesture
        expect_error("gesture/string count mismatch", document)

    _, single = plan((2,))
    expanded = deepcopy(single)
    expanded["events"][0].update(traversal_strings=[2, 1], protected_strings=[1],
        traversal_offsets_s=[-.0035, .0035], sweep_duration_s=.007)
    expect_error("gesture/string count mismatch", expanded)
    duplicate = deepcopy(gapped)
    duplicate["events"][0]["strings"] = [5, 5]
    expect_error("invalid audible/traversal", duplicate)
    outside = deepcopy(gapped)
    outside["events"][0].update(strings=[5, 0], traversal_strings=[5, 4],
        protected_strings=[4], traversal_offsets_s=[-.0035, .0035], sweep_duration_s=.007)
    expect_error("invalid audible/traversal", outside)

    # v4는 compiler와 같은 half-up 반올림을 쓰며 반 프레임 직전/이후를 구별한다.
    for fps in (30, 60, 120):
        for fraction, expected in ((.5-1e-7, 0), (.5, 1), (.5+1e-7, 1)):
            compiled, document = plan((2,), times=[fraction/fps], fps=fps)
            restored = compiled_strike_goal_from_plan_document(document)
            assert restored.events[0].frame == compiled.events[0].frame == expected
    _, centered = plan((5, 4, 3), times=[.5, .52, .54])
    current = centered["events"][0]
    assert current["frame"] == 31
    assert int(math.floor((current["time"]+current["traversal_offsets_s"][0])*60+.5)) == 30
    for invalid in (30, 9999):
        changed = deepcopy(centered)
        changed["events"][0]["frame"] = invalid
        expect_error("time/frame mismatch", changed)
    for invalid in (30.5, True, "30"):
        changed = deepcopy(single)
        changed["events"][0]["frame"] = invalid
        expect_error("invalid strike plan event", changed)
    for invalid in (0, -1, True, 60.5, "60", None):
        changed = deepcopy(single)
        changed["metadata"]["fps"] = invalid
        expect_error("metadata.fps", changed)

    # 실제 CPU 목표 로더도 같은 검증을 적용한다. 원본·GPU는 사용하지 않는다.
    with tempfile.TemporaryDirectory(prefix="strike_plan_validation_") as directory:
        path = Path(directory)/"strike_plan.json"
        path.write_text(json.dumps(gapped), encoding="utf-8")
        goals = StrikeGoalSequence(path, device="cpu")
        goals.require_supported_gestures()
        for field, value, error in (("gesture", "single_pick", "gesture/string count mismatch"),
                                    ("frame", 9999, "time/frame mismatch")):
            changed = deepcopy(gapped)
            changed["events"][0][field] = value
            path.write_text(json.dumps(changed), encoding="utf-8")
            try:
                StrikeGoalSequence(path, device="cpu")
            except ValueError as exc:
                assert error in str(exc)
            else:
                raise AssertionError("goal loader accepted malformed " + field)

    print("PASS: v4 gesture cardinality and compiler-center frame validation")


if __name__ == "__main__":
    main()
