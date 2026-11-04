"""기존 운지 후보 중 과제 조건을 만족하는 예시를 CPU에서 재현한다.

원본 배정기의 최소 비용 빔 해가 아니라 유효 후보의 seeded sample이다.
원본의 후보/누름 생성/검증 함수를 호출하며 원본 파일은 변경하지 않는다.
"""
import copy
import csv
import hashlib
import itertools
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tab2fingermapping.fingermapping import assign as fm  # noqa: E402

SEED = 20261109
TITLES = ["단일 압현", "두 손가락 동시 압현", "같은 손가락의 목표 전환",
          "손가락 교대", "유지하면서 목표 추가", "일부만 해제",
          "일부 유지하며 나머지 전환", "다중 → 다중 전체 전환", "해제 후 반복 압현"]
SUMMARIES = ["하나의 목표를 누르고 유지한 뒤 해제",
             "서로 다른 두 줄의 같은 프렛을 함께 유지",
             "같은 손가락이 다음 프렛으로 이동",
             "첫 손가락을 해제한 뒤 다른 손가락이 다음 목표 압현",
             "먼저 누른 손가락을 유지하면서 다른 손가락 추가",
             "함께 누른 두 손가락 중 하나만 해제",
             "한 손가락을 계속 유지하며 다른 손가락만 목표 변경",
             "두 손가락 모두 해제한 뒤 각각 다음 목표로 이동",
             "같은 목표에서 실제 해제 구간을 둔 뒤 다시 누르기"]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def specifications(rng):
    """손가락 번호를 넣기 전의 과제별 음·역할을 만든다."""
    cases = []
    for case in range(1, 10):
        s, fret = rng.randrange(5), rng.randrange(4, 9)
        # tuple: 역할, 줄(0=low-E), 프렛, 음 시작, 음 종료
        a = ("a", s, fret, 1.0, 2.5)
        if case == 1:
            rows = [a]
        elif case == 2:
            rows = [a, ("b", s + 1, fret, 1.0, 2.5)]
        elif case == 3:
            rows = [a, ("a", s, fret + 2, 3.0, 4.5)]
        elif case == 4:
            rows = [a, ("b", s + 1, fret + 1, 3.0, 4.5)]
        elif case == 5:
            rows = [("held", s, fret, 1.0, 4.5),
                    ("added", s + 1, fret + 1, 3.0, 4.5)]
        elif case == 6:
            # 어느 공간상의 목표를 오래 유지할지도 무작위로 정한다.
            keep_low = bool(rng.randrange(2))
            rows = [("held" if keep_low else "released", s, fret,
                     1.0, 4.5 if keep_low else 2.5),
                    ("released" if keep_low else "held", s + 1, fret + 1,
                     1.0, 2.5 if keep_low else 4.5)]
        elif case == 7:
            anchor_low = bool(rng.randrange(2))
            anchor_fret = fret if anchor_low else fret + 2
            moving_fret = fret + 1 if anchor_low else fret
            rows = [("held", s, anchor_fret, 1.0, 4.5),
                    ("moving", s + 1, moving_fret, 1.0, 2.5),
                    ("moving", s + 1, moving_fret + 1, 3.0, 4.5)]
        elif case == 8:
            rows = [a, ("b", s + 1, fret + 1, 1.0, 2.5),
                    ("a", s, fret + 1, 3.0, 4.5),
                    ("b", s + 1, fret + 2, 3.0, 4.5)]
        else:
            rows = [a, ("a", s, fret, 4.25, 5.75)]
        cases.append([dict(idx=i, role=role, s=string, fret=f,
                           midi=fm.OPEN_MIDI[string] + f, t_on=on, t_off=off)
                      for i, (role, string, f, on, off) in enumerate(rows)])
    return cases


def roles_for(notes, result):
    roles = {}
    for n in notes:
        finger = result[n["idx"]]["finger"]
        if n["role"] in roles and roles[n["role"]] != finger:
            return None
        roles[n["role"]] = finger
    return roles if len(set(roles.values())) == len(roles) else None


