"""노트 형성 디코드 + mir_eval — high frame-F1을 note-F1로 바꾸는 핵심.

research_synthesis §3 (리스크7: 단위테스트 필수):
 각 (현 s, fret f) 셀에 대해
 1. onset 발화 = onset_prob(s,f,t)가 t축 지역최대 AND > θ_on.  ← 재타현 분리의 정체
 2. 서브프레임 onset 시각 = 삼각 피크 포물선 보간(t-1,t,t+1).
 3. 노트 시작 = onset 발화 시점, 지속 = frame_prob > θ_fr, 종료 = frame 하락 또는 새 onset.
 4. 현별 단음: 한 프레임에 2fret 활성 시 확률 높은 것. 최소 길이 2프레임.
 frame-only(R0)는 threshold+run-length 폴백(v1 방식).
mir_eval: onset ±50ms, offset 무시. string-agnostic=피치만, string-dependent=현+피치.
"""
import numpy as np

OPEN_MIDI = [40, 45, 50, 55, 59, 64]


def _parabolic(a, b, c):
    d = a - 2 * b + c
    return 0.0 if abs(d) < 1e-9 else 0.5 * (a - c) / d


def decode_notes(frame_prob, onset_prob, fps, theta_on=0.4, theta_fr=0.5,
                 use_onset=True, min_frames=2):
    """frame_prob/onset_prob: (T,6,F) numpy. → 노트 [(string, fret, onset_s, offset_s)]."""
    T, S, Fr = frame_prob.shape
    notes = []
    if use_onset and onset_prob is not None:
        for s in range(S):
            for f in range(Fr):
                on = onset_prob[:, s, f]
                fr = frame_prob[:, s, f]
                t = 1
                while t < T - 1:
                    if on[t] > theta_on and on[t] > on[t - 1] and on[t] >= on[t + 1]:
                        sub = _parabolic(on[t - 1], on[t], on[t + 1])
                        onset_s = (t + sub) / fps
                        e = t + 1
                        while e < T and fr[e] > theta_fr and not (
                                e < T - 1 and on[e] > theta_on
                                and on[e] > on[e - 1] and on[e] >= on[e + 1]):
                            e += 1
                        if e - t >= min_frames:
                            notes.append([s, f, onset_s, e / fps])
                        t = e
                    else:
                        t += 1
    else:                                   # frame-only 폴백 (run-length)
        for s in range(S):
            for f in range(Fr):
                fr = frame_prob[:, s, f]
                active = fr > theta_fr
                t = 0
                while t < T:
                    if active[t]:
                        st = t
                        while t < T and active[t]:
                            t += 1
                        if t - st >= min_frames:
                            notes.append([s, f, st / fps, t / fps])
                    else:
                        t += 1
    return _mono_per_string(notes, frame_prob, fps)


def _mono_per_string(notes, frame_prob, fps):
    """현별 시간 겹침 해소 — 겹치면 평균 frame 확률 높은 노트 유지."""
    def score(x):
        a = max(0, int(x[2] * fps))
        b = min(frame_prob.shape[0], max(a + 1, int(x[3] * fps)))
        seg = frame_prob[a:b, int(x[0]), int(x[1])]
        return float(seg.mean()) if seg.size else 0.0

    by_s = {}
    for n in notes:
        by_s.setdefault(n[0], []).append(n)
    out = []
    for s, ns in by_s.items():
        ns.sort(key=lambda n: n[2])
        kept = []
        for n in ns:
            conflict = None
            for k in kept:
                if not (n[3] <= k[2] or n[2] >= k[3]):   # 시간 겹침
                    conflict = k
                    break
            if conflict is None:
                kept.append(n)
            elif score(n) > score(conflict):
                kept.remove(conflict)
                kept.append(n)
        out.extend(kept)
    return out


def notes_to_arrays(notes, string_dependent=False):
    """노트 → (intervals(N,2), pitches(N,)) for mir_eval. string_dep: 현별 구분 인코딩."""
    if not notes:
        return np.zeros((0, 2)), np.zeros(0)
    iv, pit = [], []
    for (s, f, on, off) in notes:
        iv.append([on, max(off, on + 1e-3)])
        midi = OPEN_MIDI[s] + f
        pit.append(midi + (s + 1) * 128 if string_dependent else midi)
    return np.array(iv), np.array([440.0 * 2 ** ((p - 69) / 12) for p in pit])


def note_onset_f1(ref_notes, est_notes, string_dependent=False, tol=0.05):
    import mir_eval
    ri, rp = notes_to_arrays(ref_notes, string_dependent)
    ei, ep = notes_to_arrays(est_notes, string_dependent)
    if len(ri) == 0 or len(ei) == 0:
        return dict(precision=0.0, recall=0.0, f1=0.0, n_ref=len(ri), n_est=len(ei))
    p, r, f, _ = mir_eval.transcription.precision_recall_f1_overlap(
        ri, rp, ei, ep, onset_tolerance=tol, offset_ratio=None,
        pitch_tolerance=50.0)
    return dict(precision=float(p), recall=float(r), f1=float(f),
                n_ref=len(ri), n_est=len(ei))


def frame_f1(frame_prob, frame_target, theta=0.5, lengths=None):
    """멀티핫 frame micro-F1 (활성 셀 기준). frame_prob/target (B,T,6,F)."""
    pred = frame_prob > theta
    tgt = frame_target > 0.5
    if lengths is not None:
        B, T = frame_prob.shape[:2]
        m = (np.arange(T)[None, :] < np.asarray(lengths)[:, None])[:, :, None, None]
        pred, tgt = pred & m, tgt & m
    tp = (pred & tgt).sum()
    fp = (pred & ~tgt).sum()
    fn = (~pred & tgt).sum()
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return dict(precision=float(p), recall=float(r),
                f1=float(2 * p * r / (p + r)) if p + r else 0.0)
