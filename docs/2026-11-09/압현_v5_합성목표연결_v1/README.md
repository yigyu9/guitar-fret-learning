# 압현 v5와 합성 연속 목표 실행

작성일: 2026-11-04. 사용자 지정 분류인 `2026-11-09` 아래에 보관한다.

[원본 C1~C6 목표](../압현_연속목표_손가락조합_v1/README.md)를 압현 v5에 연결한다. 한 번의 학습에서 한 조합을 선택하며, 그 안의 P1~P9를 하나의 연속 시간축으로 사용한다. 현재 V5의 신경망·보상·관절 제어·구간에서 전체 목표로 넘어가는 일정을 사용한다. 일반 곡의 기본 진입점도 이제 V5이며 [학습 안내](../../../guitar_learning/README.md)를 따른다.

## 무엇을 실행하는가

| 선택 | 담당 손가락 조합 | 등록 입력 ID |
|---|---|---|
| C1 | 검지·중지 | `press_sequence_c1_v1` |
| C2 | 중지·소지 | `press_sequence_c2_v1` |
| C3 | 약지·소지 | `press_sequence_c3_v1` |
| C4 | 중지·약지 | `press_sequence_c4_v1` |
| C5 | 검지·약지 | `press_sequence_c5_v1` |
| C6 | 검지·소지 | `press_sequence_c6_v1` |

각 조합은 20개 음·20개 누름이며 원본 길이는43.75초다. 준비3초와 마지막0.5초를 더한 전체 에피소드는47.25초, 정책60Hz 기준2,835tick이다. 예를 들어 원본 첫 압현0.88초와 음 시작1초는 시뮬레이션의3.88초와4초가 된다. 과제 사이 쉼에도 시뮬레이션은 계속되며 자세를 다시 넣지 않는다.

P1 단일 압현 → P2 동시 압현 → P3 같은 손가락 전환 → P4 손가락 교대 → P5 유지하며 추가 → P6 일부 해제 → P7 유지하며 다른 손가락 전환 → P8 동시 전환 → P9 해제 후 재압현 순서다. 모든 조합의 줄·프렛·시각은 같으며 손가락 배정이 다르다. 물리적으로 도달하거나 학습에 성공한다는 보장은 별도 실험으로 확인해야 한다.

## 코드 읽는 순서

| 파일 | 이 작업에서의 역할 |
|---|---|
| [press_sequence.py](../../../guitar_learning/tool/experiments/press_sequence.py) | C1~C6 선택, 입력 검사, 새 학습·재개·평가·렌더 명령 |
| [prepare_press_targets.py](../../../guitar_learning/tool/prepare_press_targets.py) | 원본을 등록 번들로 만들고 검증. 압현 전용 원본 시각을 연결 |
| [tool/experiments/compact_press_v5.py](../../../guitar_learning/tool/experiments/compact_press_v5.py) | 기존 v5 설정·정책·환경 연결 및 엄격한 체크포인트 검사 |
| [training/compact_press_v5.py](../../../guitar_learning/training/compact_press_v5.py) | 상태·목표 인코더, 행동망·가치망, 역할별 초기 탐색 |
| [gpu/compact_press_v5.py](../../../guitar_learning/gpu/compact_press_v5.py) | v5 관측·보상 조건·유지와 해제 완료 평가 |
| [training/finger_skill_runner.py](../../../guitar_learning/training/finger_skill_runner.py) | 구간/전체 목표 일정, 학습·저장·재개·평가 운영 |
| [training/rollout.py](../../../guitar_learning/training/rollout.py) · [ppo.py](../../../guitar_learning/training/ppo.py) | 병렬 환경에서 경험 수집 후 PPO 갱신 |
| [training/training_log_io.py](../../../guitar_learning/training/training_log_io.py) | 로그·체크포인트 저장과 운영 기록 |

V5의 상태·보상·정책 구현은 해당 V5 파일로 통합하고 공용 MLP·목표 결합은 `training/policy.py`에 둔다. 이전 compact 압현 실행기와 버전별 구현은 활성 경로에서 제거했다. 메타데이터의 `v3`·`v4` 이름은 기존 로그 필드와 계산 계약의 식별자이며 구형 실행기가 남아 있다는 의미가 아니다.

