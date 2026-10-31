# 학습 코드 읽는 순서와 작업 영역

2026-10-28 과거 전문 경로 보관 후 기준이다. 실행은 [README](/home/ajou/yigyu/3/guitar_learning/README.md)의 기본 GPU 왼손 `finger-skill` v3를 따른다.

## 먼저 읽을 여섯 파일

| 순서 | 파일 | 이 파일에서 이해할 내용 |
| --- | --- | --- |
| 1 | [training/launch.py](/home/ajou/yigyu/3/guitar_learning/training/launch.py) | 명령 입력, 공통 기본값과 현재 실행 설정 검증 |
| 2 | [training/finger_skill_runner.py](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py) | 구간·전곡 노출 일정, 학습 반복, 저장·엄격 재개·평가 |
| 3 | [training/rollout.py](/home/ajou/yigyu/3/guitar_learning/training/rollout.py) | GPU 장면·환경 구성, 제어 진행, 결정·전이 수집 |
| 4 | [gpu/finger_skill_environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py) | 악구 선택, 시간표, 현재9개 보상·손목 종료·557상태 |
| 5 | [training/policy.py](/home/ajou/yigyu/3/guitar_learning/training/policy.py) | 관측 인코더, 손가락 정책, 행동·가치·확률 계산 |
| 6 | [training/ppo.py](/home/ajou/yigyu/3/guitar_learning/training/ppo.py) | 지속시간 GAE, actor/critic 갱신, KL 보호와 진단 |

최상위 [train.py](/home/ajou/yigyu/3/guitar_learning/train.py)는 실행 진입점이며 `launch.main`을 호출한다. 별도의 start·launch_settings·finger_decisions·gpu_pool·정책 보조 파일을 오갈 필요 없이 위 파일 안에서 영역별 정의를 이어 읽을 수 있다.

```text
train.py → training/launch.py → training/finger_skill_runner.py
                                  ├─ training/rollout.py → gpu/scene.py · control.py
                                  │                        └─ gpu/finger_skill_environment.py
                                  │                             └─ gpu/environment.py
                                  ├─ training/policy.py
                                  ├─ training/ppo.py
                                  └─ training/training_log_io.py
```

기본값은 medium·128환경·H32·100업데이트·seed7·checkpoint 간격250이다. 초기035/v14 자세, GPU 물리240Hz·정책60Hz·K1·J33, 계획 전이 예산25% 이후 다음 reset부터 전곡 전환을 유지한다. 실제 출력은 `--out/J/`에 저장한다.

## 필요할 때 더 읽을 구현

| 작업 영역 | 파일 | 함께 모은 내용 |
| --- | --- | --- |
| 공용 GPU 환경 | [gpu/environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py) | 배치 관측, 접촉·음별 원장, 공용 측정·제어 경계 |
| 접촉 | [gpu/contact.py](/home/ajou/yigyu/3/guitar_learning/gpu/contact.py) | 손끝 패드, 같은 표면점 판정, 엄지 후면 안내, 오압현 원인 |
| 기하·손목 | [gpu/control.py](/home/ajou/yigyu/3/guitar_learning/gpu/control.py), [gpu/contact.py](/home/ajou/yigyu/3/guitar_learning/gpu/contact.py) | 회전·상대속도는 control, 표면·압현면·손목 영역은 contact |
| 손가락 보상 | [gpu/finger_reward.py](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py) | 목표 선택, 대기 자세·관절 모양, source 자세 해석 |
| 물리 장면 | [gpu/scene.py](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py) | 장면 생성·reset, 단일 강체 기타, 선별 손가락 충돌 |
| 물리 제어 | [gpu/control.py](/home/ajou/yigyu/3/guitar_learning/gpu/control.py) | 유한 목표·PD, 하체 유지·기하 근접 제어 |
| 진단 | [gpu/episode_diagnostics.py](/home/ajou/yigyu/3/guitar_learning/gpu/episode_diagnostics.py) | 손가락 자세·회복 창·엄지 지지·움직임 분해·악구 진단 |
| 저장·운영 | [training/training_log_io.py](/home/ajou/yigyu/3/guitar_learning/training/training_log_io.py) | 전이 로그·복구·보고서, GPU 에피소드·checkpoint 기록, 자원 감시 |
| 저수준 기록 | [training/training_log_io.py](/home/ajou/yigyu/3/guitar_learning/training/training_log_io.py) 앞 구역 | Dragon4 JSON, SHA·입력 소스 수집, 파일 저장 |
| 공용 제어 | [core/control.py](/home/ajou/yigyu/3/guitar_learning/core/control.py) | 행동 순서, 관절 목표 계약, 손가락 프로필·목표 속도표 |
| 공용 관측 | [core/geometry.py](/home/ajou/yigyu/3/guitar_learning/core/geometry.py) | CPU 기하·관측 builder, CPU/GPU 공용 관측 상수 |
| 초기 입력 | [runtime/prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/runtime/prepared_reset_v1.py) | 초기 자세·자산·저장 상태의 입력 검증과 복원 helper |
| 곡·악구 | [song/task.py](/home/ajou/yigyu/3/guitar_learning/song/task.py), [finger_phrases.py](/home/ajou/yigyu/3/guitar_learning/song/finger_phrases.py), [curriculum.py](/home/ajou/yigyu/3/guitar_learning/song/curriculum.py) | 음표 자료형·곡 일정·손목 anchor, 악구 표본, CPU/GPU 단계 |
| 입력 기반 | [song/task.py](/home/ajou/yigyu/3/guitar_learning/song/task.py), [score](/home/ajou/yigyu/3/guitar_learning/score), [historical_inputs.py](/home/ajou/yigyu/3/guitar_learning/historical_inputs.py) | 정본 목표·입력 provenance·과거 증거 검증 |
| native 입력 | [native/paths.py](/home/ajou/yigyu/3/guitar_learning/native/paths.py) | 내부화된 자산 경로와 소스 pin |

