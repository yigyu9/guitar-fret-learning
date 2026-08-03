# transcribe_v2 — Onset+Frame / HCQT 기타 탭 전사 모델 설계

> 2026-07-15. v1(`tab2fingermapping/conformer/`)은 **불변 보존** — 이 디렉토리는 별도.
> 조사·설계 근거 = `_gen/research_synthesis.md`(SOTA 5각 조사 종합), 각 결정에 `(F#)` 인용.
> 실행 = conda `tab2fm`(torch 2.5.1+cu121, nnAudio 0.3.4, mir_eval 0.8.2), GPU RTX 4070 Ti 12GB.
> 사용자 결정(07-15): 구조=Onset+Frame 듀얼헤드+HCQT / 규모=애블레이션(1~2일) / 목표=균형 note-onset F1.

## 0. 요약 (한 화면)

진단된 두 병목 — ①재타현 병합(프레임 표현이 onset 없음) ②옥타브 유령음(단층 CQT) — 을
구조로 해결: **HCQT 하모닉 입력 + 주파수축 어텐션 프런트엔드 + 시간 Conformer + Onset&Frame
듀얼 sigmoid 헤드(6현×21fret) + 지역최대 note-forming 디코드.** GuitarSet player-held-out에서
R0(v1 재현)→R4(전부)로 각 기여를 격리 측정.

## 1. 베이스라인 분석 + **R0 핵심 발견 (v1 지표 정의 확정)**

| 셋 (mir_eval, ±50ms, offset 무시, smoothing 없음) | note-F1 string-dep | string-agnostic | TDR |
|---|---|---|---|
| **test113 (융합 홀드아웃 — v1 원 테스트셋)** | **0.595** | 0.695 | 0.758 |
| GuitarSet player5 (누수 가능) | 0.872 | 0.876 | 0.995 |

**확정된 사실 (조사가 예견한 R0 필수 확인)**:
1. EVALUATION.md의 **"0.596" = 융합 test113의 string-DEPENDENT note-onset F1**(재현 0.595).
   string-agnostic은 0.695. → 진짜 목표 지표는 **string-dependent**(현+fret).
2. GuitarSet 단독 0.87은 ①v1이 player5를 학습에서 봤을 **누수** ②깨끗한 단일기타. 정직한
   홀드아웃은 test113. **새 모델은 player-disjoint(train 0-3/test 5)로 정직하게 평가.**
3. **융합 test113 TDR 0.758**(현 배정 24% 오류) — 대부분 **GuitarTechs 현-반전 라벨 버그**가
   원인(측정: 정방향 51% vs 반전 98% 유효). 새 데이터셋이 정규화로 이걸 고침.
4. **재타현 병합의 상당 부분은 자초된 것**: 파이프라인의 median smoothing(--smooth 3)이 재타현을
   뭉갬(smoothing 없이 재평가하면 v1 recall이 크게 높음). onset 헤드는 이를 원리적으로 해결하되,
   기대 이득은 "0.60→0.9"가 아니라 그보다 보수적. (정직한 재조정 — 조사 §6 경고 반영.)

**v1 구조**: CQT 288bins(36/oct) → Conformer(256/10층/4헤드/k15) → Linear(6×50 pitch), FocalLoss(γ2),
Adam **LR 1e-5(비정상 저)**, batch4, 500프레임 크롭. → 개선점: LR 정상화·스케줄러·onset·HCQT·현정규화.

## 2. 데이터 (research_synthesis §0·§6, 리스크9)

- **애블레이션·평가 = GuitarSet 단독**(360트랙, 6 player × 30진행 × 2스타일). 유일하게 현별 라벨
  깨끗. player-held-out: **train {0,1,2,3} / val {4} / test {5}** (player 절대 분리, 누수 0).
- 라벨 = CSV(=jams와 노트수 동일 확인) → 현 정규화(GuitarTechs 반전) → fret. IDMT/moum은 라벨
  버그 위험으로 주 실험 제외(R6 옵션 프리트레인만).
- fret 표현 유효율 99.6%(정규화 후), 잔여 0.4% 드롭.

## 3. 입력 — HCQT (§1)

- 하모닉 `h ∈ {0.5,1,2,3,4,5}`(6채널). 0.5 서브하모닉이 옥타브 결정 핵심 (F2 Bittner; F3 FretNet).
- 36 bins/oct(3/semitone), 베이스 CQT fmin=E1(MIDI28), 288 bins → nyquist 안전(상단 285빈≈9.8kHz).
  분류 창 = MIDI40~88 (147 bins). (F2)
