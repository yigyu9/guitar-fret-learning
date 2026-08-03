"""코드 트랙 코어 — 탭→규칙(1차 증인) + 시간 필터(①) + ACE 융합 게이팅(②).

finger mapping(docs/finger-mapping-design.md §A)의 코드 트랙 생산자.
근거: 07-15 ACE 평가(결론은 PROJECT_CONTEXT §2, 원 리포트는 07-16 유실) — 고립/희소 텍스처에서 ACE가
무너지므로(top-1 0.65) 1차 증인은 탭→규칙(match_pcset, moum 0.937 실측),
ACE는 2차(경계 힌트·모호성 해소·탭 N 구간 구제).

라벨 = chords.py의 37클래스 인덱스 (0=N, 이후 12루트×{maj,min,5}). (구 conformer_v2/chords.py 추출)
그리드 = v1 프레임 (22050/256 ≈ 86.13fps).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))   # chordtrack 디렉토리
import chords  # noqa: E402  (37클래스 어휘 — 구 conformer_v2/chords.py에서 추출, 이제 자립)

MIN_MIDI = 40
FPS = 22050 / 256                       # 86.1328125


# ---------- 1차 증인: 탭 프레임 → 규칙 디코딩 ----------

def frames_to_chord1(preds: np.ndarray) -> np.ndarray:
    """v1 프레임 예측 (T,6) 클래스 인덱스 → (T,) 37클래스 라벨.

    프레임에 서로 다른 피치클래스가 2개 미만이면 N (match_pcset 규칙).
    """
    T = preds.shape[0]
    out = np.zeros(T, dtype=np.int64)
    for t in range(T):
        midis = [int(c) + MIN_MIDI - 1 for c in preds[t] if c > 0]
        if not midis:
            continue
        pcs = {m % 12 for m in midis}
        if len(pcs) < 2:
            continue
        out[t] = chords.match_pcset(pcs, bass_pc=min(midis) % 12)
    return out


# ---------- ① 시간 필터 (탭 정보의 재배열 — 새 정보 없음) ----------

def _rle(labels):
    """런렝스 세그먼트 [(start, end_exclusive, label)]."""
    segs, s = [], 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[s]:
            segs.append((s, i, int(labels[s])))
            s = i
    return segs


def mode_smooth(labels: np.ndarray, k: int = 9) -> np.ndarray:
    """슬라이딩 최빈값 필터 (범주형이라 median 대신 mode). k프레임 ≈ k*11.6ms."""
    if k <= 1:
        return labels.copy()
    pad = k // 2
    padded = np.pad(labels, (pad, pad), mode="edge")
    out = np.empty_like(labels)
    for i in range(len(labels)):
        out[i] = np.bincount(padded[i:i + k]).argmax()
    return out


def bridge_gaps(labels: np.ndarray, max_gap_s: float = 0.35, fps: float = FPS):
    """같은 코드 사이의 짧은 N 틈(스트럼 사이 감쇠·재타현)을 그 코드로 메움."""
    segs = _rle(labels)
    out = labels.copy()
    for j in range(1, len(segs) - 1):
        s, e, lab = segs[j]
        if (lab == chords.N_LABEL and (e - s) / fps <= max_gap_s
                and segs[j - 1][2] == segs[j + 1][2] != chords.N_LABEL):
            out[s:e] = segs[j - 1][2]
    return out


def merge_min_dur(labels: np.ndarray, min_dur_s: float = 0.25, fps: float = FPS):
    """min_dur 미만 세그먼트를 이전 라벨로 흡수(맨 앞 세그먼트는 다음 라벨로)."""
    segs = _rle(labels)
    out = labels.copy()
    for j, (s, e, _lab) in enumerate(segs):
        if (e - s) / fps < min_dur_s:
            if j > 0:
                out[s:e] = out[s - 1]
            elif len(segs) > 1:
                out[s:e] = segs[j + 1][2]
    return out


def smooth_chain(labels, k=9, gap_s=0.35, min_dur_s=0.25):
    """mode → 틈 메움 → 최소지속 병합. 파라미터는 v2 INFER 관행에서 유도한 기본값."""
    return merge_min_dur(bridge_gaps(mode_smooth(labels, k), gap_s), min_dur_s)


# ---------- ACE 라벨 처리 ----------

def harte_to_idx(label: str) -> int:
    """Harte 라벨 → 37클래스 인덱스. v2 축약 원칙(3도가 장/단, {r,5}만이면 '5')."""
    import mir_eval
    if label in ("N", "X"):
        return chords.N_LABEL
    try:
        root, bitmap, _bass = mir_eval.chord.encode(label)
    except Exception:
        return chords.N_LABEL
    if root < 0:
        return chords.N_LABEL
    maj3, min3, p5 = bool(bitmap[4]), bool(bitmap[3]), bool(bitmap[7])
    if maj3 and not min3:
        return chords.label_index(int(root), "maj")
    if min3 and not maj3:
        return chords.label_index(int(root), "min")
    if maj3 and min3:
        return chords.label_index(int(root), "maj" if p5 else "min")
    if {i for i, b in enumerate(bitmap) if b} == {0, 7}:
        return chords.label_index(int(root), "5")
    return chords.N_LABEL


def lab_to_segs(intervals: np.ndarray, labels, fps: float = FPS):
    """(초 단위 구간, Harte 라벨) → 프레임 세그먼트 [(f0, f1, idx37)]."""
    return [(int(round(s * fps)), int(round(e * fps)), harte_to_idx(l))
            for (s, e), l in zip(intervals, labels)]


def rasterize(segs, T: int) -> np.ndarray:
    out = np.zeros(T, dtype=np.int64)
    for s, e, lab in segs:
        out[max(0, s):min(T, e)] = lab
    return out


# ---------- ② ACE 융합 게이팅 (새 정보 추가) ----------

def chord_pcset(idx: int) -> set:
    if idx == chords.N_LABEL:
        return set()
    root, q = (idx - 1) // 3, chords.QUALITIES[(idx - 1) % 3]
    third = {"maj": 4, "min": 3, "5": None}[q]
    pcs = {root, (root + 7) % 12}
    if third is not None:
        pcs.add((root + third) % 12)
    return pcs


def fuse(chord1s: np.ndarray, ace_segs, preds: np.ndarray):
    """chord1(스무딩 후) 위에 ACE를 게이팅.

    규칙(07-15 합의 표):
      - 탭 non-N: 탭 우선 유지. ACE 일치=고신뢰 / 불일치=저신뢰 플래그만.
      - 탭 N & ACE 코드 주장: ACE 세그먼트의 탭 시간-합집합 pcset이 그 코드
        구성음의 부분집합(≥2 pc)일 때만 구제 채택 — 아르페지오/감쇠 케이스.
    반환: (fused, conf, stats). conf: 0=N, 1=저신뢰, 2=단독증인, 3=합의.
    """
    T = len(chord1s)
    fused = chord1s.copy()
    conf = np.where(chord1s > 0, 2, 0).astype(np.int64)
    agree = disagree = rescued = 0
    for s, e, lab in ace_segs:
        if lab == chords.N_LABEL:
            continue
        s, e = max(0, s), min(T, e)
        if e <= s:
            continue
        c1 = chord1s[s:e]
        a_mask, d_mask = (c1 == lab), (c1 != lab) & (c1 > 0)
        conf[s:e][a_mask] = 3
        conf[s:e][d_mask] = 1
        agree += int(a_mask.sum())
        disagree += int(d_mask.sum())
        n_mask = c1 == chords.N_LABEL
        if n_mask.any():
            midis = {int(c) + MIN_MIDI - 1
                     for t in range(s, e) for c in preds[t] if c > 0}
            pcs = {m % 12 for m in midis}
            if len(pcs) >= 2 and pcs <= chord_pcset(lab):
                idx = np.arange(s, e)[n_mask]
                fused[idx] = lab
                conf[idx] = 2
                rescued += int(n_mask.sum())
    stats = dict(frames=T, agree=agree, disagree=disagree, rescued=rescued,
                 changed_ratio=rescued / T if T else 0.0)
    return fused, conf, stats
