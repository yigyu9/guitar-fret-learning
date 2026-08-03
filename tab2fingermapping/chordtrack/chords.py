"""코드 어휘(37클래스)와 피치클래스 집합 → 코드 라벨 결정 규칙.

어휘: 0 = N(no-chord), 이후 root(12) x quality(maj, min, 5).
설계 근거(docs/guitar-basics-notes.md §5):
  - 3도가 장/단을 결정하고, 3도가 없으면 파워코드('5').
  - 7th/6th/9th 등 텐션은 기본 3화음으로 축약(MIR 소어휘 관행).
  - 판단 불가/구성음 부족은 N — false positive가 false negative보다 해롭다.
"""
import re

PC_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_PC_OF = {n: i for i, n in enumerate(PC_NAMES)}
_PC_OF.update({"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10})
QUALITIES = ("maj", "min", "5")

N_LABEL = 0


def label_index(root_pc: int, quality: str) -> int:
    return 1 + root_pc * 3 + QUALITIES.index(quality)


def label_name(idx: int) -> str:
    if idx == N_LABEL:
        return "N"
    idx -= 1
    return f"{PC_NAMES[idx // 3]}:{QUALITIES[idx % 3]}"


# 루트 기준 허용 텐션(커버리지 점수용): 5도 변형(b5/#5), 6, b7, 7, 9, sus4
_EXTRAS = (2, 5, 6, 8, 9, 10, 11)


def match_pcset(pcs, bass_pc=None):
    """활성 피치클래스 집합(과 베이스 음)에서 코드 라벨 인덱스를 결정.

    결정 규칙(우선순위):
      1) 3도(장 또는 단)를 가진 루트 후보를 찾는다 — 베이스 루트 가점.
      2) 3도가 전혀 없으면: 정확히 {r, r+7}일 때만 파워코드 '5'.
      3) 후보 없음/구성음 <2종 → N.
    """
    pcs = set(int(p) % 12 for p in pcs)
    if len(pcs) < 2:
        return N_LABEL

    best, best_score = N_LABEL, -1.0
    for r in pcs:
        maj3 = (r + 4) % 12 in pcs
        min3 = (r + 3) % 12 in pcs
        p5 = (r + 7) % 12 in pcs
        if maj3 and not min3:
            q = "maj"
        elif min3 and not maj3:
            q = "min"
        elif maj3 and min3:                      # 극히 드묾 — 5도 있는 쪽 우선, 기본 maj
            q = "maj" if p5 else "min"
        else:
            continue
        core = 2 + (1 if p5 or (r + 6) % 12 in pcs or (r + 8) % 12 in pcs else 0)
        allowed = {r, (r + (4 if q == "maj" else 3)) % 12} | {(r + e) % 12 for e in _EXTRAS}
        coverage = len(pcs & allowed) / len(pcs)
        score = core * 2 + coverage + (10 if bass_pc is not None and r == bass_pc else 0)
        if score > best_score:
            best_score, best = score, label_index(r, q)

    if best == N_LABEL:                          # 3도 없는 집합 → 파워코드만 허용
        for r in ([bass_pc] if bass_pc in pcs else sorted(pcs)):
            if pcs == {r, (r + 7) % 12}:
                return label_index(r, "5")
    return best


# ---- 파일명 라벨 파서 (감사용): "1-E1-Major 05.xml" 류 ----
_FNAME = re.compile(r"^\d+-([A-G][#b]?)\d*-([A-Za-z0-9#]+)")
_QUAL_MAP = {"major": "maj", "minor": "min", "maj": "maj", "min": "min",
             "major7": "maj", "minor7": "min", "7": "maj", "power": "5", "5": "5"}


def parse_filename_label(stem: str):
    """파일명에서 (root_pc, quality) 기대 라벨 추출. 해석 불가 시 None."""
    m = _FNAME.match(stem)
    if not m:
        return None
    root, qual = m.group(1), m.group(2).lower()
    if root not in _PC_OF or qual not in _QUAL_MAP:
        return None
    return _PC_OF[root], _QUAL_MAP[qual]
