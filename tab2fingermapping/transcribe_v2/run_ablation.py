"""애블레이션 러너 — R0~R4 순차 학습+평가, RESULTS.md 집계. 무인·재개·크래시 격리.

각 rung 독립: 하나가 실패해도 다음 진행. 이미 result.json 있으면 학습 건너뜀(재개).
학습 후 GuitarSet player5(홀드아웃)로 평가. 마지막에 v1 참조와 함께 표 생성.

사용: python run_ablation.py [R0_baseline R1_onset ...]   (인자 없으면 R0~R4 전부)
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = str(Path.home() / "anaconda3/envs/tab2fm/bin/python")
DEFAULT = ["R0_baseline", "R1_onset", "R2_hcqt", "R3_freqattn", "R4_aug"]


def run(cmd, logf):
    with open(logf, "a") as f:
        return subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode


def main():
    rungs = sys.argv[1:] or DEFAULT
    for name in rungs:
        ck = HERE / "checkpoints" / name
        cfg = HERE / "configs" / f"{name}.json"
        best = ck / "best.pth"
        if not (ck / "result.json").exists():
            print(f"[run] training {name} ...", flush=True)
            rc = run([PY, str(HERE / "train.py"), "--config", str(cfg)],
                     HERE / "_gen" / f"{name}_run.log")
            print(f"[run] {name} train rc={rc}", flush=True)
        else:
            print(f"[run] {name} already trained (skip)", flush=True)
        if best.exists() and not (HERE / "_gen" / f"eval_{name}_guitarset_test.json").exists():
            print(f"[run] evaluating {name} ...", flush=True)
            run([PY, str(HERE / "evaluate.py"), "--ckpt", str(best),
                 "--split", "guitarset_test"], HERE / "_gen" / f"{name}_eval.log")
    aggregate(rungs)


def aggregate(rungs):
    rows = []
    # v1 참조
    for tag, split in [("v1", "guitarset_test"), ("v1", "test113")]:
        p = HERE / "_gen" / f"eval_{tag}_{split}.json"
        if p.exists():
            d = json.loads(p.read_text())
            rows.append((f"v1 ({split})", d))
    for name in rungs:
        p = HERE / "_gen" / f"eval_{name}_guitarset_test.json"
        r = HERE / "checkpoints" / name / "result.json"
        if p.exists():
            rows.append((name, json.loads(p.read_text())))
        elif r.exists():
            rd = json.loads(r.read_text())
            rows.append((name + " (val)", dict(note_sdep=rd.get("best_note_f1_sdep", 0))))

    lines = ["# transcribe_v2 애블레이션 결과", "",
             "GuitarSet player-held-out (train 0-3 / val 4 / test 5), mir_eval note-onset F1 (±50ms, offset 무시).",
             "v1은 참조(⚠️ GuitarSet에서 player5 학습 누수 가능 — 정직한 홀드아웃은 test113).", "",
             "| 구성 | note-F1 sdep | sag | onset P | onset R | frame-tab | TDR | comp | solo |",
             "|---|---|---|---|---|---|---|---|---|"]
    def g(d, k):
        v = d.get(k)
        return f"{v:.3f}" if isinstance(v, (int, float)) else "—"
    for name, d in rows:
        lines.append(f"| {name} | {g(d,'note_sdep')} | {g(d,'note_sag')} | {g(d,'onset_p')} | "
                     f"{g(d,'onset_r')} | {g(d,'frame_tab')} | {g(d,'tdr')} | "
                     f"{g(d,'note_sdep_comp')} | {g(d,'note_sdep_solo')} |")
    lines += ["", "목표선(FretNet 등): string-agnostic >0.664, string-dependent >0.506, frame-tab >0.781, TDR >0.918."]
    (HERE / "RESULTS.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\n-> {HERE / 'RESULTS.md'}")


if __name__ == "__main__":
    main()
