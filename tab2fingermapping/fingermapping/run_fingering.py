"""운지 배정 CLI — notes.csv + chords.json → fingering.json.

실행 (stdlib만 사용 — 아무 python3, 권장은 tab2fm):
  python fingermapping/run_fingering.py <notes.csv> <chords.json> [--out x.fingering.json]
전체 파이프라인은 상위 pipeline.py가 4단계로 자동 호출.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assign  # noqa: E402


def run(csv_path, chords_path, out_path):
    notes, dropped = assign.load_notes(csv_path)
    segs = assign.load_chordtrack(chords_path)
    result, hand, diags = assign.assign_fingers(notes, segs)
    violations = assign.validate(notes, result)

    out_notes = []
    for n in notes:
        a = result.get(n["idx"], dict(finger=None, barre=False, grip=None))
        rec = dict(
            t_on=round(n["t_on"], 4), t_off=round(n["t_off"], 4),
            string=n["s"], fret=n["fret"], midi=n["midi"],
            finger=a["finger"], barre=a["barre"], grip=a["grip"])
        if "t_cut" in a:
            rec["t_cut"] = a["t_cut"]                # 조기 리프트: 유효 종료시각
        out_notes.append(rec)
    presses = assign.press_events(notes, result)   # 왼손 누름 타임라인 (타현과 분리)
    out = dict(convention="string 0 = low-E (CSV/모델 관례)",
               notes=out_notes, presses=presses, hand=hand,
               diagnostics=diags, violations=violations,
               stats=dict(n_notes=len(notes), dropped_invalid_fret=dropped,
                          n_presses=len(presses),
                          n_diagnostics=len(diags), n_violations=len(violations)))
    Path(out_path).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    return out


def render_preview(out, limit=20):
    """사람 눈 검수용 텍스트 렌더."""
    lines = []
    for n in out["notes"][:limit]:
        fg = {0: "개방", None: "?"}.get(n["finger"], str(n["finger"]))
        lines.append(f"{n['t_on']:7.2f}s s{n['string']} f{n['fret']:>2} "
                     f"finger={fg:<3} {'[barre]' if n['barre'] else ''}"
                     f"{n['grip'] or ''}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="tab+chord -> left-hand fingering JSON")
    ap.add_argument("notes_csv")
    ap.add_argument("chords_json")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    out_path = args.out or str(Path(args.notes_csv).with_suffix("")) + ".fingering.json"
    out = run(args.notes_csv, args.chords_json, out_path)
    s = out["stats"]
    print(render_preview(out))
    print(f"[fingering] notes={s['n_notes']} diagnostics={s['n_diagnostics']} "
          f"violations={s['n_violations']} -> {out_path}")


if __name__ == "__main__":
    main()
