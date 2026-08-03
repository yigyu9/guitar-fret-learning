"""Onset+Frame 기타 탭 모델 — freq-attn 프런트엔드 + 시간 Conformer + 듀얼 sigmoid 헤드.

research_synthesis §2·§3:
 - 프런트엔드: conv stem(freq 보존) → gentle freq 다운샘플(3,1 stride, note 해상도까지만)
   → **주파수축 트랜스포머**(49 semitone 토큰 self-attn: 기본음↔옥타브 배음이 직접 상호작용,
   옥타브 유령음의 최강 신호. hFT note-F1 94.8 vs conv-축약 19.7) → attention-pool로 freq 붕괴.
 - 시간 백본: Conformer 6층(dim256/4헤드/kernel15). GuitarSet ~3h라 10층 대신 6층+dropout.
 - 헤드(O&F 방향): 공유 인코더 위 onset MLP + frame MLP. frame 입력에 onset.detach() concat
   → onset이 노트 시작 게이팅(.detach() 필수 — frame gradient가 onset 검출기 오염 방지).
 - offset/velocity 헤드 없음(탭은 offset 무시).

애블레이션 플래그: use_onset(듀얼 vs frame-only), use_freq_attn(어텐션 vs conv-붕괴).
입력 채널 H는 features(HCQT=6 / SingleCQT=1)가 결정.
출력: dict(onset_logits, frame_logits) 각 (B,T,6,21). sigmoid는 손실/디코드에서.
"""
import sys
from pathlib import Path

import torch
import torch.nn as nn

_CONF = Path(__file__).resolve().parent.parent / "conformer"
sys.path.insert(0, str(_CONF))
from conformer.encoder import ConformerBlock  # noqa: E402

N_STRINGS, N_FRET = 6, 21
N_OUT = N_STRINGS * N_FRET                     # 126


class FreqFrontend(nn.Module):
    """(B,H,F=147,T) → 프레임 임베딩 (B,T,D). freq-attn 또는 conv-붕괴."""
    def __init__(self, n_harmonics, n_bins=147, d_model=256, use_freq_attn=True,
                 freq_layers=2, n_heads=4, dropout=0.2):
        super().__init__()
        self.use_freq_attn = use_freq_attn
        self.stem = nn.Sequential(
            nn.Conv2d(n_harmonics, 48, 3, padding=1), nn.BatchNorm2d(48), nn.ReLU(),
            nn.Conv2d(48, 48, 3, padding=1), nn.BatchNorm2d(48), nn.ReLU(),
            nn.Dropout(0.25))
        self.down = nn.Sequential(                        # (3,1) stride: freq 147→49(=semitone)
            nn.Conv2d(48, 96, (3, 1), stride=(3, 1)), nn.BatchNorm2d(96), nn.ReLU())
        f_tokens = n_bins // 3                             # 49
        self.f_tokens = f_tokens
        if use_freq_attn:
            self.proj = nn.Linear(96, d_model)
            enc = nn.TransformerEncoderLayer(d_model, n_heads, d_model * 2,
                                             dropout=dropout, batch_first=True,
                                             activation="gelu", norm_first=True)
            self.freq_tf = nn.TransformerEncoder(enc, freq_layers)
            self.query = nn.Parameter(torch.randn(1, 1, d_model) * 0.02)
            self.pool_attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout,
                                                   batch_first=True)
        else:                                             # conv-붕괴 베이스라인
            self.collapse = nn.Linear(96 * f_tokens, d_model)

    def forward(self, x):                                 # x (B,H,F,T)
        h = self.down(self.stem(x))                       # (B,96,49,T)
        B, C, Fq, T = h.shape
        if self.use_freq_attn:
            z = h.permute(0, 3, 2, 1).reshape(B * T, Fq, C)   # (B*T, 49, 96)
            z = self.freq_tf(self.proj(z))                    # (B*T, 49, D)
            q = self.query.expand(B * T, -1, -1)
            pooled, _ = self.pool_attn(q, z, z)               # (B*T, 1, D)
            return pooled.reshape(B, T, -1)
        z = h.permute(0, 3, 1, 2).reshape(B, T, C * Fq)
        return self.collapse(z)


class ConformerStack(nn.Module):
    def __init__(self, d_model=256, n_layers=6, n_heads=4, kernel=15, dropout=0.2):
        super().__init__()
        self.layers = nn.ModuleList([
            ConformerBlock(encoder_dim=d_model, num_attention_heads=n_heads,
                           conv_kernel_size=kernel, feed_forward_dropout_p=dropout,
                           attention_dropout_p=0.1, conv_dropout_p=dropout)
            for _ in range(n_layers)])

    def forward(self, x):
        for l in self.layers:
            x = l(x)
        return x


def _head(d_in, d_hidden, d_out, dropout=0.2, bias_prior=None):
    layers = nn.Sequential(nn.LayerNorm(d_in), nn.Linear(d_in, d_hidden), nn.ReLU(),
                           nn.Dropout(dropout), nn.Linear(d_hidden, d_out))
    if bias_prior is not None:
        # 출력 bias를 클래스 사전확률로 초기화(RetinaNet): 초기 all-zero 붕괴 방지.
        import math
        nn.init.constant_(layers[-1].bias, -math.log((1 - bias_prior) / bias_prior))
    return layers


class OnsetFrameTab(nn.Module):
    def __init__(self, n_harmonics=6, d_model=256, n_layers=6, n_heads=4, kernel=15,
                 dropout=0.2, use_onset=True, use_freq_attn=True):
        super().__init__()
        self.use_onset = use_onset
        self.frontend = FreqFrontend(n_harmonics, d_model=d_model,
                                     use_freq_attn=use_freq_attn, n_heads=n_heads,
                                     dropout=dropout)
        self.encoder = ConformerStack(d_model, n_layers, n_heads, kernel, dropout)
        if use_onset:
            self.onset_head = _head(d_model, 128, N_OUT, dropout, bias_prior=0.006)
            self.frame_head = _head(d_model + N_OUT, 128, N_OUT, dropout, bias_prior=0.02)
        else:
            self.frame_head = _head(d_model, 128, N_OUT, dropout, bias_prior=0.02)

    def forward(self, feats):                             # feats (B,H,F,T)
        z = self.encoder(self.frontend(feats))            # (B,T,D)
        B, T, _ = z.shape
        if self.use_onset:
            onset = self.onset_head(z).view(B, T, N_STRINGS, N_FRET)
            of = torch.sigmoid(onset).detach().view(B, T, -1)
            frame = self.frame_head(torch.cat([z, of], -1)).view(B, T, N_STRINGS, N_FRET)
            return dict(onset_logits=onset, frame_logits=frame)
        frame = self.frame_head(z).view(B, T, N_STRINGS, N_FRET)
        return dict(onset_logits=None, frame_logits=frame)

    def count_params(self):
        return sum(p.numel() for p in self.parameters())
