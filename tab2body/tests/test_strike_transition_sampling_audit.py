"""The diagnostic distinguishes predicted window coverage from observations."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tab2body.tools.diagnose_strike_stall import _transition_sampling_audit


def main():
    rows = [dict(event_index=i, failure_score=float(i == 3), exposure_mass=10.)
            for i in range(6)]
    checkpoint = {
        "environment_state": {"song_events_per_episode": 6, "random_start": True,
                              "curriculum_stage": "S3_SONG_INTEGRATION"},
        "checkpoint_contract": {"payload": {"config": {"strike": {"curriculum": {
            "stalled_hard_rehearsal_events": 4,
            "stalled_hard_sample_fraction": .5,
            "stalled_hard_window_probability_cap": .5,
        }}}}},
    }
    result = _transition_sampling_audit(checkpoint, rows)
    focus = result["events"][0]
    assert focus["event_index"] == 3
    assert 0 < focus["hard_incoming_outgoing_probability"] <= 1
    assert focus["hard_incoming_outgoing_probability"] <= focus["hard_event_probability"]
    assert result["hard_episode_fraction"] == .5
    assert "not_measured" in result["evidence_scope"]
    config = checkpoint["checkpoint_contract"]["payload"]["config"]["strike"]["curriculum"]
    config["stalled_hard_sample_fraction"] = 0.0
    assert not _transition_sampling_audit(checkpoint, rows)["hard_sampling_active"]
    config["stalled_hard_sample_fraction"] = .5
    checkpoint["environment_state"]["random_start"] = False
    assert not _transition_sampling_audit(checkpoint, rows)["hard_sampling_active"]
    checkpoint["checkpoint_contract"] = {}
    assert not _transition_sampling_audit(checkpoint, rows)["available"]
    print("PASS: Strike transition sampling audit")


if __name__ == "__main__":
    main()
