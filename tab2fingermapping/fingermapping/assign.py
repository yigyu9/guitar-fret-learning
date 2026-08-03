"""왼손 운지 배정 — 규칙 1~5(docs/finger-mapping-design.md)의 빔 서치 구현.

입력: 탭 노트(notes.csv: string,start,end,pitch) + 코드 트랙(chords.json — chordtrack 산출).
출력: 노트별 finger(0=개방,1~4)·바레, 시간별 손 상태(P·그립), 진단 목록.

규칙 → 코드 대응:
  규칙1 사전 조회   = grips.grips_for/match_grip → 세그먼트별 그립 후보 → _grip_candidates
  규칙2 포지션      = _melody_candidates (1프렛1손가락: finger = fret − P + 1)
  규칙3 문맥/선행   = 빔 서치 + _transition_cost(앵커 보너스·시프트 비용) — 지평 전체 누적 최소화
  규칙4 생체역학    = 후보 생성 시 마스크(교차 금지·스팬·바레 그늘·1손가락1프렛)
  규칙5 울림 유지   = planted(손가락 점유: hard=울림 중, soft=그립 유지) 충돌 검사
"""
import csv
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grips  # noqa: E402
from grips import OPEN_MIDI, PC_NAMES  # noqa: E402

EPS_SONORITY = 0.05          # 같은 소노리티로 묶는 onset 간격(초)
GRACE = 0.02                 # 이 시간 안에 끝나는 지속음은 충돌로 안 봄(전사 양자화 노이즈)
BEAM_K = 20
# ---- 비용 가중치 (v0 기본값 — ALGORITHM.md §5에 근거) ----
W_SHIFT, W_PRESS, W_LIFT = 2.0, 0.4, 0.2
W_TRAVEL, W_STRETCH, W_BARRE = 0.15, 1.5, 1.0
W_FINGER = 0.08              # 손가락 강도 서열(검지>중지>약지>소지) — 제안 규칙 9
GRIP_BONUS = -0.5            # 규칙 1: 사전(관례 폼) 운지 우선 — 임의 배정보다 항상 유리하게
ANCHOR_BONUS, W_LOWPOS = -0.5, 0.02
STICKY_BONUS, RECENT_T = -0.4, 1.6   # 최근 같은 (줄,프렛) = 같은 손가락 (제안 규칙 8 축소판)
SHIFT_GAP_DISCOUNT, GAP_FREE = 0.3, 0.5   # 쉼표/개방 중 시프트 할인
W_MICRO = 0.3                # |ΔP|=1 미세 조정 — 손가락 유연성 범위라 시프트보다 훨씬 쌈
W_CUT = 2.5                  # 지속음 조기 리프트(잘림) 비용 — 규칙4·5 충돌의 물리적 해소
MAX_FRET = 22                # 현재 기타 asset에 존재하는 마지막 fret



# ---------- 입력 ----------

def load_notes(csv_path):
    notes, dropped = [], 0
    with open(csv_path) as f:
        for i, row in enumerate(csv.DictReader(f)):
            s, midi = int(row["string"]), int(float(row["pitch"]))
            if not 0 <= s < len(OPEN_MIDI):
                dropped += 1
                continue
            fret = midi - OPEN_MIDI[s]
            if not 0 <= fret <= MAX_FRET:
                dropped += 1
                continue
            notes.append(dict(idx=len(notes), s=s, fret=fret, midi=midi,
                              t_on=float(row["start"]), t_off=float(row["end"])))
    return notes, dropped


def load_chordtrack(json_path):
    """chords.json → [(t0, t1, (root_pc, qual) | None, conf)]"""
    segs = []
    for g in json.loads(Path(json_path).read_text())["segments"]:
        lab = None
        if g["label"] != "N":
            root, qual = g["label"].split(":")
            lab = (PC_NAMES.index(root), qual)
        segs.append((g["t0"], g["t1"], lab, g.get("conf", 2)))
    return segs


def build_sonorities(notes):
    order = sorted(range(len(notes)), key=lambda i: notes[i]["t_on"])
    groups, cur, t_last = [], [], None
    for i in order:
        t = notes[i]["t_on"]
        if t_last is None or t - t_last <= EPS_SONORITY:
            cur.append(i)
        else:
            groups.append(cur)
            cur = [i]
        t_last = t
    if cur:
        groups.append(cur)
    return groups


# ---------- 규칙 1: 세그먼트별 그립 후보 ----------

