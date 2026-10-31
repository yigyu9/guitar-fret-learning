# 기본 학습과 초기 학습 인터페이스 기록

## 현재 기본 학습 — 2026-10-28 기준

`python -m guitar_learning.train --out NEW`는 GPU 왼손 **finger-skill v3(J 전용)**를 실행한다. 기본값은 medium·128환경·H32·100업데이트·seed7·checkpoint 간격250이다. GPU 물리와 GPU 텐서를 사용하며 CPU 자동 대체는 없다. 실행 환경 설정·재개·평가 명령은 [README](../README.md), 코드 연결은 [CODE_STRUCTURE](CODE_STRUCTURE.md), 출력 해석은 [LOGGING](LOGGING.md)을 따른다.

Isaac Gym을 사용할 수 있는 `rl38` 환경에서 프로젝트 루트를 기준으로 실행한다. 다음은 large·1024환경의 명시적 실행 예시이며 출력 경로는 새 디렉토리여야 한다.

```bash
python -m guitar_learning.train \
  --size large --num-envs 1024 --horizon 32 --updates 3000 \
  --checkpoint-every 250 --seed 7 \
  --out /home/ajou/yigyu/3/runs/left_finger_skill_docs_01
```

저장한035/v14 초기 자세를 에피소드 경계에서 한 번 복원하고 native 대기0초로 시작한다. 물리240Hz·정책60Hz·K1이며 J33 공동 학습을 처음부터 실행한다. BC 초기화를 요구하지 않으며 R/F 단계·자동 단계 전환·단계별 이전 코드는 제거했다. H32는 PPO 수집 경계이며 장면·곡 시계·원장·종료 타이머를 초기화하지 않는다. 처음 계획한 전이 예산의25%를 PPO에 반영한 뒤 다음 reset부터 선택 구간에서67음 전곡으로 전환한다.

상태557(기반552+남은시간1+손목종료4)·이벤트24·우선 토큰8, 출력39 중 왼손33축을 사용한다. 보상은9항목이며 손목·물리 실패는 별도 종료 및 단일 실패 비용으로 처리한다. 실제 모델·로그는 `--out/J/`에 저장한다. 기본 기타는 자유 강체·중력ON·스트랩OFF, Root 고정·하체 유한 제어다. 별도 진단에서 사용한 기타 고정 조건을 기본 설정으로 해석하지 않는다.

기본 연결은 구현24개·초기화8개이며 활성 Python은281개다. CPU·오른손 song과 현행 진단·영상·로그 도구는 유지한다. 과거8실험·전문 환경·구형 CLI·매뉴얼은 [원문·SHA 보관 안내](../archive/20261028_before_legacy_retirement_v1/ARCHIVE_INDEX.md)를 따른다. 아래 명령은 보관한 과거 계약의 설명이며 현재 작업 공간의 실행 명령이 아니다.

## 초기468상태 인터페이스 — 과거 계약

2026-10-19 구조 정리: 이 문서는 초기468상태 학습 계약의 기록이다. 당시 단일환경 `guitar_learning.train` 실행기는 [보관 manifest](../archive/20261019_retired_experiments/manifest.json)에 원문으로 보존했다. 본문의 옛 명령은 원구조를 별도 작업 공간에 복원할 때의 재현 설명이며 현행 실행은 [README](../README.md)를 따른다.

당시 손별 사전학습·전문가 결합 매뉴얼은 [보관 안내](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_legacy_retirement_v1/ARCHIVE_INDEX.md)에서 확인한다. 아래 공유 Actor·통합 보상 구조는 과거 비교·재현 기록이다.

### 당시 병렬·장기 학습 설정

당시 장기 실행은 [PARALLEL_TRAINING.md](/home/ajou/yigyu/3/guitar_learning/docs/PARALLEL_TRAINING.md)를 따른다. 메모리 중단 개선 후 권장 시작값은 N8/독립 CPU PhysX·GPU 정책/medium/H256/batch2048/actor_lr3e-5/initial_std exp(-3)이며, 새 정책은 별도 dense_v2 보상을 사용한다. RAM 감시·진행 출력·검증된 상태의 실패 복구 저장을 추가했다. 과거 N16 선정 근거인 [환경 수5종과 설정3종의 실제 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/README.md)는 음악 매칭0이며 수렴·전체 곡 성공을 뜻하지 않는다. 아래 단일 환경 인터페이스와 수식은 유지한다.

