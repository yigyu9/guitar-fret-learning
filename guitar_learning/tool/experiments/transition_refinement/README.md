# 전환 학습 보완 경로

현재 단음 A의 준비 보상·유지 성공 기준·탐색·성공자료 재사용을 구현한 새 경로다. 이전 `transition/`과 모든 실행 입력은 보존했다. 구현 전33파일 보관본은 `guitar_learning/archive/20261019_before_transition_refinement/manifest.json`이다.

## 보상과 성공 판정

- 접근 진전은 `press_s <= time < onset_s`에 적용한다. `press_s=0`인 첫2초도 포함한다. 거리 potential의 부호 있는 변화량이며 접촉 성공으로 간주하지 않는다.
- 음 시작 전 마지막0.2초에는 실제 연속 접촉 준비를 보상한다. 단음은 clean 접촉이다. 같은 줄에서 높은 프렛 A가 발음하는 동안 낮은 B를 준비할 때는 A clean+B positive와 해당 증거만 허용하며, 다른 오압현을 면제하지 않는다.
- 단음 유지 성공 보너스는 실제0.5초 구간의90%에 도달해야 한 번 지급한다. Pair는 원래 선언한40%·최소50ms 기준을 유지한다. 준비·발음·해제는 별도 항목이다.
- 해제는 원래 정한 window에서 할당 손가락의 qualified 접촉 부재로 측정한다. 손 전체를 강제로 떼지 않는다. 발음 구간의 오압현·미압현, 공유 행동 변화·물리 안전 비용은 유지한다.
- 위험한60Hz tick의 신규 양성 보상은4개240Hz 표본 모두에서 억제한다.

새 보상은 `refinement_*` 항목이다. **기존 `song_left_success` 보너스는 실제 reward에서 제거한다.** 500차원 관측을 보존하기 위해 옛 SongLedger/history의40% 진행 marker는 남기지만, 현재 성공 판정에는 사용하지 않는다. `reward.refinement`가 활성 항목과 구진단 섹션을 명시한다. 최종 성공은 `transition.successful`/`refinement.successful` 및 `musical_quality.stage_success`다. `song.left_success_count`는 구 진행 진단이다.

## 정책·탐색·PPO

관측500·왼손33/전체39행동·오른손0을 유지한다. 새 정책은 기존±0.0002 평균 제한을 사용하지 않는다. 탐색은 명시된 `min_std/initial_std/max_std`를 사용하며 기본 범위는0.0001~0.05, 예시 초기값0.003이다. 이전 exp(-5) 하한을 상속하지 않는다. 수집과 평가가 같은 Gaussian/tanh 확률 정의를 사용한다.

PPO Actor 손실에 성공자료의 행동 MSE를 함께 더한다. 자료는 **새 결정론적 초기 정책 평가4회에서 실제 성공한 관측·행동**을 모은 것이며, 해당 원자료를 native 음악·안전·관측·새 보상으로 다시 감사한다. 시연은 GAE나 critic 목표에 넣지 않는다. Actor와 log_std의 학습률을 분리하고, 기존 KL 재시도/모델·Adam·RNG 원자적 복원은 유지한다. BC 보조 가중치100·Actor LR1e-7·std LR1e-5·KL0.005는 예시 시작값이며 최적 설정으로 검증한 값이 아니다.

원 BC는 실제 교사·원 모델 증거를 기존 validator로 검증한 뒤 왼손 Actor만 이전한다. Std는 새 설정으로 명시적으로 초기화하고 critic/Adam/PPO 카운터는 새로 시작한다. 허용하는 계약 변경은 `reward.refinement` 추가와 새 정책/탐색 정체성뿐이다. 원래 물리·관측·목표·행동 계약은 정확히 같아야 한다. 과거4회 성공이나 다른 탐색/보상 계약의 성공을 상속하지 않는다.

Checkpoint는 새 정책·PPO schema, 보상 계약, 탐색 범위, BC 가중치/batch/std LR와 전체 성공자료 content SHA를 포함한다. 다른 데이터·계약·설정으로 strict resume하지 않는다. 초기 평가 설정에는4gate가 필요 없지만, PPO와 PPO checkpoint 평가는 정확한 새4gate가 필요하다.

## 실행

프로젝트 루트에서 rl38 환경을 사용한다. 새 결과 경로를 지정하며 기존 결과를 덮어쓰지 않는다. Native 진입점은 Isaac을 Torch/NumPy보다 먼저 import한다.

```bash
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:${LD_LIBRARY_PATH:-}
export PYTHONFAULTHANDLER=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1

# 초기 정책을 독립 실행4회 검증한다. out의 v1을 v2/v3/v4로 바꿔 각각 실행한다.
python -m guitar_learning.tool.experiments.transition_refinement.run eval \
  --settings /home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/configs/baseline_eval.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/native_init_v1

# BC를 고정하고 탐색량별 독립 재생을 비교한다. 학습하지 않는다.
python -m guitar_learning.tool.experiments.transition_refinement.sweep \
  --settings /home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/configs/sweep.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/exploration_sweep_v1 \
  --stds 0 .001 .003 .01 .02 --repeats 3

# 새4gate 통과 후1환경/1update 연결 확인, 또는8환경/8update의 짧은 학습.
python -m guitar_learning.tool.experiments.transition_refinement.run train \
  --settings /home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/configs/training.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/training_v1
```

`training_smoke.json`은1환경/1update 연결 확인용이다. `sweep`의0은 잡음 없는 평가이며 Gaussian 표준편차0을 뜻하지 않는다. 양수 탐색량은 설정 파일과 실제 정책 모두에 적용한다. 단계별로 같은 seed 집합을 사용하되 각 case는 독립 프로세스다. 음악 실패·물리 실패·수치 오류를 구분하고, 오류를 음악 실패나 성공으로 바꾸지 않는다. 소수 반복의 최고 결과를 최적 탐색량이라고 자동 채택하지 않는다.

PPO 모델 평가는 같은 training 설정에 `eval --checkpoint /absolute/model.pt`를 사용한다. `--resume`은 같은 설정과4gate의 PPO 상태 재개다. 표준 stdout/`status.json`/`learning_metrics.jsonl`/`episodes.jsonl`/매update checkpoint를 유지하며, 새 BC MSE·PPO loss·std LR도 기록한다.

Root고정·하체유한제어·105/97/8·기타자유/중력ON/strapOFF·원 gain/제한/속도/안전 종료는 변경하지 않았다. 간헐적SIGFPE의 원인 규명이나 새 음악 성과는 이 구현의 완료와 별도다. 실제 검사·실험 상태는 `docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/`에 기록한다.