def segment_grips(notes, chord_segs, top=2):
    """각 코드 세그먼트의 발자국과 매칭되는 상위 그립을 미리 계산."""
    out = []
    for (t0, t1, lab, conf) in chord_segs:
        if lab is None:
            out.append([])
            continue
        fp = {}
        for n in notes:
            if n["t_on"] < t1 and n["t_off"] > t0:
                fp.setdefault(n["s"], set()).add(n["fret"])
        scored = []
        for g in grips.grips_for(*lab):
            cov, extras, ok = grips.match_grip(g, fp)
            if not ok or cov <= 0:
                continue
            frets = [f for f, fg in g["grip"].values() if f > 0]
            openness = sum(1 for f, _ in g["grip"].values() if f == 0)
            scored.append((cov, openness, -(min(frets) if frets else 0),
                           -(1 if g["barre"] else 0), g))
        scored.sort(key=lambda x: x[:4], reverse=True)
        out.append([g for *_, g in scored[:top]])
    return out


def _grip_candidates(son, notes, seg_grips_here, seg_end):
    """소노리티의 프렛 노트에 그립 손가락을 스탬프. 초과음은 남는 손가락."""
    cands = []
    for g in seg_grips_here:
        assign, extras, ok = {}, [], True
        barre = g["barre"]
        for i in son:
            n = notes[i]
            if n["fret"] == 0:
                if barre and barre[1] <= n["s"] <= barre[2]:
                    ok = False                       # 바레 그늘의 개방현 (규칙 4)
                    break
                assign[i] = (0, False)
                continue
            gs = g["grip"].get(n["s"])
            if gs is not None and gs[0] == n["fret"]:
                assign[i] = (gs[1], bool(barre and gs[1] == 1
                                         and barre[1] <= n["s"] <= barre[2]))
            else:
                extras.append(i)
        if not ok:
            continue
        used = {fg for fg, _ in assign.values() if fg > 0}
        anchor_f = barre[0] if barre else min(
            [f for f, fg in g["grip"].values() if f > 0], default=1)
        free = [f for f in (1, 2, 3, 4) if f not in used]
        for i in sorted(extras, key=lambda i: notes[i]["fret"]):
            n = notes[i]
            free.sort(key=lambda fg: abs(n["fret"] - (anchor_f + fg - 1)))
            picked = None
            for fg in free:
                if abs(n["fret"] - (anchor_f + fg - 1)) <= 2:
                    picked = fg
                    break
            if picked is None:
                ok = False
                break
            assign[i] = (picked, False)
            free.remove(picked)
        if not ok:
            continue
        pressed = sorted((fg, notes[i]["fret"]) for i, (fg, _b) in assign.items() if fg)
        if any(f1 > f2 for (g1, f1), (g2, f2) in zip(pressed, pressed[1:]) if g1 < g2):
            continue                                 # 초과음 배정이 교차를 만들면 탈락 (규칙 4)
        hold = {fg: (s, f) for s, (f, fg) in g["grip"].items() if f > 0}
        cands.append(dict(assign=assign, P=anchor_f, grip=g["name"],
                          barre=barre, stretch=0, hold=hold, hold_until=seg_end))
    return cands


# ---------- 규칙 2: 멜로디(포지션) 후보 ----------

def _melody_candidates(son, notes):
    fretted = sorted((i for i in son if notes[i]["fret"] > 0),
                     key=lambda i: (notes[i]["fret"], notes[i]["s"]))
    opens = {i: (0, False) for i in son if notes[i]["fret"] == 0}
    if not fretted:
        return [dict(assign=dict(opens), P=None, grip=None, barre=None,
                     stretch=0, hold=None, hold_until=None)]
    k = len(fretted)
    if k > 4:
        return []                                    # 손가락 부족 → 폴백/진단
    frets = [notes[i]["fret"] for i in fretted]
    span = max(frets) - min(frets)
    if span > 5:
        return []
    cands = []
    for combo in itertools.combinations((1, 2, 3, 4), k):   # 증가 순 = 교차 금지
        stretch = 1 if span >= 4 else 0
        feasible = True
        for a in range(k):
            for b in range(a + 1, k):
                dfret = frets[b] - frets[a]
                dfing = combo[b] - combo[a]
                if dfret > dfing + 1:                # 손가락 간격보다 2프렛 이상 벌면
                    if dfret > dfing + 2:
                        feasible = False
                    stretch = 1
        if not feasible:
            continue
        assign = dict(opens)
        for i, fg in zip(fretted, combo):
            assign[i] = (fg, False)
        P = max(1, frets[0] - (combo[0] - 1))
        cands.append(dict(assign=assign, P=P, grip=None, barre=None,
                          stretch=stretch, hold=None, hold_until=None))
    return cands


