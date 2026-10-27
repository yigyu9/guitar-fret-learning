# 실행 전 독립 검수

요약 판정: **문제없음**. 현재 검토 범위의 Critical·Warning 없음.

## 범위와 확인 결과

- `guitar_learning/training/json_io.py:32–55`: 현재 스레드의 FP 환경 저장 → FE_INEXACT만 마스킹 → JSON 쓰기 → `finally` 전체 환경 복원 순서를 확인했다. 네 writer의 기존 JSON 쓰기 6곳이 helper를 사용하며 JSON 읽기·물리·제어·PPO 변경은 없다. 원본 보관 7개 파일 SHA가 manifest와 일치한다.
- `verify_training.py:182–193, 339–384`: 첫 저장300회 + 첫 복구 저장150회 + 새1550회로 2000회/65,536,000전이를 검증한다. 미저장8회·35회를 제외하며 두 재개의 nonmetadata 상태 비교와 연속3331 curriculum 재생을 수행한다. 과거 소스는 동결 snapshot, 최종 소스는 active와 대조하고 선언된4변경·2추가만 허용한다.
- `analyze_training.py:159–185, 204–291`: 전역 offset0/300/450,100·250회 cohort, 해당 prefix 안의 체크포인트 선택과 프로세스별 메모리 기준을 확인했다. 고정 정책 평가와 학습 수집 통계를 구분한다.
- `evaluate_checkpoints.py:167–343`: 원본 initial0과 새 final2000을 평가한다. 각1024환경의 첫 에피소드만 집계하며 정책 업데이트·curriculum 승급 없이 평가한다. 최종 환경0~7의 실제 자세를 reset 전에 저장하고 native GPU 종료 후 보고서를 작성한다.
- `render_video.py:63–195`, `video_workflow.md`: 사전 선택 규칙·입력 SHA·60Hz endpoint와 실제 첫 에피소드 길이를 유지하는 전신 자세 재생 경로를 확인했다. 새 물리 적분 없이 원래 visible mesh와 여섯 현을 배치하며 프레임별 화면 범위와 pose 불변을 확인한다. 모든 JSON 쓰기는 helper를 사용한다.
- `progress.py`, `README.md`, `native_trace.gdb`: 새1550 실행 경로와 전역450 offset, 두 실패 이력 보존 및 미완료 표시가 일치한다. native trace 설정은 이전 복구 도구와 같다.

## Warning 해결 확인

이전 지적은 `finish_workflow.py:33`에서 비교 분석 도구가 자동 실행 목록에서 빠진 점이었다. 최종 파일은 `verify → analyze → evaluate → compare_evaluations → render` 순서다. `workflow_inputs.json`에 비교 도구를 포함한7개 입력이 모두 고정되어 있고, 현재 실제 SHA7개가 전부 일치한다. 비교 분석 누락 Warning은 해결됐다.

## 검증 범위

- 이 검수에서 CPU JSON subprocess6검사를 직접 실행해 통과했고, 두 검증·분석 도구의 Python3.8 AST를 확인했다. 보관 원본7개와 최종 workflow 입력7개 SHA를 직접 확인했다.
- 평가 worker의 CPU5검사·AST3개 통과 및 전체 CPU829검사/518.112초 통과는 담당자(root/worker)의 보고이며 이 검수에서 재실행하지 않았다.
- 실제 학습·최종 검증·고정 평가·GL 렌더 완료를 판정한 문서가 아니다. 최종 실행 증거는 완료 후 별도 검수해야 한다. 진행 중인 학습, GPU/GL, 동결 소스와 원자료를 실행하거나 수정하지 않았다. 이 새 검수 문서만 저장했다.
