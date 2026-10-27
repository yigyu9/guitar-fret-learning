# 실제 학습 사전 검수

요약 판정: **문제없음**. 현재 범위에서 실행 중인 학습을 중단하거나 소비 소스를 수정할 문제는 발견하지 않았다. 이 문서는 종료 후 결과 검수를 대신하지 않는다.

## Critical

없음.

## Warning

없음.

## Suggestion

- `analyze_learning.py:57`: committed 수와 보고서 전이 수는 대조하지만 discarded 수는 직접 대조하지 않는다. 종료 후 부분 수집이 발생한 경우 `report.partial_collection.discarded_transitions`와 discarded 집계 수까지 대조하면 집계 범위 확인이 더 명확하다. 현재 H=256 단위의 순차 로그 분류는 `train_parallel.py:142`의 매 step 기록과 `parallel.py:356`의 동기 수집 순서에 부합한다.

## 확인한 근거

- 설정은 N=8, H=256, 이번 실행 최대 32 업데이트, max_wall_seconds=1800이다. 시간 제한은 `guitar_learning/train_parallel.py:165`에서 업데이트 시작 전에 검사하므로 최종 수집 한 번과 저장·정리 시간만큼 1800초를 넘을 수 있다.
- resume 대상은 기존 25 업데이트 체크포인트다. `analyze_learning.py:65`에서 모델·양쪽 optimizer·cost weight·업데이트 수·Python/NumPy/Torch/CUDA RNG를 `initial.pt`와 대조하고, 최종 업데이트 수가 25+이번 실행 완료 수인지 검사한다.
- 기존 helper의 1.0~1.12초 압현 구간과 67/60초 근접 onset 표본 정의는 현재 고정 첫 단음 설정에 맞는다. 다른 목표·tempo로 일반화된 분석은 아니다.
- `analyze_runtime.py:61`은 동일한 8개 worker ID와 현재 RSS/PSS가 모두 있는 표본만 합산하고, PID 변경 표본을 분리한다. RSS·PSS·peak의 의미를 구분하며 짧은 관측창과 OLS의 한계를 출력한다.
- `analyze_runtime.py:197`과 `:213`은 core 완료와 persistent audit, core SHA 연결, worker별 최종 lifecycle을 따로 확인한다. 분석 파일 무결성과 학습 완료 여부가 별도 필드여서 실패를 성공으로 바꾸지 않는다. canonical `report.json`이 최종 판정이고 `status.json`은 core 상태다.
- `analyze_learning.py:33`은 정리 산출물이 생긴 후 분석하도록 제한하고, 자원 분석은 부모 학습 프로세스가 살아 있으면 중단한다. 이번 검수에서 실제 gzip 로그 분석·후처리를 실행하지 않았다.
- source_run_v1의 73개 항목에 대해 원래 경로와 보관 경로 SHA를 모두 확인했으며 차이는 0개였다. 학습·설정·원자료를 변경하지 않았다.

## 수행한 검사

- 두 신규 분석 파일 AST 문법 검사 통과.
- 작은 가짜 자원 표본으로 OLS 단위, 빈/단일 표본, 불완전 worker 제외, PID 변경 제외, RSS/PSS 합산, 실패 상태 보존 검사 통과.
- native 실행·중단·재시작, 실행 중 transitions gzip 분석, 실제 후처리는 수행하지 않았다.

종료 후 실제 canonical/core 보고서, lifecycle, 집계 검증, 체크포인트 연결, 그림과 문서의 수치·주장 범위를 다시 검수해야 한다.
