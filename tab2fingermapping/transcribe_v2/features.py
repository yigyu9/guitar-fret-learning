"""HCQT 특징 — 단일 베이스 CQT + 하모닉 빈-롤 스태킹 (basic-pitch 방식).

설계 근거(research_synthesis §1):
 - 하모닉 h ∈ {0.5,1,2,3,4,5}를 채널로 스태킹 → 배음 정렬이 채널 축에 드러나 옥타브
   유령음 완화. 0.5 서브하모닉이 옥타브 결정의 핵심 신호.
 - **6개 개별 CQT가 아니라 CQT 1개 + 정수 빈-롤**: shift_h = round(36·log2(h)).
   → 계산 1×CQT, pitch-shift 증강이 창(window) 이동으로 공짜.
 - 36 bins/oct(3/semitone), 베이스 fmin = E1(MIDI 28, 41.2Hz), 288 bins → nyquist 안전
   (최상단 필요 빈 285 → 9.8kHz < 11025). 분류 창 = MIDI 40~88 (147 bins).

pitch-shift(capo): 창 시작을 3k 빈 이동 = k 반음. 라벨 fret도 +k (dataset에서).
반환: (B, H, 147, T) — H=하모닉, 147=MIDI40~88 창.
"""
import numpy as np
import torch
import torch.nn as nn
from nnAudio.Spectrogram import CQT1992v2

BINS_PER_OCT = 36
BASE_FMIN_MIDI = 28                 # E1 = 41.2 Hz
BASE_N_BINS = 288                   # E1..(E1+8oct) → 최상단 9.8kHz < nyquist
WIN_LO_MIDI, WIN_HI_MIDI = 40, 88   # 분류 창(기타 음역)
WIN_LO_BIN = (WIN_LO_MIDI - BASE_FMIN_MIDI) * 3      # 36
WIN_N_BINS = (WIN_HI_MIDI - WIN_LO_MIDI) * 3 + 3     # 147
HARMONICS = (0.5, 1, 2, 3, 4, 5)


def _fmin_hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12.0)


class HCQT(nn.Module):
    def __init__(self, sr=22050, hop_length=256, harmonics=HARMONICS,
                 bins_per_octave=BINS_PER_OCT, base_n_bins=BASE_N_BINS,
                 base_fmin_midi=BASE_FMIN_MIDI, win_lo_bin=WIN_LO_BIN,
                 win_n_bins=WIN_N_BINS, max_pitch_shift=6):
        super().__init__()
        self.sr, self.hop_length = sr, hop_length
        self.harmonics = list(harmonics)
        self.win_lo_bin, self.win_n_bins = win_lo_bin, win_n_bins
        self.fps = sr / hop_length
        self.shifts = [int(round(bins_per_octave * np.log2(h))) for h in harmonics]
        self.base = CQT1992v2(sr=sr, hop_length=hop_length,
                              fmin=_fmin_hz(base_fmin_midi), n_bins=base_n_bins,
                              bins_per_octave=bins_per_octave,
                              output_format="Magnitude", trainable=False)
        self.base_n_bins = base_n_bins
        # 리스크6: 하모닉 롤이 창을 벗어나지 않는지 사전 검증
        max_top = win_lo_bin + win_n_bins + 3 * max_pitch_shift + max(self.shifts)
        assert max_top <= base_n_bins, f"HCQT 창 초과: {max_top} > {base_n_bins}"

    @property
    def n_harmonics(self):
        return len(self.harmonics)

    @torch.no_grad()
    def forward(self, waveform, pitch_shift=0):
        """waveform (B, samples) → (B, H, win_n_bins, T). pitch_shift: int 또는 (B,) 텐서."""
        base = torch.log1p(self.base(waveform))               # (B, F, T)
        B, F, T = base.shape
        if isinstance(pitch_shift, int):
            pitch_shift = torch.full((B,), pitch_shift, device=base.device, dtype=torch.long)
        out = base.new_zeros(B, self.n_harmonics, self.win_n_bins, T)
        for hi, sh in enumerate(self.shifts):
            for b in range(B):
                lo = self.win_lo_bin + 3 * int(pitch_shift[b]) + sh
                hi_b = lo + self.win_n_bins
                s = max(lo, 0)
                e = min(hi_b, F)
                if s < e:
                    out[b, hi, s - lo:e - lo] = base[b, s:e]
        return out


class SingleCQT(nn.Module):
    """단층 CQT (R0/R1 베이스라인 애블레이션). 반환 (B, 1, win_n_bins, T)."""
    def __init__(self, sr=22050, hop_length=256, bins_per_octave=BINS_PER_OCT,
                 base_n_bins=BASE_N_BINS, base_fmin_midi=BASE_FMIN_MIDI,
                 win_lo_bin=WIN_LO_BIN, win_n_bins=WIN_N_BINS, max_pitch_shift=6):
        super().__init__()
        self.sr, self.hop_length = sr, hop_length
        self.win_lo_bin, self.win_n_bins = win_lo_bin, win_n_bins
        self.fps = sr / hop_length
        self.base = CQT1992v2(sr=sr, hop_length=hop_length, fmin=_fmin_hz(base_fmin_midi),
                              n_bins=base_n_bins, bins_per_octave=bins_per_octave,
                              output_format="Magnitude", trainable=False)
        self.base_n_bins = base_n_bins

    @property
    def n_harmonics(self):
        return 1

    @torch.no_grad()
    def forward(self, waveform, pitch_shift=0):
        base = torch.log1p(self.base(waveform))
        B, F, T = base.shape
        if isinstance(pitch_shift, int):
            pitch_shift = torch.full((B,), pitch_shift, device=base.device, dtype=torch.long)
        out = base.new_zeros(B, 1, self.win_n_bins, T)
        for b in range(B):
            lo = self.win_lo_bin + 3 * int(pitch_shift[b])
            e = min(lo + self.win_n_bins, F)
            if lo < e:
                out[b, 0, :e - lo] = base[b, lo:e]
        return out
