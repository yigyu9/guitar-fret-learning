# 현재 guitar_learning의 타현 구조와 코드 지도

확인 기준: 2026-11-04 프로젝트 작업 트리. 이 문서는 과거 Strike-v2를 참고하여 현재 타현 작업을 이어받는 연구원을 위한 안내다. **현행 소스는 프로젝트 루트의 `guitar_learning/`에 있으며, 이 패키지의 `tab2body/`와 별도 구현이다.** 패키지만 다른 컴퓨터로 복사하면 아래 현행 소스 링크는 연결되지 않으므로 현재 프로젝트 코드·자산·검수된 입력도 별도로 확보해야 한다.

현재 프로젝트 루트는 `/home/ajou/yigyu/3`이다. 아래 파일 경로는 이 루트를 기준으로 읽는다. 함수·클래스 이름을 함께 적어 이후 행 번호가 달라져도 찾을 수 있게 했다. 확인한 소스 SHA와 함수의 시작 행은 [소스 위치 기록](../verification/current_guitar_learning_sources.json)에 있다.

## 1. 전체 프레임워크에서 타현이 맡는 부분

전체 설계는 압현33축·타현27축·전신37축의 정책을 같은 물리 장면에서 운용하는 구조다. 타현은 줄·방향·시각에 따라 피크를 움직이며, 스트럼과 다음 목표를 위한 분리·회복을 처리한다. 오른쪽 흉곽·어깨의6축은 전신 역할에 포함되고 타현27축에는 들어가지 않는다.

현재 압현과 타현은 **각각의 실행·학습 경로**를 갖는다. 전신은 별도의 준비 자세 지지 학습 경로가 추가되었으며, 세 정책의97축 공동 실행·공동 학습은 아직 연결하지 않았다. 현재 타현 실행에서 정책이 담당하지 않는 관절은 기존 유지·지지 제어를 사용한다.

```text
검수된 곡 번들: 오디오·운지·타현 계획·manifest
    → song/strike_task.py: 단일 타현·스트럼 시간표
    → gpu/compact_strike.py: 실제 상태 + 현재/다음 목표 관측
    → training/compact_strike.py: Actor가27축 행동 선택
    → tool/experiments/right27/control.py: 실제 관절 목표각
    → gpu/control.py + gpu/scene.py: 유한 구동·240Hz 물리
    → gpu/strike_events.py: 교차 승인·순서·시각·회복 원장
    → gpu/strike_reward.py: 보상 / 환경의 물리 비용·종료
    → training/rollout.py: 경험 수집
    → training/ppo.py: PPO로 Actor와 보상·비용 Critic 갱신
```

정책 주기는60Hz이고 한 행동마다 실제 물리 표본4개를240Hz로 받는다. 보상·종료·원장은 환경이 계산한다. 정책이 각 단계의 정답 목표각을 외부에서 받아 실행하는 진단 제어와는 구분한다.

## 2. 먼저 읽을 핵심 파일

