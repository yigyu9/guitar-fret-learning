"""
csv_to_notejson — transcription CSV -> guitar-repo note JSON (tabproc input).
(07-15 재구성: tabtrans/ → tab2fingermapping/. pipeline.py --bpm 경로에서 자동 호출)

Bridges Stage-1 (audio -> per-string note CSV, transcribe.py) to the tab
pipeline: [{tempo, notes:[{t:"n/16", effects:{tied:[6]?}, frets:[6]}]}].
stdlib-only on purpose (runs anywhere; no ML deps).

Key conversions:
  * STRING INDEX FLIP (verified trap): model/CSV string 0 = low-E (GuitarSet),
    note-JSON index 5 = low-E -> json_idx = 5 - csv_string.
  * pitch -> fret: fret = pitch - open_pitch[csv_string],
    open = [40,45,50,55,59,64] (standard tuning, low-E..high-e).
    Invalid frets (<0 or >22) are DROPPED and reported, never emitted.
  * BPM: --bpm if known; otherwise grid-fit estimation over 40..240 from note
    onsets (relative quantization error; ties resolved toward slower tempo to
    avoid the degenerate fast-grid optimum). The model has no tempo head.
  * timing: onsets/offsets snapped to a 1/16-note grid; simultaneous onsets
    (same grid slot) become ONE chord event; notes sustaining across later
    onsets carry effects.tied on the continuation events; silent stretches
    become rest events (all -1).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from fractions import Fraction

N_STRINGS = 6
OPEN_PITCH = [40, 45, 50, 55, 59, 64]      # csv string 0(low-E) .. 5(high-e)
MAX_FRET = 22
GRID_DIV = 16                               # quantization grid: 1/16 note


def load_csv(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append((int(r["string"]), float(r["start"]),
                         float(r["end"]), int(round(float(r["pitch"])))))
    return rows


def estimate_bpm(onsets, lo=40, hi=240):
    """Grid-fit search: minimize relative quantization error of onsets.
    Among near-optimal candidates prefer the slowest tempo (largest grid)."""
    if len(onsets) < 4:
        return 120.0
    t0 = min(onsets)
    xs = sorted(o - t0 for o in onsets)
    scored = []
    bpm = float(lo)
    while bpm <= hi:
        grid = 60.0 / bpm / (GRID_DIV / 4)          # seconds per 1/16 at this bpm
        err = sum(abs(x / grid - round(x / grid)) for x in xs) / len(xs)  # in grid units
        scored.append((err, bpm))
        bpm += 0.5
    best_err = min(e for e, _ in scored)
    near = [b for e, b in scored if e <= best_err * 1.05 + 1e-9]
    return min(near)                                 # slowest near-optimal


def convert(rows, bpm=None, grid_div=GRID_DIV):
    report = {"notes_in": len(rows), "dropped_invalid_fret": 0,
              "events_out": 0, "chord_events": 0, "tied_marks": 0}
    notes = []
    for s, t0, t1, pitch in rows:
        fret = pitch - OPEN_PITCH[s]
        if fret < 0 or fret > MAX_FRET:
            report["dropped_invalid_fret"] += 1
            continue
        notes.append((5 - s, t0, t1, fret))          # index flip to note-JSON convention

    if not notes:
        sys.exit("no valid notes after conversion")
    onsets = [t0 for _, t0, _, _ in notes]
    if bpm is None:
        bpm = estimate_bpm(onsets)
    grid = 60.0 / bpm / (grid_div / 4)
    base = min(onsets)

    # quantize to grid slots
    q = []
    qerr = []
    for j, t0, t1, fret in notes:
        on = int(round((t0 - base) / grid))
        off = max(on + 1, int(round((t1 - base) / grid)))
        qerr.append(abs((t0 - base) / grid - on) * grid)
        q.append((j, on, off, fret))
    report["bpm"] = round(bpm, 2)
    report["mean_onset_qerr_ms"] = round(1000 * sum(qerr) / len(qerr), 1)

    # event boundaries = every onset slot (+ final end)
    bounds = sorted({on for _, on, _, _ in q})
    end_slot = max(off for _, _, off, _ in q)
    bounds.append(end_slot)

    events = []
    for bi in range(len(bounds) - 1):
        b, b_next = bounds[bi], bounds[bi + 1]
        frets = [-1] * N_STRINGS
        tied = [0] * N_STRINGS
        for j, on, off, fret in q:
            if on == b:
                frets[j] = fret                       # strike (fret 0 = open)
            elif on < b < off:
                frets[j] = fret                       # sustain continuation
                tied[j] = 1
        dur = Fraction(b_next - b, grid_div).limit_denominator(64)
        note = {"t": f"{dur.numerator}/{dur.denominator}" if dur.denominator > 1
                else str(dur.numerator),
                "effects": ({"tied": tied} if any(tied) else {}),
                "frets": frets}
        events.append(note)
        report["tied_marks"] += sum(tied)
        struck = sum(1 for i in range(N_STRINGS) if frets[i] >= 0 and not tied[i])
        if struck >= 2:
            report["chord_events"] += 1
    report["events_out"] = len(events)
    return [{"tempo": round(bpm, 2), "notes": events}], report


def main(argv=None):
    ap = argparse.ArgumentParser(description="transcription CSV -> note JSON (tabproc input)")
    ap.add_argument("csv_path")
    ap.add_argument("--out", default=None, help="output json (default: <csv>.notes.json)")
    ap.add_argument("--bpm", type=float, default=None, help="known tempo; omit to estimate")
    args = ap.parse_args(argv)

    rows = load_csv(args.csv_path)
    data, report = convert(rows, bpm=args.bpm)
    out = args.out or (args.csv_path.rsplit(".", 1)[0] + ".notes.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=1)
    print(f"[convert] {report}")
    print(f"[convert] -> {out}")


if __name__ == "__main__":
    main()
