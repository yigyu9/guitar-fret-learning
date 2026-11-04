"""기존 운지 후보로 9개 과제를 이어 붙인 여섯 손가락 조합을 만든다.

원본 운지 규칙과 앞선 예시 생성기를 읽기 전용으로 재사용한다.
각 조합에 동일한 줄·프렛·시간을 사용하고 전체 press를 다시 계산한다.
"""
import csv
import hashlib
import importlib.util
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
PREVIOUS = OUT.parent / "압현_예시목표_시각화_v1" / "도구" / "build_examples.py"
spec = importlib.util.spec_from_file_location("press_example_builder", PREVIOUS)
examples = importlib.util.module_from_spec(spec)
spec.loader.exec_module(examples)
fm = examples.fm
SEED = 20261110
SECTION_NOTE_GAP = 1.75  # 원본 병합 임계 1.5초보다 길게 설정


def source_hashes():
    baseline = json.loads((OUT / "검증" / "source_before.json").read_text())["files"]
    current = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in baseline}
    if current != baseline:
        raise ValueError("Original sources or the previous builder changed")
    return current


def select_mapping(notes, pair, rng):
    sons = fm.build_sonorities(notes)
    candidates = [fm._melody_candidates(son, notes) for son in sons]
    eligible = []
    for choices in itertools.product(*candidates):
        result = {i: dict(finger=fg, barre=barre, grip=None)
                  for c in choices for i, (fg, barre) in c["assign"].items()}
        used = {r["finger"] for r in result.values()}
        if not used <= set(pair):
            continue
        roles = examples.roles_for(notes, result)
        if roles is None or (len(roles) == 2 and used != set(pair)):
            continue
        checked = examples.checked_mapping(notes, result)
        if checked:
            eligible.append((choices, result))
    if not eligible:
        raise ValueError(f"No valid candidate for finger pair {pair}")
    return rng.choice(eligible), len(eligible)


def build_version(version_id, pair, specifications, rng):
    notes, result, hand, sections, local_cases = [], {}, [], [], []
    next_onset = 1.0
    for case, local_notes in enumerate(specifications, 1):
        (choices, local_result), count = select_mapping(local_notes, pair, rng)
        offset = next_onset - min(n["t_on"] for n in local_notes)
        indices = []
        for n in local_notes:
            idx = len(notes)
            indices.append(idx)
            notes.append(dict(n, idx=idx, role=f"P{case}:{n['role']}",
                              t_on=n["t_on"] + offset, t_off=n["t_off"] + offset,
                              section_id=f"P{case}"))
            result[idx] = dict(local_result[n["idx"]])
        for son, candidate in zip(fm.build_sonorities(local_notes), choices):
            hand.append(dict(t=local_notes[son[0]]["t_on"] + offset,
                             P=candidate["P"], grip=None, barre=None))
        last_note = max(notes[i]["t_off"] for i in indices)
        sections.append(dict(case_id=f"P{case}", title=examples.TITLES[case - 1],
                             first_note=next_onset, last_note=last_note,
                             end=last_note, roles=examples.roles_for(local_notes, local_result),
                             note_indices=indices, eligible_candidate_paths=count))
        local_cases.append((local_notes, local_result, offset))
        next_onset = last_note + SECTION_NOTE_GAP

    # 각 구간의 press를 이어 붙이지 않고 전체 입력으로 다시 생성한다.
    presses = fm.press_events(notes, result)
    violations = fm.validate(notes, result)
    press_violations, intervals = examples.press_checks(presses)
    if violations or press_violations:
        raise ValueError(f"{version_id}: {violations}, {press_violations}")
    for n in notes:
        matching = [p for p in presses if p["finger"] == result[n["idx"]]["finger"]
                    and p["string"] == n["s"] and p["fret"] == n["fret"]
                    and n["t_on"] in p["strikes"]]
        if len(matching) != 1:
            raise ValueError("Each note must belong to exactly one press")
        p = matching[0]
        if not p["t_press"] <= n["t_on"] < n["t_off"] <= p["t_release"]:
            raise ValueError("A note was delayed or shortened by press generation")
    for case, (section, local) in enumerate(zip(sections, local_cases), 1):
        local_notes, local_result, offset = local
        onsets = {notes[i]["t_on"] for i in section["note_indices"]}
        section["press_indices"] = [i for i, p in enumerate(presses)
                                     if any(t in onsets for t in p["strikes"])]
        selected = [presses[i] for i in section["press_indices"]]
        section["start"] = min(p["t_press"] for p in selected)
        if any(p["t_release"] > section["last_note"] for p in selected):
            raise ValueError("A press was merged across section boundaries")
        local_presses = [dict(p, t_press=p["t_press"] - offset,
                             t_release=p["t_release"] - offset,
                             strikes=[t - offset for t in p["strikes"]]) for p in selected]
        examples.task_contract(case, local_notes, local_result, local_presses)
    assigned_presses = [i for s in sections for i in s["press_indices"]]
    if sorted(assigned_presses) != list(range(len(presses))):
        raise ValueError("A press is missing or shared between sections")
    boundaries = []
    for previous, following in zip(sections, sections[1:]):
        note_gap = following["first_note"] - previous["last_note"]
        press_gap = following["start"] - previous["last_note"]
        if note_gap != SECTION_NOTE_GAP or press_gap <= 0:
            raise ValueError("Section boundary must contain a release interval")
        boundaries.append(dict(after=previous["case_id"], before=following["case_id"],
                               note_gap_s=note_gap, no_press_gap_s=round(press_gap, 4)))
    data = dict(metadata=dict(version_id=version_id, finger_pair=list(pair), seed=SEED,
                              sections=sections, duration=sections[-1]["last_note"],
                              section_note_gap_s=SECTION_NOTE_GAP,
                              selection="seeded valid-candidate sampling restricted to each finger pair; not minimum-cost beam search",
                              string_convention="0=low-E=6번줄, 5=high-e=1번줄",
                              scope="운지 규칙 검증; 물리 압현 성공은 미검증"),
                notes=[dict(idx=n["idx"], string=n["s"], fret=n["fret"], midi=n["midi"],
                            t_on=n["t_on"], t_off=n["t_off"], role=n["role"],
                            section_id=n["section_id"], **result[n["idx"]]) for n in notes],
                presses=presses, hand=hand, diagnostics=[])
    report = dict(version_id=version_id, finger_pair=list(pair),
                  note_count=len(notes), press_count=len(presses),
                  original_validate_violations=violations,
                  press_boundary_violations=press_violations,
                  active_intervals_checked=len(intervals),
                  note_duration_preserved=True, original_candidates_only=True,
                  all_nine_task_contracts_passed=True, section_boundaries=boundaries)
    return data, report


