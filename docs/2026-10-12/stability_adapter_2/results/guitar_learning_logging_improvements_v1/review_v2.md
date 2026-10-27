# 로그 개선 최종 독립 검수

- 요약 판정: **문제없음**
- 상태: **completed=true**, 최종 확정(2026-10-19).
- 범위: 동결된 로그 개선 코드, CPU 검사 근거, 실제 학습·재개·평가 및 복구 산출물, 최종 README의 주장.
- 수정 범위: 이 신규 보고서만 작성했다. 생산 코드·기존 결과·사전 검수 [review_v1.md](review_v1.md)는 변경하지 않았다. 검수자가 새 native 실험이나 학습을 실행하지 않았다.

## Critical / Warning / Suggestion

남은 차단 문제나 필수 수정 사항은 없다. 이번 범위에서 추가 권고도 없다.

사전 검수에서 발견한 기록 후 fsync 예외의 마지막 행 집계 누락, 누적 episode 목록의 메모리 증가, 비활성 손 기준 raw 선택, stream close 실패 및 부분 수집 회계 혼동은 동결 전에 수정됐다. 기록된 행은 정상·예외 경로에서 한 번만 집계하고 원 IO 예외를 유지한다. standard 보고서는 누적 카운터와 episode 파일 참조를 사용한다. 역할별 raw 선택, recovery 집계의 window 해제, 평가 seed의 설정 출처 표기도 확인했다. 상세 해결 이력은 보존한 사전 보고서에 있다.

## 코드 및 CPU 근거

- 변경 범위에서 보상·성공 판정·관측/행동 계약·물리 제어를 변경한 부분은 발견하지 않았다. PPO 진단은 추가 sampling 없이 계산된다.
- 검수자가 실행한 PPO 3개, log IO 10개, runner 2개 검사가 통과했다. 원본 대비 모델·Adam·RNG·기존 PPO scalar의 동일성 및 기록 직후 실패 회귀를 확인했다.
- 생산자가 실행한 최종 전체 검사는 [cpu_all_final_v1.txt](cpu_all_final_v1.txt)의 **335개 통과 / 151.200초**다. 이를 검수자의 전체 재실행으로 표현하지 않는다.
- 최종 상태의 중복 주기 저장 생략을 확인했다. 이번 native 최종 모델은 모두 `full_save`다. 정확히 같은 전체 상태의 hardlink 게시 분기는 CPU 검사 근거이며 native 사용 실적으로 확대하지 않는다.

## 실제 실행 대조

| 실행 | 전이 / 물리 표본 | 완료 episode | 검수 결과 |
| --- | --- | --- | --- |
| 왼손 학습 | 840 / 3360 | 2 | update 2, 품질 성공 0/2 |
| 오른손 학습 | 420 / 1680 | 1 | update 1, 품질 성공 0/1 |
| 왼손 strict 재개 | 16 / 64 | 0 | optimizer update 2→3, 성공률 null |
| 별도 오른손 평가 | 420 tick / 1680 | 1 | strict load, timing-only 1/1·품질 0/1 |

- 학습·재개 합계는 **1276전이 / 5104물리 표본**이다. 별도 평가를 학습량에 더하지 않았다. 세 학습 실행은 sampled=logged=durable=committed이며 discarded=0, guard 오류=0이다.
- 왼손 첫 update는 완료 episode 0개·미완료 worker 2개이고 다음 update에서 완료 2개다. standard 보고서의 빈 상세 episode 목록과 별도 파일 참조는 의도한 형식이며 집계 누락이 아니다.
- strict 재개의 source final과 initial checkpoint를 직접 비교했다. metadata 외 모델·optimizer·RNG·identity가 같고 카운터는 2→2→3으로 이어진다.
- 왼손은 clean audible 100%여도 release 미완료·late 접촉 2.5478초로 실패한다. 오른손 학습의 accepted `1032:2`, **+177.248588ms**와 평가의 `1010:2`, **+85.135316ms**는 별도 실행이다. extra/wrong 각 1회와 회복 여부를 성공 판정과 구분했다.
- 평가는 completed/source_unchanged=True이고 물리 실패 0이다. 설정 seed는 명시적 reseeding 실행의 증거로 해석하지 않았다.

## 원자료·보존·주장 범위

- [verify_native_v1.py](verify_native_v1.py)의 읽기 전용 대조 함수를 세 학습 실행에 적용한 반환값이 [native_verification_v1.json](native_verification_v1.json)과 일치했다. 전이 보상 항목 합, 종료 집계, episode 분모 및 참조 파일 SHA를 확인했다.
- 안전 극값의 원자료 독립 대조 범위는 **선택된 12 제어 tick / 48 물리 표본**이다. 전체 5104표본의 raw 재감사로 확대하지 않는다. 연속 이탈의 tick 경계 처리는 별도 CPU 검사가 다룬다.
- 복구 fixture가 왼손 원본 gzip에서 마지막 8바이트만 제거한 별도 사본임을 직접 확인했다. CRC가 검증된 **390행 / 780전이**를 복구하고 미완성 member를 보고했다. 원본은 그대로이며 완료 episode·PPO commit·모델 유효성을 추정하지 않는다.
- 동결 현행 **169파일**, 이전 archive **157파일**, 기존 결과·감사 **270파일**을 재해시해 변경 없음을 확인했다.
- journal의 encode/gzip/flush·fsync 시간은 부모 기록 경로의 계측이다. 장치 IO 전체나 이전 실행 대비 속도 개선의 증거로 사용하지 않았다.
- 최종 [README.md](README.md)의 21개 로컬 링크가 존재한다. 문서 SHA는 `c59517dd2bca921a1b1093a366424189f0970aa683297017aae74e20a3afe4de`다.

최종 README는 로그 정확성 검증과 음악 수행 결과를 구분한다. 이번 짧은 실행으로 성능 개선·장기 수렴을 주장하지 않으며, 남은 품질 실패를 기록한 것으로 설명한다. 추가 수정 없이 검수를 확정한다.
