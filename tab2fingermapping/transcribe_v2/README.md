# transcribe_v2 — Onset+Frame / HCQT 기타 탭 전사 (재학습)

> 최종 갱신: 2026-08-03. 이 디렉터리는 실험용 전사 경로이며 기본 운영 파이프라인의 Stage 1은
> 상위 [`../pipeline.py`](../pipeline.py)에서 호출한다. 아래 R0~R4 결과는 재현·비교용 기록이다.

> v1(`../conformer/`)·guitar_v3 학습코드 **불변**. 별도 디렉토리. 설계·근거 = `DESIGN.md`,
> SOTA 조사 종합 = `_gen/research_synthesis.md`. 실행 환경 = conda `tab2fm`.

## 목적

v1의 진단된 두 병목을 **구조**로 해결: ①재타현 병합 → onset 헤드, ②옥타브 유령음 → HCQT+주파수축
어텐션. GuitarSet player-held-out에서 R0(v1 재현)→R4로 각 기여를 격리 측정(균형 note-onset F1).

## 파일

| 파일 | 역할 |
|---|---|
| `features.py` | HCQT(단일 베이스 CQT + 하모닉 빈-롤, pitch-shift 공짜) / SingleCQT(베이스라인) |
| `dataset.py` | GuitarSet 로드·현 정규화·fret 라벨·삼각 onset·pitch-roll. player 분할 |
| `model.py` | 주파수축 어텐션 프런트엔드 + Conformer + Onset&Frame 듀얼 sigmoid 헤드 |
| `losses.py` | frame weighted-BCE + onset 가중 BCE + (옵션) 옥타브 억제 |
| `decode.py` | 지역최대 note-forming 디코드 + mir_eval (재타현 분리 핵심) |
| `train.py` | config 구동 학습(AdamW·웜업+코사인·EMA·bf16·조기종료·재개·예외격리) |
| `evaluate.py` | 종합 평가(note-F1 sdep/sag·onset P/R·frame-tab·TDR) + v1 재평가 |
| `run_ablation.py` | R0~R4 순차 학습+평가 → `RESULTS.md` |
| `configs/` | R0~R4 애블레이션 설정(JSON) |

## 실행

```bash
export PROJECT_ROOT="/path/to/yigyu/3"
conda activate tab2fm
PY="$(command -v python)"
cd "$PROJECT_ROOT/tab2fingermapping/transcribe_v2"
$PY run_ablation.py                       # R0~R4 전체 → RESULTS.md
$PY train.py --config configs/R4_aug.json # 단일 rung
$PY evaluate.py --ckpt checkpoints/R4_aug/best.pth --split guitarset_test
$PY evaluate.py --v1 --split test113      # v1 재평가(지표 확정용)
```

## 핵심 발견 (DESIGN §1·§11)

- **v1의 "0.596" = 융합 test113의 string-DEPENDENT note-onset F1**(mir_eval 재평가로 확정).
  GuitarSet 단독 0.87은 player 학습 누수+깨끗한 단일기타. 진짜 목표 지표 = string-dependent.
- 데이터에 **GuitarTechs 현-반전 라벨 버그** 발견(정규화로 수정) — v1의 융합 TDR 0.758 원인.
- 재타현 병합 상당부분은 **median smoothing 자초** — onset 헤드는 원리적 해결.
- 학습 안정화 3종(bias 사전확률 초기화·스레드 제한·예외 격리)이 붕괴/크래시 해결 — DESIGN §11.
