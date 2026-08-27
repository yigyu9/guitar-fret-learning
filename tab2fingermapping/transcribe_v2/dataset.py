"""Onset+Frame 기타 탭 데이터셋 — sigmoid 멀티핫 (6현×21fret), 현 정규화, pitch-roll.

research_synthesis §4 반영:
 - 클래스: 6현 × 21fret(0~20), **독립 sigmoid**(무음=all-off). softmax 아님 —
   O&F onset 헤드·억제손실과 호환. FretNet/TabCNN 방식.
 - onset 타깃: Kong 삼각 soft-label g(n)=max(0,1-|n|/J), J=5(±5프레임≈58ms). BCE.
 - **현 관례 정규화**: GuitarTechs는 현 인덱스 반전(측정 51%→98% 유효). IDMT/GuitarSet 정방향.
 - pitch-shift(capo): dataset이 k∈U{-3..+6} 샘플→라벨 fret +k, k를 반환(feature 창-롤용).
   상향 편향(저음현=피치 바닥). audio 재합성 아니라 CQT 창 이동이라 정확·무비용.
GuitarSet player 분할 지원(player = unique_id의 '_0X_').
반환: waveform, frame(T,6,21) float, onset(T,6,21) float, pitch_shift k, length.
"""
import os
import random

import numpy as np
import pandas as pd
import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import Dataset

import torchaudio

SR, HOP = 22050, 256
OPEN_MIDI = [40, 45, 50, 55, 59, 64]
MAX_FRET = 20
N_FRET = MAX_FRET + 1                 # 21 (fret 0..20), sigmoid 멀티핫(무음=all-off)
REVERSED_SOURCES = {"GuitarTechs"}
ONSET_J = 5


def load_audio(path, sr=SR, min_length=33000):
    try:
        wav, sr0 = torchaudio.load(path)
    except Exception:
        return None
    if sr0 != sr:
        wav = torchaudio.transforms.Resample(sr0, sr)(wav)
    if wav.shape[0] > 1:
        wav = wav.mean(0, keepdim=True)
    wav = wav.squeeze(0)
    if wav.shape[-1] < min_length:
        wav = torch.nn.functional.pad(wav, (0, min_length - wav.shape[-1]))
    return wav


def player_of(uid):
    """GuitarSet unique_id → player 0..5 ('audio_mono-mic_04_...' → 4). 아니면 None."""
    import re
    m = re.search(r"_0(\d)_", str(uid))
    return int(m.group(1)) if m else None


