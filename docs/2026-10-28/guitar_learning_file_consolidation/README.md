# guitar_learning 파일 통합 결과

2026-10-28 사용자 요청에 따라 작은 공용 Python 파일11개를 관련 파일에 통합했다. 활성 파일은 **518→507개**다(archive 제외). 기능을 넘기는 빈 호환 파일은 남기지 않았으며 호출 코드·검사·활성 안내 링크를 실제 위치로 수정했다.

| 현재 파일 | 흡수한 파일 |
| --- | --- |
| `training/recording.py` | `training/json_io.py` |
| `training/training_log_io.py` | `training/training_log_format.py`, `training/training_reports.py` |
| `training/parallel.py` | `training/persistent_parallel.py`, `training/persistent_audit.py` |
| `training/ppo.py` | `training/ppo_diagnostics.py`, `training/decision_ppo.py` |
| `core/control.py` | `core/finger_control.py` |
| `core/task_measurement.py` | `core/task_measurement_v2.py` |
| `quality/actionable_preparation_environment.py` | `core/environment_v5.py` |
| `quality/runtime.py` | `timing/recording.py` |

보상·제어·관측·성공·종료·PPO 계산과 로그 schema를 유지했다. 통합한 기록·병렬 모듈을 읽을 때 NumPy·Torch·Isaac Gym을 불러오지 않으며, 필요한 import는 기존 초기화 순서를 지키도록 지연했다. 기본 명령과 기존 도구의 CLI도 유지한다.

## 검증

- 통합 전 관련39모듈241검사와 통합 후 동일 범위의 실패 사례가 일치했다. 기존7모듈의 오류 외 새 실패는 없다.
- 전체188모듈을 각각 별도 CPU 프로세스로 검사했다. **158모듈 통과**, 총1,318건 실행을 기록했다. 나머지30모듈의 모든 실패 사례는 변경 전 원문을 읽는 별도 프로세스에서도 동일하게 재현했다.
- 기존 실패는 삭제된 과거 로그·모델과 현재 관측/진단 계약에 맞지 않는 시험 자료 등에 관한 것이다. 검사 기준을 완화하거나 원자료를 생성해 통과시킨 것이 아니다.
- 독립 change-reviewer가 별도37검사를 통과했고 통합된 정의·상수·상속·지연 import를 검수했다. Critical/Warning/Suggestion은 없다.
- 전체507개 Python 문법, 삭제 모듈을 향하는 import0개, 변경 전 보관546개 파일 SHA, 보호 대상3개 원문, 기본/기존 CLI 도움말을 확인했다.
- GPU 물리·학습은 실행하지 않았다. 이번 검증은 구조 통합에 관한 것이며 연주 성능 개선을 뜻하지 않는다.

추가 실패 비교는 현재 트리를 복원하거나 수정하지 않고, 별도 unittest 프로세스에서 보관 원문을 원래 `__file__` 경로로 읽어 자산 경로를 유지한 방법이다. 실패 사례 비교용이며 과거 체크포인트의 재개·입력 검증을 우회한 실행이 아니다.

## 보관과 체크포인트

변경 전 활성 Python518개와 문서28개는 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_file_consolidation/manifest.json)에 원래 경로·SHA·통합 위치와 함께 보존했다. 기존 미커밋 변경도 보관 시점 그대로 담았다. 현재 코드는 이 보관본을 import하지 않는다.

체크포인트는 전체 활성 Python 경로·SHA를 검사한다. **이전 체크포인트는 통합 후 트리에서 바로 strict 재개·평가할 수 없다.** 기존 pin·검증 규칙을 변경하지 않았으며 과거 실행 재현에는 해당 실행의 원문 소스가 필요하다.

## 검사 자료

- [검증 요약](validation.json) · [전체 CPU 검사](cpu_test_summary.json)
- [직접 관련 검사 전후 비교](focused_comparison.json) · [전체 실패 원문 비교](all_failure_comparison.json)
- [실제 실패 출력](failure_outputs.txt) · [독립 검수](review.json)
- [통합 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_file_consolidation_20261028.md) · [현재 코드 배치](/home/ajou/yigyu/3/guitar_learning/docs/CODE_STRUCTURE.md)