def _barre_candidates(son, notes):
    """일반 바레 솔버 — 사전에 없는 형태를 검지 바레로 해소 (설계 §6 케이스 4).

    소노리티 최저 프렛(>0)을 2줄 이상 공유하면 그 프렛을 검지 바레로 가정,
    나머지 음은 손가락 2~4에 배정. 손가락 4개를 초과하는 비관례 보이싱(5~6음
    동시)을 구제한다. W_BARRE 비용 때문에 일반 운지로 풀리는 경우엔 선택되지
    않는다 — "바레로 해결할 수 있는 것만 바레로" 가 비용 구조에서 창발.
    """
    fretted = [i for i in son if notes[i]["fret"] > 0]
    if len(fretted) < 2:
        return []
    barf = min(notes[i]["fret"] for i in fretted)
    barred = [i for i in fretted if notes[i]["fret"] == barf]
    if len(barred) < 2:
        return []
    rest = sorted((i for i in fretted if notes[i]["fret"] > barf),
                  key=lambda i: (notes[i]["fret"], notes[i]["s"]))
    if len(rest) > 3:
        return []
    s_lo = min(notes[i]["s"] for i in barred)
    s_hi = max(notes[i]["s"] for i in barred)
    assign = {}
    for i in son:
        n = notes[i]
        if n["fret"] == 0:
            if s_lo <= n["s"] <= s_hi:
                return []                            # 바레 그늘의 개방현 (규칙 4)
            assign[i] = (0, False)
    for i in barred:
        assign[i] = (1, True)
    prev_f, prev_fg = barf, 1
    for i, fg in zip(rest, (2, 3, 4)):
        f = notes[i]["fret"]
        if f - prev_f > (fg - prev_fg) + 2:          # 벌림 한계 (규칙 4)
            return []
        assign[i] = (fg, False)
        prev_f, prev_fg = f, fg
    stretch = 1 if rest and max(notes[i]["fret"] for i in rest) - barf >= 4 else 0
    return [dict(assign=assign, P=barf, grip=None,
                 barre=(barf, s_lo, s_hi), stretch=stretch,
                 hold=None, hold_until=None)]


# ---------- 규칙 3+5: 빔 서치 ----------

def _transition_cost(st, cand, gap, t_on=0.0):
    cost = 0.0
    P_new = cand["P"] if cand["P"] is not None else st["P"]
    if st["P"] is not None and P_new is not None and P_new != st["P"]:
        d = abs(P_new - st["P"])
        disc = SHIFT_GAP_DISCOUNT if gap >= GAP_FREE else 1.0
        cost += (W_MICRO if d == 1 else W_SHIFT * (0.5 + 0.5 * d)) * disc
    for i, (fg, _b) in cand["assign"].items():
        if not fg:                                   # 0=개방, None=배정 불가(진단행)
            continue
        pl = st["planted"].get(fg)
        here = (cand["_notes"][i]["s"], cand["_notes"][i]["fret"])
        if pl is not None and (pl[0], pl[1]) == here:
            cost += ANCHOR_BONUS                     # 앵커 핑거 (규칙 3)
        else:
            cost += W_PRESS + W_FINGER * (fg - 1)
            if pl is not None:
                cost += W_TRAVEL * (abs(here[1] - pl[1]) + 0.5 * abs(here[0] - pl[0]))
            r = st.get("recent", {}).get(here)       # 같은 자리 재타현 = 같은 손가락
            if r is not None and t_on - r[1] <= RECENT_T and fg == r[0]:
                cost += STICKY_BONUS
    cost += W_STRETCH * cand["stretch"]
    if cand["grip"]:
        cost += GRIP_BONUS                           # 규칙 1: 암기된 폼 그대로
    if cand["barre"] and cand["barre"] != st.get("barre"):
        cost += W_BARRE                              # 새 바레 잡기 (유지 중엔 무료)
    if P_new is not None:
        cost += W_LOWPOS * P_new
    return cost


