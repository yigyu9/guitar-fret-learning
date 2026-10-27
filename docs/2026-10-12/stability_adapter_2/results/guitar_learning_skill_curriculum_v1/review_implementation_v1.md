# Skill curriculum v1 구현 독립 검수

요약 판정: **수정 권장**. 물리·행동·실패 종료나 성공 집계에서 Critical 결함은 발견하지 않았다. 다만 새 단계의 보상·성공에 쓰이는 별도 이력이 정책과 Critic 관측에서 빠져 있어, 해당 상태를 추가한 새 버전에서 학습을 이어가는 것이 적절하다. 소비된 v1은 수정하지 않고 보존한다.

## 범위와 방법

- 읽기 전용 검수 대상: `guitar_learning/skill_environment.py`, `skill_settings.py`, `skill_parallel.py`, `train_skills.py`, `tests/test_skill_environment.py`, `tests/test_skill_runner.py`.
- 사용자 지침, `guitar_learning/AGENTS.md`·README 및 `docs/plans/guitar_learning_skill_curriculum_20261018.md`를 확인했다. 연결 계약을 판단하는 데 필요한 기존 TrainingEnvironment, SpecialistLedger/Policy/runner, 음악 측정·관측과 병렬 수집 API만 대조했다. 다른 소스·시험·결과는 수정하거나 실행하지 않았다.
- 신규 두 시험 파일의 15개 검사 내용을 검토했다. root가 실행한 `/tmp/guitar_skill_cpu_v1.log`의 마지막 결과는 **183 tests, OK**다. 이는 CPU 계약 검사이며 native 학습 성취의 증거가 아니다.

## Critical

없음.

## Warning

1. **`guitar_learning/skill_environment.py:258`, `:294`, `:314` — 단계 보상 이력이 반환 관측에 포함되지 않는다.** `skill_ledger`는 `super().reset()`이 관측을 만든 뒤 생성되고, step도 기존 관측을 받은 뒤 이 ledger를 갱신하여 그대로 반환한다. `reached`·`contacts`·`held`·`crossed`, `ready_dwell`, 원래 악보 창 밖의 연속 접촉 이력 및 별도 timed specialist 이력은 `info['specialist']`로만 전달된다. 기존 토큰의 dwell/match는 원래 공동 음악 ledger의 값이어서 이들을 대체하지 못한다. 따라서 feed-forward Actor/Critic은 동일한 현 상태에서도 첫 획득·성공 bonus의 소비 여부나 다음 표본이 hold/ready 문턱을 넘는지 구별하지 못한다. **제안:** 모든 단계가 공유하는 명명된 관측 계약에 실제 보상·성공에 필요한 단계 이력을 추가하고, 연속 dwell/중단/reset·중복 bonus·timed 이력 및 단계 간 actor 전달을 검사한 새 버전을 사용한다. 이 지적만으로 v1의 물리 측정이나 실제 성취 판정이 거짓이 되는 것은 아니다.

## 확인한 계약

- 기존 39행동 shape/유한값/범위와 비활성 손의 정확한 0을 native step 전에 검사한다. persistent 환경을 생성할 때만 기존 ContactEnvironment 바인딩을 일시 교체하며 원문 소스·자산·native 제어기를 변경하지 않는다.
- 단일 fretted B 목표, 원래 악보 onset/press/end와 50/100ms 독립 기록을 유지한다. 네 단계 물리 표본의 시각 정합성과 SpecialistLedger의 연속 240Hz 검사를 이용한다. any-time contact/hold/cross와 원래 timed 기준을 구별한다.
- 공통 4초 horizon과 전체 기간의 목표 토큰 가시성을 사용한다. 안전한 `timeline_complete`와 해당 단계 성취를 모두 충족해야 `stage_success`다. 조기 성공 종료·truncation·안전 실패를 완료 성공으로 바꾸지 않는다. 실패 control tick의 양의 단계 보상을 억제하고 기존 안정성 비용·실패 종료를 보존한다.
- reach/ready는 기하 준비 proxy로 명시한다. 원래 native contact candidate와 LH 조건 없는 기하 crossing은 실제 현 압력·소리·공동 음악 성공을 인증하지 않는다. 원래 공동 음악 지표는 별도로 보존한다.
- 단계·역할을 설정에서 명시하고 frozen partner를 거부한다. 기존 strict resume는 관측·행동·task·reward·termination/PPO identity를 비교한다. actor-only 전달은 source 단일 손 역할·업데이트·유한 model·관측/행동/종료와 공통 task를 검증하고 단계 메타데이터·보상 차이만 허용한다. source 형식 검사는 실제 기술 성공의 인증이 아니며 자동 승격 기능도 없다.
- 비용 비교용 두 가중치 설정은 신규 파서에서 양수로 보존된다. 동일 초기 모델·RNG 및 실제 수집 예산의 일치는 실제 실행 자료에서 별도 검증해야 한다.

## 실행 기록의 해석

검수 중 확인된 `left_cost1p0_run_v1`, `left_cost0p1_run_v1`, `right_cost1p0_run_v1`은 root가 관측 보완을 위해 중단한 기록이다. 각각 report의 `completed=false`, `stopped=interrupted`, committed transitions **0**, `changed_inputs=[]`이며 specialist 요약의 logged transitions는 **256 / 92 / 58**이다. 셋 모두 완료 episode와 성공 episode는 0이다. 부분 수집과 복구용 초기 checkpoint를 학습 업데이트나 비용 가중치 효과의 비교 결과로 해석할 수 없다. 네 번째 실행은 시작하지 않았다는 root 보고와 구분해, 여기서는 존재하는 세 report만 읽었다.

`train_skills.py:35–36`의 skill 요약 생성은 정상 반환 뒤에만 실행된다. 중단 시 상위 runner가 만든 `report.json`·`specialist_report.json`을 실패의 근거로 사용해야 하며, `skill_report.json` 부재를 로그 소실이나 성공으로 해석하지 않는다.

후속 v2의 관측 보완 및 시험·native 결과는 이 보고서의 승인 범위에 포함되지 않는다.
