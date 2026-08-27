"""tab2fingermapping 통합 파이프라인 — 오디오 한 파일로 Stage1 전체를 한 번에.

  audio ─┬→ conformer(v1) ─→ <stem>.notes.csv   (string,start,end,pitch)
         │                └→ (--bpm 시) <stem>.notes.json  (tab2body goal 입력)
         ├→ ACE ──────────→ <stem>.lab           (2차 증인, Harte 라벨)
         ├→ chordtrack ───→ <stem>.chords.json   (탭→규칙 1차 + ACE 융합, conf 채널)
         └→ fingermapping → <stem>.fingering.json (왼손 운지: 손가락·포지션·바레)

v1 추론은 1회만 수행해 탭 CSV와 코드 트랙이 공유한다.
실행 (conda env `tab2fm` — v1·ACE 의존성 모두 보유, 셋업·검증 = SETUP.md):
  cd ~/yigyu/3/tab2fingermapping
  /home/ajou/anaconda3/envs/tab2fm/bin/python pipeline.py <audio.wav> \
      [--out-dir DIR] [--bpm 117] [--skip-ace] [--smooth 3]
"""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CONFORMER = HERE / "conformer"
ACE_ROOT = HERE / "ace"
sys.path.insert(0, str(ACE_ROOT))
sys.path.insert(0, str(HERE / "chordtrack"))

import core  # noqa: E402  (chordtrack — 내부에서 legacy 어휘 로드)

_spec = importlib.util.spec_from_file_location("tt_v1", CONFORMER / "transcribe.py")
tt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tt)

ACE_THRESHOLD, ACE_MIN_DUR, CHUNK_DUR = 0.3, 0.25, 20.0   # ace_eval 완화 세트(검증됨)
SR, HOP_ACE = 22050, 512


def run_conformer(audio: Path, out_csv: Path, device, smooth: int):
    """v1 탭 전사. 프레임 예측을 반환해 chordtrack이 재사용."""
    import torch
    model = tt.GuitarConformer().to(device)
    model.load_state_dict(torch.load(str(CONFORMER / "checkpoints/best_model.pth"),
                                     map_location=device, weights_only=True))
    model.eval()
    extractor = tt.AudioFeatureExtractor()
    extractor.cqt_layer = extractor.cqt_layer.to(device)
    waveform = extractor.load_audio(str(audio))
    if waveform is None:
        sys.exit(f"오디오 로드 실패: {audio}")
    preds = tt.predict_frames(waveform, model, extractor, device)
    if smooth and smooth > 1:
        preds = tt.median_smooth(preds, smooth)
    notes = tt.segment_notes(preds, extractor.fps)
    with open(out_csv, "w") as f:
        f.write("string,start,end,pitch\n")
        for s, t0, t1, p in notes:
            f.write(f"{s},{t0},{t1},{p}\n")
    print(f"[1/3 conformer] {len(notes)} notes, {preds.shape[0]} frames -> {out_csv}")
    return preds


def run_ace(audio: Path, out_lab: Path, device):
    """consonance-ACE 추론 → .lab (실길이 클립). 반환: 프레임 세그먼트."""
    import librosa
    from ACE.inference import load_model, predict, write_lab
    from ACE.mir_evaluation import convert_predictions_decomposed
    from ACE.preprocess.audio_processor import AudioChunkProcessor
    from ACE.preprocess.transforms import CQTransform

    model = load_model(str(ACE_ROOT / "ACE/checkpoints/conformer_decomposed_smooth.ckpt"),
                       vocab_path=str(ACE_ROOT / "ACE/chords_vocab.joblib"))
    dur = librosa.get_duration(path=str(audio))
    chunker = AudioChunkProcessor(
        audio_path=audio, target_sample_rate=SR, hop_length=HOP_ACE,
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
    if iv_all:
        iv = np.vstack(iv_all)
        keep = iv[:, 0] < dur
        iv, labs = iv[keep], [l for l, k in zip(lab_all, keep) if k]
        iv[:, 1] = np.minimum(iv[:, 1], dur)
    else:
        iv, labs = np.zeros((0, 2)), []
    write_lab(out_lab, iv, labs)
    print(f"[2/3 ACE] {len(labs)} segments -> {out_lab}")
    return core.lab_to_segs(iv, labs)


def run_chordtrack(preds, ace_segs, out_json: Path):
    """탭→규칙(1차) + 시간 필터 + (있으면) ACE 융합 → chords.json."""
    c1s = core.smooth_chain(core.frames_to_chord1(preds))
    conf = None
    labels = c1s
    src = "tab-rule+smooth"
    if ace_segs is not None:
        labels, conf, stats = core.fuse(c1s, ace_segs, preds)
        src += "+ace-fuse"
        print(f"[3/3 chordtrack] agree={stats['agree']} disagree={stats['disagree']} "
              f"rescued={stats['rescued']} / {stats['frames']} frames")
    segs = []
    for s, e, lab in core._rle(labels):
        seg = dict(t0=round(s / core.FPS, 3), t1=round(e / core.FPS, 3),
                   label=core.chords.label_name(lab))
        if conf is not None:
            seg["conf"] = int(np.bincount(conf[s:e]).argmax())
        segs.append(seg)
    out_json.write_text(json.dumps(dict(fps=core.FPS, source=src, segments=segs),
                                   indent=1, ensure_ascii=False))
    print(f"[3/3 chordtrack] {len(segs)} segments -> {out_json}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="audio -> tab CSV + chord track (+note JSON)")
    ap.add_argument("audio")
    ap.add_argument("--out-dir", default=None, help="기본: ./<stem>_stage1/")
    ap.add_argument("--bpm", type=float, default=None,
                    help="지정 시 csv_to_notejson으로 note JSON까지 생성")
    ap.add_argument("--skip-ace", action="store_true", help="ACE 없이 탭→규칙+필터만")
    ap.add_argument("--smooth", type=int, default=0, help="탭 프레임 median 필터 폭(예: 3)")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args(argv)

    import torch
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    audio = Path(args.audio)
    out = Path(args.out_dir) if args.out_dir else Path.cwd() / f"{audio.stem}_stage1"
    out.mkdir(parents=True, exist_ok=True)
    stem = out / audio.stem

    preds = run_conformer(audio, Path(f"{stem}.notes.csv"), device, args.smooth)
    ace_segs = None if args.skip_ace else run_ace(audio, Path(f"{stem}.lab"), device)
    run_chordtrack(preds, ace_segs, Path(f"{stem}.chords.json"))

    sys.path.insert(0, str(HERE / "fingermapping"))
    import run_fingering
    fout = run_fingering.run(f"{stem}.notes.csv", f"{stem}.chords.json",
                             f"{stem}.fingering.json")
    fs = fout["stats"]
    print(f"[4/4 fingermapping] notes={fs['n_notes']} diagnostics={fs['n_diagnostics']} "
          f"violations={fs['n_violations']} -> {stem}.fingering.json")

    if args.bpm:
        subprocess.run([sys.executable, str(HERE / "csv_to_notejson.py"),
                        f"{stem}.notes.csv", "--bpm", str(args.bpm),
                        "--out", f"{stem}.notes.json"], check=True)
        print(f"[+] note JSON -> {stem}.notes.json")
    print(f"[done] bundle: {out}")


if __name__ == "__main__":
    main()