| 순서 | 현행 파일 | 읽을 클래스·함수 | 담당 내용 |
| --- | --- | --- | --- |
| 1 | [tool/experiments/compact_strike.py](../../../../guitar_learning/tool/experiments/compact_strike.py) | `build_settings()`, `train()`, `runtime()` | 전용 설정과 학습 진입점. 실제 타현 환경·제어기·정책·PPO를 공용 실행기에 연결 |
| 2 | [song/strike_task.py](../../../../guitar_learning/song/strike_task.py) | `StrikeEvent`, `StrikeTask`, `load_strike_task()` | 검수된 번들을 단일 타현·스트럼 이벤트로 읽고 출처·시간·주법 검증 |
| 3 | [gpu/compact_strike.py](../../../../guitar_learning/gpu/compact_strike.py) | `STATE_FIELDS`, `GOAL_FIELDS`, `observation()`, `_goals()` | 상태450 및 목표79×2의 실제 조립·정규화·마스크 |
| 4 | [training/compact_strike.py](../../../../guitar_learning/training/compact_strike.py) | `CompactStrikeEncoder`, `CompactStrikePolicy`, `forward()` | 상태·목표 분리 인코더,27축 Actor, 보상·비용 Critic |
| 5 | [gpu/compact_strike.py](../../../../guitar_learning/gpu/compact_strike.py) | `_snapshot()`, `_crossings()`, `substep()` | 실제 피크 이동 선분의 교차·방향·깊이·재타현 가능 상태 측정 |
| 6 | [gpu/strike_events.py](../../../../guitar_learning/gpu/strike_events.py) | `StrikeLedger.cross()`, `update_ready()`, `advance()`, `update_recovery()` | 줄별 승인·오타현·누락·순서·준비·회복·중복 보상 방지 |
| 7 | [gpu/strike_reward.py](../../../../guitar_learning/gpu/strike_reward.py) | `S3_WEIGHTS`, `STRIKE_REWARD_CONTRACT`, `compute_s3_reward()` | S3 계수와 현재 원장에 적용되는 항별 보상 계산 |
| 8 | [tool/experiments/right27/control.py](../../../../guitar_learning/tool/experiments/right27/control.py) | `ACTION_NAMES`, `Right27Controller.targets()` |27축을 native105 목표에 배치, 손가락 직접 목표각·속도 제한 |

`compact_strike.py`라는 이름이 환경·정책·진입점의 세 위치에 있다. `gpu/`는 관측과 판정, `training/`은 신경망, `tool/experiments/`는 실행 연결을 담당한다.

## 3. 목표 입력과 관측을 고치는 위치

현재 `load_strike_task()`는 임의의 목표 사전을 바로 받지 않고 **등록된 곡 번들**을 읽는다. 기본 입력은 `data/song_bundles/00_SS1-68-E_comp/`이며 manifest에 기록된 파일 SHA·크기와 오디오·운지·계획의 대응을 검사한다. 단일 타현과 스트럼을 지원하고 `alternate_restrike`는 명시적으로 거부한다.

이벤트에는 발음할 줄, 물리적으로 통과할 줄과 순서, 방향, 줄별 시간 offset, 스윕 길이가 들어간다. 런타임 줄 인덱스는0=1번 줄,5=6번 줄이며 방향은down=+1,up=-1이다. 기본 준비3초와 말미0.5초를 시간표에 포함한다.

입력 전처리의 추가 위치는 다음과 같다. 과거 패키지에서 만든 plan 파일을 현행 학습에 직접 넣는 CLI는 없으므로 등록 번들 계약을 확인한다.

| 파일 | 읽을 부분 | 역할 |
| --- | --- | --- |
| [tool/build_strike_training_data.py](../../../../guitar_learning/tool/build_strike_training_data.py) | `build_strike_training_data()` | 원시 타현 목표 자료 작성 |
| [tool/build_strike_plan.py](../../../../guitar_learning/tool/build_strike_plan.py) | `build_strike_plan()` | 목표 검증 후 계획 생성 도구 |
| [tool/_strike_goal_compiler.py](../../../../guitar_learning/tool/_strike_goal_compiler.py) | `compile_strike_events()`, `strike_plan_document()` | 원시 목표를 제스처로 묶고 방향·전환·줄별 offset을 계산해 계획 문서 작성 |
| [score/strike_goal_compiler.py](../../../../guitar_learning/score/strike_goal_compiler.py) | `CompiledStrikeEvent`, `compiled_strike_goal_from_plan_document()` | 계획 자료형·줄별 순서·전환 의미 해석 |
| [score/canonical.py](../../../../guitar_learning/score/canonical.py) | `compile_song_bundle_events()`, `validate_timeline()` | 번들 전체의 표준 이벤트와 시간표 검증 |