단일 환경 실행 진입점은 [train.py](/home/ajou/yigyu/3/guitar_learning/archive/20261019_retired_experiments/guitar_learning/train.py), 환경 API는 [TrainingEnvironment](/home/ajou/yigyu/3/guitar_learning/core/training_environment.py)다. 정본 음악 목표 → 실제 관측 → 39개 행동 → 유한 관절 제어 → 240Hz 접촉·타현 측정 → 보상/비용 → PPO로 연결했다. 여기서 타현은 피크 마커의 기하 통과이며, 실제 현 압력·진동·음향의 성공 판정은 아니다.

이하의 ‘현재’·‘기본’·옛 명령은 당시468상태 계약을 뜻한다. 현행 기본 실행의 관측·행동·보상·종료·CLI에 적용하지 않는다.

## 환경과 제어

`reset()`은 `(observation, info)`, `step(action39)`은 `(observation, reward, terminated, truncated, info)`를 반환한다. 실제 물리 240Hz, 정책 60Hz이며 각 정책 단계의 네 물리 표본을 모두 측정한다. 안전 임계값을 중간 표본에서 넘었다가 마지막 표본에서 돌아와도 실패로 남긴다. 종료 반환은 현재 60Hz 단계가 끝나는 시점이다.

저장한 준비 자세를 reset 초기값으로 한 번 적용하고 손 준비·안정화 2초 후 음악 시간을 0으로 시작한다. 준비 시간은 1~2초로 선택할 수 있다. 과거 22초 검증을 매 reset마다 반복하지 않는다. 기타의 지속 상태 덮어쓰기나 직접 보조 힘은 사용하지 않는다.

정책 출력은 왼팔 12축·왼손 21축·오른팔꿈치/손목 6축의 **39개 정규화 목표 오프셋**이다. 오른손 파지·상체 지지 등 상체 42축은 준비 완료 목표를 유지한다. 하체 24채널은 기존 유한 접지 제어가 담당한다. 105개 채널을 물리적으로 제어하지만 정책이 모든 관절의 목표를 직접 학습하는 구조는 아직 아니다. Root 고정, 비영범위 97축과 원래 영범위 8축, 자유 기타·중력 ON·스트랩 OFF를 유지한다.

기본 오프셋 반범위는 왼팔 0.35rad, 왼손 0.5rad, 오른팔꿈치/손목 0.25rad다. 기존 관절 한계·목표 변화율·평활화 계수 0.2가 추가 적용된다. 이 범위는 학습 시작값이며 모든 프렛의 도달 가능성이나 큰 탐색 행동에서의 안정성을 보증하지 않는다. 연결 시험은 별도로 명시한 작은 범위 0.002rad를 사용한다.

## 관측

배우와 가치망에는 같은 고정 스케일 관측을 전달한다. 실행 중 이동 평균 정규화는 하지 않는다. 비유한 값은 수집 오류로 중단하고, 유효 값은 명시한 scale로 나눈 뒤 ±10으로 자른다. 정확한 필드명·순서·scale은 실행의 `training_contract.json`에 저장한다.

| 상태 블록 | 차원 | 주요 단위/scale |
| --- | ---: | --- |
| 105관절 준비 목표 대비 각도 | 105 | rad / 1 |
| 105관절 속도 | 105 | rad/s / 10 |
| 현재 제출 목표−실제 관절각 | 105 | rad / 1 |
| 이전 정규화 행동 | 39 | 1 |
| 골반 기준 기타 위치·6D 회전·선속도·각속도 | 15 | m / 0.5, m/s / 1, rad/s / 10 |
| 기타 기준 양 손목·피크·왼손 끝 5개 위치/속도 | 48 | m / 0.5, m/s / 1 |
| 지지 3부위·왼손 5손가락·양발 접촉 | 10 | 실제 양성 raw 접촉 flag |
| 준비 이후 기타 위치/회전 편차 | 6 | m / 0.02, rad / 0.2 |
| 양 발목 준비 위치 편차 | 6 | m / 0.02 |
| 음악 진행·매칭·유지 등 전역 상태 | 8 | 곡 길이·목표 수 등 고정 scale |
| 현별 타현 재준비·측면·대기 상태 | 18 | 1, step |
| 전체 지지·양발 접촉 소실 시간 | 3 | s / 0.25 |
| **합계** | **468** | |

