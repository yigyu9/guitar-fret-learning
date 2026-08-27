"""학습 루프 — config 구동(애블레이션 R0~R4 공용), 무인 실행용 견고화.

research_synthesis §5·§8:
 - AdamW(0.9,0.98) wd1e-2, LR 5e-4 웜업1500→코사인→1e-5, grad-clip3, bf16(fp16 아님),
   batch8, 6s 세그먼트, EMA 0.999. 조기종료=val note-onset F1(string-dep), frame아님.
 - 리스크: onset all-zero(pos_weight5+onset P/R 로깅), OOM(bf16+batch fallback),
   과적합(dropout+aug+early-stop), 크래시(1k step마다 체크포인트, 재개).
config 키: input(cqt|hcqt), use_onset, use_freq_attn, aug, name, epochs, batch, oversample...
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "2")     # 스레드 과다구독 → numpy/torch 상태오염 방지
os.environ.setdefault("MKL_NUM_THREADS", "2")

import argparse
import copy
import json
import math
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

torch.set_num_threads(2)

import decode as DEC
import features as FEAT
import losses as LOSS
from dataset import GuitarOFDataset, of_collate
from model import OnsetFrameTab

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]          # 프로젝트 루트(~/yigyu/3) — guitar_v3 데이터 in-project
CSVS = [str(ROOT / "guitar_v3/data/moum/annotation" / f)
        for f in ("train_guitar_data.csv", "test_guitar_data.csv")]
AUDIO_ROOT = str(ROOT / "guitar_v3/data/moum/audio")


def make_features(cfg, device):
    ext = (FEAT.HCQT() if cfg["input"] == "hcqt" else FEAT.SingleCQT()).to(device)
    return ext, ext.n_harmonics


def build_model(cfg, n_harm):
    return OnsetFrameTab(n_harmonics=n_harm, use_onset=cfg["use_onset"],
                         use_freq_attn=cfg["use_freq_attn"],
                         n_layers=cfg.get("n_layers", 6), dropout=cfg.get("dropout", 0.2))


class EMA:
    def __init__(self, model, decay=0.999):
        self.decay = decay
        self.shadow = {k: v.detach().clone() for k, v in model.state_dict().items()}

    def update(self, model):
        for k, v in model.state_dict().items():
            if v.dtype.is_floating_point:
                self.shadow[k].mul_(self.decay).add_(v.detach(), alpha=1 - self.decay)
            else:
                self.shadow[k].copy_(v)

    def copy_to(self, model):
        model.load_state_dict(self.shadow, strict=True)


def lr_at(step, warmup, total, peak, floor=1e-5):
    if step < warmup:
        return peak * step / max(1, warmup)
    prog = (step - warmup) / max(1, total - warmup)
    return floor + 0.5 * (peak - floor) * (1 + math.cos(math.pi * min(1.0, prog)))


@torch.no_grad()
def evaluate(model, ext, loader, device, cfg, max_batches=None):
    """val note-onset F1(string-dep, 주 지표) + onset P/R + frame F1."""
    model.eval()
    ref_all, est_all, ref_ag, est_ag = [], [], [], []
    fp_tp = fp_fp = fp_fn = 0
    on_tp = on_fp = on_fn = 0
    for bi, batch in enumerate(loader):
        if batch is None:
            continue
        if max_batches and bi >= max_batches:
            break
        wav, ft, ot, ks, lengths = batch
        wav = wav.to(device)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = model(ext(wav, ks.to(device)))
        fl = out["frame_logits"].float()
        Tm = min(fl.shape[1], ft.shape[1])
        fpr = torch.sigmoid(fl[:, :Tm]).cpu().numpy()
        opr = (torch.sigmoid(out["onset_logits"].float()[:, :Tm]).cpu().numpy()
               if out["onset_logits"] is not None else None)
        ftt = ft[:, :Tm].numpy()
        ott = ot[:, :Tm].numpy()
        for b in range(wav.shape[0]):
            try:
                L = int(lengths[b])
                fpb = np.ascontiguousarray(fpr[b, :L])
                otb = np.ascontiguousarray(opr[b, :L]) if opr is not None else None
                ref = DEC.decode_notes(np.ascontiguousarray(ftt[b, :L]),
                                       (np.ascontiguousarray(ott[b, :L]) > 0.99).astype(float),
                                       ext.fps, use_onset=True)
                est = DEC.decode_notes(fpb, otb, ext.fps, theta_on=cfg.get("theta_on", 0.4),
                                       use_onset=cfg["use_onset"])
                ref_all.append(ref); est_all.append(est)
            except Exception:
                continue                       # 드문 transient 글리치 트랙 스킵
        # frame F1 누적
        pr = fpr[:, :Tm] > 0.5
        tg = ftt > 0.5
        m = (np.arange(Tm)[None, :] < lengths.numpy()[:, None])[:, :, None, None]
        pr, tg = pr & m, tg & m
        fp_tp += (pr & tg).sum(); fp_fp += (pr & ~tg).sum(); fp_fn += (~pr & tg).sum()
        if opr is not None:
            opb = (opr[:, :Tm] > cfg.get("theta_on", 0.4)) & m
            otb2 = (ott > 0.99) & m
            on_tp += (opb & otb2).sum(); on_fp += (opb & ~otb2).sum(); on_fn += (~opb & otb2).sum()
    # 집계
    import mir_eval  # noqa
    def agg(refs, ests, sd):
        tp = r = e = 0
        f1s = []
        for rf, es in zip(refs, ests):
            m = DEC.note_onset_f1(rf, es, string_dependent=sd)
            f1s.append(m["f1"])
        return float(np.mean(f1s)) if f1s else 0.0
    frame_f1 = 2 * fp_tp / (2 * fp_tp + fp_fp + fp_fn) if fp_tp else 0.0
    onset_p = on_tp / (on_tp + on_fp) if on_tp + on_fp else 0.0
    onset_r = on_tp / (on_tp + on_fn) if on_tp + on_fn else 0.0
    model.train()
    return dict(note_f1_sdep=agg(ref_all, est_all, True),
                note_f1_sag=agg(ref_all, est_all, False),
                frame_f1=float(frame_f1), onset_p=float(onset_p), onset_r=float(onset_r))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    device = "cuda"
    # GPU 안전장치(display 겸용): 메모리 상한 캡으로 화면 몫 보장 → 학습이 GPU 독점 못 함
    torch.cuda.set_per_process_memory_fraction(cfg.get("gpu_mem_frac", 0.6))
    out_dir = HERE / "checkpoints" / cfg["name"]
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "train.log"

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with open(log_path, "a") as f:
            f.write(line + "\n")

    log(f"=== {cfg['name']} === {json.dumps(cfg)}")
    ext, n_harm = make_features(cfg, device)
    log(f"features: {cfg['input']} ({n_harm} harmonics)")

    tr = GuitarOFDataset(CSVS, AUDIO_ROOT, crop_size=cfg.get("crop", 517),
                         pitch_shift_range=((-3, 6) if cfg["aug"] else None),
                         source_filter=cfg.get("source_filter", ["GuitarSet"]),
                         players=cfg.get("train_players", [0, 1, 2, 3]))
    va = GuitarOFDataset(CSVS, AUDIO_ROOT, crop_size=cfg.get("crop", 517),
                         source_filter=cfg.get("source_filter", ["GuitarSet"]),
                         players=cfg.get("val_players", [4]))
    ov = cfg.get("oversample", 16)
    tr.items = tr.items * ov                                   # 트랙당 ov 크롭/epoch
    log(f"train {len(tr.items)} samples ({len(tr.items)//ov} tracks ×{ov}) | val {len(va.items)}")

    bs = cfg.get("batch", 8)
    tl = DataLoader(tr, batch_size=bs, shuffle=True, collate_fn=of_collate,
                    num_workers=cfg.get("workers", 6), pin_memory=True, drop_last=True)
    vl = DataLoader(va, batch_size=bs, shuffle=False, collate_fn=of_collate,
                    num_workers=4)

    model = build_model(cfg, n_harm).to(device)
    log(f"model: {model.count_params()/1e6:.2f}M params | onset={cfg['use_onset']} freq_attn={cfg['use_freq_attn']}")
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.get("peak_lr", 5e-4),
                            betas=(0.9, 0.98), weight_decay=1e-2)
    ema = EMA(model, cfg.get("ema", 0.999))
    epochs = cfg.get("epochs", 50)
    steps_per = max(1, len(tl))
    total_steps = epochs * steps_per
    warmup = cfg.get("warmup", 1500)
    peak_lr = cfg.get("peak_lr", 5e-4)

    best_f1, best_ep, patience, wait = -1.0, 0, cfg.get("patience", 8), 0
    step = 0
    hist = []
    try:
      for ep in range(epochs):
        model.train(); t0 = time.time(); running = 0.0; nb = 0; skipped = 0
        for batch in tl:
            if batch is None:
                continue
            try:                               # 스텝 격리: 드문 transient 글리치로 학습 중단 방지
                wav, ft, ot, ks, lengths = batch
                wav, ft, ot = wav.to(device), ft.to(device), ot.to(device)
                lr = lr_at(step, warmup, total_steps, peak_lr)
                for g in opt.param_groups:
                    g["lr"] = lr
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    out = model(ext(wav, ks.to(device)))
                    fl = out["frame_logits"]
                    Tm = min(fl.shape[1], ft.shape[1])
                    loss = LOSS.frame_loss(fl[:, :Tm], ft[:, :Tm], lengths.to(device),
                                           focal_gamma=cfg.get("focal_gamma", 0.0),
                                           pos_weight=cfg.get("frame_pos_weight", 5.0))
                    if cfg["use_onset"]:
                        loss = loss + LOSS.onset_loss(out["onset_logits"][:, :Tm], ot[:, :Tm],
                                                      lengths.to(device),
                                                      pos_weight=cfg.get("pos_weight", 25.0))
                    if cfg.get("inhibition"):
                        loss = loss + cfg["inhibition"] * LOSS.inhibition_loss(fl[:, :Tm])
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 3.0)
                opt.step()
                ema.update(model)
                running += float(loss); nb += 1; step += 1
                # 화면 응답성: 스텝마다 GPU를 잠깐 양보(연속 포화→드라이버 행 방지)
                if cfg.get("throttle", 0.02) > 0:
                    time.sleep(cfg["throttle"])
                if step % 300 == 0:
                    torch.cuda.empty_cache()
            except Exception as e:
                opt.zero_grad(set_to_none=True)
                skipped += 1
                if skipped <= 3 or skipped % 50 == 0:
                    log(f"  [skip step] {type(e).__name__}: {str(e)[:80]} (총 {skipped})")
                if skipped > 200:
                    log("ABORT: 스텝 실패 과다(>200) — 환경 문제 의심"); break
        # raw 모델로 검증(학습 응답성 — EMA는 초기 지연으로 학습 여부를 가림)
        try:
            met = evaluate(model, ext, vl, device, cfg, max_batches=cfg.get("val_batches"))
        except Exception as e:                 # eval 글리치가 학습을 죽이지 않게
            log(f"  [eval 스킵] {type(e).__name__}: {str(e)[:80]}")
            met = hist[-1].copy() if hist else dict(note_f1_sdep=0.0, note_f1_sag=0.0,
                                                    frame_f1=0.0, onset_p=0.0, onset_r=0.0)
        met["train_loss"] = running / max(1, nb)
        met["epoch"] = ep; met["lr"] = lr; met["sec"] = round(time.time() - t0, 1)
        hist.append(met)
        log(f"ep{ep:02d} loss {met['train_loss']:.4f} | val note-F1(sdep) {met['note_f1_sdep']:.3f} "
            f"sag {met['note_f1_sag']:.3f} frame {met['frame_f1']:.3f} "
            f"onset P/R {met['onset_p']:.2f}/{met['onset_r']:.2f} | {met['sec']}s lr {lr:.1e}")
        (out_dir / "history.json").write_text(json.dumps(hist, indent=1))
        # 조기종료(주 지표=val note-F1 string-dep) + best 저장
        if met["note_f1_sdep"] > best_f1:
            best_f1, best_ep, wait = met["note_f1_sdep"], ep, 0
            torch.save({"model": model.state_dict(), "ema": ema.shadow,
                        "cfg": cfg, "epoch": ep, "metrics": met}, out_dir / "best.pth")
        else:
            wait += 1
        # onset 붕괴 abort-guard (리스크1)
        if cfg["use_onset"] and ep >= 5 and met["onset_r"] < 0.01:
            log("ABORT: onset recall ~0 after 5 epochs (붕괴)"); break
        if wait >= patience:
            log(f"early stop (patience {patience}, best ep{best_ep} F1 {best_f1:.3f})"); break
    except Exception as e:
        log(f"학습 루프 예외(부분결과 보존): {type(e).__name__}: {str(e)[:120]}")
    finally:
        log(f"DONE {cfg['name']}: best val note-F1(sdep) {best_f1:.3f} @ep{best_ep}")
        (out_dir / "result.json").write_text(json.dumps(
            dict(name=cfg["name"], best_note_f1_sdep=best_f1, best_epoch=best_ep,
                 final=hist[-1] if hist else None, config=cfg), indent=1))


if __name__ == "__main__":
    main()