- **단일 베이스 CQT + 정수 빈-롤 스태킹**: shift_h=round(36·log2 h)=[-36,0,36,57,72,84]. 6개 CQT
  아님 → 계산 절약 + **pitch-shift 증강이 창 이동으로 공짜·정확**. (F2 basic-pitch)
- log1p 압축. 리스크6 범위 assert 코드화(HCQT 생성자). 하모닉 정렬 단위검증 완료.

## 4. 인코더 — 주파수축 어텐션 + 시간 Conformer (§2)

가장 강한 단일 신호 = **시간 전에 주파수를 어텐션**(F4 hFT: note-F1 94.8 vs conv-축약 19.7).
1. Conv stem 6→48(3×3)×2 +BN+ReLU+Dropout0.25 — freq 147 보존. 1×1이 정렬 하모닉 템플릿 봄.
2. Gentle freq 다운샘플 Conv(3,1 stride) → 49 semitone × 96. note 해상도까지만(과축약 아님).
3. **주파수축 트랜스포머 2층·4헤드·dim256** — 49 semitone 토큰 self-attn. 기본음↔옥타브(12반음)
   직접 상호작용 = 옥타브 유령음 어텐션 수준 해결. (F4 hFT/SpecTNT)
4. Attention-pool(학습 query)로 freq 붕괴 → 256/프레임.
5. **시간 Conformer 6층**·dim256·4헤드·k15·dropout0.2. 10층 대신 6층(GuitarSet ~3h 과적합, F3 Kim).
파라미터 ≈ 11M. batch8·6s에서 peak 5.6GB(측정). 애블레이션 플래그로 conv-붕괴/단층CQT 전환.

## 5. 헤드 + 디코드 (§3, 리스크7)

- 클래스 = **6현 × 21fret(0~20), 독립 sigmoid**(무음=all-off). softmax 아님(O&F·억제손실 비호환, F3).
- **onset 헤드**(MLP 256→128→126) + **frame 헤드**(입력=concat[enc256, **onset.detach()**126] →126).
  detach 필수(frame gradient가 onset 검출기 오염 방지, F1 함정). offset/velocity 헤드 없음(탭 무관).
- **note-forming 디코드**(high frame-F1을 note-F1로 바꾸는 핵심):
  1. onset 발화 = onset_prob 셀이 t축 **지역최대** AND >θ_on. ← 재타현 분리(단순 threshold는 병합, F1 Kong)
  2. 서브프레임 onset 시각 = 삼각 피크 포물선 보간(11.6ms 프레임을 50ms 허용오차에서 회복).
  3. 노트 시작=발화, 지속=frame>θ_fr, 종료=frame 하락 또는 새 onset(재타현→새 노트).
  4. 현별 단음(겹치면 확률 높은 것), 최소 2프레임. θ_fr=0.5, θ_on=0.4(스윕 0.3~0.5).
  단위검증: 50ms 간격 같은피치 2타 → 노트 2개 ✓ (frame-only 폴백은 1개=병합, onset 필요성 방증).

## 6. 라벨 + 손실 (§4)

- frame 타깃 = sounding 프레임 1 (멀티핫). 손실 **focal-BCE(γ2)** — 무음 지배 처리(v1 계승).
- onset 타깃 = **Kong 삼각 soft-label** g(n)=max(0,1-|n|/J), J=5(±5프레임≈58ms). 라벨 지터 관용 +
  서브프레임 타이밍. 손실 **BCEWithLogits pos_weight=5**(양성 ~0.6% sparse, all-zero 붕괴 방지, F1/F5).
- 헤드 등가중(w_frame=w_onset=1, O&F 기본 — 손 튜닝 안 함). 억제손실(옥타브 중복)은 R7 옵션.

## 7. 학습 레시피 (§5)

| 항목 | 값 | 근거 |
|---|---|---|
| optimizer | AdamW(0.9,0.98), wd 1e-2 | 트랜스포머 표준 (F4/F5) |
| LR | peak **5e-4**, 웜업 1500스텝 → 코사인 → 1e-5 | Kong CRNN; 웜업이 어텐션 안정 (v1의 1e-5는 과소) |
| precision | **bf16** autocast (fp16 아님 — overflow) | F1/F5 |
| grad-clip | norm 3.0 | O&F |
| batch | 8 (6s=517프레임), oversample 8(트랙당 크롭) | 12GB peak 5.6GB (F5) |
| epochs | 60, early-stop patience 8 (**val note-F1 string-dep** 기준, frame 아님) | F5 함정 |
| EMA | decay 0.999 | F5 |
| 증강(R4) | pitch-shift 빈-롤 k∈U{-3,+6}(상향편향=저음현 바닥) + SpecAugment(time2·freq2≤12bins) | F5 (pitch-shift 최강, 좁은 freq mask만) |

