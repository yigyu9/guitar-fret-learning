# NEW MODEL DESIGN SPEC — "HCQT Onsets-&-Frames Conformer for Guitar Tablature" (v2)

Consolidated from all 5 facets. Every choice is decisive and build-ready for unattended overnight runs. Citations in `(F#: paper)` form.

---

## 0. Resolved conflicts (read first)

| Conflict | Decision | Loser & why |
|---|---|---|
| HCQT via 6 separate CQTs vs single-CQT bin-roll | **Single base CQT + integer bin-roll harmonic stacking** | 6× compute/OOM risk on 12GB (F2: basic-pitch) |
| Onset target: binary window vs Kong triangular regression | **Triangular soft target + BCE + sub-frame decode** | Binary is brittle to GuitarSet label jitter — 96.5 vs 76.5 note-F1 under 50ms jitter (F4: Riley 2024) |
| Softmax-per-string vs sigmoid-per-(string,fret) | **Independent sigmoid per (string,fret)** | Softmax is incompatible with O&F onset heads + inhibition loss (F3: Cwitkowitz 2022) |
| Keep 10-layer Conformer vs shrink | **6-layer time-Conformer + prepend 2-layer freq-axis attention** | 10 layers overfits ~3h data; freq-attention is the strongest octave-ghost signal (F3: Kim; F4: hFT) |
| Loss weights: equal vs onset-heavy | **Equal head weights (1.0/1.0); handle sparsity inside onset BCE via pos_weight=5** | Hand-tuning head weights first is the published anti-pattern (F1: Kong/Hawthorne) |
| Fuse all data vs GuitarSet-first | **GuitarSet-only for ablations/eval; IDMT+moum as optional string-agnostic pretrain** | Only GuitarSet has clean per-string labels; fusing raw injects label-mapping bugs into overnight runs |
| Offset/velocity heads | **Omit both** | Tab F1 ignores offsets; velocity is piano-only (F3; F1) |

---

## 1. Input representation — HCQT

- **Harmonics: `h ∈ {0.5, 1, 2, 3, 4, 5}` (6 channels).** — Proven minimum; 0.5 sub-harmonic is the *specific* octave-ghost fix, extra basic-pitch harmonics (6,7) cost memory for marginal gain (F2: Bittner 2017; F3: FretNet).
- **Bins/octave = 36 (3 bins/semitone).** — Matches baseline + basic-pitch + FretNet; leaves room for pitch-bend contour, collapsed later (F2; F3).
- **sr = 22050, hop = 256 → 11.6 ms/frame.** — Keep baseline front-end; fine hop beats Kong's local-max 4-frame re-strike floor (46 ms << typical 75 ms re-strikes) (F1: Kong; F2: basic-pitch).
- **Construction: ONE base CQT, then harmonic channels by integer freq-bin rolls** — `shift_bins = round(36·log2(h))` → h=0.5:−36, h=1:0, h=2:+36, h=3:+57, h=4:+72, h=5:+84. Cost ≈ 1 CQT + cheap rolls, not 6 CQTs (F2: basic-pitch HarmonicStacking).
- **Base CQT range: fmin ≈ 41.2 Hz (E1, = 0.5·E2), n_bins = 264 (7.33 oct, top ≈ 6.6 kHz).** — Guarantees h=0.5 valid for low-E and h=5 (+84 bins) valid for high notes; otherwise top-fret harmonic channels zero-pad and you lose the disambiguation you added (F2 pitfall).
- **Network input = harmonic-stack, crop to fundamental window MIDI 40–88: `6 × 147 × T`** (147 = 49 semitones × 3). — Guitar range only; don't waste channels on out-of-range bins (F3 pitfall).
- **Compression: `log1p` on magnitude.** — Keep baseline's proven front-end scaling.
- **Precompute the 264-bin base log-CQT to disk (npy/HDF5); do harmonic-stack + pitch-roll aug + crop on GPU per batch.** — Avoids recomputing CQT every step and makes pitch-shift a free roll (F5 pitfall).

**Memory:** 6×147×517 (6 s) ≈ 0.9 MB/sample (bf16); batch 8 input ≈ 7 MB. Trivial — Conformer activations dominate, comfortably inside 12 GB with bf16 + grad-checkpointing.

---

## 2. Encoder — freq-axis attention front-end + time-axis Conformer

**Keep the Conformer, but only as the TIME axis, and shrink it.** The single strongest architectural signal across facets is *attend across frequency before time* (F4: hFT ablation Note-F1 94.81 vs 19.68 for 2-D conv-subsampling; SpecTNT; PerceiverTF).