상태450은 전신 관절315 + 이전 행동27 + 기타/손목/피크 상대 상태45 + 접촉10 + 초기 대비 변화12 + 줄별 타현18 + 준비/회복4 + 골반9 + 접촉 상실 타이머3 + 진행 상태7이다.

목표79는 기본 목표16 + 제스처2 + 줄별 계획·진행36 + 사건 진행19 + 회복 경로6이다. `current_event_including_recovery`와 `next_event`의2슬롯을 사용한다. **한 슬롯 안에 스트럼 최대6줄의 정보가 들어가므로 두 슬롯을 두 줄로 해석하지 않는다.**

관측을 확장한다면 `STATE_FIELDS/STATE_SCALES`, `GOAL_FIELDS/GOAL_SCALES`, `_goals()/observation()`, 정책 생성자의 계약 검사, 진입점의 `configuration()` 및 관련 검사를 함께 확인한다. 입력 차원만 바꾸고 기존 모델을 같은 계약으로 재개하지 않는다.

## 4. 신경망·학습 방법·실제 출력

신경망은 MLP 기반 Actor–Critic이고 학습 알고리즘은 PPO다. 상태 인코더와 목표 인코더를 별도로 사용한다.

```text
상태450 → 256 → 256 ────────────────────┐
                                       ├→ 결합384 → 512 → 256 → 평균27
현재/다음 목표79 → 공유64 → 64, 각2개 ──┘

Critic: 별도 상태·목표 인코더 → 결합384 → 256 → 256 → 보상 가치1 / 비용 가치1
```

은닉층은Tanh이고 attention·순환망은 없다. 목표 인코더는 두 슬롯 사이에서 공유하지만 Actor와 Critic의 인코더는 분리한다. 빈 목표는 인코딩 후에도 마스크를 적용해0으로 만든다. 학습 시 행동은tanh Gaussian이고 초기 잠재 표준편차는exp(-3)다. `--size`는 기록되지만 compact 신경망의 폭을 바꾸지 않는다.

실제 학습 축은 **오른손 손가락21 + 오른쪽 팔꿈치3 + 손목3 = 27**이다. 공용 PPO와의 전달 벡터는39칸이며 앞12칸은0, 나머지27칸만 행동 확률·엔트로피·KL에 참여한다. 이에 관한 `act()/evaluate()/log_probability()/analytic_kl()`은 [right27/policy.py](../../../../guitar_learning/tool/experiments/right27/policy.py)의 `Right27Policy`에서 재사용한다. 그 파일의 과거 attention 인코더를 compact 신경망의 구조로 혼동하지 않는다.

평가 행동은 `tanh(mean)`을 사용한다. 제어 행동은 Actor의 출력으로 결정되며 Critic의 값은 학습을 돕는다. 다만 현행 타현은 공통 `forward()`에서 두 경로를 함께 계산하므로, 평가 때 Critic 계산 자체를 생략하는 전용 경로까지 구현됐다는 의미는 아니다.

## 5. 실제 타현 판정과 보상 연결

`CompactStrikeEnvironment`의 `_crossings()`가 실제240Hz 피크 이동 선분을 측정한다. 같은 줄을 다시 승인하려면 최소2개 물리 step과3mm 분리가 필요하다. `StrikeLedger.cross()`는 계획된 다음 줄·방향·순서·미승인 상태를 검사하고 오타현·중복·순서 위반을 기록한다. 스트럼은 발음 줄뿐 아니라 계획한 전체 통과 줄을 순서대로 지나야 한다.

clean 완료에는 준비 자격, 오류 없는 통과, 줄별 시각 오차±50ms가 필요하다. 현재 준비 자격은 초기 준비 조건을 얻으면 에피소드 동안 유지되는 방식이다. 매 이벤트마다 준비0.1초를 새로 요구하는 방식으로 읽지 않는다. 분리·재무장·경로 여유와 회복 시간은 `update_recovery()` 및 환경의 단계 계산을 확인한다.

