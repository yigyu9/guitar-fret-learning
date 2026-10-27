# 첫 두 음 도달성과 전환 학습 구조 — 구현·검증 결과

2026-10-19 구현. **새 구조와 자료 채택 경로를 구현했지만, 현재 기하 교사는 두 단음의 실제 압현에 성공하지 못했다. 성공자료 BC·교사 없는 정책 평가·PPO는 아직 실행하지 않았다.** 기존 모델과 실험을 수정하지 않았다.

## 구현한 것

- [코드와 실행 방법](../../../../../guitar_learning/transition/README.md): `task/metrics/environment`, `solver/teacher`, `probe/capture`, `policy/transfer/learning/train/evaluate/worker`를 새 `guitar_learning/transition/`에 분리했다.
- 첫 목표 A(2번 줄 7프렛 약지/down), B(2번 줄 5프렛 검지/up)의 개별 도달·유지·해제, A clean+B positive 준비, reset 없는 A→B 전환 task를 구현했다. 원곡 고유 목표 30개와 순서 있는 전환 55종을 목록화하는 함수도 제공한다. 전체 30목표의 도달성을 검증했다는 뜻은 아니다.
- `pair`는 음악 시간만 0.25/0.5/1배로 변경한다. 물리240Hz·정책60Hz·원 제어/안전 기준은 유지한다. 속도 간 자동 checkpoint 승급은 구현하지 않았으며, 각 task 계약으로 BC와 실제 평가를 다시 수행한다.
- 실제 동작 전에 관측을 저장하고, 행동당 4개 물리 표본에서 음악·안전을 재계산한다. SHA·시계·원자료·최종 publication까지 확인한 성공 case만 BC 자료로 받는다.
- 500차원 관측/39행동을 유지하는 목표 조건부 왼손 정책과 BC를 연결했다. 기존 24-update 모델에서는 선택 Actor/std만 이전한다. Critic·Adam·PPO 카운터는 새로 시작한다. 오른손 비활성 6축은 정확히 0이며 원 물리·기타 자유 조건은 유지한다.
- 동일 BC와 task의 **교사 없는 native 성공 case 4개**를 확인해야 fresh PPO가 시작된다. 원 모델이나 교사 성공을 정책 성공으로 상속하지 않는다. 왼손-only와 joint의 성공 기준도 분리했다.

## 실제 검증

[CPU 기록](cpu_tests_v1.log): **53개 통과, 94.485초**. 목표/시간표, 하위 프렛 사전접촉, 접촉 기반 해제, 행동 제한, 관측 정규화, 실제 원 모델의 선택 Actor 이전, BC·PPO gate, 실제 측정 재계산과 위조/누락/순서/cleanup 반례를 검사했다. 이 중 정상 capture fixture는 과거 실제 상태를 고정한 CPU 재생이므로 새 물리 성공으로 세지 않는다.

별도 change-reviewer가 최종 변경을 검수했고 Critical/Warning은 없었다. 동결된 활성 파일·보관본 24개의 SHA 일치도 독립 확인했다.

| 실제 실행 | 완주 | 압현 유지 | 종료·자료 판정 |
| --- | --- | --- | --- |
| [A 교사 v1](single_a_solver_v1/result.json) | 4초 / 240행동 / 960물리표본 | clean 0% | 안전 완주·정상 close, 성공자료에서 제외 |
| [B 교사 v1 실패 기록](single_b_solver_v1_process_failure.json) | 미완주 | 판정 불가 | SIGFPE/exit136, producer 최종 결과·close 기록 없음, 제외 |
| [B 교사 v2](single_b_solver_v2/result.json) | 4초 / 240행동 / 960물리표본 | clean 0% | 동일 입력 재실행, 안전 완주·정상 close, 제외 |

각 완주 실행은 create_sim/create_env 1회, load_asset 2회, destroy_sim 1회였다. 기타 직접 보조/실행 중 상태 덮어쓰기 등 금지 호출은 0회였고, 입력 변경·누락 import pin·물리 조건 변경은 없었다. 현재 native는 PhysX CPU 장면이며 정책 장치 설정 `cuda:0`과 구분한다.

B v1의 부분 gzip에서 온전히 복구된 마지막 행은 0.533333초였고 그때 안전 종료 이유는 없었다. 버퍼에 남은 후속 행이 있을 수 있어 이것을 정확한 crash 시점으로 단정하지 않는다. 같은 입력 v2는 완주했으므로 수치 오류 원인은 아직 확정하지 않았다. v1 원자료와 로그는 그대로 보존했다.

