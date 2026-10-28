# guitar_learning 파일 통합 (2026-10-28)

사용자 요청: 역할이 가까운 Python 파일을 합쳐 현재 학습 코드의 파일 수를 줄인다.
현재 활성 Python 518개(archive 제외)에서 11개 감소한 507개를 목표로 한다.
학습 수식·상태·제어·성공·종료 조건은 유지하고, 이전 실행 자료는 수정하지 않는다.

## 통합 범위

| 유지 파일 | 흡수 파일 |
| --- | --- |
| training/recording.py | training/json_io.py |
| training/training_log_io.py | training/training_log_format.py, training/training_reports.py |
| training/parallel.py | training/persistent_parallel.py, training/persistent_audit.py |
| training/ppo.py | training/ppo_diagnostics.py, training/decision_ppo.py |
| core/control.py | core/finger_control.py |
| core/task_measurement.py | core/task_measurement_v2.py |
| quality/actionable_preparation_environment.py | core/environment_v5.py |
| quality/runtime.py | timing/recording.py |

## 계획·검증 체크리스트

- [x] 통합 전 관련 기존 CPU 검사와 입력 소스 보존
- [x] 내부 정의 통합·실제 import/patch/명시적 소스 목록 갱신
- [x] 활성 코드에 없어진 모듈 참조·순환·이름 충돌이 없는지 검사
- [x] 관련 검사 전후 비교 및 전체 CPU 회귀 검사
- [x] 별도 change-reviewer 검수 및 필요한 보정
- [x] README·코드 배치·활성 계약 문서와 실제 파일 수 확인

## 보존과 제약

- 변경 직전 활성 Python 전체와 수정 문서를 `guitar_learning/archive/20261028_before_file_consolidation/`에 보관하고 원래 경로·SHA·대체 파일을 manifest에 기록한다. 기존 사용자 미커밋 변경도 그 상태로 보존한다.
- 전체 활성 Python 경로·SHA가 실행 입력이다. 기존 체크포인트의 strict 재개·평가 규칙을 완화하거나 저장된 pin을 변경하지 않는다. 과거 소스 복원용 보관본은 현행 코드에서 import하지 않는다.
- `music_task.py`, `song/task.py`, `song/__init__.py`, native/자산 및 봉인된 과거 결과는 수정하지 않는다.
- Isaac Gym보다 NumPy/Torch가 먼저 로드되지 않도록 기존 지연 import를 유지한다. 로그 포맷의 NumPy는 함수 안에서만 사용한다.
- 동일 이름/전역 schema가 얽힌 song 원장·worker 버전은 이번 범위에서 합치지 않는다.
- 이미 수정 중인 짧은 진단 도구의 기능 변경은 보존하고 이 작업에 필요한 import만 갱신한다.

## 결과

완료. 활성 Python은518→507개이며 이름만 남긴 호환 파일은 추가하지 않았다. 관련39모듈241검사의 변경 전후 실패 사례는 동일하다. 전체188모듈에서158개 통과, 나머지30개는 변경 전 원문으로도 같은 실패를 재현했다. 독립 검수는 문제없음이며 별도37검사를 통과했다. 삭제된 과거 로그·모델 및 낡은 관측/진단 계약을 기대하는 기존 검사는 이번 통합 범위 밖의 문제로 남겨 두었다.

전체507개 문법·삭제 모듈 import0·보관546개 SHA·기본/기존 CLI 도움말을 확인했다. GPU 물리·학습은 실행하지 않았다. [완료 보고서](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_file_consolidation/README.md)와 그 아래 검사·검수 자료를 따른다.