## 모델과 학습 흐름

1. 선택한 번들의 원본·파생 파일 SHA, 줄·프렛·손가락·시간을 검사한다.
2. 기존 곡 입력 검증을 통과시킨 뒤 압현 목표의 동시 시작 시각을 원본대로 적용한다.
3. v9 초기 자세에서 왼손33축 정책을 학습한다. 상태464 → 256, 목표26 × 8개 각각 → 64, 결합768 → 512 → 256 → 행동33이다. 가치망은 분리한다. 골반 입력을 선택하면 상태473이다.
4. 초기 탐색은 팔12축·엄지5축0.15, 검지~소지16축0.35다. 학습 중 표준편차도 갱신된다. 기본 보상 조건은 `corrected`다.
5. 처음 계획한 `updates × horizon × num_envs` 전이의25%를 반영한 뒤 새로 시작하는 에피소드부터 전체47.25초 목표로 넘어간다. 진행 중 구간을 강제로 끊지 않는다. 초기 구간 학습은20개 전체를 매번 재생하는 방식이 아니다.
6. H32라면 환경당32tick 수집 후 PPO를 갱신한다. 보상·음별 수행·실패·모델을 저장한다. 정상 종료나 실패가 일어나면 해당 환경을 초기화한다.

손가락 직접 목표각 제어, 손가락 움직임 비용0, 자유 기타·root 고정·유한 전신 지지는 유지한다. 보상과 v5 비교 조건의 상세는 [v5 구조 안내](../압현_구조개선_v5/README.md)를 따른다.

## 명령

프로젝트 루트에서 실행한다. 아래 `python`은 Isaac Gym을 사용할 수 있는 환경의 Python이다. 이 PC에서는 `/home/ajou/miniconda3/envs/rl38/bin/python`을 사용한다. 출력은 실행마다 새로운 디렉토리로 지정한다.

목록과 입력 검사에는 GPU가 필요 없다.

```bash
python -m guitar_learning.tool.experiments.press_sequence list
python -m guitar_learning.tool.experiments.press_sequence check --all
```

다음은 C1 새 학습 명령 예시다.1024환경·1000반복은 실행값의 예시이며 수렴을 보장하는 예산이 아니다. `--size large`여도 v5의 신경망 폭은 위 고정 구조를 사용한다.

```bash
python scripts/tab2body.py --cache-root .runtime/cache run \
  -m guitar_learning.tool.experiments.press_sequence train C1 \
  --size large --num-envs 1024 --horizon 32 --updates 1000 \
  --checkpoint-every 250 --seed 7 --improvement-profile corrected \
  --out runs/press_v5_c1_01
```

재개는 저장된 C조합·설정·입력·소스·신경망 계약을 그대로 사용한다. 아래500회는 추가 반복 수다. 처음 계획한25% 문턱을 다시 계산하지 않는다.

```bash
python scripts/tab2body.py --cache-root .runtime/cache run \
  -m guitar_learning.tool.experiments.press_sequence train \
  --resume runs/press_v5_c1_01/J/final.pt --updates 500 \
  --out runs/press_v5_c1_resume_01
```

평가와 영상은 저장본에 기록된 C조합을 사용한다. `full_song`은 여기서는20개 전체 연속 목표를 의미한다.

```bash
python scripts/tab2body.py --cache-root .runtime/cache run \
  -m guitar_learning.tool.experiments.press_sequence evaluate \
  runs/press_v5_c1_01/J/final.pt --scope full_song --num-envs 2 \
  --out runs/press_v5_c1_eval_01

python scripts/tab2body.py --cache-root .runtime/cache run \
  -m guitar_learning.tool.experiments.press_sequence render \
  runs/press_v5_c1_01/J/final.pt --scope full_song --num-envs 2 \
  --out runs/press_v5_c1_video_01
```

다른 조합으로 학습하려면 `train C2`처럼 새 실행을 시작한다. 여섯 조합을 자동으로 섞거나 C1 저장본을 C2로 바꿔 재개하지 않는다. C번들은 이 `press_sequence` 실행기를 사용해야 정확한 압현 시각이 적용된다. 기존 곡용 `compact_press_v5 --song ...`에 직접 넣는 것은 이 실행 계약에 포함되지 않는다.

