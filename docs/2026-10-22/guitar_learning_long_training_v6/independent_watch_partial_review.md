# 모니터 update JSON 읽기 경쟁 조건 독립 검수

2026-10-22, `/root/review_gpu`. 판정: **문제없음(PASS), 수정된 모니터 읽기 경계에 한함.**

`watch_training_restart1_hardened.log`에 남은 `JSONDecodeError: Expecting value: line 1 column 1`과 기존 최신 파일 직접 읽기 코드를 확인했다. 이는 모니터의 실패 기록이며 진행 중 GPU 학습 실패로 확대하지 않는다.

`watch_training_before_partial_read_fix.py`와 현재 `watch_training.py`의 차이는 최신 update 파일 목록을 역순으로 읽으면서 `FileNotFoundError`·`JSONDecodeError`를 건너뛰고 첫 파싱 완료 JSON을 사용하는 변경뿐이다. 전부 미완성이면 빈 행에서 계속 진행하므로 업데이트 수를 추정하거나 허위 commit으로 채우지 않는다. 실제 학습 로그의 손상 허용 여부는 별도 최종 검증기가 판단하며, 모니터 fallback을 로그 무결성 통과로 해석하지 않는다.

임시 디렉토리와 mock만 사용한 CPU 검사4개를 직접 실행했다.

| 경로 | 확인 결과 |
|---|---|
| 최신 파일 empty, 이전 파일 valid | 이전 완료 update 사용, progress 기록 후 다음 감시 주기 진입 |
| 최신 파일 조회 중 삭제, 이전 파일 valid | `FileNotFoundError`를 건너뛰고 이전 완료 update 사용 |
| 모든 update가 invalid, 정상 디스크 | update 값은 `None`, progress 기록 후 감시 지속 |
| 모든 update가 invalid, 디스크 floor 미달 | update 값은 `None`, PID identity 재확인 후 mock SIGINT1회, 반환2 |

모든 검사는 PASS였다. 실제 `/proc`·프로세스 신호·`nvidia-smi`·GPU·native·GL은 사용하지 않았다. 학습·원자료·활성 소스·모니터 도구를 직접 변경하거나 실제 감시를 재시작하지 않았다. 이 검수 기록 파일만 작성했다.

검수한 watcher SHA256: `768876acddd553f39ecbb35c5b036b955d8ade900e0215ea91c0158e7d7d6b3d`.

이 PASS는 전체 장기 실행의 완료·학습 성능·모든 운영 오류에 대한 보증이 아니다. 실제 모니터 교체와 실행 상태 확인은 root가 수행한다.
