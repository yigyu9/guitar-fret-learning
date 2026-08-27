"""코드 트랙 변형 4종의 moum 비교 평가 (2026-07-15).

변형: ace_only(2차 증인 단독 — 07-15 ace_eval 완화 세트와 동일 조건),
     chord1_raw(탭→규칙), chord1_smooth(+시간 필터), fused(+ACE 게이팅).
데이터·GT·지표는 ace_eval/eval_moum.py와 동일(88 코드 + 156 단음 파일).

실행:
  /home/ajou/anaconda3/envs/tab2fm/bin/python chordtrack/eval_moum.py  (환경 = ../SETUP.md)
출력: ../chordtrack/_gen/chordtrack_moum.json + stdout 표.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

import librosa
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                       # ~/yigyu/3/tab2fingermapping
ACE_ROOT = ROOT / "ace"
CONFORMER = ROOT / "conformer"
MOUM_AUDIO = Path.home() / "yigyu" / "guitar_v3" / "data" / "moum" / "audio"

sys.path.insert(0, str(ACE_ROOT))
sys.path.insert(0, str(HERE))

import core  # noqa: E402  (내부에서 legacy/conformer_v2.chords 로드)
from core import chords  # noqa: E402

from ACE.inference import load_model, predict  # noqa: E402
from ACE.mir_evaluation import convert_predictions_decomposed  # noqa: E402
from ACE.preprocess.audio_processor import AudioChunkProcessor  # noqa: E402
from ACE.preprocess.transforms import CQTransform  # noqa: E402

# v1 전사 모듈 (transcribe.py가 자체적으로 conformer 패키지 경로를 등록)
_spec = importlib.util.spec_from_file_location("tt_v1", CONFORMER / "transcribe.py")
tt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tt)

CHORD_DIRS = ["Fender_Strat_Clean_Neck_SC_Chords", "Ibanez_Power_Strat_Clean_Bridge_HU_Chords"]
MELODY_DIRS = ["Fender_Strat_Clean_Neck_SC", "Ibanez_Power_Strat_Clean_Bridge_Neck_SC"]
ACE_THRESHOLD, ACE_MIN_DUR, CHUNK_DUR = 0.3, 0.25, 20.0   # ace_eval 완화 세트
SR, HOP_ACE = 22050, 512
VARIANTS = ["ace_only", "chord1_raw", "chord1_smooth", "fused"]


def gt_from_filename(stem: str):
    parsed = chords.parse_filename_label(stem)
    take = re.search(r"(\d+)\s*$", stem)
    if parsed is None or take is None:
        return None
    root_pc, qual = parsed
    return chords.label_index((root_pc + int(take.group(1))) % 12, qual)


def ace_intervals(model, wav: Path, device):
    """ACE 추론 → (intervals, harte_labels), 실길이 클립. (ace_eval과 동일 로직)"""
    dur = librosa.get_duration(path=str(wav))
    chunker = AudioChunkProcessor(
        audio_path=wav, target_sample_rate=SR, hop_length=HOP_ACE,
        max_sequence_length=CHUNK_DUR, device=device,
        transform=CQTransform(SR, HOP_ACE), normalize=True)
    iv_all, lab_all = [], []
    for i in range(int(np.ceil(dur / CHUNK_DUR))):
        feats = chunker.process_chunk(onset=i * CHUNK_DUR)
        feats = feats.unsqueeze(0).unsqueeze(0) if feats.ndim == 2 else feats.unsqueeze(0)
        res = predict(model, feats)
        iv, labs = convert_predictions_decomposed(
            root_predictions=res["root"], bass_predictions=res["bass"],
            chord_predictions=res["chord"], segment_duration=CHUNK_DUR,
            threshold=ACE_THRESHOLD, remove_short_min_duration=ACE_MIN_DUR)
        if len(iv):
            iv_all.append(iv + i * CHUNK_DUR)
            lab_all.extend(labs)
    if not iv_all:
        return np.zeros((0, 2)), []
    iv = np.vstack(iv_all)
    keep = iv[:, 0] < dur
    iv = iv[keep]
    iv[:, 1] = np.minimum(iv[:, 1], dur)
    return iv, [l for l, k in zip(lab_all, keep) if k]


def file_metrics(labels: np.ndarray, gt_idx=None):
    T = len(labels)
    cnt = np.bincount(labels, minlength=37)
    non_n = {i: int(c) for i, c in enumerate(cnt) if i > 0 and c > 0}
    coverage = sum(non_n.values()) / T if T else 0.0
    maj = max(non_n, key=non_n.get) if non_n else 0
    m = dict(coverage=coverage, majority=chords.label_name(maj))
    if gt_idx is not None:
        m["top1"] = maj == gt_idx
        m["root_ok"] = maj > 0 and (maj - 1) // 3 == (gt_idx - 1) // 3
        m["acc_dur"] = float(cnt[gt_idx]) / T if T else 0.0
    else:
        m["fp"] = coverage
    return m


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    v1 = tt.GuitarConformer().to(device)
    v1.load_state_dict(torch.load(str(CONFORMER / "checkpoints/best_model.pth"),
                                  map_location=device))
    v1.eval()
    extractor = tt.AudioFeatureExtractor()
    extractor.cqt_layer = extractor.cqt_layer.to(device)
    ace = load_model(str(ACE_ROOT / "ACE/checkpoints/conformer_decomposed_smooth.ckpt"),
                     vocab_path=str(ACE_ROOT / "ACE/chords_vocab.joblib"))

    def variants_for(wav: Path):
        waveform = extractor.load_audio(str(wav))
        preds = tt.predict_frames(waveform, v1, extractor, device)      # (T,6)
        T = preds.shape[0]
        c1 = core.frames_to_chord1(preds)
        c1s = core.smooth_chain(c1)
        iv, harte = ace_intervals(ace, wav, device)
        segs = core.lab_to_segs(iv, harte)
        fused, _conf, fstats = core.fuse(c1s, segs, preds)
        return dict(ace_only=core.rasterize(segs, T), chord1_raw=c1,
                    chord1_smooth=c1s, fused=fused), fstats

    results = {"chord": [], "melody": []}
    for d in CHORD_DIRS:
        for wav in sorted((MOUM_AUDIO / d).glob("*.wav")):
            gt = gt_from_filename(wav.stem)
            if gt is None:
                continue
            var, fstats = variants_for(wav)
            row = dict(file=wav.name, folder=d, gt=chords.label_name(gt), fuse=fstats,
                       **{v: file_metrics(lab, gt) for v, lab in var.items()})
            results["chord"].append(row)
    for d in MELODY_DIRS:
        for wav in sorted((MOUM_AUDIO / d).glob("*.wav")):
            var, fstats = variants_for(wav)
            row = dict(file=wav.name, folder=d, fuse=fstats,
                       **{v: file_metrics(lab) for v, lab in var.items()})
            results["melody"].append(row)

    summary = {}
    for v in VARIANTS:
        ch, me = results["chord"], results["melody"]
        summary[v] = dict(
            top1=float(np.mean([r[v]["top1"] for r in ch])),
            root=float(np.mean([r[v]["root_ok"] for r in ch])),
            acc_dur=float(np.mean([r[v]["acc_dur"] for r in ch])),
            coverage=float(np.mean([r[v]["coverage"] for r in ch])),
            melody_fp=float(np.mean([r[v]["fp"] for r in me])),
            melody_files_fp=int(sum(r[v]["fp"] > 0 for r in me)))
    summary["fusion"] = dict(
        rescued_ratio_chord=float(np.mean([r["fuse"]["changed_ratio"] for r in results["chord"]])),
        rescued_ratio_melody=float(np.mean([r["fuse"]["changed_ratio"] for r in results["melody"]])),
        disagree_frames=int(sum(r["fuse"]["disagree"] for r in results["chord"] + results["melody"])))

    out_dir = HERE / "_gen"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "chordtrack_moum.json").write_text(
        json.dumps(dict(summary=summary, **results), indent=1, ensure_ascii=False))

    hdr = f"{'variant':14s} {'top1':>6s} {'root':>6s} {'accDur':>7s} {'cov':>6s} {'melFP':>7s} {'FPfiles':>7s}"
    print("\n==== moum 88 chord / 156 melody ====")
    print(hdr)
    for v in VARIANTS:
        s = summary[v]
        print(f"{v:14s} {s['top1']:6.3f} {s['root']:6.3f} {s['acc_dur']:7.3f} "
              f"{s['coverage']:6.3f} {s['melody_fp']:7.3f} {s['melody_files_fp']:7d}")
    print("fusion:", summary["fusion"])


if __name__ == "__main__":
    main()
