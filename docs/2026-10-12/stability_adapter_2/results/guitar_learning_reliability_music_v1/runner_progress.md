# Runner reliability implementation

소유 파일: `guitar_learning/train_parallel.py`, `monitoring.py`, `tests/test_train_parallel.py`, `tests/test_monitoring.py`.

- 기본 N8/H256/checkpoint5. 명시한 기존 N/H/checkpoint 값은 그대로 수용한다. PPO 수치 기본값과 legacy 음악 동작은 유지한다.
- 설정에 RAM 여유 4GiB, heartbeat10초, 자원5초, worker timeout300초와 music(reward_mode legacy|dense_v2, goal_event_indices null|명시한 단음목록)를 추가하고 검증한다.
- stdlib Monitor가 배경 스레드에서 시작/준비/수집/업데이트 중에도 자원·heartbeat를 기록한다. `/proc/MemAvailable`, 부모 및 살아있는 worker의 현재 RSS/PSS(허용될 때), lifetime RSS peak를 분리한다. resources/events JSONL은 매 기록 flush, status는 temp+replace다.
- RAM 기준 미달은 background에서 latch하고 Pool 짧은 대기 poll 및 Collector control tick callback에서 `LowMemoryError`로 중단한다. PPO 업데이트 도중에는 비동기 예외를 주입하지 않고 완료/rollback 후 foreground 경계에서 처리한다. 자원 간격 사이 급격한 메모리 고갈이나 OS SIGKILL 자체의 저장은 보장하지 않는다.
- 실패 이유 memory_guard/worker_timeout/worker_failed/interrupted/error를 구분한다. trainer 존재 시 `failure_last_valid.pt`를 exclusive save하고 부분 rollout은 폐기한다. 원 오류/저장 실패/미완료 수집 틱/마지막 checkpoint 경로/worker close diagnostics를 보고한다. 기존 정기/최종 checkpoint 형식과 strict load는 유지한다.
- current all-source rglob로 새 monitoring/task_sampling/dense_environment도 before pin에 포함된다. actual parent/child import census, 원본 model parity와 guard checks는 유지했다.
- 관련 CPU 검사 11개 통과(모니터7+설정4), `--help` 통과. fake memory probe로 저메모리·조용한 작업중 heartbeat·probe실패·저장실패를 검사했고 실제 OOM/native 학습은 실행하지 않았다.

루트 담당 잔여 검증: 전체 CPU/병렬 콜백 통합 검사, 실제 기존 checkpoint strict resume, native 정상 수집 및 중도중단 저장/정확한 report를 새 결과 폴더에서 검증한다.

## Resume 검수 보완

수정 직전 소유4파일을 `runner_before_resume_eligibility/`에 SHA일치 보관했다. `recovery_eligible`은 fresh trainer 초기화 또는 strict resume load 성공 후에만 켠다. strict 계약 불일치/손상/부분 load 실패에서는 `failure_last_valid.pt`를 만들지 않고 path=null/reason=resume_not_validated로 보고한다. 원 checkpoint는 수정하지 않는다. 실제 PPO legacy/dense 계약 불일치 거부와 SHA보존, 올바른 strict resume 후 recovery 저장·재로드 검사를 추가했고 관련 CPU **13개 통과**했다.