몸체의 COM 선속도와 몸체 원점의 속도를 구분하며, 기타 회전에 따른 상대 속도 항도 포함한다. 손가락 끝 위치는 몸체 원점 proxy다. 접촉 flag는 힘의 크기나 뉴턴 단위 하중이 아니다.

별도로 **64×24 음악 토큰과 bool mask**, 현재/가장 가까운 strict deadline 우선 토큰 **2×24와 mask**를 제공한다. 토큰에는 시작·종료·압현 준비 잔여시간, 현/프렛/손가락/방향, 현재/준비 여부, 50/100ms 매칭, 연속 접촉·유지 시간/비율, 해제, 목표 상대 위치·속도, 마감 시간이 들어간다. 상대 위치 scale은 0.25m, 속도는 1m/s, 주요 시간은 2초다. 목표는 종료 후 해제 확인 창 0.1초까지 남긴다. 용량 초과를 조용히 잘라내지 않는다.

## 음악 목표와 판정

정본은 [05_BN2-131-B_solo](/home/ajou/yigyu/3/data/song_bundles/05_BN2-131-B_solo)다. 기존 정본 compiler와 SHA·이벤트 ID·원 시간 정보를 보존한다. B=명시한 단일 압현음, C=연속 두 이벤트, D=명시한 길이의 연속 구간이다. 앞 1초 preroll 이후 원 타이밍을 사용하며 tempo 변경은 provenance에 기록한다. 단계를 자동으로 올리는 curriculum scheduler는 아직 두지 않았다.

지정 손가락–지정 현/프렛의 양성 실제 접촉과 기하 조건을 압현 후보로 사용한다. 240Hz 구간의 양 끝 모두 후보여야 그 구간의 유지 시간을 적립하며, 실제 발음 목표 시간과 겹친 부분만 더한다. 열린 현은 해당 현을 막는 손가락 접촉을 검사한다. 단순 넥 접촉을 지정 압현 성공으로 취급하지 않는다.

피크는 각 표본의 **현재 기타 좌표계**에서 비교한다. 유한한 현 선분 통과, 횡방향 속도 ≥0.05m/s, 깊이 1~15mm, 기타 로컬 y −0.385~−0.255m 영역을 검사한다. 현에서 3mm 이상 떨어지고 2물리 step 이상 지나야 재준비한다. 통과 시각은 한 물리 구간 안에서 선형 보간한다. 이는 근사 마커 검출이며 연속 충돌 검출이나 현 동역학이 아니다. 몸과 기타가 함께 움직여 상대 위치가 같으면 타현으로 판정하지 않는다.

타현은 현·방향·시간과 압현 후보를 함께 검사하고 동일 통과를 중복 적립하지 않는다. 목표 시각 ±50ms를 strict, ±100ms를 lenient로 따로 집계한다. **지정 목표의 압현 접촉 후보가 소실될 때** 해제를 기록하고, 종료 후 0.1초 안의 필요한 해제에 보상을 준다. 다른 현/프렛으로 이동해 기타 접촉은 남아 있어도 후보가 소실될 수 있으므로, 이것은 왼손 전체의 완전 비접촉 판정이 아니다. 같은 현/프렛/손가락을 계속 쓰는 이어지는 음에는 불필요한 완전 해제를 요구하지 않는다.

**전체 곡에는 미지원 이벤트가 있다.** `event-000042`는 기존 compiler가 같은 이벤트로 묶은 두 음의 `alternate_restrike`다. 이 이벤트를 포함하는 선택과 `--stage full`은 현재 명시적 오류로 거부한다. 원본을 고치거나 해당 음을 누락하지 않았다. 이 복합 이벤트의 표현/타현 분리가 전체 곡 지원의 남은 구현이다.

## 보상·비용·종료

