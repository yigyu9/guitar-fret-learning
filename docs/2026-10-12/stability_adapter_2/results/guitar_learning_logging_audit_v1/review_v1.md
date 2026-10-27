# 학습 로그 감사 독립 검수

**요약 판정: 문제없음.** 미해결 Critical·Warning·Suggestion과 전달 차단 문제는 없다. 검수자는 분석 대상의 생산 코드·기존 로그·체크포인트·타인 산출물을 수정하지 않고 이 보고서만 작성했다. 새 native 실행·학습·전체 테스트는 수행하지 않았다.

범위는 phase README, `metrics_semantics_v1.md`, `verify_metrics_v1.py`·`metrics_audit_v1.json`, `storage_audit_v1.py/.json`, 점검 계획과 해당 주장에 연결되는 현행 logger/PPO/요약 코드다. 실제 완료 학습2개와 시작 실패1개, 저장량 비교용 평가2개를 대조했다.

## 지표 의미와 수치

`verify_metrics_v1.audit`를 원자료 읽기만으로 호출해 양손 결과를 다시 계산했다. Python3.13에서 저장된 두 결과와 전체 항목이 정확히 일치하고 errors[]다. rl38/Python3.8에서도 허용 오차 내에 일치하며 왼손 합산의 마지막 약4.44e−16 차이만 있다. 두 실행 각각420전이, 보상/비용/품질 종료 집계, nested timing과60Hz 시계/4-step 진행, 핵심 소스7개 SHA의 문서 설명은 맞다.

README는 다음 구분을 정확히 설명한다.

- 실행 완료·시간표 완주·품질 성공과 비활성 손 진단을 분리한다. 양손 timing-only1/1과 품질0/1을 혼동하지 않는다.
- 누적 점유 시간/이벤트 수를420행 전체에 다시 합하지 않고, 증분 reward_terms·cost와 구분한다. `music.wrong=2`, `timing.wrong=1`, extra1도 독립 오류4회로 더하지 않는다.
- compact의 순간 stability/fretting은60Hz 끝 표본이며, 네240Hz 표본의 실패 원인을 모은 failure_reasons와 다르다. 끝 표본의 최대값·접촉률을 전체240Hz 지표로 확대하지 않는다. 근거: `guitar_learning/parallel.py:45`, `training_environment.py:125`.
- PPO의 loss/actor grad norm은 마지막 미니배치 값이고 norm은 clipping 전이다. 최종 전체 rollout analytic KL과 거절된 시도까지 포함하는 최대 KL을 구분한다. 근거: `guitar_learning/ppo.py:156`, `ppo.py:195`.
- best 접촉 오차·거리 proxy·50/100ms/joint 음악 기록을 최초 도착·clean 접촉·압력·음향 성공으로 대체하지 않는다. 현재 `timing_report`도 품질 gate가 적용된 성공을 센다는 설명이 맞다.

## 저장량·중복

저장량 JSON의95개 파일 기록을 실제 stat에 대조했고 모두 일치했다. 다섯 gzip을 스트리밍으로 해제해 바이트 수를 확인했으며 모두 일치한다. source_evidence15개 SHA도 일치한다. 실행 폴더와 인접 stdout/stderr 로그의 논리 바이트 수, decimal MB, 평가 full trace와 학습 compact를 분리한 분모가 명확하다.

완료 학습 총량72.917011MB/72.689722MB·시작 실패0.368469MB, 학습 compact 합597,325바이트, checkpoint 비중92.531194%와 중복 가능량55,581,028바이트가 README의 반올림 수치와 맞다. 평가 gzip43.226701MB/42.838457MB를 학습 매 단계의 저장량으로 오인하지 않는다. 실패의43바이트 gzip은 실제 해제0바이트다.

양손 `checkpoint_000000.pt`와 `final.pt`를 별도 재귀 비교해 model·optimizer·RNG·identity·updates가 정확히 같고 metadata만 다른 것을 재확인했다. torch 파일 바이트 동일성과 의미적 동일성을 구분한 설명이 적절하다. 중복 JSON 값 크기는 key/delimiter를 제외한 해제 값 추정이며, gzip 절감량으로 그대로 더하지 않는다는 한계도 명시돼 있다.

## 실패 처리·권고 범위

품질/준비 요약이 하위 실행의 정상 반환 뒤에만 생성되는 반면 핵심 report/전이 close/복구 처리는 finally 경로라는 구분은 코드와 맞다. 0전이 초기화 실패를 실제 음악 기록 손실 사례로 과장하지 않는다. 강제 종료·전원 손실에 대한 gzip trailer/fsync 내구성이나 로깅 I/O 병목을 미측정 상태에서 보장·단정하지 않는다.

역할별 업데이트 요약·분모·중단 prefix 정리 우선, 선택적 상세 기록/중복 모델 정리 후 계측·대시보드라는 권고는 확인된 문제와 연결된다. 기존 봉인 증거 삭제나 현재 로그 일괄 축소를 요구하지 않으며, 불필요한 생산 구현 변경을 이번 분석에 포함하지 않는다. 로그 전용 시간 계측 없이는 현재 학습 속도의 주원인이라고 결론 내리지 않은 점도 적절하다.

추가된 `metrics_semantics_v1.md`도 확인했다. 정상 wall budget 종료를 포함하는 report.completed, 현재 연속 dwell과 최장/latch 이력, release_late 점유와 최초 해제 지연, 마지막 worker 측정과 다중 worker 평균을 구분한다. RH extra `1354:2`를 후속 결정적 평가의 이벤트로 명시했으며 실제 평가 result에 일치한다. 문서의 source/결과 SHA18개가 모두 일치하고 local 링크48개가 유효하다.

최종 README local 링크22개도 모두 존재하고 줄번호 범위가 유효하다. 지표 의미·수치·저장량·한계를 최종 확인했으며 이 검수 보고서를 확정한다. 추가 수정하지 않는다.