def assign_fingers(notes, chord_segs):
    """메인 진입점. 반환: (per-note assign dict, hand track, diagnostics)."""
    sons = build_sonorities(notes)
    seg_grip_list = segment_grips(notes, chord_segs)

    def seg_at(t):
        for k, (t0, t1, lab, conf) in enumerate(chord_segs):
            if t0 <= t < t1:
                return k
        return None

    states = [dict(cost=0.0, planted={}, P=None, grip=None, barre=None,
                   recent={}, hist=[])]
    diagnostics = []
    t_prev_off = 0.0

    for si, son in enumerate(sons):
        t_on = min(notes[i]["t_on"] for i in son)
        gap = max(0.0, t_on - t_prev_off)
        t_prev_off = max(notes[i]["t_off"] for i in son)
        k = seg_at(t_on)
        seg_end = chord_segs[k][1] if k is not None else None
        cands = []
        if k is not None and seg_grip_list[k]:
            cands += _grip_candidates(son, notes, seg_grip_list[k], seg_end)
        cands += _melody_candidates(son, notes)
        cands += _barre_candidates(son, notes)       # 3층: 일반 바레 솔버
        forced = False
        if not cands:                                # 손가락 부족/스팬 초과 → 폴백
            fretted = sorted((i for i in son if notes[i]["fret"] > 0),
                             key=lambda i: notes[i]["fret"])
            frets = [notes[i]["fret"] for i in fretted]
            # 스팬 ≤5 최대 부분집합만 배정 — 이탈 음(옥타브 오검출 등)은 배정 불가
            best_lo, best_n = 0, 1
            for lo in range(len(frets)):
                n_in = sum(1 for f in frets[lo:] if f - frets[lo] <= 5)
                if n_in > best_n:
                    best_lo, best_n = lo, n_in
            chosen = fretted[best_lo:best_lo + min(best_n, 4)]
            assign = {i: (0, False) for i in son if notes[i]["fret"] == 0}
            for j, i in enumerate(chosen):
                assign[i] = (j + 1, False)
            for i in fretted:
                if i not in assign:
                    assign[i] = (None, False)
            cands = [dict(assign=assign, P=notes[chosen[0]]["fret"], grip=None,
                          barre=None, stretch=1, hold=None, hold_until=None)]
            diagnostics.append(dict(t=round(t_on, 3), issue="unassignable-sonority",
                                    n_fretted=len(fretted),
                                    n_unassigned=len(fretted) - len(chosen)))
            forced = True
        for c in cands:
            c["_notes"] = notes

        nxt = []
        for st in states:
            for c in cands:
                cand_f = {fg: (notes[i]["s"], notes[i]["fret"])
                          for i, (fg, _b) in c["assign"].items() if fg}
                # 규칙 4·5를 '지속음 ∪ 새 배치' 합집합에 적용. 충돌하는 지속음은
                # 조기 리프트(잘림) — 사람이 실제로 하는 해소이며 비용을 치른다.
                trunc = []
                for fg, pl in st["planted"].items():
                    s0_, f0_, until, hard, nidx = pl
                    if not hard or until <= t_on + GRACE:
                        continue
                    if fg in cand_f:
                        if cand_f[fg] == (s0_, f0_):
                            continue                          # 앵커/재타현
                        trunc.append((fg, nidx))              # 규칙5: 손가락 재사용
                        continue
                    for fgc, (_sc, frc) in cand_f.items():
                        if (fg - fgc) * (f0_ - frc) < 0 or abs(f0_ - frc) > 5:
                            trunc.append((fg, nidx))          # 규칙4: 교차/스팬
                            break
                cost = (st["cost"] + _transition_cost(st, c, gap, t_on)
                        + W_CUT * len(trunc))
                cut_fgs = {fg for fg, _ in trunc}
                reassigned = set(cand_f)
                planted = {fg: v for fg, v in st["planted"].items()
                           if v[2] > t_on and fg not in reassigned
                           and fg not in cut_fgs}
                for i, (fg, _b) in c["assign"].items():
                    if fg:
                        planted[fg] = (notes[i]["s"], notes[i]["fret"],
                                       notes[i]["t_off"], True, i)
                if c["hold"]:                        # 그립 유지(아르페지오) = soft plant
                    for fg, (s, f) in c["hold"].items():
                        if fg not in planted or not planted[fg][3]:
                            planted[fg] = (s, f, c["hold_until"], False, None)
                recent = {k: v for k, v in st.get("recent", {}).items()
                          if t_on - v[1] <= RECENT_T}
                for i, (fg, _b) in c["assign"].items():
                    if fg:
                        recent[(notes[i]["s"], notes[i]["fret"])] = (fg, notes[i]["t_off"])
                nxt.append(dict(cost=cost, planted=planted,
                                P=c["P"] if c["P"] is not None else st["P"],
                                grip=c["grip"], barre=c["barre"], recent=recent,
                                hist=st["hist"] + [(si, c, t_on, trunc)]))
        nxt.sort(key=lambda s: s["cost"])
        states = nxt[:BEAM_K]

    best = states[0]
    result = {}
    hand = []
    n_cut = 0
    for si, c, t_on, trunc in best["hist"]:
        hand.append(dict(t=round(t_on, 3), P=c["P"], grip=c["grip"],
                         barre=list(c["barre"]) if c["barre"] else None))
        for i, (fg, b) in c["assign"].items():
            result[i] = dict(finger=fg, barre=b, grip=c["grip"])
        for _fg, nidx in trunc:                      # 조기 리프트된 지속음
            if nidx is not None and nidx in result:
                result[nidx]["t_cut"] = round(t_on, 4)
                n_cut += 1
    if n_cut:
        diagnostics.append(dict(issue="sustain-truncated", count=n_cut,
                                note="규칙4·5 충돌로 조기 리프트된 음 — 전사 오류 후보"))
    return result, hand, diagnostics