음악 보상은 다음 항의 합이다. 이벤트 보상은 새 사건에 한 번만, 시간 항은 실제 물리 초 단위로 적분한다. 가중치는 초기 학습 설정이며 실험으로 최적화된 값은 아니다.

| 항 | 보상 |
| --- | ---: |
| 새로운 strict 타현 매칭 | +1 |
| 새로운 lenient만 매칭 | +0.25 |
| 매칭되지 않은 유효 기하 타현 | −0.25 |
| strict 마감 경과 후 미스 | −0.5, 목표당 한 번 |
| 압현 후보 실제 유지 | +2 × 유지 초, 목표별 합 |
| 필요한 시점의 실제 해제 | +0.25 |
| 압현 준비~타현 시점 목표 접근 | +0.2 × exp(−(거리/0.03m)²) /초, 해당 목표 평균 |
| 행동 변화 | −0.01 × mean((현재−이전 행동)²) /초 |
| 안정성 실패 | −2, 에피소드당 한 번 |

안정성 비용률은 `(기타 이동/0.02m)² + (기타 회전/0.15rad)² + mean((양발 이동/0.02m)²) + 전체 지지 소실 flag + mean(양발 접촉 소실 flag)`다. 각 1/240초를 곱해 누적하고 실패 시 비용 5를 한 번 더한다. 개별 지지점의 짧은 이탈이나 접촉 분담 변화만으로 실패시키지 않는다. 이 비용은 가치망의 별도 cost return과 PPO 배우 목적에 들어가며 안전을 수학적으로 보장하는 제약은 아니다.

| 종료 조건 | 초기 임계값 |
| --- | --- |
| 준비 상태 대비 기타 이동 | >8cm |
| 기타 회전 | >0.35rad |
| 어느 한 발목의 이동 | >4cm |
| 세 주요 지지점 전체 소실 또는 어느 한쪽 발 접지 소실 | 연속 >0.25초 |
| 실제 관절 속도 | >50rad/s |
| 음악 시간표 종료 | 마지막 음 종료+0.1초 |

안정성 실패/시간표 완료는 `terminated`, 선택한 실행 시간 제한만 `truncated`다. 시간 제한이 있으면 마지막 실제 관측으로 bootstrap하고, 실제 terminal은 bootstrap을 0으로 둔다. 수치 오류·물리 guard 위반·잘못된 표본은 정상 실패 에피소드와 구분해 예외로 중단하고 부분 rollout을 학습하지 않는다. 이 임계값은 V3 초기 자세의 정밀 감사 기준과 별도다.

## 네트워크·PPO·체크포인트

Actor와 Value는 별도 인코더를 쓴다. 각각 상태 인코더 256→256, 공유 이벤트 인코더 128→128, 상태 query 기반 attention, 현재/마감 우선 토큰 연결 후 fusion을 통과한다. 기본 fusion은 **512→512→256**, 출력은 왼손/팔 33과 오른팔꿈치/손목 6이다. 행동은 정규분포 latent를 tanh로 변환하며 log probability에도 변환 Jacobian을 적용한다. 가치 인코더 뒤 reward return과 cost return 두 head를 둔다.

small fusion=256→256→256, medium=512→512→256, large=1024→1024→512다. 관측·입출력·역할은 같고 fusion 크기만 바뀐다. medium/상태468의 실제 파라미터 수는 **1,931,600**이다. GRU·모션 생성 모델은 사용하지 않는다.

PPO 기본값: actor lr 3e−5, value lr 3e−4, reward gamma 0.99, cost gamma 1, GAE lambda 0.95, clip 0.2, epoch 2, minibatch 256, gradient norm 0.5, analytic KL 한도 0.02, 비용 가중치 1이다. KL 초과 시 actor와 Adam을 복원하고 낮춘 학습률로 재시도한다. 업데이트 도중 다른 오류가 나면 전체 정책·가치·optimizer·RNG를 복원한다. 비용 예산을 명시하면 완료한 유효 에피소드에 한해 multiplier를 갱신할 수 있으며, 기본은 고정 가중치다.

train.py의 collector는 단일 환경용이다. terminal/truncation/rollout 경계의 bootstrap을 구분하고 재시작 관측으로 이전 에피소드 가치를 계산하지 않는다. 병렬 수집은 별도 parallel.py와 train_parallel.py에서 구현했으며 같은 bootstrap 원칙과 worker별 부분reset을 적용한다.

