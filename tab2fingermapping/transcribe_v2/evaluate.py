"""종합 평가 — GT 노트 이벤트 기준 note-onset F1 등 전 지표 + v1 재평가.

research_synthesis §6:
 지표(mir_eval, onset ±50ms, offset 무시): note-onset F1 string-DEP & string-AGNOSTIC,
 onset P/R 별도, frame multipitch F1, frame-tab F1(string-dep), TDR.
 목표선: string-agnostic >0.664, string-dependent >0.506, frame-tab >0.781, TDR >0.918.
 - v1 재평가(R0 핵심 확인): v1의 0.60이 string-dep인지 agnostic인지 확정.
 - GT는 CSV 노트 이벤트에서 직접(현 정규화 적용) — 래스터 재디코드 아님(엄정).

사용:
  evaluate.py --ckpt checkpoints/R4_aug/best.pth [--split guitarset_test|test113]
  evaluate.py --v1                                          # v1 재평가
"""
import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch

import decode as DEC
import features as FEAT
from dataset import OPEN_MIDI, REVERSED_SOURCES, load_audio, player_of
from model import OnsetFrameTab

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]          # 프로젝트 루트(~/yigyu/3) — guitar_v3 데이터 in-project
CSVS = [ROOT / "guitar_v3/data/moum/annotation" / f
        for f in ("train_guitar_data.csv", "test_guitar_data.csv")]
AUDIO_ROOT = ROOT / "guitar_v3/data/moum/audio"
CHUNK = 1000


def gt_notes(note_df):
    """CSV 노트 → [(string, fret, onset_s, offset_s)] (현 정규화)."""
    out = []
    for _, r in note_df.iterrows():
        s = int(r["string"])
        if not (0 <= s < 6):
            continue
        if str(r.get("source", "")) in REVERSED_SOURCES:
            s = 5 - s
        fret = int(r["pitch"]) - OPEN_MIDI[s]
        if 0 <= fret <= 20:
            out.append([s, fret, float(r["start"]), float(r["end"])])
    return out


def load_split(split):
    df = pd.concat([pd.read_csv(c) for c in CSVS], ignore_index=True)
    tracks = []
    for uid, g in df.groupby("unique_id"):
        r = g.iloc[0]
        if split == "guitarset_test":
            if r["source"] != "GuitarSet" or player_of(uid) != 5:
                continue
        elif split == "test113":
            # v1 테스트셋(113트랙)만
            tdf = pd.read_csv(CSVS[1])
            if uid not in set(tdf["unique_id"]):
                continue
        path = AUDIO_ROOT / str(r["directory_name"]) / (str(r["audio_name"]) + ".wav")
        if path.exists():
            style = "comp" if "comp" in uid.lower() else ("solo" if "solo" in uid.lower() else "other")
            tracks.append((uid, str(path), g, style))
    return tracks


@torch.no_grad()
def infer_v2(model, ext, wav, device, use_onset):
    """긴 트랙 청크 추론 → (frame_prob, onset_prob) 전체 (T,6,21)."""
    fr_all, on_all = [], []
    total = wav.shape[0] // ext.hop_length
    for c0 in range(0, total, CHUNK):
        seg = wav[c0 * ext.hop_length:(c0 + CHUNK) * ext.hop_length].unsqueeze(0).to(device)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = model(ext(seg))
        fr_all.append(torch.sigmoid(out["frame_logits"].float())[0].cpu().numpy())
        if use_onset and out["onset_logits"] is not None:
            on_all.append(torch.sigmoid(out["onset_logits"].float())[0].cpu().numpy())
    fr = np.concatenate(fr_all)[:total]
    on = np.concatenate(on_all)[:total] if on_all else None
    return fr, on


def frame_tab_f1(frame_prob, gt_events, fps, theta=0.5):
    """string-dependent frame F1 (현+fret 셀 단위)."""
    T = frame_prob.shape[0]
    tgt = np.zeros((T, 6, 21), dtype=bool)
    for (s, f, t0, t1) in gt_events:
        a, b = int(t0 * fps), min(T, int(t1 * fps))
        if a < b:
            tgt[a:b, s, f] = True
    pred = frame_prob > theta
    tp = (pred & tgt).sum(); fp = (pred & ~tgt).sum(); fn = (~pred & tgt).sum()
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return float(2 * p * r / (p + r)) if p + r else 0.0