Pipeline (input `6×147×T`):
1. **Conv stem:** Conv2D 6→48 (3×3) → BN → ReLU → Conv2D 48→48 (3×3) → BN → ReLU → Dropout 0.25. Stride 1, **freq resolution preserved at 147.** — 1×1 over the 6 harmonic channels already sees the aligned harmonic template (0.5-channel breaks octave ties); 3×3 adds local context (F2: basic-pitch; F3: FretNet conv blocks).
2. **Gentle freq downsample:** Conv2D 48→96, kernel (3,1), stride (3,1) → **49 freq × 96 ch** (3 bins/semitone → 1 bin/semitone). — Removes only sub-semitone bins (not needed for fret ID); this is *not* the aggressive subsampling hFT warns against — it stops at note resolution (F2; F3: FretNet).
3. **Frequency-axis Transformer:** project 96→256, then **2 layers, 4 heads, dim 256, FFN 512**, self-attention across the 49 semitone-tokens per frame. — Lets a fundamental and its octave ghost (12 semitones apart) interact directly — the octave-ghost fix at the attention level (F4: hFT/SpecTNT).
4. **Freq collapse:** attention-pool (1 learned query) over 49 tokens → **256-vec per frame.** — Collapse *after* full-resolution freq-attention respects the "don't pool freq early" lesson (hFT collapses F→P via its converter identically) (F4).
5. **Time-axis Conformer: 6 layers, dim 256, 4 heads, conv-kernel 15, dropout 0.2, attention-dropout 0.1.** — Conformer's conv+relative-attention is the right time backbone; 6 (not baseline's 10) because GuitarSet is ~3 h and Kim's *winning* config was 1 block — lean on depth-cut + dropout + aug against overfit (F3: Kim; F4: hFT uses 3/axis).