def build_all():
    """파일을 쓰지 않고 전체 산출물과 검사 보고서를 재생성한다."""
    hashes = source_hashes()
    rng = random.Random(SEED)
    pairs = list(itertools.combinations(range(1, 5), 2))
    rng.shuffle(pairs)
    specifications = examples.specifications(random.Random(SEED))
    outputs, reports = [], []
    for i, pair in enumerate(pairs, 1):
        data, report = build_version(f"C{i}", pair, specifications, rng)
        outputs.append(data)
        reports.append(report)
    geometries = [[(n["string"], n["fret"], n["t_on"], n["t_off"])
                   for n in data["notes"]] for data in outputs]
    if any(g != geometries[0] for g in geometries[1:]):
        raise ValueError("Versions must share identical geometry and timing")
    if {tuple(d["metadata"]["finger_pair"]) for d in outputs} != set(
            itertools.combinations(range(1, 5), 2)):
        raise ValueError("The six distinct finger pairs are not covered")
    if source_hashes() != hashes:
        raise ValueError("Source hashes changed during generation")
    report = dict(seed=SEED, all_passed=True, physical_validation_performed=False,
                  source_files_unchanged=True, source_sha256=hashes,
                  all_six_finger_pairs_covered=True, same_geometry_and_timing=True,
                  parameters=dict(lead=fm.PRESS_LEAD, merge_gap=fm.PRESS_MERGE_GAP,
                                  finger_move_t=fm.FINGER_MOVE_T, max_shave=fm.MAX_SHAVE,
                                  allow_barre=False), versions=reports)
    return outputs, report


def main():
    outputs, report = build_all()
    for data in outputs:
        prefix = OUT / "입력" / data["metadata"]["version_id"]
        examples.write_json(prefix.with_suffix(".fingering.json"), data)
        examples.write_json(prefix.with_suffix(".chords.json"), dict(segments=[
            dict(t0=0.0, t1=data["metadata"]["duration"], label="N", conf=0)]))
        with prefix.with_suffix(".notes.csv").open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["string", "start", "end", "pitch"])
            writer.writerows((n["string"], n["t_on"], n["t_off"], n["midi"])
                             for n in data["notes"])
        reloaded, dropped = fm.load_notes(prefix.with_suffix(".notes.csv"))
        expected = [dict(idx=n["idx"], s=n["string"], fret=n["fret"], midi=n["midi"],
                         t_on=n["t_on"], t_off=n["t_off"]) for n in data["notes"]]
        if dropped or reloaded != expected:
            raise ValueError("Raw CSV round-trip failed")
    report["all_raw_csv_roundtrips_passed"] = True
    examples.write_json(OUT / "검증" / "rules_report.json", report)
    print(json.dumps(dict(versions=len(outputs), duration=outputs[0]["metadata"]["duration"],
                          all_passed=True), ensure_ascii=False))


if __name__ == "__main__":
    main()
