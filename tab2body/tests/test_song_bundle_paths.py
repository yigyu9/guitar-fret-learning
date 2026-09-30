"""CPU checks for canonical song-bundle path resolution."""
from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.cfg import FRET  # noqa: E402
from tab2body.song_bundles import (  # noqa: E402
    DEFAULT_SONG_ID,
    SONG_BUNDLES_ROOT,
    fret_goal_path,
    hand_targets_path,
    strike_goal_path,
)
from tab2body.strike_cfg import (  # noqa: E402
    DEFAULT_STRIKE_SONG_ID,
    STRIKE,
)
from tab2body.train_fret import (  # noqa: E402
    canonical_song_bundle_for_goal,
    goal_identity,
    resolve_hand_targets,
    rollout_video_command,
)
from tab2body.train_strike import _song_identity  # noqa: E402


def main():
    fret = fret_goal_path()
    hand = hand_targets_path()
    strike = strike_goal_path(DEFAULT_STRIKE_SONG_ID)
    assert fret.is_file() and hand.is_file() and strike.is_file()
    assert Path(FRET["goal_path"]) == fret
    assert Path(FRET["hand_targets_path"]) == hand
    assert Path(STRIKE["goal_path"]) == strike

    assert goal_identity(fret)[1] == DEFAULT_SONG_ID
    assert canonical_song_bundle_for_goal(fret) == (
        SONG_BUNDLES_ROOT / DEFAULT_SONG_ID)
    assert canonical_song_bundle_for_goal(
        PROJECT_ROOT / "custom.fret_training.json") is None
    assert _song_identity(strike)[1] == DEFAULT_STRIKE_SONG_ID
    assert resolve_hand_targets(fret) == str(hand)
    command = rollout_video_command("checkpoint.pt", fret, hand, 60)
    assert command[1:3] == ["-m", "tab2body.tools.record_fret_rollout"]
    expected_audio = SONG_BUNDLES_ROOT / DEFAULT_SONG_ID / "source" / "audio.wav"
    assert str(expected_audio) in command

    manifests = sorted(SONG_BUNDLES_ROOT.glob("*/manifest.json"))
    assert len(manifests) == 8
    ready_strike = 0
    ineligible_strike = 0
    unsupported_strike = 0
    infeasible_strike = 0
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["schema"] == "tab2body.song_bundle.v1"
        assert manifest["availability"]["tablature"]
        assert manifest["availability"]["fingering"]
        assert manifest["training_status"]["fret"]["state"] == "ready"
        state = manifest["training_status"]["strike"]["state"]
        ready_strike += state == "ready"
        ineligible_strike += state == "ineligible"
        unsupported_strike += state == "unsupported"
        infeasible_strike += state == "infeasible"
    assert ready_strike == 6
    assert ineligible_strike == 1
    assert unsupported_strike == 1
    assert infeasible_strike == 0
    print(
        "PASS: 8 bundles, 6 ready strike plans, 1 unsupported, "
        "1 ineligible, 0 infeasible")


if __name__ == "__main__":
    main()
