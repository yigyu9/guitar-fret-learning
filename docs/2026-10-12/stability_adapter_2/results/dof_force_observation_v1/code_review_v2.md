# DOF force 관측 asset 참조 보존 재검수

검수일: 2026-10-07. 기존 `code_review.md`와 첫 실행 원자료는 수정하지 않았다. 변경 범위는 `run_dof_force_observation.py:26–27` 및 계획의 첫 실패·재시도 설명이며 reviewer native 실행은 없다.

## 요약 판정

**문제없음. 남은 Critical / Warning / Suggestion 없음.** 이 수정은 asset wrapper의 Python 참조 수명을 늘리는 재시도이며 실패 원인을 확정하거나 실행 성공을 입증하지 않는다.

보존된 `source_native_v1/run_dof_force_observation.py`와 현재 소스의 diff는 `get_actor_asset` 반환값을 `self.force_asset`에 보관하고 local `asset`이 이를 참조하도록 바꾼 두 줄뿐이다. 새 asset 생성·교체·삭제나 native pose/state/목표/PD/길이/solver 변경은 없다. 센서 활성화 시점, 완료 step의 읽기, 읽기 불변성 검사, 원래 runner의 sim 종료 및 outer finally의 class/argv 복구·부분 기록 저장은 그대로다.

첫 실행 기록은 returncode 1, `MemoryError: std::bad_alloc`, 센서 지원 true, 완료 physics step 0이다. 따라서 force 측정·trajectory 동일성·안정성을 확인한 실행으로 셀 수 없다. 계획도 실패와 소스·로그·부분 자료 보존, 원인 미확정 및 별도 `attempt_v2` 재시도를 구별한다. 문법 검사 통과 기록과 최소 diff를 확인했으며 실제 재시도 결과는 별도로 검수해야 한다. 본 재검수 기록을 동결한다.