`capture.audit_capture`가 위 세 실제 실행 모두를 학습 자료에서 거부함도 확인했다. [검증 요약 JSON](verification_v1.json)에는 각 producer 결과·lifecycle·SHA와 거부 이유를 보관했다. 겹친 준비와 느린 전환의 native 성공 검증은 단음 성공 뒤에 수행하며, 이번에는 시행하지 않았다.

## 첫 음 실패에서 확인한 것

정적 solver는 source 손가락 표면을 목표 현에서 약 0.5mm 떨어진 곳까지 배치했으나, 실제 재생의 2~2.5초 구간에는 원본 STL 표면을 측정 body pose로 변환한 뒤의 목표 거리가 약 4.7mm였다. 가상 현 목표에 가장 가까운 해당 표면점의 높이는 현보다 약 4.5mm 높았다. 이 거리는 cooked 충돌 형상의 접촉 간격이 아니다. 별도로 해당 손가락의 실제 접촉도 관측되지 않았다.

같은 구간에서 측정 관절각으로 FK를 다시 계산하면 손가락 body 위치가 native와 약 0.04mm 이내로 맞았다. 기타 이동은 약 0.6mm였다. 반면 팔 관절의 목표 대비 잔류 오차가 복합되어, 목표각의 정적 표면 위치와 실제 표면 위치가 달라졌다. 접근 명령이 끝난 뒤에도 이 차이가 거의 줄지 않아, **현재 증거로는 유한 제어의 잔류 추종 오차를 실제 접촉 관측으로 보정하는 것이 다음 우선순위**다. 정확한 힘 수준의 원인을 확정한 것은 아니다.

또 하나의 독립적인 한계는 solver가 겨냥한 가상 현 중간점 자체가 충돌 표면이 아니라는 점이다. source 형상 기준 원하는 표면점 높이 11.8mm는 평평한 넥 표면 9.3mm보다 2.5mm 높다. 따라서 관절 추종을 개선해도 현재 목표만으로 실제 접촉을 보장하지 못한다. 실제 허용 프렛/넥 표면과 접촉 증거를 함께 사용해야 한다. 이는 XML/OBJ 기하 분석이며 PhysX cooked 형상·rest offset·침투 깊이를 측정한 결과가 아니다. [전체 분석과 소비한 28파일 SHA](single_a_diagnostic_v1.json)에 수치·표본 범위·계산 한계를 기록했다.

접촉하지 않은 음의 해제 부재율이 100%여도 도달·유지 실패를 상쇄하지 않는다. 손끝 거리나 정적 최적화 성공만으로 BC 자료를 채택하지 않은 이유다.

## 다음에 할 것

1. 같은 물리·gain·행동 범위 안에서 실제 손/기타 상태와 접촉을 보며 접근 목표를 작게 보정하는 교사를 새 버전으로 구현한다. 접근점도 허용 프렛/넥 표면을 기준으로 검토한다. 준비시간만 늘리거나 gain·가동범위를 늘려 성공을 대신하지 않는다.
2. A/B 각각의 실제 도달·유지·해제를 확보한다. B 최초 실행의 native 수치 오류도 별도 추적한다.
3. A clean+B positive 준비 후 A 해제→B clean을 같은 실행에서 검증한다.
4. 성공자료 BC→교사 없는 실제 평가 4회→fresh PPO를 진행한다. 0.25배 전환부터 시작하고, 속도별 계약과 성공 근거를 다시 만든다.

새 BC/PPO 결과나 모든 목표 도달 가능성, 두 음 전환 성공, 전체 곡 개선을 현재 결과로 주장하지 않는다.

## 설정·보관 위치

- 단음: [single_a_settings_v1.json](single_a_settings_v1.json), [single_b_settings_v1.json](single_b_settings_v1.json)
- 준비/전환: [overlap_settings_v1.json](overlap_settings_v1.json), [pair_quarter_settings_v1.json](pair_quarter_settings_v1.json), [pair_half_settings_v1.json](pair_half_settings_v1.json), [pair_original_settings_v1.json](pair_original_settings_v1.json)
- 초기 소스 14모듈+10검사: [source_pins_v1.json](source_pins_v1.json), `source_snapshot_v1/`
- 과거 입력·현재 동결본·native 시도 보존: [preservation_audit_v1.json](preservation_audit_v1.json), **18개 manifest / 1,964개 서로 다른 파일 확인, 불일치 0**. 이는 실제 접촉 성공과 별도의 보존 검사다.
- 작업 체크리스트: [구현 계획](../../../../plans/guitar_learning_transition_20261019.md)

설정의 기본 PPO 예산은 연결 검증용이며 장기 학습에 선정된 값이 아니다. 새 결과는 존재하지 않는 새 디렉토리에 생성하며, 기존 실행 입력과 실패 기록은 덮어쓰지 않는다.