`gpu/strike_reward.py`는 과거 고정 기타 S3 계수를 바탕으로 준비·통과 시점·스트럼 진행/완료·회복·오타현/누락 등을 계산한다. `end_control()`은 이를 환경의 물리 비용 및 종료와 연결한다. 과거의 모든 보상 수식·단계별 커리큘럼을 그대로 복제한 것은 아니다. 현행은 고정 S3 조건으로 전체 타현 과제를 학습하며 과거9단계 커리큘럼은 연결하지 않았다.

접촉·교차 측정은 기하와 몸체 합력을 사용하는 대리 지표다. 이 경로가 왼손 압현 성공, 실제 피크 파지력, 현 진동 또는 생성 음의 품질까지 판단하는 것은 아니다.

## 6. 공용 물리·제어·PPO에서 연결되는 부분

| 현행 파일 | 읽을 부분 | 타현과의 연결 |
| --- | --- | --- |
| [gpu/scene.py](../../../../guitar_learning/gpu/scene.py) | `GpuScene`, `reset()`, `step()` | 인간Root고정·자유 기타·035/v14 준비 상태·native 물리 |
| [gpu/control.py](../../../../guitar_learning/gpu/control.py) | `BatchedController.targets()/efforts()` | 기존 PD·중력 보상·가슴/상완 지지·발 보정·힘 상한 |
| [training/rollout.py](../../../../guitar_learning/training/rollout.py) | `GpuPool.step()/reset()`, `TensorCollector.collect()` | 네 물리 표본 수집, 종료 관측과 다음 가치 기록, 종료 환경만 초기화 |
| [training/ppo.py](../../../../guitar_learning/training/ppo.py) | `PPOConfig`, `DecisionPPOTrainer`, `compute_decision_gae()` | 보상·비용 가치, GAE, clipped PPO, KL 검사, optimizer·난수 저장 |
| [tool/training/legacy_gpu_runner.py](../../../../guitar_learning/tool/training/legacy_gpu_runner.py) | `run()` | 현행 compact 진입점이 재사용하는 반복 학습·로그·저장 실행기 |
| [portability.py](../../../../guitar_learning/portability.py) | `checkpoint_inputs()`, `validate_checkpoint_inputs()` | 소스·입력 SHA와 설정·모델 identity 검증 |

전용 진입점의 `runtime()`은 해당 명령 프로세스 안에서 공용 실행기의 factory를 타현 전용으로 바꾸고 종료 시 복원한다. 압현 기본 진입점인 `guitar_learning.train`이 자동으로 이 타현 정책을 만드는 구조는 아니다.

또한 [gpu/right_strike_environment.py](../../../../guitar_learning/gpu/right_strike_environment.py)의 `RightStrikeEnvironment`는 지정된 한 줄의 준비·교차·회복을 기록하는 진단 경로다. 이름이 비슷하지만 현재 단일 타현·스트럼 학습의 환경은 `gpu/compact_strike.py`의 `CompactStrikeEnvironment`다.

## 7. 학습·재개·평가·영상 명령

프로젝트 루트에서 실행한다. 현재 compact 타현 실행 설정은 `cuda:0`을 사용하며 `--device` 선택 옵션은 없다. 다른 실험이 사용하는 같은 GPU에서 동시에 실행하지 않는다. 아래는 실행 안내이며 이 문서 추가 중 GPU 학습을 수행한 것은 아니다.

