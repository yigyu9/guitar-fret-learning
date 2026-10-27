# 단음 성공 후 조건부 확장 독립 검수

- 현재 판정: **watcher 범위 문제없음**.
- 상태: watcher 사전 검수 완료. 새 curriculum core·이전 계약·실행 pin 및 native 결과는 아직 최종 검수하지 않았다.
- 검수자는 생산 코드·기존 봉인 결과를 수정하지 않았으며 이 보고서만 신규 작성했다. 새 native 실험·학습을 실행하지 않았다.

## 판정 원칙

- 현재 단음 학습을 먼저 마치고 손별로 독립 판단한다. 최근64개 닫힌 episode의 품질 성공률90% 이상과 안전 실패0을 요구한다. 정수로는 최소58/64이며 열린 prefix는 분모에 넣지 않는다. invalid/물리 terminal은 제거하지 않고 진급을 막는다.
- 같은 시작 상태의 결정적 native 평가4/4 품질·안전 성공도 필요하다. 같은 시작 반복 성공을 일반화나 양손 결합 성공으로 확대하지 않는다.
- 첫 확장은 source event `[0,2]` 두 종류의 단음을 episode별로 선택하는 pool이다. 한 episode의 두 음 프레이즈·화음으로 설명하지 않는다. 새 목표의 critic·optimizer·RNG를 fresh로 시작하는 명시적 Actor 이전과 기존 strict resume를 구분해야 한다.
- 두 목표를 모두 실행하는 native preflight2회에서 안전·완주·coverage를 확인한 뒤에만 해당 손의 제한된 후속 학습을 시작한다. 새 목표 preflight에 음악 성공을 요구하지 않는 것은 진급 게이트의 완화와 구분한다.

## watcher 실제 확인

- [watch_and_expand_v1.py](watch_and_expand_v1.py)의 최근 학습 게이트, 기존 evaluator CLI·결과 schema 연결, 결정적 평가 게이트, 두 목표 preflight 후 후속 실행 순서를 읽었다. [계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_single_note_curriculum_20261019.md)과 [progression_plan_v1.json](progression_plan_v1.json)의 승인 범위에 맞는다.
- 원 supervisor 종료 결과가 생기기 전에는 대기하고, 새 native 단계 시작 전에 pin과 여유 메모리를 검사한다. 출력 디렉토리는 새 경로를 사용하며 실행은 파일 stdout/stderr·독립 session으로 관리한다.
- [tests/test_progression.py](tests/test_progression.py)를 검수자가 실행해 **15개 통과**를 확인했다. 게이트의 표본 수·최근 window·90% 경계·역할·열린 prefix·invalid/physical terminal·평가 완료/입력 불변 조건을 포함한다.
- CPU mock으로 발견했던 종료 경쟁은 자식별 `ProcessLookupError`/`OSError` 처리로 해결됐다. watcher가 생성한 session인지 확인하고 SIGINT300초→TERM20초→KILL5초로 정리하며 생존 자식과 정리 오류를 기록한다. 원 학습 supervisor나 임의의 다른 process group을 종료하지 않는다.
- 확장 trainer의 nonzero exit 또는 실패/누락 report가 watcher에서 정상 종료로 보이던 문제는 `expanded_execution_failed`와 exit2로 해결됐다. 순수 품질 미달은 진급 보류로 기록하고 확장하지 않으며 exit0이다.
- 상태 저장 IO 실패로 정리가 중단되거나 원 예외가 덮이던 문제를 CPU mock으로 재현한 뒤 수정본을 확인했다. cleanup 중 저장 실패에도 신호 단계·stream close가 계속되고, main의 부차적 저장 오류 뒤에도 원 예외를 다시 올린다. 관련 회귀2개가 포함된다.

## Critical / Warning / Suggestion

현재 검수한 watcher에서 남은 차단 문제·필수 수정·추가 구현 권고는 없다. 위 해결 이력은 모두 실행·동결 전 수정에 대한 CPU 근거다.

## 남은 검수·native 범위

- 새 curriculum core가 아직 최종 CPU 검사 중이므로 환경의 목표 선택/관측·clock, 명시563 Actor 이전·fresh critic/optimizer/RNG, strict resume, runner/evaluator 연결의 최종 판정을 유보한다.
- 최종 소스·실행 설정·watcher를 봉인한 pin의 내용과 실제 detached 시작 상태는 생성 후 확인해야 한다. 현재 보고서는 watcher가 이미 실행됐다는 증거가 아니다.
- 기존 단음 학습 종료 후의 실제 최근64개 게이트·결정적4회 평가와, 통과한 손의 pool native preflight는 아직 실행하지 않았다. 실제 안전·두 목표 coverage·Actor 이전 및 자원 정리는 해당 결과로 확인해야 한다.
- 후속 학습의 시작/완료·음악 품질 개선·2시간 수렴은 현재 CPU 검수로 주장하지 않는다. 기존 단음 학습과169개 봉인 소스를 유지하는 조건도 최종 실행 pin과 함께 다시 확인한다.