`policy.py`에는 공유·전문가·손가락 정책이 함께 있다. 현재 기본 학습을 읽을 때는 `Encoder`와 `FingerSkillPolicy`부터 읽으면 된다. `finger_skill_environment.py`는 현재 `FingerSkillEnvironment` 하나로 J 전용 동작을 정의한다. 상위 `TensorSongEnvironment`는 공용 측정·원장 기반이다. `SimplifiedFingerEnvironment`와 R/F 분기는 제거했다. 상태는 기반552+남은시간1+손목종료4=557이며 정책v2·환경v3 계약을 사용한다.

## 파일 수와 연결 범위

| 기준 | 직전 상태 | 현재 보관 정리 후 |
| --- | ---: | ---: |
| 전체 활성 Python(archive 제외) | 474 | 281 |
| 기본 진입점의 정적 의존성 | 32 | 32 |
| 위 항목 중 구현 파일 | 24 | 24 |
| 위 항목 중 패키지 초기화 | 8 | 8 |
| GPU 디렉토리 Python | 8 | 8 |

정적 의존성은 함수·조건문 안의 import도 포함해 같은 방법으로 센 것이다. 한 번의 학습에서 실제 실행한 파일 수와 다르다. 전체 체크포인트 입력 SHA는 여전히 활성281개 Python 전체를 포함한다.

이 기본 경로의 구현24개·패키지 초기화8개에는 역할과 기존 설명 주석을 한글로 작성했다. 파일 SHA는 `training/training_log_io.py`의 `digest`, 정책의 가치망 매개변수 선택은 `Policy.value_parameters`, 장면의 자세·속도 행 변환은 `_body_row`를 공유한다. CPU/GPU의 서로 다른 판정·설정은 각각 유지한다. [중복 정제·한글 주석 검증](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_refinement_ko/README.md).

공용 설정을 읽기 위한 CPU runner import, 관측 상수를 읽기 위한 CPU song 환경/원장 import, 준비 입력을 읽기 위한 CPU native 세션 import를 분리했다. 원문 기능을 보존하면서 기본 GPU 경로의 불필요한 연결을 제거한 것이다.

## 별도 구현과 도구

CPU 접촉·측정·안전은 [core/measurement.py](/home/ajou/yigyu/3/guitar_learning/core/measurement.py)에 모았다. CPU 장면과 headless·persistent 세션, 기존 song·오른손 실행은 각 계약대로 유지한다. CPU `PreparedSession`은 [runtime/native_session.py](/home/ajou/yigyu/3/guitar_learning/runtime/native_session.py)에 있다. 0초 준비는 [runtime/persistent_environment.py](/home/ajou/yigyu/3/guitar_learning/runtime/persistent_environment.py)의 `PreparedFreeGuitarEnvironment` → `PreparedContactEnvironment` → `PreparedPersistentContactEnvironment`에 모았다. 기존 접촉 snapshot과 지속 세션의 생성·reset·실패 정리 순서는 유지하며 song·finger_motion이 이 공용 계층을 사용한다.