```bash
python scripts/tab2body.py run -m guitar_learning.tool.experiments.compact_strike train \
  --song 00_SS1-68-E_comp --num-envs 4 --horizon 32 --updates 2 \
  --out runs/compact_strike_handoff_smoke

python scripts/tab2body.py run -m guitar_learning.tool.experiments.compact_strike train \
  --resume runs/compact_strike_handoff_smoke/final.pt --updates 2 \
  --out runs/compact_strike_handoff_resume

python scripts/tab2body.py run -m guitar_learning.tool.experiments.compact_strike evaluate \
  runs/compact_strike_handoff_smoke/final.pt --num-envs 4 \
  --out runs/compact_strike_handoff_eval

python scripts/tab2body.py run -m guitar_learning.tool.experiments.compact_strike render \
  runs/compact_strike_handoff_smoke/final.pt --num-envs 4 \
  --out runs/compact_strike_handoff_video
```

출력은 매번 존재하지 않는 새 디렉토리를 지정한다. 최종 모델은 지정한 출력 바로 아래의 `final.pt`이며 압현 경로의 `J/` 하위와 구분한다. 평가는 각 환경의 첫 에피소드를 집계하고 영상은 미리 지정한 환경0을 기록한다. 실패를 포함한 전체 분모를 확인한다.

`read_checkpoint()`는 물리 장면을 만들기 전에 현재 소스·입력SHA·저장 설정·전체policy/control 계약을 대조한다. 연구 중 보상·관측·제어를 바꾼 경우 새 계약·새 실험으로 구분하며, 과거 checkpoint를 통과시키기 위해 검증을 비활성화하지 않는다.

## 8. 과거 코드와 현재 코드의 차이

| 항목 | 이 패키지의 과거 Strike-v2 | 현재 guitar_learning compact 타현 |
| --- | --- | --- |
| 기타·신체 | 고정 기타 기준의 과거 환경 | 인간Root고정·자유 기타·기존 유한 지지 제어 |
| 정책 축 | 어깨3+팔꿈치3+손목3+손21 =30 | 팔꿈치3+손목3+손21 =27 |
| 관측과 목표 |303차원,11개 의미 블록 | 상태450, 목표79×2 |
| 인코더 | 블록별 인코딩 합계552 | 상태256 + 목표64×2 =384 |
| 가치 추정 | 가치1 | 보상 가치1 + 비용 가치1 |
| 보상·진행 | 과거 단계별 학습·S3 등 | 고정 S3 계수 기반의 현재 사건 원장 |
| 재개 | 과거 자체 identity | 현행 전용 identity·입력/소스 계약 |

현재 타현 연구의 변경은 위 코드 지도에서 담당 부분을 찾아 진행한다. 기본 압현·전신 경로와 공용 물리 코드를 수정해야 하는 경우 영향 범위를 별도로 검토한다. 개별 타현의 성공과 압현·전신을 합친 연주 성공은 따로 평가해야 한다.

## 9. CPU 검사와 구현 상태 확인

현재 프로젝트의 관련 검사는 다음 명령으로 확인할 수 있다. 이 패키지 자체의 과거 검사 명령인 `tools/verify_cpu.py`와 구분한다.

```bash
CUDA_VISIBLE_DEVICES='' python -m unittest \
  guitar_learning.tests.test_compact_strike_entry \
  guitar_learning.tests.test_compact_strike_policy \
  guitar_learning.tests.test_compact_strike_environment \
  guitar_learning.tests.test_strike_task \
  guitar_learning.tests.test_strike_events \
  guitar_learning.tests.test_strike_reward -v
```

이6개 모듈의63검사는 앞선 구현 확인에서 통과했다. [초기 구현 검증 기록](../../../plans/compact_strike_20261104/검증.json)에도 신규63개와 재사용12개를 포함한 당시 검증 범위가 남아 있다. 이번 문서 추가에서는 코드 위치·SHA·링크·명령 형식을 대조했으며 GPU 학습은 실행하지 않았다. CPU 계산·PPO 업데이트·저장복원 검사와 실제 GPU 물리·정책 성능은 구분한다. 세 정책 공동 학습을 이어갈 때에는 공통 초기 자세, 음악 시계,97축 명령 배치, 공동 평가와 경험 수집이 추가로 필요하다.