def eval_tracks(decode_fn, tracks, fps):
    """decode_fn(uid,path,gdf)→(est_notes, frame_prob). 전 지표 집계."""
    agg = defaultdict(list)
    for uid, path, gdf, style in tracks:
        ref = gt_notes(gdf)
        est, frame_prob = decode_fn(uid, path, gdf)
        sdep = DEC.note_onset_f1(ref, est, string_dependent=True)
        sag = DEC.note_onset_f1(ref, est, string_dependent=False)
        row = dict(note_sdep=sdep["f1"], note_sag=sag["f1"],
                   onset_p=sag["precision"], onset_r=sag["recall"],
                   frame_tab=frame_tab_f1(frame_prob, ref, fps) if frame_prob is not None else 0.0,
                   n_ref=sdep["n_ref"], n_est=sdep["n_est"])
        # TDR = (string 맞은 노트) / (pitch 맞은 노트)
        row["tdr"] = (sdep["f1"] / sag["f1"]) if sag["f1"] > 0 else 0.0
        for k, v in row.items():
            agg[k].append(v)
        agg[f"_style_{style}"].append(sdep["f1"])
    summary = {k: float(np.mean(v)) for k, v in agg.items() if not k.startswith("_style")}
    for style in ("comp", "solo"):
        vals = agg.get(f"_style_{style}", [])
        if vals:
            summary[f"note_sdep_{style}"] = float(np.mean(vals))
    summary["n_tracks"] = len(tracks)
    return summary


def eval_v2(ckpt_path, split):
    device = "cuda"
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    cfg = ck["cfg"]
    ext = (FEAT.HCQT() if cfg["input"] == "hcqt" else FEAT.SingleCQT()).to(device)
    model = OnsetFrameTab(n_harmonics=ext.n_harmonics, use_onset=cfg["use_onset"],
                          use_freq_attn=cfg["use_freq_attn"],
                          n_layers=cfg.get("n_layers", 6)).to(device)
    model.load_state_dict(ck.get("model", ck.get("ema"))); model.eval()
    tracks = load_split(split)

    def dfn(uid, path, gdf):
        wav = load_audio(path)
        fr, on = infer_v2(model, ext, wav, device, cfg["use_onset"])
        est = DEC.decode_notes(fr, on, ext.fps, theta_on=cfg.get("theta_on", 0.4),
                               use_onset=cfg["use_onset"])
        return est, fr
    return eval_tracks(dfn, tracks, ext.fps)


def eval_v1(split):
    """v1(pitch 6×50) 재평가 — 0.60 지표 정의 확정."""
    device = "cuda"
    conf_dir = HERE.parent / "conformer"
    spec = importlib.util.spec_from_file_location("tt_v1", conf_dir / "transcribe.py")
    tt = importlib.util.module_from_spec(spec); spec.loader.exec_module(tt)
    v1 = tt.GuitarConformer().to(device)
    v1.load_state_dict(torch.load(conf_dir / "checkpoints/best_model.pth",
                                  map_location=device, weights_only=True))
    v1.eval()
    ex = tt.AudioFeatureExtractor(); ex.cqt_layer = ex.cqt_layer.to(device)
    tracks = load_split(split)
    fps = ex.fps

    def dfn(uid, path, gdf):
        wav = ex.load_audio(path)
        preds = tt.predict_frames(wav, v1, ex, device)      # (T,6) pitch-class
        # pitch-class(1..49=MIDI40..88) → fret 노트 (run-length)
        est = []
        T = preds.shape[0]
        for s in range(6):
            t = 0
            while t < T:
                c = int(preds[t, s])
                if c > 0:
                    st = t
                    while t < T and int(preds[t, s]) == c:
                        t += 1
                    midi = c + 39
                    fret = midi - OPEN_MIDI[s]
                    if 0 <= fret <= 20 and t - st >= 2:
                        est.append([s, fret, st / fps, t / fps])
                else:
                    t += 1
        return est, None
    return eval_tracks(dfn, tracks, fps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--v1", action="store_true")
    ap.add_argument("--split", default="guitarset_test", choices=["guitarset_test", "test113"])
    args = ap.parse_args()
    res = eval_v1(args.split) if args.v1 else eval_v2(args.ckpt, args.split)
    tag = "v1" if args.v1 else Path(args.ckpt).parent.name
    res["tag"] = tag; res["split"] = args.split
    print(json.dumps(res, indent=1, ensure_ascii=False))
    out = HERE / "_gen" / f"eval_{tag}_{args.split}.json"
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