체크포인트는 관측·행동·실제 음악 목표·보상·종료·망 크기·PPO 설정과 optimizer/RNG를 함께 저장하고 불일치 시 로드를 거부한다. 기존 파일을 덮어쓰지 않는다. `--resume`은 **PPO/optimizer/RNG를 복원한 새 물리 에피소드**다. PhysX solver 내부 상태를 이어받는 체크포인트가 아니다.

## 실행과 확인 범위

명시한 업데이트 수와 rollout 길이 없이는 학습이 시작되지 않는다. 다음은 작은 행동으로 연결만 확인하는 실행 예다. 출력 디렉토리는 새 경로를 사용한다.

```bash
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
PYTHONDONTWRITEBYTECODE=1 /home/ajou/miniconda3/envs/rl38/bin/python \
  -m guitar_learning.train \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_new_run \
  --stage B --size medium --updates 1 --rollout-steps 96 --action-half-range .002
```

`--action-half-range`를 생략하면 역할별 기본 학습 범위를 사용한다. `--stage C/D`, `--start-event-index`, `--phrase-events`, `--tempo-scale`, `--time-limit`, `--resume`을 명시적으로 선택할 수 있다. 실제 사용한 입력·XML 선언 mesh·소스의 전후 SHA, 관측 계약, native 상태/접촉/보상, rollout, 업데이트 지표와 체크포인트가 출력된다. 매 reset에 과거 검증 실험을 호출하지 않으며 별도 영상 인코딩도 요구하지 않는다.

구현·CPU 검사·실제 연결 결과와 제한은 [이번 작업 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_interface_v1/README.md)에 정리한다. 연결 시험은 음악 연주 성능 평가가 아니다. 기본 행동 범위에서의 도달성·안정성, 보상 가중치/비용 tradeoff, 학습 수렴, 다중 이벤트와 복합 재타현, 다른 곡 일반화가 다음 검증 대상이다.

## 기본 범위 추가 검증

[실제9개 실행과 제한 학습4회 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/README.md): 전체 CPU89개, native2,248전이/8,992물리표본을 확인했다. 일부 큰 왼팔/복합 동작은 기타 이동80mm 한계로 실패했으며, 정책 전후 음악 수행 개선은 없었다. 현재 기본 행동 범위를 모든 조합에 안전한 영역이나 연주 성공 설정으로 사용하지 않는다. 기존 범위·보상·gain을 통과 목적으로 바꾸지 않았다.

새 [validate.py](/home/ajou/yigyu/3/guitar_learning/tool/validate.py)는 `--mode zero/right/left_arm/fingers/all/policy`, `--stage B/C/D`를 받는다. 예를 들어 새 출력 경로와 함께 `--mode right --stage D --seconds 5 --episodes 1`로 진단한다. policy 모드는 `--checkpoint`가 필수이며 환경 계약을 그대로 복원·검사하고 tanh(mean)로 평가한다. 평가 예산은 학습 계약과 별개다. 준비2초부터 종료까지 기록한 [정책 전후 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/media_index.md)도 보존했다.


## 장기 학습 중단 이후 개정

당시 병렬 실행은 N8/H256/batch2048, RAM 여유4GiB 보호,5초 자원 기록,10초 heartbeat,5업데이트 주기 저장과 오류·중단 시 failure_last_valid.pt를 사용한다. 새 dense_v2는 TrainingEnvironment를 상속한 별도환경이며 기존 접촉/음악 성공과 안정성 비용을 유지하고 조기 왼손 접근·움직이는 기타 상대 우손 타현 경로 보상을 더한다. 기존 고정목표 legacy 경로의 계약은 유지한다. 명시한 B단음 pool 선택 시 공통 후보 계약과 실제 episode 목표를 분리해 보존한다. 새 보상이나 pool은 새 정책으로 시작한다. 자세한 보상식·설정·실행·복구·로그 의미는 [PARALLEL_TRAINING.md](/home/ajou/yigyu/3/guitar_learning/docs/PARALLEL_TRAINING.md)에 있다.
