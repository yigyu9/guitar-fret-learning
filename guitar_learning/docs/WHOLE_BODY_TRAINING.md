# 전신 37축 지지 학습 v1

전신 학습 정책을 독립 경로로 추가했다. 압현 v5와 compact 타현의 기존 소스·실험·보상·PD·접촉 조건은 수정하지 않았다. 타현은 이미 상태450·목표79×2·출력27, 학습·평가·렌더까지 구현되어 있다.

## 구현 범위

현재 전신 과제는 **인간 Root 고정·자유 기타·v9 준비 자세에서 양손을 기준 자세로 유지하며 전신 지지를 학습**하는 첫 단계다. 기존 지지 제어 위에 정책이 관절 목표각 보정을 더한다. 세 정책 공동 실행, 움직이는 손에 대한 지지 적응, 자유 Root 균형, 학습 성능 향상은 아직 검증하지 않았다.

| 파일 | 역할 |
| --- | --- |
| [gpu/whole_body.py](../gpu/whole_body.py) | 상태·보상·종료·에피소드 지표 |
| [gpu/whole_body_control.py](../gpu/whole_body_control.py) | 전신37축 소유권, 기존 유한 지지 제어에 목표각 보정 연결 |
| [training/whole_body.py](../training/whole_body.py) | 상태 전용 Actor–Critic, Actor 전용 추론 |
| [training/whole_body_runner.py](../training/whole_body_runner.py) | GPU 장면·경험 수집·공용 PPO·저장/재개·평가 |
| [tool/training/train_whole_body.py](../tool/training/train_whole_body.py) | 실행 명령 |

## 관측과 신경망

원안480차원에 종료 조건의 내부 상태4개를 추가하여 **484차원**이다. 목표 입력은 없다.

| 상태 블록 | 차원 |
| --- | --- |
| 관절 기준각 차이·속도·목표각 추종 오차 | 315 |
| 이전 전신 행동 | 37 |
| 골반 기준 기타·기타 기준 양손 손목 | 45 |
| 접촉 플래그 | 10 |
| 초기 대비 기타 위치·회전벡터·양발 이동 | 12 |
| 골반의 중력 방향·선속도·각속도·높이 | 10 |
| 골반 기준 양발 상태 | 30 |
| 신체+기타 질량중심 위치·상대속도 | 6 |
| 가슴·오른상완·오른허벅지·양발 접촉 합력 | 15 |
| 상체 지지·좌우 발의 연속 접촉 상실 시간 | 3 |
| 남은 과제 시간 | 1 |
| 합계 | **484** |

질량중심은 인간과 논리 기타 몸체의 소스 질량·COM으로 계산하고 의자를 제외한다. 기타39개 논리 몸체의 질량을 합산한 뒤 실제 단일 강체의 전체 질량을 다시 더하지 않는다. 접촉 합력은 특정 기타/지면 접촉쌍의 힘이나 실제 현 압력을 인증하지 않는다.

```text
Actor:  상태484 → 256 → 256 → 512 → 256 → 37
Critic: 상태484 → 256 → 256 → 256 → 256 → 보상 가치1 / 비용 가치1
```

Actor와 Critic은 별도의 인코더를 사용한다. 은닉층은 Tanh, 행동은 tanh Gaussian, 초기 잠재 표준편차는 exp(-3)이다. 실제 출력은37축이며 기존 PPO의39차원 전달 규격에는 두 개의 고정0을 붙인다. 행동 확률·엔트로피·KL은37축만 사용한다. `actor_action()`은 Critic을 계산하지 않고37축만 반환하며 평가 실행이 이 경로를 사용한다.

## 제어

소유권은 몸통9 + 오른쪽 흉곽/어깨6 + 목/머리6 + 하체16 = 37축이다. 왼손33·오른손27·영범위8축과 겹치지 않는다.

기존 유한 지지 제어가 만든 기준 목표각에 최대 **±0.10rad**의 정책 잔차를 더하고 기존 관절 속도·native 범위 제한을 적용한다. 실제 관절각이나 기타 상태를 매 tick 덮어쓰지 않는다. PD·힘 상한·중력 보상·가슴/오른상완 지지·발 IK·48개 position/57개 effort 구동 분할을 보존한다.

발 IK 계산의 이전 기준과 정책이 적용된 이전 명령을 별도로 저장한다. 따라서 일정한 정책 출력을 반복해도 잔차가 계속 누적되지 않는다. 0 행동은 속도 제한을 지키며 기존 지지 제어의 기준 명령으로 돌아간다. 이는 **기존 지지 제어 위의 잔차 정책**이며37축을 정책만으로 구동하는 시스템이라는 뜻은 아니다.

## 보상과 종료

다음 계수는 새 전신 과제를 위한 초기 설계값이며 최적화되거나 성능이 입증된 값이 아니다. 양의 항은 실제240Hz 표본마다 시간 적분한다.