`quality/`에는 현재 사용하는 `fretting_quality.py`·`strike_quality.py`를 유지한다. `skills/`·`imitation/`·`timing/`과 quality의 과거 전문6모듈은 보관했다. 공용·전문가·손가락 정책 구현은 `training/policy.py`에 있으며 현재 song 실행에도 사용한다. `tool/`은 기존 song 학습·J 평가·영상·입력·검증 진입점, `tests/`는 현재 회귀 검사다. `tool/experiments/`의 활성 실험은 `short_finger_learning` 하나다. [도구 안내](/home/ajou/yigyu/3/guitar_learning/tool/README.md)를 따른다.

## 보관과 검증

직전474개 Python 중 과거 전문 구현123개·검사/보조70개를 보관해 현재281개를 유지한다. 전문 실험8개·기존 단계별 CLI·`render_timing_video_v1.py`와 전문 매뉴얼6개도 보관했다. [이번 보관 안내](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_legacy_retirement_v1/ARCHIVE_INDEX.md) · [원문 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_legacy_retirement_v1/manifest.json) · [활성 제거 목록](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_legacy_retirement_v1/retired_files.json). 보관본은 당시 구현·계약의 참고 자료이며 현재 명령으로 안내하지 않는다.


변경 전507개 Python과 문서28개는 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_domain_consolidation/manifest.json)에 원래 경로·SHA·대체 파일과 함께 보존했다. 보관본을 현재 코드에서 import하지 않는다.

기존 checkpoint는 경로·소스 SHA가 달라 현재 트리에서 바로 strict 재개·평가할 수 없다. 기존 pin과 입력 검증을 유지한다. [통합 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_domain_consolidation_20261028.md) · [검증 결과](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_domain_consolidation/README.md).

그 외 TRAINING·LOGGING·PARALLEL_TRAINING 문서의 앞부분은 현재 기본 안내, 보관된 전문 문서의 차원·보상·단음 성과는 해당 이전 계약에 관한 기록이다. 이전 계약을 기본 학습의 선행조건으로 적용하지 않는다.


## 현재 추가 통합의 원문과 상세 해설

직전487개 Python과 당시 코드해설·경로는 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_learning_consolidation_v2/manifest.json)에 보존했다. 이전 모듈을 실행하는 facade는 남기지 않았다. 현재24개 구현 각각의 설명은 [코드해설 목차](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/README.md), CPU/GPU·입력·엄격 재개 검증은 [추가 통합 결과](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_consolidation_v2/README.md)를 따른다.


## J 전용 실행 계약

`training/finger_skill_runner.py`의 `ExposureSchedule` → `run` → `_train_phase` → `evaluate_checkpoint` 순서로 읽는다. R/F 학습·auto 전환·숙련도 gate·단계별 actor 이전은 남아 있지 않다. `_train_phase`는 J 실행 하나이고, `phase` 표기는 출력의 고정 역할 식별자다. `DecisionCollector`는 매 tick 새 행동을 만들고 `[H,N,...]`의 모든 슬롯에 duration1·validTrue를 저장한다. F 전용 명령 유지나 계획 길이 관측은 없다.

환경 `finger_skill.v3`, 정책 `finger_skill_policy.v2`, 실행 `finger_skill_run.v2`, 재개 `finger_skill_resume.v3`를 사용한다. 기존 체크포인트를 받아들이는 호환 분기는 제거했으며 현재 동일 계약·동일 입력 SHA만 엄격 재개한다. 보상·종료·제어와 고정25% 구간→전곡 노출 일정은 유지한다. 변경 전 **480개 Python 원문**은 [J 전용 전환 전 보관본](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_joint_only_v3/manifest.json)에 있다.


## 코드 안에서 읽는 단위

주요 파일의 한글 구간 주석을 따라 읽으면 된다. runner에서는 수집→PPO→저널 commit→노출 commit→다음 reset 진행도, 정책에서는 지지17→손가락별 입력과4축→오른손6패딩, PPO에서는 GAE→유효 결정 선택→actor KL→critic 순서를 따른다. GPU 환경에서는 선택 마스크→240Hz 측정→음별 정산→60Hz 최종9보상→종료 관측 순서다. `note`는 에피소드, `terms`는 제어 tick, `reward_window`는 수집 창의 수명을 갖는다.

`ar/ac/rr/rc` 같은 주경로 약어는 `reward_advantage/cost_advantage/reward_return/cost_return`으로, runner의 저장 가능 flag는 `recovery_eligible`로 풀어 썼다. 공개 함수 인자·로그 키·checkpoint 구조는 유지한다. [현재 가독성 정리](/home/ajou/yigyu/3/docs/2026-10-28/guitar_readability_v1/README.md).