**Params ≈ 12 M** (between hFT's 5.5 M and the baseline). Fits 12 GB at batch 8 / 6 s with bf16 + grad-checkpointing.

---

## 3. Heads + note-forming decode

**Two heads off the shared encoder, O&F direction (onset → frame):**
- **Onset head:** MLP 256 → 128 → **126** (6 strings × 21 frets), sigmoid. — Dedicated onset predictor; its detached output gates note starts (F1: Hawthorne 2018 — the single biggest note-F1 lever).
- **Frame head:** input = `concat[encoder_feat (256), onset_logits.detach() (126)]` → MLP 376 → 128 → **126**, sigmoid. — Frame conditioned on onset; **the `.detach()` is mandatory** or frame-loss gradients corrupt the onset detector (F1 pitfall #1).
- **No offset head, no velocity head.** — Tab F1 ignores offsets; velocity is piano-only (F3; F1).

**Decode (this — not the architecture — converts high frame-F1 into note-F1):** for each (string s, fret f) cell:
1. **Onset fires** iff `onset_reg(s,f,t)` is a **local maximum in t** AND `> θ_on`. — Local-max is what separates two same-pitch re-strikes; plain threshold merges them (F1: Kong; the exact fix for weakness #1).
2. **Sub-frame onset time** from the triangular peak (parabolic interp over t−1,t,t+1). — Recovers timing lost to 11.6 ms frames at the 50 ms mir_eval tolerance (F1: Kong).
3. **Note starts** only at a fired onset; **sustains** while `frame_prob(s,f,t) > θ_fr`; **ends** when frame drops below `θ_fr` OR a new onset(s,f) fires (re-strike → new note) (F1: Hawthorne).
4. **Monophonic-per-string:** if >1 fret active on a string in a frame, keep highest-prob. **Min note length = 2 frames.**
- **Thresholds:** `θ_fr = 0.5`; tune `θ_on ∈ {0.3, 0.4, 0.5}` on val note-onset F1 (F1).

---

## 4. Labels + losses

- **Class layout: 6 strings × 21 frets (fret 0–20), independent sigmoid; silence = all-off.** — Fret-relative is 2.4× more compact, exploits per-string timbre, sigmoid is O&F/inhibition-native (F3: FretNet/Cwitkowitz). Use GuitarSet's native `.jams` string+fret directly (no MIDI→string ambiguity). Notes needing fret >20 (rare) are logged/dropped.
- **Frame target:** 1 for every frame a cell sounds (onset→offset). **Loss: Focal (γ=2)** — keep baseline's choice; handles the dominant silence class (F5).
- **Onset target: Kong triangular soft label, peak 1.0 at GT onset frame, `g(n)=max(0, 1−|n|/J)`, `J=5` (nonzero ±5 frames ≈ ±58 ms).** **Loss: BCE with `pos_weight=5`.** — Soft target tolerates label jitter + gives sub-frame timing; pos_weight stops the sparse onset head (~1% positives) collapsing to all-zero; BCE (not MSE) keeps it consistent with frame loss (F1: Kong; F5: O&F c=5).
- **Total: `L = L_frame + L_onset`, equal head weights (1.0/1.0).** — Published default across O&F/Kong/hFT; tune HCQT + decode thresholds first, never loss coefficients (F1; F4).

*(Phase-2 only, after baseline is solid: add pairwise-inhibition `L_inh`, `w=(1−IoU)^128`, `λ=1`, requires the sigmoid formulation above — cut duplicate-pitch errors 24.3→10.6/track (F3: Cwitkowitz 2022).)*

---

## 5. Training recipe

- **Optimizer: AdamW, betas (0.9, 0.98), weight decay 1e-2.** — Transformer-standard (F4; F5).
- **LR: peak 5e-4, linear warmup 1500 steps → cosine decay to 1e-5 over ~60 epochs.** — Kong's 5e-4 CRNN setting; warmup stabilizes attention; NOT MT3's 1e-3 (that's seq2seq) (F5: Kong; F4 pitfall).
- **Grad-clip norm 3.0; bf16 autocast (not fp16 — overflow); grad-checkpointing on Conformer blocks.** — O&F clip; bf16 is the safe half-precision (F1; F5).
- **Batch: physical 8 at 6 s segments (fallback 4 + accum 2 → effective 8) if OOM.** — Matches O&F batch-8 regime on 12 GB (F5).
- **Segments: 6 s (~517 frames), sampled per-track with 1 s hop overlap.** — Iteration/sequence sampling equalizes track influence + multiplies the tiny dataset (F3: FretNet/inhibition; F4: hFT 10 s/1 s hop).
- **Epochs: budget 60–120, early-stop patience 12 on val note-onset F1 (string-dependent), keep best; weight EMA decay 0.999.** — Select on the metric you care about, NOT frame F1/loss (F5 pitfall).

**Augmentation (ranked by impact):**
1. **Pitch-shift = base-CQT roll by `3k` bins, `k ∈ U{−3,…,+6}` semitones (capo semantics: every fret f→f+k same string; drop f+k∉[0,20]).** — Single most effective AMT aug; free on CQT; up-biased because low-E is a pitch floor; strumming-paper optimum ±6 (F5: strumming 2025; MAESTRO ±2).
2. **SpecAugment on HCQT: 2 time masks (≤10% frames), 2 freq masks (≤12 bins ≈ ⅓ octave), p=0.5.** — Narrow freq masks only — a wide mask erases a note's fundamental in a CQT (F5 pitfall).
3. **(Offline, optional) amp/effects: distortion, overdrive, EQ, reverb, compression, noise SNR 10–30 dB — EXCLUDE delay/echo.** — Delay injects false repeated onsets = your exact failure mode (F5: Wiggins 2024).
- **Skip mixup** (blends onset targets into non-physical soft onsets, hurts the timing you're optimizing) and **skip aggressive time-stretch** (smears onsets) (F5 pitfalls).

---

## 6. Evaluation protocol

**Run BOTH tracks:**

**(A) Head-to-head vs v1 — same split.** Reuse the existing **113-track split** the baseline was scored on so model changes are isolated. **CRITICAL FIRST STEP: re-evaluate v1 to pin its 0.60 metric definition** — published GuitarSet string-*agnostic* note-F1 tops out ~0.664 (FretNet) and string-*dependent* ~0.506; if v1's 0.60 is string-agnostic it is already near-SOTA and the real headroom is string-*dependent* (F3: critical reality check). Verify the 113-track split is player-disjoint; if it leaks players, flag 0.835 as optimistic.

**(B) Literature-comparable — GuitarSet 6-fold player-held-out CV** (4 train / 1 val / 1 test per fold, mic audio, never split a player), **final config only** (6× cost → overnight). Report mean ± std (F3; F5).

**Metrics (mir_eval, 50 ms onset tolerance, offset ignored):**
- **Note-onset F1 — string-DEPENDENT and string-AGNOSTIC** (report both; string-dependent is the genuine target).
- **Onset precision & recall separately** — the onset head buys precision/segmentation, and can *lower* aggregate recall-inflated F1; don't judge it on F1 alone (F3 caveat).
- **Frame multipitch F1** (compare v1's 0.835) + **frame tablature F1** (string-dependent).
- **TDR** (tablature disambiguation rate).
- **Beat targets:** string-agnostic note F1 > 0.664, string-dependent > 0.506, frame tab F1 > 0.781, TDR > 0.918 (F3).

---

## 7. Ablation plan (1–2 days, GuitarSet single fold, ~60 epochs, ~2–3 h each)

Ordered to isolate ONE change per run; each unattended with checkpoint/early-stop/logging. Same fold throughout.

| # | Run | Change isolated | Expected signal | Time |
|---|---|---|---|---|
| **R0** | Reproduce v1 (single CQT, frame-only, 6×50) | sanity / metric pin-down | match 0.835 frame; fix note-F1 metric definition | 2–3 h |
| **R1** | **+ Onset head** (O&F dual-head, 6×21 sigmoid, note-forming decode) | onset head + decode | note-onset F1 ↑, especially precision & re-strike splits (F1; F3) | 2–3 h |
| **R2** | **+ HCQT** (single CQT → 6-harmonic HCQT input) | octave-ghost fix | string-agnostic note-F1 ↑ (FretNet ablation 0.629→0.664) (F2; F3) | 2–3 h |
| **R3** | **+ Freq-axis attention** front-end | spectral attention | note-F1 ↑, fewer octave false-positives (F4: hFT) | 2–3 h |
| **R4** | **+ Augmentation** (pitch-roll + SpecAugment) | data aug | F1 ↑, rare-fret recall ↑; pitch-shift dominates (F5) | 2–3 h |
| **R5** | **+ Triangular onset regression + sub-frame decode** | label-jitter robustness | onset timing ↑ at 50 ms (Riley 96.5 vs 76.5) (F4; F1) | 2–3 h |
| *R6* | *(opt) + IDMT/moum string-agnostic pretrain → GuitarSet finetune* | extra data / timbres | robustness ↑ | +overnight |
| *R7* | *(opt) + inhibition loss* | duplicate-pitch suppression | dup-pitch errors ↓ (F3) | +2–3 h |

**Total R0–R5 ≈ 12–18 h.** Then run the **winning config through full 6-fold CV overnight (~12 h)** for the literature number. Binary-window and triangular targets share the same local-max/BCE code path, so R5 is a low-risk target-shape swap (and the safe fallback if regression decode misbehaves).

---

## 8. Top risks for unattended training + mitigations

1. **Onset head collapses to all-zero** (1% positives). → `pos_weight=5` + triangular soft targets; **log onset positive-rate & onset P/R every epoch**; abort-guard if onset recall = 0 after 5 epochs (F5 pitfall).
2. **OOM on 12 GB.** → bf16 + grad-checkpointing + 6 s cap + batch-8→(4+accum2) fallback; freq-attention runs on the **49**-token (not 147) axis to keep per-frame attention cheap.
3. **Overfit on ~3 h data.** → 6-layer (not 10) Conformer, dropout 0.2/0.25, pitch-shift + SpecAugment, EMA, early-stop on val note-F1 (F3).
4. **NaN / divergence** (attention). → warmup 1500 steps, grad-clip 3, bf16 (never fp16), peak LR 5e-4 (fallback 3e-4) (F4; F5).
5. **Wrong checkpoint selection.** → select/early-stop on **val note-onset F1**, never frame F1 (baseline already 0.835 there) (F5 pitfall).
6. **HCQT harmonic roll-off** silently zeroes top-fret h=5. → **unit-assert** base CQT spans MIDI 40−36 … 88+84 before training; visualize one HCQT frame.
7. **Decode bugs** (local-max / sub-frame) silently tank note-F1. → unit-test decode on synthetic onset trains (two same-pitch strikes 50 ms apart must yield 2 notes) before the overnight queue.
8. **Metric ambiguity** (string-dep vs agnostic) wastes the night chasing a phantom gap. → **R0 pins v1's metric first** (F3 critical check).
9. **Cross-dataset label noise** (IDMT/moum string conventions). → keep them OUT of the primary runs; if used (R6), supervise only string-agnostic pitch (max-projection over cells), full 6×21 grid on GuitarSet only.
10. **Mid-run crash.** → checkpoint every ~1 k steps, resumable, launch `run_in_background` with rotating logs; each ablation independent so one failure doesn't block the queue.

---

**Build order:** implement + unit-test HCQT (risk 6) and decode (risk 7) → R0 metric pin-down → queue R1→R5 unattended → pick winner → 6-fold overnight. Do NOT add inhibition or the Kim&Bello cGAN until R1–R5 land — both are phase-2 refinements worth ≤1.5 note-F1 and add GAN/loss-tuning instability (F1; F3).