# ---------- 누름(press) 타임라인 — 왼손 모터 goal ----------

PRESS_LEAD = 0.12            # 타현 전 선행 누름 리드(초) — 준비 동작
PRESS_MERGE_GAP = 1.5        # 같은 (손가락,줄,프렛) 재타현 사이 이 간격 이하면 누름 유지
FINGER_MOVE_T = 0.03         # 같은 손가락이 다른 자리로 옮기는 최소 시간
MAX_SHAVE = 0.08             # 리드 확보 위해 차단하는 앞 음을 앞당겨 끊는 한도
MIN_SOUND = 0.05             # 앞 음이 최소한 울려야 하는 시간(마지막 타현 이후)


def press_events(notes, result, lead=PRESS_LEAD, merge_gap=PRESS_MERGE_GAP,
                 allow_barre=False):
    """운지 배정 → 왼손 누름 이벤트 [(finger,s,fret,barre,t_press,t_release,strikes)].

    소리 구간(t_on~t_off)과 누름 구간을 분리한다: 기타는 프렛을 누른 채 타현해야
    소리가 나므로 누름은 타현(t_on)보다 lead만큼 앞서고, 재타현이 이어지면 떼지
    않고 유지(병합)하며, 마지막 사용 후에 손가락이 이동한다.
    선행 누름의 물리 클램프:
      - 같은 줄에서 직전 음이 아직 울리고 그 프렛이 지금보다 낮으면(개방 포함)
        미리 누르면 음이 바뀌므로 그 음이 끝난 뒤로 지연.
      - 같은 손가락이 다른 (줄,프렛)을 누르고 있으면 릴리즈+이동시간 뒤로 지연.
      - ``allow_barre=True``이고 두 이벤트가 모두 명시적 검지 바레일 때만 같은
        프렛의 여러 줄을 병렬로 누를 수 있다. 기본 S0에서는 같은 프렛이어도
        다른 줄로 갔다면 이동으로 간주해 과거 이벤트를 다시 병합하지 않는다.
    """
    def eff_end(n):
        a = result.get(n["idx"], {})
        return min(n["t_off"], a.get("t_cut", n["t_off"]))

    by_string = {}
    for n in sorted(notes, key=lambda n: n["t_on"]):
        by_string.setdefault(n["s"], []).append(n)

    events = []
    last_at = {}                              # (fg, s, f) -> 진행 중 이벤트 (바레 병렬 지원)
    last_by_finger = {}                       # fg -> 가장 최근 이벤트
    last_on_string = {}                       # s -> 그 줄의 가장 최근 누름 이벤트
    for n in sorted(notes, key=lambda n: n["t_on"]):
        a = result.get(n["idx"])
        if not a or not a.get("finger") or n["fret"] == 0:
            continue
        fg, s, f = a["finger"], n["s"], n["fret"]
        requested_barre = bool(a.get("barre"))
        le = last_at.get((fg, s, f))
        lb = last_by_finger.get(fg)
        parallel_barre = bool(
            allow_barre and fg == 1 and requested_barre and lb is not None
            and bool(lb.get("barre")) and lb["fret"] == f)
        moved_away = (le is not None and lb is not None and lb is not le
                      and not parallel_barre
                      and lb["t_press"] >= le["t_press"])
        if le and n["t_on"] - le["t_release"] <= merge_gap and not moved_away \
                and not any(m["fret"] < f and le["t_release"] < m["t_on"] < n["t_on"]
                            for m in by_string[s]):
            # 유지(병합) — 단, 그 사이 ①손가락이 딴 프렛으로 이동했거나 ②같은 줄에서
            # 더 낮은 프렛/개방 음이 나와야 하면 누르고 있을 수 없으므로 병합 금지
            le["t_release"] = max(le["t_release"], eff_end(n))
            le["strikes"].append(round(n["t_on"], 4))
            last_by_finger[fg] = le
            last_on_string[s] = le
            continue
        tp = n["t_on"] - lead
        prev = None                            # 같은 줄 직전 음
        for m in by_string[s]:
            if m["t_on"] >= n["t_on"]:
                break
            prev = m
        if prev is not None and prev["fret"] < f:
            # 낮은 프렛/개방이 아직 울림 → 원칙은 지연이지만, 리드 확보를 위해
            # 앞 음을 최대 MAX_SHAVE만큼 일찍 끊는다(사람의 트레이드오프).
            pe = last_on_string.get(s)
            limit = min(eff_end(prev), pe["t_release"]) if pe else eff_end(prev)
            if limit > tp:
                shaved = max(tp, limit - MAX_SHAVE, prev["t_on"] + MIN_SOUND)
                if pe is not None and prev["fret"] > 0:
                    pe["t_release"] = min(pe["t_release"], round(shaved, 4))
                tp = shaved + 0.01             # (개방현이면 소리만 새 누름에 잘림)
        if lb and not parallel_barre:
            need = lb["t_release"] + FINGER_MOVE_T
            if need > tp:                      # 손가락 점유 — 앞 이벤트도 조기 릴리즈
                shaved = max(tp - FINGER_MOVE_T, lb["t_release"] - MAX_SHAVE,
                             lb["strikes"][-1] + MIN_SOUND)
                lb["t_release"] = min(lb["t_release"], round(shaved, 4))
                tp = max(tp, lb["t_release"] + FINGER_MOVE_T)
        tp = max(0.0, min(tp, n["t_on"]))
        ev = dict(finger=fg, string=s, fret=f, barre=requested_barre,
                  t_press=round(tp, 4), t_release=eff_end(n),
                  strikes=[round(n["t_on"], 4)], grip=a.get("grip"))
        events.append(ev)
        last_at[(fg, s, f)] = ev
        last_by_finger[fg] = ev
        last_on_string[s] = ev
    for ev in events:
        ev["t_release"] = round(ev["t_release"], 4)
    return sorted(events, key=lambda e: e["t_press"])