| 항 | 계산 |
| --- | --- |
| 기타 자세 | 초당 최대0.5, exp(-위치오차제곱/0.02² - 회전벡터제곱/0.15²) |
| 양발 접촉 | 두 발의 접촉 후보가 모두 있을 때 초당0.2 |
| 상체 지지 | 기존 세 지지 후보 중 하나 이상 있을 때 초당0.2 |
| 전신 자세 | 초당 최대0.1, 37축 준비 기준각 오차의 평균제곱을0.20rad 척도로 감쇠 |
| 행동 변화 | 60Hz마다 -0.01 × 평균(현재행동-이전행동)² / 60 |

물리 비용은 기존 기타 이동·회전, 발 이동, 지지 상실의 비용률을240Hz 적분한다. 실패 때는 `5 + 2 × 남은 시간`을 한 번 더 청구하고 해당 tick의 양의 보상을 억제한다. Critic은 보상·비용을 별도로 추정하며 PPO는 고정 가중치1의 보상 우위−비용 우위를 사용한다.

실패 기준은 기존 기타 이동8cm, 회전0.35rad, 발 이동4cm, 접촉 상실0.25초 초과, 관절속도50rad/s 초과, 지지 제어 무효다. 비유한 상태·인증되지 않은 제어는 실행 오류로 중단한다. 정상 과제 종료와 물리 실패는 종료로 기록하며, 시간표 끝을 학습 수집 구간 끝과 혼동하지 않는다. H32 경계에서는 초기화하지 않고 종료 환경만 초기화한다.

`safe_completion`은 정해진 시간까지 물리 실패 없이 끝낸 지표다. 음악 수행이나 자유 균형 성공을 뜻하지 않는다. 각 에피소드에는 실패 원인, 항별 보상, 누적 비용,37축 관절 추종 RMSE와 최대 오차를 저장한다.

## 실행 명령

프로젝트 루트에서 사용한다. 물리 학습은 명시적인 CUDA 장치가 필요하며 CPU 물리로 자동 대체하지 않는다. 다른 실험이 사용하는 GPU에서 동시에 실행하지 않는다. 다음 명령은 준비된 실행 예시이며 이번 구현 검증에서는 GPU 학습을 시작하지 않았다.

```bash
# CPU에서 설정만 확인
python -m guitar_learning.tool.training.train_whole_body inspect

# GPU 확보 후 작은 실제 물리·학습 검증
python scripts/tab2body.py run -m guitar_learning.tool.training.train_whole_body train \
  --device cuda:0 --num-envs 4 --horizon 32 --updates 2 \
  --duration-s 2 --out runs/whole_body_support_v1_smoke

# 같은 설정·입력·소스에서 추가 학습. --updates는 추가 횟수
python scripts/tab2body.py run -m guitar_learning.tool.training.train_whole_body train \
  --device cuda:0 --num-envs 4 --horizon 32 --updates 2 \
  --duration-s 2 --resume runs/whole_body_support_v1_smoke/final.pt \
  --out runs/whole_body_support_v1_resume

# 결정론적 Actor로 각 환경 첫 에피소드 평가
python scripts/tab2body.py run -m guitar_learning.tool.training.train_whole_body evaluate \
  runs/whole_body_support_v1_smoke/final.pt --out runs/whole_body_support_v1_eval
```

기본값은128환경·H32·100업데이트·10초 과제다. Actor/가치 학습률은3e-5/3e-4, reward/cost 할인율0.99/1, GAE0.98, PPO clip0.2, epoch2, minibatch4096이다. 실행마다 존재하지 않는 새 출력 디렉토리를 사용한다.

학습 출력은 `initial.pt`, `checkpoint_*.pt`, `final.pt`, `settings.json`, `training_contract.json`, `inputs_before.json`, `learning_metrics.jsonl`, `episodes.jsonl`, `status.json`, `report.json`이다. 평가 결과는 `evaluation.json`에 첫 에피소드 전체 분모와 실패를 포함해 기록한다. 재개는 정책·optimizer·난수를 복원하고 물리 장면은 새 준비 에피소드에서 시작한다. 입력·소스 SHA, 설정, 전체 관측·제어·보상·PPO identity 불일치를 거부한다. 다른 손 정책이나 구형 전신 CPU 제어 모델을 자동 이전하지 않는다.

타현의 기존 실행은 다음과 같다.

```bash
python scripts/tab2body.py run -m guitar_learning.tool.experiments.compact_strike train \
  --song 00_SS1-68-E_comp --num-envs 4 --horizon 32 --updates 2 \
  --out runs/compact_strike_smoke
```

이 명령 역시 GPU를 확보한 뒤 별도로 실행한다. 전신·타현의 물리 실행, 학습 수렴, 실제 연주 성능은 CPU 검사와 구분한다.
