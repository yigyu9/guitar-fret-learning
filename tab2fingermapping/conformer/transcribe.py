"""
transcribe — audio -> per-string note CSV (Stage 1 inference CLI).
(07-15 재구성: tabtrans/ → tab2fingermapping/conformer/. 통합 실행은 ../pipeline.py)

Ported from ~/yigyu/guitar_v3 (canonical Conformer tab-transcription project),
minimal file set: conformer/ (encoder lib), feature_extractor.py (22050 Hz mono
-> CQT hop 256, 288 bins, ~86.13 fps), checkpoints/best_model.pth (eval:
frame micro F1 0.835, note-level F1 0.596 on 113 tracks).

Changes vs the original inference.py:
  * CLI args instead of hardcoded paths,
  * chunked inference (500-frame chunks, evaluate_metrics.py pattern) instead
    of whole-track attention (O(T^2) memory on long songs),
  * optional median smoothing over frame predictions (--smooth) to reduce
    single-frame flicker before note segmentation.

Output CSV: string,start,end,pitch
  string: 0 = low-E (bass) .. 5 = high-e  (GuitarSet convention — NOTE this is
  the REVERSE of the note-JSON/tabproc convention; csv_to_notejson.py flips it)
  start/end: seconds; pitch: MIDI (40..88)

Run (needs torch/nnAudio/torchaudio — conda env `tab2fm`(../SETUP.md) 또는 guitar_eval):
  python tab2fingermapping/conformer/transcribe.py <audio.wav> --out song.csv
"""
from __future__ import annotations

import argparse
import os
import sys

import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conformer.encoder import ConformerEncoder            # noqa: E402
from feature_extractor import AudioFeatureExtractor       # noqa: E402

MIN_MIDI, MAX_MIDI = 40, 88
NUM_CLASSES = (MAX_MIDI - MIN_MIDI) + 2                   # silence + 49 pitches


class GuitarConformer(nn.Module):
    """identical architecture to guitar_v3 (checkpoint-compatible)"""

    def __init__(self, num_classes=NUM_CLASSES, input_dim=288, encoder_dim=256,
                 num_encoder_layers=10, num_attention_heads=4, conv_kernel_size=15):
        super().__init__()
        self.conformer = ConformerEncoder(
            input_dim=input_dim, encoder_dim=encoder_dim,
            num_layers=num_encoder_layers,
            num_attention_heads=num_attention_heads,
            conv_kernel_size=conv_kernel_size,
            input_dropout_p=0.0, attention_dropout_p=0.0, conv_dropout_p=0.0)
        self.classifier = nn.Linear(encoder_dim, 6 * num_classes)
        self.num_classes = num_classes

    def forward(self, inputs, input_lengths):
        enc, _ = self.conformer(inputs, input_lengths)
        logits = self.classifier(enc)
        b, t, _ = logits.shape
        return logits.view(b, t, 6, self.num_classes)


def predict_frames(waveform, model, extractor, device, chunk_frames=500):
    """chunked argmax predictions -> (T, 6) class indices"""
    import numpy as np
    hop = extractor.hop_length
    chunk_samples = chunk_frames * hop
    wav = waveform.squeeze(0)
    preds = []
    pos = 0
    with torch.no_grad():
        while pos < wav.shape[0]:
            seg = wav[pos:pos + chunk_samples]
            n_valid = -(-seg.shape[0] // hop)              # ceil frames in this chunk
            if seg.shape[0] < chunk_samples:
                seg = torch.nn.functional.pad(seg, (0, chunk_samples - seg.shape[0]))
            feat = extractor.cqt_layer(seg.unsqueeze(0).to(device))
            feat = torch.log1p(feat.squeeze(1).permute(0, 2, 1))
            length = torch.tensor([feat.shape[1]], device=device)
            logits = model(feat, length)
            p = torch.argmax(logits, dim=-1).squeeze(0).cpu().numpy()
            preds.append(p[:n_valid])
            pos += chunk_samples
    return np.concatenate(preds, axis=0)


def median_smooth(preds, k=3):
    """per-string temporal median filter (odd k) on class indices"""
    import numpy as np
    if k <= 1:
        return preds
    pad = k // 2
    padded = np.pad(preds, ((pad, pad), (0, 0)), mode="edge")
    out = np.empty_like(preds)
    for i in range(preds.shape[0]):
        out[i] = np.median(padded[i:i + k], axis=0)
    return out.astype(preds.dtype)


def segment_notes(preds, fps):
    """(T,6) class indices -> note rows (run-length merge; guitar_v3 logic)"""
    notes = []
    T = preds.shape[0]
    for s in range(6):
        cur, start, active = 0, 0, False
        for t in range(T + 1):
            c = preds[t, s] if t < T else 0
            if c > 0:
                pitch = c + MIN_MIDI - 1
                if not active:
                    cur, start, active = pitch, t, True
                elif pitch != cur:
                    notes.append((s, start / fps, t / fps, cur))
                    cur, start = pitch, t
            elif active:
                notes.append((s, start / fps, t / fps, cur))
                active = False
    notes.sort(key=lambda r: (r[1], r[0]))
    return notes


def main(argv=None):
    ap = argparse.ArgumentParser(description="audio -> guitar tab note CSV")
    ap.add_argument("audio")
    ap.add_argument("--out", default=None, help="output csv (default: <audio>.notes.csv)")
    ap.add_argument("--model", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "checkpoints", "best_model.pth"))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--chunk", type=int, default=500, help="chunk frames (training crop size)")
    ap.add_argument("--smooth", type=int, default=0, help="median filter width (0/1=off, try 3)")
    args = ap.parse_args(argv)

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    model = GuitarConformer().to(device)
    model.load_state_dict(torch.load(args.model, map_location=device))
    model.eval()
    extractor = AudioFeatureExtractor()
    extractor.cqt_layer = extractor.cqt_layer.to(device)

    waveform = extractor.load_audio(args.audio)
    if waveform is None:
        sys.exit(f"failed to load audio: {args.audio}")
    preds = predict_frames(waveform, model, extractor, device, args.chunk)
    if args.smooth and args.smooth > 1:
        preds = median_smooth(preds, args.smooth)
    notes = segment_notes(preds, extractor.fps)

    out = args.out or (os.path.splitext(args.audio)[0] + ".notes.csv")
    with open(out, "w") as f:
        f.write("string,start,end,pitch\n")
        for s, t0, t1, p in notes:
            f.write(f"{s},{t0},{t1},{p}\n")
    print(f"[transcribe] {len(notes)} notes ({preds.shape[0]} frames @ {extractor.fps:.2f}fps, "
          f"device={device.type}) -> {out}")


if __name__ == "__main__":
    main()
