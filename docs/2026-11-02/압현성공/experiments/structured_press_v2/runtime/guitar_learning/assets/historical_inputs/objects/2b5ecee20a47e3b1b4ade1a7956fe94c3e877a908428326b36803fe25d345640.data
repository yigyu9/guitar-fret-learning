# 성공 궤적에서 초기화한 손별 학습

현재 실행 진입점은 `guitar_learning.tool.training.train_imitation_ppo_v2`다. 실제 물리에서 성공했던 한 손의 행동을 Actor에 먼저 학습시키고, 학습된 정책을 같은 시뮬레이터에서 검증한 뒤 PPO로 보완한다. 무작위 정책이 접촉을 발견할 때까지 기다리는 문제를 줄이기 위한 초기화다. 두 손은 별도로 학습한다.

[이번 실행·결과 정본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/README.md) · [계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_imitation_training_20261018.md).

## 환경과 전달 범위

상태505, 이벤트64×24, 우선 이벤트2×24, 행동39(LH33/RH6), medium 모델2,920,528개 파라미터는 기존 단계 환경과 같다. 반대 손은 행동0의 기준 목표를 유지한다. 전신을 관측하지만 정책이105축을 모두 직접 출력하지 않는다. Root고정·하체유한제어·105/97/8·기타자유/중력ON/스트랩OFF·손 준비2초와 기존 물성/접촉/제어/종료 조건을 유지한다.

이번 profile은 첫 단음(물리2번줄·7프렛·약지·down), 왼손 `hold`, 오른손 `cross`에 한정한다. 왼손은 실제 성공에도 distal원점15mm조건을 만족하지 않았으므로 원점거리 접근 보상을0으로 한다. 실제 native 접촉 후보와 연속50ms 성공 조건은 유지한다. 오른손 guide는 기존 허용 타현 영역 안에서 검증했던 y−.36m/depth4mm/앞뒤8mm를 사용한다. 기존 속도·방향·깊이·유한현범위·재준비 판정을 유지한다. 두 변경 모두 계약에 명시한다.

교사 행동을 이 profile에서 다시 실제 재생하여 **행동 직전 관측**을 수집한다. 사람 motion 데이터가 아니며, 데이터240행의 행동과 관측을 학습했다는 사실만으로 실제 성공이라고 하지 않는다.

BC는 해당 손의 Actor 인코더·출력만 학습한다. Critic·반대 손·표준편차는 BC에서 최적화하지 않는다. PPO 초기화에서는 활성 Actor와 명시한 표준편차만 복사하며, Critic·optimizer·업데이트 counter는 새로 구성한다. 별도 `guitar_learning.imitation.v1` 형식의 `actor_initialization.pt`에 데이터 SHA·손·구조·계약·fit 결과를 저장한다. BC 수치 오차 목표와 실제 물리 성공은 별도 지표다.

PPO는 BC의 해당 Actor와 명시한 std.02를 불러온 다음 새 Critic·optimizer·업데이트0에서 시작한다. `initial.pt`와 `actor_initialization.json`으로 출발점을 남긴다. 같은 PPO 실행의 중단 복구는 엄격한 기존 체크포인트 검증을 사용한다. BC초기화와 PPO resume를 혼동하지 않는다.

## 실제 실행

이번 설정은 양손 각각2환경·240tick·24업데이트 상한·soft wall1800초, actor_lr1e−5, cost_weight1, 초기std.02다. 성공 초기 모델을 망가뜨리지 않도록 작은 탐색과 업데이트로 시작한 제한 실험이며, 장기 최적값으로 확정한 값은 아니다.

```bash
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.tool.training.train_imitation_ppo_v2 \
  --settings /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/left_ppo_settings_v1.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/새_왼손_초기화_PPO_실행
```

오른손은 `right_ppo_settings_v1.json`을 사용한다. 출력 경로는 새 디렉토리여야 한다. 초기화 파일은 설정의 `actor_initialization`에 절대 경로로 적는다. 같은 실행 복구에만 `--resume /절대/경로/checkpoint.pt`를 추가한다.

학습 후 `evaluate_imitation_v2 --run /절대/학습출력 --role left|right --out /절대/새평가경로`로 실제 결정적 평가2회를 수행한다. BC 자체는 `--run` 대신 `--initialization /절대/actor_initialization.pt`로 검사한다. reward 증가와 탐색 중 성공만으로 최종 모델을 선택하지 않는다. 마지막 PPO가 기능을 잃으면 검증된 초기 BC 모델을 보존한다.

## 파일과 기록

- `guitar_learning/imitation/imitation_environment.py`: 위 profile과 계약.
- `guitar_learning/tool/demonstration/capture_imitation.py`: 기존 성공 행동의 새 profile 실제 재생·데이터 수집.
- `guitar_learning/imitation/imitation.py`, `guitar_learning/tool/training/train_imitation.py`: 데이터 검증·Actor 모방학습·별도 초기화 저장.
- `guitar_learning/imitation/imitation_v2.py`: JSON계약의 list/tuple 표현만 정규화하는 엄격한 Actor전달. 키/값/크기/손/구조와 tensor 검사는 유지한다.
- `guitar_learning/tool/training/train_imitation_ppo_v2.py`: 새 Actor초기화 전달을 PPO에 연결한다. v1 runner는 공용 활성 의존성이다.
- `guitar_learning/tool/evaluation/evaluate_imitation_v2.py`: 실제 정책 행동·매 tick 관측·240Hz 측정·에피소드 결과.
- `guitar_learning/imitation/imitation_io.py`: 준비 자세·자산·실행 소스 SHA 고정과 종료 시 검사.
- `tests/test_imitation*.py`: 실제 코드 경로를 검사한다. 이번 전체 CPU검사207개 통과.

데이터 수집에는 `demonstration.npz`, `trace.json.gz`, `reset.json`, `result.json`을 남긴다. BC에는 초기화 파일·fit.jsonl·report.json을, PPO에는 기존 initial/final/주기 checkpoint·상태·자원·업데이트·전이·episode·재사용 lifecycle 기록을 남긴다. 평가 trace는 `transitions.json.gz`다.

이번 v1 평가의 JSON list/native tuple 비교 거부는 실행 전 실패로 보존했다. v2는 값이 같은 계약의 저장 표현만 정규화한다. 기존5개 파일은 `archive/20261018_before_imitation_contract_v2/`, 작업 이전87개는 `archive/20261018_before_imitation/`에 원 경로/SHA와 함께 보관했다. 현행 공용 의존성은 원 경로를 유지하며 archive를 import하지 않는다.

단일 목표·동일 준비 시작의 접촉 후보/기하 통과 성공은 음악 타이밍, 실제 압력·음향, 다른 곡 일반화, 양손 결합, 왼손 하중 비의존, 초기 자세V3 모든 정밀 조건의 검증을 뜻하지 않는다. 기타 직접 힘·부착·연속 상태 덮어쓰기를 사용하지 않는다.
