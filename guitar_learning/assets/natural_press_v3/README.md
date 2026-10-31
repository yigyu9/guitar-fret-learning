# 자연스러운 압현 준비 v3 실험 입력

`catalog.json`은 검증된 네 단일 목표의 기하·정렬 reset 상태 데이터다. 원본 바이트를 그대로 복사했으며 출처 SHA는 `provenance.json`에 기록한다. 과거 Python generator/실행기를 import하지 않는다. 현재 물리 입력144개는 원본과 같은 SHA인지 실행 전에 검사한다. 검증된 정렬 초기 상태가 새 보상 학습의 성공을 뜻하지 않는다.

실행기는 활성 패키지의 `tool/experiments/natural_press.py` 하나이며 공식 J runner/PPO/제어/접촉을 재사용한다. 새 정책은601열·독립탐색·K1의 별도 v3 schema다. 과거 structured/기본557 checkpoint를 호환 모드로 읽지 않는다. E0~E4 관측·보상 차이는 활성 `FingerSkillEnvironment.natural_preparation`에 명시한다.

| 초기 분포/활성 범위 | 실제 reset | 비활성 팔 실행 | 비목표 손가락 실행 |
|---|---|---|---|
| aligned / goal4 | 검증된 정렬 상태 | 정렬 IK 유지 | 정렬 초기 유지 |
| v9 / goal4 | 원래 v9 | 고정 정렬 IK로 이동, 팔 학습 아님 | v9 초기 유지 |
| aligned 또는 v9 / arm16 | 선택한 초기 상태 | 팔12축+목표4축 정책, 같은 초기 IK bias에서 피드백 학습 | 선택 초기 유지 |
| aligned 또는 v9 / full33 | 선택한 초기 상태 | 전체33축 정책 | 전체33축 정책 |

모든 조건에서 phase별 팔 clamp/잠금은 없다. 목표 손가락4축도 첫 tick부터 실행 가능하다. 관측용 phase/hold latch44열은 실행 유지 명령과 분리되어 고정 IK를 바꾸지 않는다. directly requested angle의 전체 범위·LH21 4rad/s·움직임 비용0·물리·접촉/음 원장은 유지한다.

```bash
python -m guitar_learning.tool.experiments.natural_press train \
  --condition E0 --song virtual_finger_v9_middle_s3_f6 \
  --distribution aligned --axes goal4 --size large --num-envs 64 \
  --updates 100 --seed 7 --out runs/natural_press_v3/middle_E0_100

python -m guitar_learning.tool.experiments.natural_press train \
  --resume runs/natural_press_v3/middle_E0_100/J/final.pt \
  --updates 100 --seed 7 --out runs/natural_press_v3/middle_E0_200

python -m guitar_learning.tool.experiments.natural_press evaluate \
  --checkpoint runs/natural_press_v3/middle_E0_100/J/final.pt \
  --free-v9 --out runs/natural_press_v3/middle_E0_100_free
```

로컬 Isaac Gym 실행기 환경에서는 위 `python`을 프로젝트의 `scripts/tab2body.py run -m ...` 방식으로 호출한다. 최초 import는 Isaac Gym→Torch 순서다. 출력은 새 경로만 허용한다. E1~E4는 조건만 바꿔 fresh 학습하며 서로의 모델/Adam을 암묵 이전하지 않는다. resume는 저장된 조건·분포·축·입력 SHA·PPO identity를 엄격히 유지한다.

resume의 `--updates`는 이번에 **추가할 반복 수**다. 최초 블록과 다른 길이도 공식 runner의 수동 예산 확장으로 허용하지만 최초 planned_transitions/full_song_after 노출 문턱은 다시 계산하지 않는다. 예를 들어100회 모델에 `--updates 100`을 지정하면 누적200회까지 진행한다.

기본 evaluate는 저장된 조건에서32환경의 최초 episode를 모은다. `--free-v9`는 먼저 같은 v3의 원본 identity/입력을 검사하고 활성 mask만 변경한0업데이트 모델을 `model_only/J`에 만든 뒤, 원래 v9/full33의 공식 평가를 `evaluation/`에 저장한다. 이는 학습이나 원본 checkpoint 재개가 아니다. 물리 tick/optimizer update0·mask 외 가중치 exact를 확인한다. 실패도32 분모에 포함한다. `render`도 같은 저장본/선택적 free 이전을 사용한다.

CPU 검사는 `python -m unittest guitar_learning.tests.test_natural_press_runtime -v`다. native GPU 학습·재개·최초32 평가 smoke와 별도 검수 후에만 장기 실험을 진행한다.