def press_checks(presses):
    """모든 press 경계 사이의 활성 합집합을 검사(lead/해제 시점 포함)."""
    issues, intervals = [], []
    bounds = sorted({p[k] for p in presses for k in ("t_press", "t_release")})
    for start, end in zip(bounds, bounds[1:]):
        t = (start + end) / 2
        active = [p for p in presses if p["t_press"] <= t < p["t_release"]]
        if not active:
            continue
        if len({p["finger"] for p in active}) != len(active):
            issues.append("duplicate_finger")
        if len({p["string"] for p in active}) != len(active):
            issues.append("duplicate_string")
        if any(p["barre"] or not 1 <= p["fret"] <= 14 for p in active):
            issues.append("barre_or_fret_range")
        proxy = [dict(idx=i, s=p["string"], fret=p["fret"])
                 for i, p in enumerate(active)]
        expected = {i: (p["finger"], False) for i, p in enumerate(active)}
        candidates = fm._melody_candidates(list(range(len(proxy))), proxy)
        if not any(c["assign"] == expected for c in candidates):
            issues.append("active_union_not_original_candidate")
        intervals.append(dict(start=start, end=end, active_count=len(active)))
    for finger in range(1, 5):
        ordered = sorted((p for p in presses if p["finger"] == finger),
                         key=lambda p: p["t_press"])
        for previous, following in zip(ordered, ordered[1:]):
            moved = (previous["string"], previous["fret"]) != (
                following["string"], following["fret"])
            gap = following["t_press"] - previous["t_release"]
            if gap < (fm.FINGER_MOVE_T if moved else 0) - 1e-9:
                issues.append("insufficient_finger_move_time")
    return sorted(set(issues)), intervals


def checked_mapping(notes, result):
    if roles_for(notes, result) is None or fm.validate(notes, result):
        return None
    presses = fm.press_events(notes, result)  # 원본 기본값 사용, 바레 제외
    issues, intervals = press_checks(presses)
    if issues:
        return None
    for n in notes:
        finger = result[n["idx"]]["finger"]
        matching = [p for p in presses if p["finger"] == finger
                    and p["string"] == n["s"] and p["fret"] == n["fret"]
                    and n["t_on"] in p["strikes"]]
        if len(matching) != 1 or matching[0]["t_press"] > n["t_on"]:
            return None
        if matching[0]["t_release"] < n["t_off"] or "t_cut" in result[n["idx"]]:
            return None  # 원래 음 길이를 줄여야 성립하는 예시는 제외한다.
    return presses, intervals


def task_contract(case, notes, result, presses):
    """입력의 시간 순서와 역할이 과제 이름에 부합하는지도 검사한다."""
    by_role = {}
    for n in notes:
        by_role.setdefault(n["role"], []).append(n)
    pos = lambda n: (n["s"], n["fret"])
    a, last = notes[0], notes[-1]
    if case == 1:
        ok = len(notes) == len(presses) == 1
    elif case == 2:
        ok = (len(notes) == 2 and a["t_on"] == last["t_on"]
              and a["t_off"] == last["t_off"] and a["fret"] == last["fret"])
    elif case in (3, 4):
        same = result[0]["finger"] == result[1]["finger"]
        ok = (len(notes) == 2 and a["fret"] != last["fret"]
              and a["t_off"] < last["t_on"] and same == (case == 3))
    elif case == 5:
        held, added = by_role["held"][0], by_role["added"][0]
        ok = held["t_on"] < added["t_on"] < held["t_off"] == added["t_off"]
    elif case == 6:
        held, released = by_role["held"][0], by_role["released"][0]
        ok = held["t_on"] == released["t_on"] and released["t_off"] < held["t_off"]
    elif case == 7:
        held, moving = by_role["held"][0], by_role["moving"]
        ok = (len(moving) == 2 and held["t_on"] == moving[0]["t_on"]
              and held["t_off"] == moving[1]["t_off"]
              and moving[0]["t_off"] < moving[1]["t_on"]
              and moving[0]["fret"] != moving[1]["fret"])
    elif case == 8:
        ok = (all(len(ns) == 2 and pos(ns[0]) != pos(ns[1])
                  and ns[0]["t_off"] < ns[1]["t_on"] for ns in by_role.values())
              and notes[0]["t_on"] == notes[1]["t_on"]
              and notes[0]["t_off"] == notes[1]["t_off"]
              and notes[2]["t_on"] == notes[3]["t_on"]
              and notes[2]["t_off"] == notes[3]["t_off"])
    else:
        ok = (len(presses) == 2 and pos(a) == pos(last)
              and last["t_on"] - a["t_off"] > fm.PRESS_MERGE_GAP
              and presses[1]["t_press"] > presses[0]["t_release"])
    if not ok or roles_for(notes, result) is None:
        raise ValueError(f"P{case}: temporal role contract failed")


