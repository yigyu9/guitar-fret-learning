# 장기 학습 중단·음악 목표 발견 개선

원실행의 중단과 음악 학습 정체를 별도로 다뤘다. 기존52파일을 보존한 뒤 실행 감시·복구를 수정하고 별도 dense_v2 보상과 선택형 단음 pool을 구현했다. 기존 초기 자세·물성·충돌·gain·역할별 행동 범위·안정성 한계·음악 성공 판정은 바꾸지 않았다. 현재 문서는 실제 검증 결과를 정리 중이다.

## 확인했던 문제

[원실행 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_analysis_v1/README.md): host global OOM과 별도 rg 약7.86GiB RSS/OOM kill이 있었고 학습 worker0이 응답하지 않아 timeout으로 끝났다. 학습 worker 직접 OOM kill이나 단독 무한 누수는 확정하지 않았다. 부모는14업데이트 후15번째 수집 도중 실패했지만 stopped가 updates_complete로 잘못 남았다. 실패 checkpoint가 없어 마지막10업데이트 모델만 남았다. 완료320episode에서 음악 타현 매칭·목표 접촉 유지0이며 physical failure0, KL상한 내였다. critic loss 감소는 음악 성공의 증거가 아니었다.

기존 fretted 목표 접근 보상은 press~onset 약120ms에만 적용됐고, 오른손에는 fretted 음의 올바른 시간·방향 타현 경로로 접근하는 dense 신호가 없었다. 이것이 유일한 정체 원인이라는 증거는 없지만 학습 신호의 확인 가능한 빈 구간이었다. 네트워크를 더 키우거나 timeout만 늘리는 변경은 하지 않았다.

## 수정한 내용

| 부분 | 변경 |
| --- | --- |
| 메모리 | 기본8환경×256=2048batch, host MemAvailable4GiB 미만 중단. 현재 RSS/PSS와 peak를 따로5초 기록 |
| 진행 |10초 heartbeat, phase/update/tick/대기 worker, atomic status.json 및 flush된 events/resources JSONL |
| IPC |0.5초 poll, 응답순서와반환순서분리, worker PID/exitcode 즉시진단, 살아있는 무응답300초 timeout 유지 |
| 실패 복구 | 중단·오류 시 검증된 trainer만 failure_last_valid.pt 저장. 부분 rollout 폐기·정확한 stopped/부분 전이 수·종료 진단 |
| 음악 보상 | 별도 dense_v2. 왼손 초기 접근과 실제 움직이는 기타 상대 우손 목표현/깊이/타이밍/방향 경로 신호를240Hz 적분 |
| 목표 선택 | 기본첫음고정 유지, 명시한지원B단음pool 선택옵션. 공통후보계약과실제episode목표를분리보존 |
| 호환성 | 기존 legacy의 고정목표/보상 contract는 보존. 새 보상·pool은 새 정책으로 시작하며 strict mismatch 우회 없음 |

세부 가중치·목표·실행·복구 명령은 [PARALLEL_TRAINING.md](/home/ajou/yigyu/3/guitar_learning/PARALLEL_TRAINING.md)에 있다. 접근거리와 가이드 보상은 기하 proxy이며 실제 압현·발음 성공이 아니다. 정책39축, 하체 외부유한제어, Root고정/105·97·8/자유기타/중력ON/스트랩OFF/준비2초를 유지한다.

## CPU·검수

최종 전체 CPU126검사 통과(27.320초). [로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/cpu_tests.log). fake memory probe와 fake worker를 사용해 실제 OOM을 만들지 않았다. legacy strict resume 성공/dense mismatch거부, signed가이드의 실제StrikeDetector 통과, 반대방향·90ms늦음의 보상 감소, 동일행동에서 legacy/dense 음악·비용·관측 동일, reward와episode누적 일치, balanced sampler를 검사했다.

사전검수에서 terminal tick 후 reset 실패 시 전이 수가 한 tick 적게 기록되는 결함과 strict resume 실패 후 무작위 모델을 복구 파일로 저장하는 결함을 발견했다. 수정 전 파일을 별도로 보존하고 각각 회귀검사를 추가했다. Native 검증은 별도 새 실행 경로에서 진행한다.

## 보존

- [이전52파일과SHA](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_reliability_music/archive_manifest.json)
- [실행전소스71파일](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/source_run_v1/manifest.json)
- [Pool 재검수 수정전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/pool_before_tick_accounting/manifest.json)
- [Runner 재검수 수정전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/runner_before_resume_eligibility/manifest.json)
