# Pool 관측 정규화 수정 사전 검수

**요약 판정: 문제없음.** 전체 CPU 검사 통과 확인 후 새 pool native 실행으로 연결을 검증할 수 있다. 이전 pool_native_v1의 계약 불일치 실패는 보존해야 하며 이번 코드 검수로 실제 실행 통과를 대신하지 않는다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

보관본 대비 task_sampling.py와 tests/test_task_sampling.py의 변경을 읽었다. 이전 세 파일의 archive manifest SHA가 모두 일치함을 확인했다. 기존 observations.py와 training_environment.py는 reliability 개선 전 보관본과 내용이 동일하다. 검수자는 기존 검수·소스·원자료를 수정하지 않았다.

실패 원인은 공통 task 계약을 사용하더라도 기존 ObservationBuilder가 각 단음의 duration을 정규화 scale에 포함하는 데 있었다. 수정은 wrapper에 한정되며 다음 순서로 실제 값과 계약을 함께 바꾼다.

1. pool 전체의 `max(1, duration_s)`를 고정값으로 계산한다.
2. 매 reset의 실제 builder.scales에서 `music.remaining_s`, `music.held_total_s`, `music.elapsed_s` 세 필드만 이름으로 찾아 바꾼다.
3. builder.spec와 contract.observation의 scales를 동기화하고, pool v2 계약에 override 값을 명시한다.
4. 기존 reset 반환 관측을 버리고 현재 builder로 `_observation()`을 다시 구성한다. 이후 step도 동일 builder를 사용한다.

현재 pool은 명시적으로 단일 fretted B 이벤트만 허용하므로 모든 후보의 target 수는1이고, 남은 task-dependent state scale은 위 세 duration 항이다. 음악 시간·목표·원래 종료 조건을 변경하지 않아 각 episode는 실제 선택된 단음의 duration으로 종료된다. reward ledger·dense 보상 적분·성공 판정은 관측 재구성과 분리되어 있다. legacy 고정 목표 경로는 wrapper를 거치지 않아 기존 관측과 checkpoint 계약을 유지한다. pool v2 계약 변경은 기존 pool v1과 strict checkpoint 호환으로 간주해서는 안 된다.

기존 fake 환경 대신 실제 TrainingEnvironment/DenseTrainingEnvironment/ObservationBuilder와 RecordedSession을 사용하는 검사로 확대된 점을 확인했다. 서로 다른 duration의 반복 reset/step, 다른 worker의 계약 일치, 실제 remaining/elapsed/held 값의 공통 scale 나눗셈, 개별 timeline 종료, 고정 legacy 경로를 검사한다. ExtendedRecordedSession의 마지막 body 상태 반복은 CPU timeline 검사용이며 native 운동 재현을 입증하는 fixture가 아니다.

담당자는 해당5개 CPU 검사 통과를 보고했다. 루트의 전체127개 검사 및 N2/H512 새 pool native 결과는 후속 증거로 확인해야 한다. 이번 리뷰는 새 물리·학습·전체 검사를 실행하지 않았다.

검수 시점 SHA256:

- task_sampling.py: `69e9f91b6cff221006480d40a662bf6c4a9ba0525266c52395e5c4a6009acaa2`
- tests/test_task_sampling.py: `6a1fce117cc593d1c50824c4107498cf556092fb67528046867b3022a6d40e92`
