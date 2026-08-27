"""CPU checks for single-finger occupancy and the explicit barre extension."""
from assign import press_events


def note(idx, string, fret, onset, offset):
    return {
        "idx": idx,
        "s": string,
        "fret": fret,
        "t_on": onset,
        "t_off": offset,
    }


def main():
    # Returning to the original string at the same fret is still a real move.
    # It must not merge across the intervening other-string event.
    notes = [
        note(0, 0, 4, 1.0, 1.1),
        note(1, 1, 4, 1.3, 1.4),
        note(2, 0, 4, 1.6, 1.7),
    ]
    assignments = {
        idx: {"finger": 2, "barre": False, "grip": None}
        for idx in range(3)
    }
    events = press_events(notes, assignments, allow_barre=False)
    assert len(events) == 3
    assert [(event["string"], event["fret"]) for event in events] == [
        (0, 4), (1, 4), (0, 4)]
    assert all(len(event["strikes"]) == 1 for event in events)
    assert all(left["t_release"] <= right["t_press"]
               for left, right in zip(events, events[1:]))

    # The future extension remains explicit: only an index-finger event marked
    # barre on both strings may overlap at one fret.
    barre_notes = [
        note(0, 0, 3, 2.0, 2.5),
        note(1, 1, 3, 2.0, 2.5),
    ]
    barre_assignments = {
        idx: {"finger": 1, "barre": True, "grip": None}
        for idx in range(2)
    }
    barre_events = press_events(
        barre_notes, barre_assignments, allow_barre=True)
    assert len(barre_events) == 2
    assert all(event["barre"] for event in barre_events)
    assert barre_events[0]["t_press"] == barre_events[1]["t_press"]
    assert barre_events[0]["t_release"] == barre_events[1]["t_release"]

    print("PASS: cross-string moves do not merge; explicit barre remains available")


if __name__ == "__main__":
    main()