class GuitarOFDataset(Dataset):
    def __init__(self, annotation_files, audio_root, crop_size=517,
                 pitch_shift_range=None, spec_augment=False,
                 source_filter=None, players=None, cache_audio=True, sr=SR, hop=HOP):
        self.audio_root = audio_root
        self.crop_size = crop_size
        self.pitch_shift_range = pitch_shift_range     # (lo, hi) 또는 None
        self.spec_augment = spec_augment
        self.sr, self.hop = sr, hop
        self.fps = sr / hop
        self.items = self._load(annotation_files, source_filter, players)
        # 오디오 인메모리 캐싱 — oversample 시 16× 재로드 방지(GuitarSet 300트랙 ≈ 0.9GB)
        self._cache = {}
        if cache_audio:
            for path, _ in self.items:
                if path not in self._cache:
                    self._cache[path] = load_audio(path, sr)

    def _load(self, files, source_filter, players):
        dfs = [pd.read_csv(f) for f in files if os.path.exists(f)]
        notes = pd.concat(dfs, ignore_index=True)
        if source_filter:
            notes = notes[notes["source"].isin(source_filter)]
        items = []
        for uid, g in notes.groupby("unique_id"):
            if players is not None:
                p = player_of(uid)
                if p is None or p not in players:
                    continue
            r = g.iloc[0]
            path = os.path.join(self.audio_root, str(r["directory_name"]),
                                str(r["audio_name"]) + ".wav")
            if not os.path.exists(path):
                continue
            # 노트를 numpy 배열로 미리 추출(현 정규화 포함) — __getitem__에서 pandas 회피
            # (iterrows가 워커에서 numpy/pandas 버그 유발 + 느림). 열: [string, pitch, t0, t1]
            s = g["string"].to_numpy()
            rev = g["source"].isin(REVERSED_SOURCES).to_numpy()
            s_norm = np.where(rev, 5 - s, s)
            arr = np.stack([s_norm, g["pitch"].to_numpy(),
                            g["start"].to_numpy(), g["end"].to_numpy()], axis=1).astype(np.float64)
            arr = arr[(arr[:, 0] >= 0) & (arr[:, 0] < 6)]
            items.append((path, arr))
        print(f"[dataset] {len(items)} tracks "
              f"(filter={source_filter}, players={players})")
        return items

    def _events(self, note_arr, k=0):
        """정규화 (string, fret, start, end). fret+k 적용, 무효 드롭. note_arr=[s,pitch,t0,t1]."""
        ev = []
        for row in note_arr:
            s = int(row[0])
            fret = int(row[1]) - OPEN_MIDI[s] + k
            if 0 <= fret <= MAX_FRET:
                ev.append((s, fret, float(row[2]), float(row[3])))
        return ev

    def _targets(self, events, total_frames):
        frame = torch.zeros((total_frames, 6, N_FRET))
        onset = torch.zeros((total_frames, 6, N_FRET))
        for (s, fret, t0, t1) in events:
            f0, f1 = int(t0 * self.fps), int(t1 * self.fps)
            a, b = max(0, f0), min(total_frames, f1)
            if a < b:
                frame[a:b, s, fret] = 1.0
            if 0 <= f0 < total_frames:
                for d in range(-ONSET_J + 1, ONSET_J):
                    fi = f0 + d
                    if 0 <= fi < total_frames:
                        v = max(0.0, 1.0 - abs(d) / ONSET_J)
                        onset[fi, s, fret] = max(float(onset[fi, s, fret]), v)
        return frame, onset

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        try:
            return self._get(idx)
        except Exception:                      # 무인 학습: 드문 글리치로 죽지 않게(collate가 None 필터)
            return None

    def _get(self, idx):
        path, note_df = self.items[idx]
        wav = self._cache.get(path) if self._cache else None
        if wav is None:
            wav = load_audio(path, self.sr)
        if wav is None:
            return None
        k = 0
        if self.pitch_shift_range:
            k = random.randint(*self.pitch_shift_range)
        total_frames = int(wav.shape[0] / self.hop)
        frame, onset = self._targets(self._events(note_df, k), total_frames)

        cs = self.crop_size
        if cs and total_frames > cs:
            f0 = random.randint(0, total_frames - cs)
            wav = wav[f0 * self.hop:(f0 + cs) * self.hop]
            frame, onset, n = frame[f0:f0 + cs], onset[f0:f0 + cs], cs
        elif cs:
            n = total_frames
            wav = torch.nn.functional.pad(wav, (0, max(0, cs * self.hop - wav.shape[0])))
            frame = torch.cat([frame, torch.zeros(cs - frame.shape[0], 6, N_FRET)])
            onset = torch.cat([onset, torch.zeros(cs - onset.shape[0], 6, N_FRET)])
        else:
            n = total_frames
        return wav, frame, onset, k, n


def of_collate(batch):
    batch = [b for b in batch if b is not None and b[4] > 0]
    if not batch:
        return None
    wav = pad_sequence([b[0] for b in batch], batch_first=True)
    frame = pad_sequence([b[1] for b in batch], batch_first=True)
    onset = pad_sequence([b[2] for b in batch], batch_first=True)
    ks = torch.tensor([b[3] for b in batch], dtype=torch.long)
    lengths = torch.tensor([b[4] for b in batch])
    return wav, frame, onset, ks, lengths
