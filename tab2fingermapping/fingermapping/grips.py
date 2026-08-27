"""코드 그립 사전 — (root, quality) → 운지 템플릿(손가락 번호까지).

규칙 1(코드면 사전 조회)의 구현. docs/finger-mapping-design.md §6.
줄 인덱스 = CSV/모델 관례: s0=low-E(6번줄) … s5=high-e(1번줄).
finger: 0=개방(손가락 없음), 1=검지, 2=중지, 3=약지, 4=소지.
그립 = dict s → (fret, finger). 사전에 없는 줄 = 뮤트/미사용.
barre = (fret, s_from, s_to) — 검지 바레 구간.

폼 원천: 교본 코드 차트(오픈 폼) + CAGED 이동 폼(E폼=루트 6번줄, A폼=루트 5번줄)
+ 파워코드. moum 파일명 의미론(`E1-Major 05` = E폼 +5프렛)과 동일 원리.
"""

OPEN_MIDI = [40, 45, 50, 55, 59, 64]          # s0..s5 개방현 MIDI
PC_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# ---- 오픈 폼 (루트pc, 성질, {s: (fret, finger)}) — 교본 관례 운지 ----
_OPEN_FORMS = [
    ("E:maj/open", 4, "maj", {0: (0, 0), 1: (2, 2), 2: (2, 3), 3: (1, 1), 4: (0, 0), 5: (0, 0)}),
    ("E:min/open", 4, "min", {0: (0, 0), 1: (2, 2), 2: (2, 3), 3: (0, 0), 4: (0, 0), 5: (0, 0)}),
    ("A:maj/open", 9, "maj", {1: (0, 0), 2: (2, 1), 3: (2, 2), 4: (2, 3), 5: (0, 0)}),
    ("A:min/open", 9, "min", {1: (0, 0), 2: (2, 2), 3: (2, 3), 4: (1, 1), 5: (0, 0)}),
    ("D:maj/open", 2, "maj", {2: (0, 0), 3: (2, 1), 4: (3, 3), 5: (2, 2)}),
    ("D:min/open", 2, "min", {2: (0, 0), 3: (2, 2), 4: (3, 3), 5: (1, 1)}),
    ("C:maj/open", 0, "maj", {1: (3, 3), 2: (2, 2), 3: (0, 0), 4: (1, 1), 5: (0, 0)}),
    ("G:maj/open", 7, "maj", {0: (3, 2), 1: (2, 1), 2: (0, 0), 3: (0, 0), 4: (0, 0), 5: (3, 3)}),
]


def _norm(form):
    """fret 0 항목은 finger 0으로, barre는 fret>0일 때만."""
    grip, barre = {}, form.get("barre")
    for s, (f, fg) in form["map"].items():
        grip[s] = (f, 0) if f == 0 else (f, fg)
    if barre and barre[0] <= 0:
        barre = None
    return dict(name=form["name"], grip=grip, barre=barre)


def grips_for(root_pc: int, quality: str):
    """(root_pc, quality) → 그립 후보 목록 (관용도 순: 오픈 → E폼 → A폼)."""
    out = []
    if quality in ("maj", "min"):
        for name, pc, q, m in _OPEN_FORMS:
            if pc == root_pc and q == quality:
                out.append(_norm(dict(name=name, map=m, barre=None)))
        r = (root_pc - 4) % 12                     # E폼: 루트 = 6번줄 R프렛
        if r > 0:
            m = ({0: (r, 1), 1: (r + 2, 3), 2: (r + 2, 4), 3: (r + 1, 2), 4: (r, 1), 5: (r, 1)}
                 if quality == "maj" else
                 {0: (r, 1), 1: (r + 2, 3), 2: (r + 2, 4), 3: (r, 1), 4: (r, 1), 5: (r, 1)})
            out.append(_norm(dict(name=f"{PC_NAMES[root_pc]}:{quality}/E-form@{r}",
                                  map=m, barre=(r, 0, 5))))
        r = (root_pc - 9) % 12                     # A폼: 루트 = 5번줄 R프렛
        if r > 0:
            m = ({1: (r, 1), 2: (r + 2, 2), 3: (r + 2, 3), 4: (r + 2, 4), 5: (r, 1)}
                 if quality == "maj" else
                 {1: (r, 1), 2: (r + 2, 3), 3: (r + 2, 4), 4: (r + 1, 2), 5: (r, 1)})
            out.append(_norm(dict(name=f"{PC_NAMES[root_pc]}:{quality}/A-form@{r}",
                                  map=m, barre=(r, 1, 5))))
    if quality in ("maj", "min", "5"):             # 파워코드(루트+5도) — '5'는 이것만
        for rs in (0, 1):                          # 루트 줄 = 6번줄 또는 5번줄
            r = (root_pc - OPEN_MIDI[rs]) % 12
            m = {rs: (r, 1 if r else 0), rs + 1: (r + 2, 3)}
            out.append(_norm(dict(name=f"{PC_NAMES[root_pc]}:5/P{rs + 1}@{r}",
                                  map=m, barre=None)))
    return out


def match_grip(grip: dict, footprint: dict):
    """그립 vs 세그먼트 발자국 매칭.

    footprint: {s: set(frets)} — 세그먼트 동안 그 줄에서 관측된 프렛들.
    반환 (coverage, extras, ok):
      coverage = 그립이 설명하는 관측 노트 비율(개방 포함),
      extras   = 그립 밖의 (s, fret) 목록 (코드 위 멜로디 등),
      ok       = 치명적 모순 없음 (바레 아래 개방현 등).
    """
    total = covered = 0
    extras = []
    barre = grip.get("barre")
    for s, frets in footprint.items():
        for f in frets:
            total += 1
            g = grip["grip"].get(s)
            if g is not None and g[0] == f:
                covered += 1
            else:
                if f == 0 and barre and barre[1] <= s <= barre[2]:
                    return 0.0, [], False          # 바레 그늘의 개방현 = 모순 (규칙 4)
                extras.append((s, f))
    return (covered / total if total else 0.0), extras, True
