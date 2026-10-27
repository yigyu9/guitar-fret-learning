# 준비 자세 유지 제어 후속 계획

2026-10-17 KST. 최신 요구조건은 `paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/REQUIREMENTS_v2.md`이다. 이 문서는 후속 계획이며 새 runtime·native·연속77초 실행을 완료했다고 뜻하지 않는다.

## 현재 판정과 변경 근거

.15mm 추가 Spine 여유 후보(native_baseline_v8/native_repeat_v8)는 정지5초와 반복 타현의 기본 동적 지지·발·타현·건강 수치 budget을 통과했다. 그러나 반복 타현 source 검사에서 Spine/Torso와 LH_grip 두 조건이 실패했으므로 채택하지 않는다. 같은 원자료의 누락12부위 감사는 두 실행 모두 통과했다. 임계값을 완화하거나 강도를 키우지 않고, 실제 q와 제출 목표의 차이를 반영한 최소 수정을 먼저 진단한다.

## 단계와 확인 기준

- [x] 기존 자료의 추가12부위–기타 source1068쌍을 전 구간 확인한다. 각1381시각, 부족0. 기존 반복 타현의 두 실패는 유지한다.
- [ ] Spine 수정: 제출 목표의 Chest pose를 보존하고 실제 자세에서 Spine 여유를 늘리는 두 작은 증분을 진단한다. 원 Body9/Chest 보정10..10.5초와 정지11..16초를 보존하고 새 증분은16..16.5초에만 부드럽게 추가하는 조건을 검토한다. 목표와 실제 두 좌표계, 전행 조건부 source·tilt·제한을 구분한다.
- [ ] LH 수정: 실제16초 자세와 제출16초 자세의 기타 상대 기준을 비교한다. 실제 관절–목표 오차를 보존한 증분 응답을 주된 조건부 예측으로, 완전 추종 가정을 보조 진단으로 기록한다. 실제 손가락의 native 형상은 손목의 공통 rigid delta로 운반하고 오차 있는 전체 손가락 FK로 대체하지 않는다.
- [ ] 두 진단의 독립 검수·Root ACK 뒤 실제 계산을 수행한다. 유효 후보가 없으면 새 제어에 넣지 않는다. 계산에서의 통과는 실제 동적 통과가 아니다.
- [ ] 선택된 경우에만 새 runtime/runner/분석기/설정/Root 실행 wrapper를 작성한다. 기존 소비 코드·설정·결과는 보존한다. 기존 finite effort/SO3·gain/cap·Root 고정·하체 해제·기타 자유 조건을 유지한다. LH는 gripped 구간16초 이후 arm12 목표에만 보정하고 finger14와 RH finger21은 유지하는 얇은 확장을 우선 검토한다. 기존 release/regrasp 경로는 분리한다.
- [ ] 새 Root wrapper는 baseline 분석의 정확29 gate와 action 분석의 정확30 gate 및 `--baseline` 실제 명령을 확인한다. 부분 분석 통과와 source 전체 조건을 구분하며 실패 후보로 다음 물리를 진행하지 않는다.
- [ ] 새 regular 실행에서 native joint 이름·type, DOF type, 사용 가능한 actor DOF frame·joint transform을 getter로 기록하는 방안을 포함한다. 설치된 Gym의 local API 설명을 먼저 읽고 반환 schema를 작은 CPU fixture로 확인한다. joint frame의 의미나 내부 SDK revision을 추측하지 않는다. getter 기록은 상태나 목표를 변경하지 않아야 한다. 이는 미기록 native 좌표 정보를 보완하는 것이며 제한 잔차 원인 확정을 선취하지 않는다.
- [ ] 생산 코드 독립 검수·CPU 검증·prospective 입력 봉인 뒤 정지5초가 포함된 baseline부터 실행한다. 기본 지지/발/타현/형상/수동/건강과 압현 준비 기하를 모두 검사한 뒤 repeat→release15→free_strike→regrasp를 같은 후보로 차례로 진행한다. 각 실패는 보존하고 다음 실행을 멈춘다.
- [ ] 단독5단계가 통과하고 최종 불채택 사유가 해결된 경우 연속77초와 fresh77초를 각각 확인한다. 기존77 설계의 절대 일정과 두 해제15초 조건을 유지하되, 새 Body9/LH 유지 보정으로 변경되는 목표 소유권은 새 버전 설계에서 명시한다. 원 계획의 첫59초 전체 목표 literal 동일 주장을 그대로 전용하지 않는다.

## 해석 제한

원97축 scalar limit EPS0와 zero8 실제 미세잔차, solver 원인 미확정은 수치 budget와 별도로 보존한다. 정적 source 방향분리 예산은 cooked 침투 깊이가 아니다. 준비 중 원본 형상과 실제 fresh 접촉·전 구간 동작을 구분한다. 현재 비충돌 string marker와의 기하적 타현/압현 준비는 실제 현 힘·진동·음향 검증이 아니다. 새 PPO, 기타 직접 보조 힘·고정·매 step 상태 주입은 도입하지 않는다.
