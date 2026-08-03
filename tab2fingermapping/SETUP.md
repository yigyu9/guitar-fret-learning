# tab2fingermapping 환경 셋업 매뉴얼 (conda `tab2fm`)

> 최종 갱신: 2026-08-03. Stage1(conformer v1 + consonance-ACE + chordtrack + pipeline.py)의
> **단일 실행 환경 = conda env `tab2fm`**. 이전의 `ace/.venv`(가상환경)는 폐기 —
> venv는 절대경로 기반이라 디렉토리 이동 시 깨졌던 교훈(07-15 재구성 때 재생성 필요했음).
> conda env는 이름 기반이라 프로젝트 폴더를 옮겨도 안전하다.

## 1. 환경이 커버하는 것

| 컴포넌트 | 필요 의존성 | 비고 |
|---|---|---|
| `conformer/` (v1 탭 전사) | torch 2.5.1+cu121, torchaudio, nnAudio | guitar_eval에서 상속 |
| `ace/` (consonance-ACE) | lightning, librosa, mir_eval, harte, pumpp, jams, gin, torchmetrics | pip 추가분 |
| `chordtrack/`, `pipeline.py` | 위 둘의 합집합 + numpy | — |
| `csv_to_notejson.py` | stdlib만 | 아무 python3 가능 |

미설치(의도적): `wandb`(학습 전용), `beat-this`(`--beat-sync` 옵션 전용 — 필요 시
`pip install beat-this`).

## 2. 생성 절차 (이 머신에서 실행된 그대로)

```bash
# ① guitar_eval(torch 2.5.1+cu121·nnAudio 보유)을 클론 — GPU 스택 재다운로드 회피,
#    하드링크 공유라 디스크 부담 적음
conda create -y -n tab2fm --clone guitar_eval

# ② ACE 추론 의존성 추가 (버전 = ace/requirements.txt 기준, torch 계열 제외)
conda activate tab2fm
python -m pip install \
    lightning==2.5.1 gin-config==0.5.0 librosa==0.11.0 mir_eval==0.8.2 \
    harte-library==0.4.5 pumpp==0.6.0 jams==0.3.5 scikit-learn==1.6.1 \
    tqdm torchmetrics
```

처음부터 만들 경우(다른 머신 등): `conda create -n tab2fm python=3.10` 후
`pip install torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121`,
`pip install nnAudio pandas` + 위 ② 목록.

## 3. torch 버전 노트

- ACE 업스트림 요구는 torch 2.6.0이지만 **2.5.1에서 추론 동작을 검증**했다
  (체크포인트 로드·CQT·forward 모두 정상 — 07-15 moum 244파일 + rock3 실측).
- python은 3.10 — ACE의 py3.11 전용 코드(enum.verify)는 로컬 패치로 해결(§4).

## 4. ACE 로컬 패치 (⚠️ `ace/`를 재클론하면 재적용 필요)

| 파일 | 수정 | 이유 |
|---|---|---|
| `ace/ACE/preprocess/audio_processor.py` | `from transforms import` → `from ACE.preprocess.transforms import` | 패키지 실행(`python -m`) 시 ImportError |
| `ace/ACE/preprocess/chord_utils.py` | `from enum import CONTINUOUS, Enum, verify`에 try/except 폴백(no-op verify) | enum.verify는 py3.11+ 전용 |

체크포인트 `ace/ACE/checkpoints/conformer_decomposed_smooth.ckpt`(55MB)는 레포 동봉 —
재클론 시 존재 확인.

## 5. 실행

```bash
export PROJECT_ROOT="/path/to/yigyu/3"
conda activate tab2fm
PY="$(command -v python)"
cd "$PROJECT_ROOT/tab2fingermapping"

$PY pipeline.py <audio.wav> --bpm 117          # 전체 번들 → <stem>_stage1/
$PY pipeline.py <audio.wav> --skip-ace         # 탭→규칙+필터만 (ACE 생략)
$PY conformer/transcribe.py <audio.wav>        # 탭 CSV만
(cd ace && $PY -m ACE.inference --audio <wav> --out x.lab \
    --threshold 0.3 --chord-min-duration 0.25) # ACE 단독 (검증된 완화 파라미터)
$PY chordtrack/build_track.py <wav> --ace-lab x.lab   # 코드 트랙만
python3 fingermapping/run_fingering.py <notes.csv> <chords.json>   # 운지만 (stdlib — 아무 python3)
```

평가 하니스 재현(리포트 재현 절과 동일):

```bash
cd "$PROJECT_ROOT/tab2fingermapping/ace"
$PY ../chordtrack/eval_moum.py                 # 4변형 moum 비교
$PY ../ace_eval/eval_moum.py 0.3 0.25 relaxed  # ACE 단독 평가
```

## 6. 설치 검증 (새 환경을 만들면 이것부터)

```bash
export PROJECT_ROOT="/path/to/yigyu/3"
conda activate tab2fm
PY="$(command -v python)"
# ① 임포트 체크
$PY -c "import torch, nnAudio, lightning, mir_eval, pumpp, harte; \
        print('OK torch', torch.__version__, 'cuda', torch.cuda.is_available())"
# ② 파이프라인 스모크 (rock3 comp — 기대값: 105 events, qerr ~22ms)
cd /tmp && $PY "$PROJECT_ROOT/tab2fingermapping/pipeline.py" \
    /path/to/audio.wav \
    --smooth 3 --bpm 117
```

## 7. 트러블슈팅

- `ImportError: cannot import name 'CONTINUOUS' from 'enum'` → §4 패치 유실(재클론?).
- `ModuleNotFoundError: transforms` → §4 패치 ① 유실.
- `chords_vocab.joblib` 없다는 에러는 **무시 조건 확인**: 분해형 모델 추론은 vocab
  불필요(경로만 전달됨). 에러가 실제로 나면 `--model-name conformer`(비분해형)를 쓴 것.
- legacy(conformer_v2) 관련 임포트 에러 → 현재 Stage1은 `tab2fingermapping/conformer/`의
  v1 경로만 사용하므로 legacy 설정을 호출하지 않는지 확인한다.
- 다른 conda env(guitar 등)와 혼용 금지 — Isaac Gym 계열은 PROJECT_CONTEXT §6 참조.
