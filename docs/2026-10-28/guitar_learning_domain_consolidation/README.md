# 학습 작업 영역 통합 결과

2026-10-28. 기본 학습을 읽을 때 여러 파일을 오가야 하는 부분을 작업 영역별로 묶고, 공용 입력을 가져오면서 불필요하게 연결되던 CPU 전용 코드를 분리했다.

| 기준 | 통합 전 | 통합 후 |
| --- | ---: | ---: |
| 활성 Python 전체(archive 제외) | 507 | 487 |
| 기본 학습 진입점의 정적 연결 파일 | 152 | 40 |
| 위 항목 중 구현 파일 | 132 | 31 |
| 위 항목 중 초기화 파일 | 20 | 9 |
| GPU 디렉토리 Python | 18 | 9 |

25개 파일의 정의를 관련 파일로 모으고5개의 통합 파일을 만들어 전체20개를 줄였다. 정적 연결의 추가 감소는 CPU 전용 연결 분리 때문이다. 이 숫자는 함수·조건문 안의 import까지 포함한 동일 방식의 전후 비교이며, 실제 한 번의 학습에서 실행한 파일 수나 삭제한 파일 수로 해석하지 않는다.

## 먼저 읽을 흐름

1. [실행·설정](/home/ajou/yigyu/3/guitar_learning/training/launch.py)
2. [일정·학습·저장·재개](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py)
3. [GPU 환경 진행·수집](/home/ajou/yigyu/3/guitar_learning/training/rollout.py)
4. [손가락 환경·보상·종료](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py)
5. [정책](/home/ajou/yigyu/3/guitar_learning/training/policy.py)
6. [PPO](/home/ajou/yigyu/3/guitar_learning/training/ppo.py)

접촉·기하·장면·제어·진단·저장의 세부 파일과 추가 입력은 [현재 읽기 지도](/home/ajou/yigyu/3/guitar_learning/docs/CODE_STRUCTURE.md)에 설명했다.

## 통합 영역

| 영역 | 통합 위치 |
| --- | --- |
| CLI·공용 설정 | `training/launch.py` |
| 환경 풀·결정 수집 | `training/rollout.py` |
| 공유·전문가·손가락 정책 | `training/policy.py` |
| 구간·전곡 일정과 실행 | `training/finger_skill_runner.py` |
| 로그·checkpoint·모니터링 | `training/training_log_io.py` |
| GPU 패드·엄지·오압현 | `gpu/contact.py` |
| GPU 기하·압현면·손목 영역 | `gpu/geometry.py` |
| GPU 장면·강체 기타·선별 충돌 | `gpu/scene.py` |
| GPU 에피소드·자세·움직임 진단 | `gpu/episode_diagnostics.py` |
| 악구 환경과 현재 단순화 환경 | `gpu/finger_skill_environment.py` |
| 공통 기하·관측 상수 | `core/geometry.py` |
| CPU 접촉·타현·음별 측정·안전 | `core/measurement.py` |

현재 GPU 경로는 공용 설정을 얻기 위해 CPU runner를 불러오지 않는다. CPU/GPU가 같은 `LEFT_FIELDS/LEFT_SCALES`, `HISTORY_FIELDS/HISTORY_SCALES`를 사용하되 CPU song 환경·원장을 경유하지 않는다. 제어 속도표는 `core/control.py`에 있고, 초기 자세 입력 loader는 CPU `PreparedSession`을 불러오지 않는다. CPU 클래스는 `runtime/native_session.py`에서 기존 상속·동작을 유지한다.

## 검증 결과

- 전체188개 검사 모듈·1,318건 실행:158모듈 통과, 기존30모듈 실패 유지. 실패 모듈·검사 사례·예외 메시지가 변경 전과 일치하며 새 실패는 없다. 변경 전507개 소스 SHA가 직전 전체 검사의 봉인과 같음을 확인했다.
- 원문 정책과9가지 설정에서 구조·초기 파라미터·RNG·확률·행동 출력이 완전히 일치했다. 설정 정상3종·거부7종도 결과가 같았다.
- 이동한 함수·클래스·상수 AST를 대조했다. import 위치·참조 경로·충돌하는 private 이름 변경 외 계산을 유지했다. 기록·설정 모듈의 지연 import를 확인했다.
- GPU PhysX·GPU tensor pipeline에서2환경·H8·small·2업데이트·32전이 학습을 완료했다.561상태·기존 계약과 모델 저장·장면 종료를 확인했다.
- 위 모델을 동일 소스에서 strict 재개하여1업데이트·16전이를 추가했다. optimizer_updates는2→3이며 입력 변경·누락 pin·cleanup 오류가 없고 장면 종료도 확인했다.
- 모든487개 Python 문법, 보관535개 SHA, native65개와 보호 소스3개 원문 불변을 확인했다.
- 별도 change-reviewer의 정적·독립 CPU·기본 연결 그래프 대조는 [검수 기록](review.json)을 따른다.

GPU 최초 시도 `gpu_smoke`는 실행 환경의 PATH에 rl38/bin이 없어 Ninja를 찾지 못하고 장면 구성 전에 종료했다. 원자료는 보존하고 올바른 환경 PATH로 새 `gpu_smoke_v2`를 실행했다. 소스를 바꿔 오류를 우회하지 않았다. 짧은 구동·재개 확인이며 연주 성능·장기 안정성 개선의 증거는 아니다.

## 원문과 체크포인트

[보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_domain_consolidation/manifest.json)에 변경 전507개 Python·문서28개, 원래 경로·SHA·통합 위치를 기록했다. 기존 사용자 변경도 보관 시점 그대로 포함한다. 과거 결과·native·자산·checkpoint pin은 수정하지 않았다.

변경 전 체크포인트는 소스 경로·SHA가 달라 통합 후 코드에서 바로 strict 재개·평가할 수 없다. 당시 소스로 재현해야 하며 현재 코드는 보관본을 import하거나 입력 검증을 완화하지 않는다.

## 검사 자료

[검증 요약](validation.json) · [CPU 검사](cpu_test_summary.json) · [실제 검사 출력](cpu_test_output.txt) · [전후 검사 비교](test_comparison.json) · [정책 동등성](policy_equivalence.json) · [연결40개 목록](dependency_after.json) · [독립 연결 그래프](independent_graph.json) · [독립 검수](review.json)

실제 GPU 결과는 [새 학습](gpu_smoke_v2/report.json)과 [재개](gpu_resume/report.json)에 있다. [계획·체크리스트](/home/ajou/yigyu/3/docs/plans/guitar_learning_domain_consolidation_20261028.md).