## 입력 시각과 보존

공식 타현 계획은 동시 두 줄에 순차 타현 시간차를 넣는다. 이번 목표는 압현 전용이므로 이 시간차를 압현 시작에 반영하지 않는다. 공식 타현 계획·manifest·입력 SHA 검사는 유지하고, 검증된20개 목표를 원본 note index로 연결한 뒤 음 시작만 원본 시각으로 복원한다. target ID·줄·프렛·손가락·누름·해제·순서·전체 길이는 유지한다. 메타데이터에는 보정 전후 시각과 압현 전용 의미를 남긴다.

원본의 줄 번호는 `0=낮은 E=실제6번줄`이다. 환경 목표에서는 `0=높은 e=실제1번줄`이므로 변환은 한 번만 한다. P7의 연속 누름과 P9의 두 번 누름을 최종 목표 전체에서 원본과 대조한다.

번들 내부에 원본 JSON·CSV·chords 사본과 생성 근거를 보관한다. 학습·평가에는 다른 PC의 경로나 원본 문서 디렉토리에 접근할 필요가 없다. 무음 WAV는 기존 번들 형식의 길이 운반용이며 실제 음악 오디오나 음향 성공 자료가 아니다.

각 번들은11개 파일이며6개 합계는 약18MB다. 준비 도구의 `prepare C1` 또는 `prepare --all`은 **등록 디렉토리가 아직 없을 때만** 사용한다. 이미 생성된 번들은 `check`로 검사하고 덮어쓰지 않는다. 재생성에는 위 원본 문서의 입력이 필요하지만, 등록 후 학습에는 번들 내부 사본만 필요하다.

## 출력과 검증 근거

학습 출력은 `--out`의 `settings.json`, `report.json`과 `J/` 아래에 저장한다. 주요 파일은 `final.pt`, `checkpoint_manifest.jsonl`, `learning_metrics.jsonl`, `episodes.jsonl`, `episode_metadata.json`, `finger_control_diagnostics.json`, `training_contract.json`, `inputs_before.json`이다. 에피소드 압축 메타데이터를 복원해 읽을 때는 `training_log_io.iter_episode_rows()`를 사용한다.

`learning_metrics.jsonl`에는 항목별 보상·탐색·학습률과 구간/전체 목표 노출이 기록된다. 평가의 `press_completion`은 전체 유지, 해제, 두 조건의 완료 성공을 구분한다. `report.completed`는 실행 완료이며 압현 성공률을 의미하지 않는다.

**목표 연결 당시의 검증 기록:** CPU50개 검사와 독립 검수를 통과했다. GPU에서 C1을8환경4회 학습하고2회 재개했으며,2환경 전체 평가가47.25초를 물리·손목 실패 없이 완주했다. 목표·시각·입력·저장본 SHA와 재개 가중치 보존을 확인했다. 평가 압현 달성은0/20이며, 학습 중 탐색에는 기타 이탈 종료가 있었다. 실행 준비를 확인한 결과이고 장기 성능 비교는 아니다.

위 수치는 목표 연결 당시 원문에 대한 기록이며 이번 활성 코드 통합의 새 검증 수치가 아니다. 이번 정리 검증은 [정리 기록](../../maintenance/v5_project_cleanup_20261104/)을 따른다. 소스가 바뀌기 전 모델은 원래 봉인 runtime에서만 사용하며 checkpoint의 SHA·입력·identity 검사를 완화하지 않는다.

연결 당시 손목 검사 한 종류는 구 실험 fixture의 I/O 오류로 실행되지 않았다. 이번 목표의 손목 track과 환경 연결은 신규 CPU·GPU 검사로 확인했다. 상세와 원자료는 [검증 결과](검증결과.md), 재현 명령은 [실행 명령](실행명령.txt)에 있다. 원본 보존 기준은 [작업 전 SHA](작업전_SHA.json), 작업 범위와 완료 항목은 [계획](../../plans/press_v5_targets_20261104.md)에서 확인한다.
