"""오디오 → 코드 트랙 JSON (finger mapping §A 입력 생산자).

1차 = v1 탭→규칙(match_pcset) + 시간 필터. 2차(옵션) = ACE .lab 융합 게이팅.
ACE는 별도 산출물(.lab)로 소비 — 이 모듈은 ACE 의존성이 없다.

실행 (conda env `tab2fm`(../SETUP.md) 또는 guitar_eval — torch/nnAudio만 필요):
  python chordtrack/build_track.py <audio.wav> [--ace-lab x.lab] [--out x.chords.json]
전체 파이프라인은 상위의 pipeline.py 사용 (v1 추론 1회 공유).
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                       # ~/yigyu/3/tab2fingermapping
CONFORMER = ROOT / "conformer"
sys.path.insert(0, str(HERE))
import core  # noqa: E402
from core import FPS, chords  # noqa: E402

_spec = importlib.util.spec_from_file_location("tt_v1", CONFORMER / "transcribe.py")
tt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tt)


def read_lab(path: Path):
    iv, labs = [], []
    for line in path.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            iv.append((float(parts[0]), float(parts[1])))
            labs.append(parts[2])
    return np.array(iv), labs


def segments(labels: np.ndarray, conf=None):
    out = []
    for s, e, lab in core._rle(labels):
        seg = dict(t0=round(s / FPS, 3), t1=round(e / FPS, 3),
                   label=chords.label_name(lab))
        if conf is not None:
            seg["conf"] = int(np.bincount(conf[s:e]).argmax())
        out.append(seg)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="audio -> chord track JSON")
    ap.add_argument("audio")
    ap.add_argument("--ace-lab", type=Path, default=None,
                    help="consonance-ACE .lab (있으면 융합 게이팅 수행)")
    ap.add_argument("--out", default=None, help="기본: <audio>.chords.json")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args(argv)

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    v1 = tt.GuitarConformer().to(device)
    v1.load_state_dict(torch.load(str(CONFORMER / "checkpoints/best_model.pth"),
                                  map_location=device, weights_only=True))
    v1.eval()
    extractor = tt.AudioFeatureExtractor()
    extractor.cqt_layer = extractor.cqt_layer.to(device)

    waveform = extractor.load_audio(args.audio)
    if waveform is None:
        sys.exit(f"오디오 로드 실패: {args.audio}")
    preds = tt.predict_frames(waveform, v1, extractor, device)
    c1s = core.smooth_chain(core.frames_to_chord1(preds))

    conf = None
    labels = c1s
    if args.ace_lab:
        iv, harte = read_lab(args.ace_lab)
        labels, conf, stats = core.fuse(c1s, core.lab_to_segs(iv, harte), preds)
        print(f"[fuse] agree={stats['agree']} disagree={stats['disagree']} "
              f"rescued={stats['rescued']} / {stats['frames']} frames")

    segs = segments(labels, conf)
    out = args.out or (str(Path(args.audio).with_suffix("")) + ".chords.json")
    Path(out).write_text(json.dumps(
        dict(fps=FPS, source="tab-rule+smooth" + ("+ace-fuse" if args.ace_lab else ""),
             segments=segs), indent=1, ensure_ascii=False))
    for s in segs:
        print(f"{s['t0']:8.2f} {s['t1']:8.2f}  {s['label']:8s}"
              + (f"  conf={s['conf']}" if conf is not None else ""))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