# ---------- 검증기 (규칙 4·5 사후 전수 검사) ----------

def validate(notes, result):
    """동시 활성 배정에 대해 교차·스팬·중복 손가락 검사. 위반 목록 반환."""
    violations = []
    events = sorted(notes, key=lambda n: n["t_on"])

    def off(m):
        a = result.get(m["idx"], {})
        return min(m["t_off"], a.get("t_cut", m["t_off"]))

    for n in events:
        t = n["t_on"]
        active = [(m, result[m["idx"]]) for m in notes
                  if m["t_on"] <= t and off(m) > t + GRACE and m["idx"] in result
                  and result[m["idx"]]["finger"]]
        seen = {}
        for m, a in active:
            fg = a["finger"]
            if fg in seen and seen[fg] != m["fret"]:
                violations.append(dict(t=round(t, 3), issue="finger-two-frets",
                                       finger=fg))
            seen.setdefault(fg, m["fret"])
        pressed = sorted((a["finger"], m["fret"]) for m, a in active)
        for (f1, fr1), (f2, fr2) in zip(pressed, pressed[1:]):
            if f1 < f2 and fr1 > fr2:
                violations.append(dict(t=round(t, 3), issue="finger-crossing"))
        frets = [m["fret"] for m, _ in active]
        if frets and max(frets) - min(frets) > 5:
            violations.append(dict(t=round(t, 3), issue="span>5"))
    return violations
