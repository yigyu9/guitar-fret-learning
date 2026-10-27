# 모니터 파일 크기 집계 경쟁 조건 독립 검수

2026-10-22, `/root/review_gpu`. 판정: **문제없음(PASS), 요청한 두 CPU mock 경계에 한함.**

`watch_training_before_size_race_fix.py`와 현재 도구를 대조했다. 변경은 `run_bytes` 집계의 `is_file()` 이후 `stat()` 전에 임시 파일이 사라질 때 `FileNotFoundError`를 받아 해당 표본의 전체 크기를 `None`으로 두는 부분뿐이다. 부분 합계를 정확한 전체 크기처럼 기록하지 않으며, 디스크 여유는 별도 `statvfs` 값으로 guard에 사용한다. 이 경쟁 조건의 실제 모니터 실패가 관측됐다는 주장은 하지 않는다.

| 직접 실행한 CPU mock | 결과 |
|---|---|
| 임시 파일 `is_file=True` 직후 `stat=FileNotFoundError`, 정상 디스크 | `run_bytes=None`, progress 기록 후 다음 감시 주기 진입, SIGINT0회 |
| 동일한 stat 실패, 디스크 floor 미달 | `run_bytes=None`, 이벤트 기록·PID identity 재확인 후 mock SIGINT1회, 반환2 |

2개 모두 PASS다. 실제 파일 삭제·프로세스 접근·신호 전달·GPU 조회는 하지 않았고 subprocess/신호는 모두 mock했다. GPU·native·GL·학습·실제 모니터를 실행하거나 조작하지 않았다. 활성 소스·원자료·도구는 수정하지 않았으며 이 검수 기록만 작성했다.

현재 watcher SHA256: `007eeedfb965fd1235eab5a67d26dd6c844536e0dce7295a320fa2e938c71ce4`.

실제 모니터 교체는 root가 담당하며, 이 검수는 장기 학습의 완료나 성능을 인증하지 않는다.