증강 제외: mixup(onset 타깃 오염), 강한 time-stretch(onset 뭉갬), delay/echo(가짜 재타현).

## 8. 평가 프로토콜 (§6)

- (A) **GuitarSet player5 홀드아웃**(주) — 애블레이션 공통. player-disjoint, 정직.
- (B) test113 — v1과 head-to-head(단 v1은 융합, 새 모델은 GuitarSet 학습이라 도메인 상이 주의).
- 지표(mir_eval, ±50ms, offset 무시): note-F1 **string-dep(주)**+agnostic, onset P/R 별도,
  frame-tab F1, TDR. 목표선(FretNet): sag>0.664, sdep>0.506, frame-tab>0.781, TDR>0.918.

## 9. 애블레이션 (§7) — GuitarSet 단일 fold, ~60ep, ~1.5h/런

| # | 구성 | 격리 | 기대 |
|---|---|---|---|
| R0 | 단층CQT + frame-only + conv-붕괴 | v1 재현 베이스라인(정직 홀드아웃) | 기준점 |
| R1 | +onset 헤드(듀얼, 지역최대 디코드) | onset 기여 | note-F1↑(특히 P·재타현) |
| R2 | +HCQT(단층→6하모닉) | 옥타브 유령음 | sag↑(FretNet 0.629→0.664) |
| R3 | +주파수축 어텐션 | 스펙트럴 어텐션 | note-F1↑, 옥타브 오탐↓ |
| R4 | +증강(pitch-roll+SpecAug) | 데이터 증강 | F1↑, 희귀fret recall↑ |
| R5~R7 | (옵션) 삼각onset·프리트레인·억제손실 | phase-2 | R1~R4 착지 후 |

삼각 onset·서브프레임 디코드는 R1부터 기본 적용(온셋 정석). R0~R4 ≈ 8h.

## 10. 무인 학습 리스크·완화 (§8)

1. onset all-zero 붕괴 → pos_weight5 + 삼각타깃 + onset P/R 매 epoch 로깅 + 5ep 후 recall~0 abort.
2. OOM → bf16 + batch fallback (측정 5.6GB, 여유). 3. 과적합 → 6층 + dropout + 증강 + EMA + early-stop.
4. NaN/발산 → 웜업1500 + clip3 + bf16 + LR5e-4. 5. 잘못된 체크포인트 → **val note-F1로 선택**(frame 아님).
6. HCQT 롤오프 → 생성자 범위 assert(코드화). 7. 디코드 버그 → 재타현 단위검증(완료).
8. 지표 모호 → **R0가 v1 지표 확정**(완료: 0.60=string-dep). 9. 크로스데이터 라벨노이즈 → GuitarSet만.
10. 크래시 → best 체크포인트·result.json·재개(러너가 완료 rung 스킵), 각 rung 독립.

## 11. 학습 안정화 — 실측으로 얻은 3가지 (무인 실행 전 필수)

1. **출력 bias 사전확률 초기화(RetinaNet)** = 가장 결정적. 없으면 sparse 타깃(onset 0.6%·frame 2%)에서
   모델이 "전부 0" 자명해로 **붕괴**(loss는 낮지만 F1=0, onset recall→0). 헤드 최종 bias를
   -log((1-π)/π)로 초기화(onset π0.006, frame π0.02)하니 ep0부터 F1 0.31→0.56 정상 상승. + onset
   pos_weight 25·frame pos_weight 5(pos_weight 5 단독은 부족). + LR 5e-4→3e-4.
2. **스레드 과다구독 → numpy/torch 상태오염**. 학습 중 서로 무관한 위치(dataset의 `self.fps`,
   clip_grad의 `named_modules`, pandas)에서 "불가능한" 랜덤 AttributeError/ValueError 발생(단독 재현
   불가). `OMP/MKL_NUM_THREADS=2` + `torch.set_num_threads(2)`로 해소.
3. **스텝·아이템 예외 격리** = 보험. `__getitem__`(→None, collate 필터)과 학습 스텝(→skip+zero_grad)을
   try/except로 감싸 드문 글리치가 8h 런을 죽이지 않게. >200 스킵 시 abort(환경 문제 감지).
+ raw 모델로 val 평가(EMA 초기 지연이 학습 여부를 가림), best는 val note-F1 string-dep로 선택.

**빌드 상태**: features/dataset/model/losses/decode/train/evaluate/run_ablation 구현+검증 완료.
HCQT 범위·하모닉 정렬·재타현 디코드 단위검증 통과. R0 v1 재평가 완료(지표 확정). 붕괴/크래시 해결 후
애블레이션 큐 정상 학습 확인(R0 ep4 sdep 0.44↑) → 실행 중, 완료 시 `RESULTS.md`.
