# Skill curriculum v2 구현 독립 검수

요약 판정: **문제없음**. 검토 범위에서 Critical·Warning 및 제한 native 파일럿을 차단할 결함을 발견하지 못했다. v1에서 지적한 보상·성공 이력의 관측 누락은 v2의 공통 37개 필드와 반환 관측 재구성으로 해소됐다. 이는 구현 검수이며 기술 성공이나 학습 효과의 판정이 아니다.

## 범위와 근거

- 신규 `guitar_learning/skill_environment_v2.py`, `skill_parallel_v2.py`, `train_skills_v2.py`, `tests/test_skill_environment_v2.py`만 변경 검수했다. 연결 규약은 직전 v1 검수에서 확인한 기존 환경·관측·SpecialistPolicy/runner와 대조했다.
- 코드는 읽기 전용으로 검수했으며 테스트·native 실행이나 소비된 파일의 수정은 하지 않았다. 소유한 이 보고서만 작성했다.
- 신규 6개 CPU 검사의 내용을 확인했다. root가 실행한 정본 `cpu_tests_v2.log`에서 전체 회귀 **189 tests, 99.775s, OK**를 확인했다. 검수자가 직접 실행한 결과는 아니다. v1 전체 **183 tests OK**는 `/tmp/guitar_skill_cpu_v1.log`에서 확인한 별도 기록이며, v2 전체189에 다시 더하지 않는다.

## 해결된 지적

1. **보상·성공 이력의 노출 — `skill_environment_v2.py:14`, `:35`, `:79`.** 역사적 reach/contact/hold/ready/cross 성취, 이전 후보·연속/최장/누적 접촉, ready 연속 시간, 첫 성공, 안전 무효화 및 별도 timed 획득·dwell·미스·50/100ms 매칭·해제 이력을 이름과 고정 scale이 있는 37개 필드로 추가한다. 원래 468개 상태와 음악 토큰은 유지하며 상태만 505차원으로 확장한다. 이 단일 목표 계약에서 각 bonus의 소비 여부와 다음 dwell 성취에 필요한 이력이 노출된다. duplicate 처리에 쓰이는 ID 집합 자체를 노출하는 대신 native detector의 단조 증가 물리 step/string ID를 전제로 한다는 범위도 계약에 명시돼 있다.
2. **동일 tick의 최신 이력 — `skill_environment_v2.py:105`.** 상속된 v1 step이 네 물리 표본과 skill ledger를 모두 갱신한 다음 `_observation()`을 다시 호출하여 반환한다. v1이 먼저 만든 이전 이력의 관측을 반환하지 않는다. 원래 reward·cost·종료·음악 및 단계 성공의 기준은 바꾸지 않는다.
3. **reset 이력 격리 — `skill_environment_v2.py:93`.** base reset 이전에 `skill_ledger=None`으로 만들고, 새 base builder와 새 ledger가 생성된 뒤 fresh observation을 다시 만든다. persistent native session의 재사용과 별개로 이전 episode의 성취·첫 성공·dwell이 남지 않는다. reset 표본에서 실제 candidate가 참이면 그 이전 후보 필드는 참으로 시작하며, 가상의 첫 접촉 시간을 더하지 않는다.

## 연결 계약 확인

- 7개 기술 모두 동일한 505개 이름·순서·scale과 기존 39행동·물리 종료 계약을 사용한다. 원래 음악 목표와 공통 horizon은 유지된다. 단계 역할·보상·성취 기준은 기존처럼 명시적인 단계 메타데이터로 구별된다. 다만 `provisional_success`·`first_success_s`는 **선택 기술의 성취**이며, RH `ready_dwell_s`·`ready`는 그 기술에 지정된 front/rear/timed guide 기준이다. 따라서 공통 history schema가 모든 단계에서 동일한 물리 사건을 뜻한다는 주장은 하지 않는다. 이 차이는 명시된 목적 변경을 허용하는 actor-only warm initialization의 범위이며, 전체 strict resume의 호환성 주장이 아니다.
- 같은 손의 v2 단계 간 actor warm-start는 기존 검증 경로를 이용한다. 공통 관측·행동·종료와 목표가 일치해야 하며 `task.specialist`와 보상 차이만 허용한다. 모델 전달은 성공 승격을 인증하지 않는다. 전체 strict resume는 reward·task를 포함한 기존 identity 검사를 그대로 사용한다.
- v1의 상태468 checkpoint를 v2의 상태505에 암묵적으로 padding하거나 변환하는 경로는 없다. 기존 architecture의 차원·관측 계약 검사에서 거부되는 것이 정상이다. 이번 파일럿은 v2에서 새로 초기화한 모델을 사용해야 한다.
- v2 worker factory는 module-level 함수로 spawn 경로에 전달된다. runner의 일시 바인딩은 `with patch`로 제한되고, 기존 specialist→skill→v2 Pool 연결을 통해 v2 환경이 선택된다. 중단 시 바인딩을 원복하는 검사도 있다.
- 새 6개 검사는 동일 물리 상태의 서로 다른 성취/dwell 관측, timed 보상·미스 이력, 반환 tick 최신 상태, persistent reset 무누출, 7단계 공통505 계약, v1과 reward/cost/음악/종료 일치 및 중단 시 실행 경로 복원을 다룬다. recorded/synthetic fixture 검증을 native 물리 성과로 부르지 않는다.

## Critical / Warning

없음.

## 실제 결과의 범위

이번 변경은 관측과 신규 실행 진입점을 보완한다. 기존 240Hz 접촉·기하 타현 판정, 실패 종료·안정성 비용·자유 기타·하체 유한 제어를 완화하지 않는다. reach/ready는 준비 기하 성취이며 contact/cross와 공동 음악 성공은 별도다. 비용 가중치1/0.1의 효과는 동일 초기 모델·RNG·목표·수집 예산을 맞춘 실제 실행 및 평가 결과로 확인해야 한다. v1의 중단된 0업데이트 실행과 v2 실행을 합쳐 완료된 학습으로 세지 않는다.