def build_case(case, notes, rng):
    sons = fm.build_sonorities(notes)
    candidate_sets = [fm._melody_candidates(son, notes) for son in sons]
    eligible = []
    for choices in itertools.product(*candidate_sets):
        result = {i: dict(finger=fg, barre=barre, grip=None)
                  for choice in choices for i, (fg, barre) in choice["assign"].items()}
        checked = checked_mapping(notes, result)
        if checked:
            eligible.append((choices, result, checked))
    if not eligible:
        raise ValueError(f"P{case}: no valid role-preserving candidate")
    choices, result, (presses, intervals) = rng.choice(eligible)
    task_contract(case, notes, result, presses)
    output_notes = [dict(idx=n["idx"], string=n["s"], fret=n["fret"],
                         midi=n["midi"], t_on=n["t_on"], t_off=n["t_off"],
                         role=n["role"], **result[n["idx"]]) for n in notes]
    data = dict(metadata=dict(case_id=f"P{case}", title=TITLES[case - 1],
                             task_summary=SUMMARIES[case - 1], seed=SEED,
                             roles=roles_for(notes, result),
                             selection="seeded sample of valid original melody candidates; not minimum-cost beam output",
                             string_convention="0=low-E=6번줄, 5=high-e=1번줄",
                             scope="무바레 운지 규칙 검사; 실제 물리 압현 가능성은 미검증"),
                notes=output_notes, presses=presses,
                hand=[dict(t=notes[son[0]]["t_on"], P=c["P"], grip=None, barre=None)
                      for son, c in zip(sons, choices)], diagnostics=[])
    report = dict(case_id=f"P{case}", eligible_candidate_paths=len(eligible),
                  roles=data["metadata"]["roles"], note_count=len(notes),
                  press_count=len(presses), original_sonority_candidate_match=True,
                  original_validate_violations=fm.validate(notes, result),
                  press_boundary_violations=press_checks(presses)[0],
                  press_intervals_checked=intervals, sound_duration_preserved=True,
                  temporal_role_contract_passed=True)
    return data, report


def main():
    sources = [Path(fm.__file__), Path(fm.grips.__file__)]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sources}
    rng = random.Random(SEED)
    inputs, reports, coverage = [], [], Counter()
    for case, notes in enumerate(specifications(rng), 1):
        data, report = build_case(case, notes, rng)
        inputs.append(data)
        reports.append(report)
        coverage.update(data["metadata"]["roles"].values())
        prefix = OUT / "입력" / f"P{case}"
        write_json(prefix.with_suffix(".fingering.json"), data)
        write_json(prefix.with_suffix(".chords.json"), dict(segments=[
            dict(t0=0.0, t1=max(n["t_off"] for n in notes), label="N", conf=0)]))
        with prefix.with_suffix(".notes.csv").open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["string", "start", "end", "pitch"])
            writer.writerows((n["s"], n["t_on"], n["t_off"], n["midi"]) for n in notes)
        reloaded, dropped = fm.load_notes(prefix.with_suffix(".notes.csv"))
        if dropped or reloaded != [{k: v for k, v in n.items() if k != "role"} for n in notes]:
            raise ValueError(f"P{case}: raw note CSV round-trip failed")
    if set(coverage) != {1, 2, 3, 4}:
        raise ValueError("The seeded examples do not cover all four fingers")
    # 같은 프렛 다른 줄에 같은 손가락 / 같은 줄 두 손가락: 원 validate의 사각을
    # 추가 press 검사에서 실제로 거부하는지 확인한다.
    negative = []
    for kind in ("duplicate_finger", "duplicate_string"):
        bad = copy.deepcopy(inputs[1]["presses"])
        key = "finger" if kind == "duplicate_finger" else "string"
        bad[1][key] = bad[0][key]
        issues, _ = press_checks(bad)
        if kind not in issues:
            raise ValueError(f"Negative check did not reject {kind}")
        negative.append(dict(mutation=kind, rejected=True, issues=issues))
    if any(hashlib.sha256(p.read_bytes()).hexdigest() != hashes[str(p.relative_to(ROOT))]
           for p in sources):
        raise ValueError("Original mapping source changed during generation")
    write_json(OUT / "검증" / "rules_report.json", dict(
        seed=SEED, all_passed=True, physical_validation_performed=False,
        mapping_sources_sha256=hashes, original_sources_unchanged=True,
        parameters=dict(lead=fm.PRESS_LEAD, merge_gap=fm.PRESS_MERGE_GAP,
                        finger_move_t=fm.FINGER_MOVE_T, max_shave=fm.MAX_SHAVE,
                        allow_barre=False), role_finger_counts=dict(sorted(coverage.items())),
        cases=reports, negative_checks=negative))
    print(json.dumps(dict(cases=len(reports), all_passed=True,
                          role_finger_counts=dict(sorted(coverage.items()))), ensure_ascii=False))


if __name__ == "__main__":
    main()
