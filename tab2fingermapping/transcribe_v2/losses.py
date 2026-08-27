"""손실 — frame focal-BCE + onset 가중 BCE (+ 옥타브 억제, 옵션).

research_synthesis §4:
 - frame: 멀티핫 sigmoid → focal-BCE(γ=2, 무음 지배 처리, v1 계승).
 - onset: 삼각 soft-label → BCEWithLogits pos_weight=5(양성 ~0.6% sparse, all-zero 붕괴 방지).
 - 헤드 등가중(w_frame=w_onset=1, O&F 기본). 억제손실은 R7 옵션(HCQT와 상보).
마스킹: 패딩 프레임 제외(lengths).
"""
import torch
import torch.nn.functional as F

from dataset import OPEN_MIDI, N_FRET


def _length_mask(T, lengths, device):
    return (torch.arange(T, device=device)[None, :] < lengths[:, None])   # (B,T)


def frame_loss(frame_logits, frame_target, lengths=None, focal_gamma=0.0, pos_weight=5.0):
    """멀티핫 weighted-BCE(+옵션 focal). frame 양성 ~2% → pos_weight로 붕괴 방지.

    O&F는 weighted BCE(focal 아님). 초기 실험서 focal γ2 단독은 전부-0 붕괴 → pos_weight 채택.
    """
    B, T, S, Fr = frame_logits.shape
    pw = torch.tensor(pos_weight, device=frame_logits.device)
    bce = F.binary_cross_entropy_with_logits(frame_logits, frame_target,
                                             reduction="none", pos_weight=pw)
    if focal_gamma > 0:
        p = torch.sigmoid(frame_logits)
        pt = torch.where(frame_target > 0.5, p, 1 - p)
        bce = (1 - pt).clamp(min=1e-6) ** focal_gamma * bce
    if lengths is not None:
        m = _length_mask(T, lengths, frame_logits.device)[:, :, None, None]
        return (bce * m).sum() / m.expand_as(bce).sum().clamp(min=1)
    return bce.mean()


def onset_loss(onset_logits, onset_target, lengths=None, pos_weight=5.0):
    B, T, S, Fr = onset_logits.shape
    pw = torch.tensor(pos_weight, device=onset_logits.device)
    bce = F.binary_cross_entropy_with_logits(onset_logits, onset_target,
                                             reduction="none", pos_weight=pw)
    if lengths is not None:
        m = _length_mask(T, lengths, onset_logits.device)[:, :, None, None]
        return (bce * m).sum() / m.expand_as(bce).sum().clamp(min=1)
    return bce.mean()


_PITCH = None


def _pitch_table(device):
    global _PITCH
    if _PITCH is None or _PITCH.device != device:
        t = torch.zeros(6, N_FRET, dtype=torch.long)
        for s in range(6):
            for f in range(N_FRET):
                t[s, f] = OPEN_MIDI[s] + f
        _PITCH = t.to(device)
    return _PITCH


def inhibition_loss(frame_logits, lo=40, hi=88):
    """같은 절대 피치가 여러 (현,fret)에서 동시 활성되는 초과분 벌점(옥타브/중복 억제)."""
    B, T, S, Fr = frame_logits.shape
    p = torch.sigmoid(frame_logits)
    tab = _pitch_table(frame_logits.device)
    total = frame_logits.new_zeros(B, T, hi - lo + 1)
    for s in range(S):
        for f in range(Fr):
            m = int(tab[s, f])
            if lo <= m <= hi:
                total[:, :, m - lo] += p[:, :, s, f]
    return (total - 1.0).clamp(min=0.0).mean()
