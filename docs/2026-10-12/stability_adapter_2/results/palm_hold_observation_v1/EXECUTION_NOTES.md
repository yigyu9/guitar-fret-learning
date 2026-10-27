# 관측 실행 기록의 범위

관측 baseline/full은 각각 기존 .45 bias/작은 결합 보정 전체 목표각을 사용한다.
두 실행 모두 센서를 추가했고 각자의 이전 센서 없는 원자료5배열과 exact다.
실행 기록 execution.json의 두 terminal exit code는 0이며 총2init/48step이다.

baseline의 콘솔 출력은 실행 도구에 반환됐지만 전체 콘솔 파일로 저장하지 않았다.
baseline_summary.log는 observation.json에서 만든 완료 요약이며 전체 콘솔 로그가 아니다.
full.log는 실제 실행의 stdout/stderr를 파일로 캡처한 콘솔 로그다.
analysis.json은 저장 자료의 분석 결과이며 별도의 신규 물리 실행을 뜻하지 않는다.

첫 plot의 잘못된 full 범례는 관측 추가가 아니라 전체 목표 보정으로 정정했다.
수정 전 producer/문서/그림/manifest/실행 기록은 artifacts_attempt_v1에 보존하고,
canonical 그림은 artifacts_v2다. 그래프는 저장 자료의 과학 그래프이며 Gym camera가 아니다.
