# 유한 왼손 유지 제어와 작은 엄지 자세 보정 — 구현 전 설계

이 문서는 후속 구현 설계다. Thumb 후보는 아직 선정되지 않았고, 새로운 Motion/정규 native 실행은0이다. 이전 V2/V4의 실제 실패는 보존한다. Body .12mm 새 경로 설계만 별도로 다음 동적 시험 후보로 선정됐다.

## 현재 실제 정적 진단

V4의 고정16초 관절 오차 보정은16/23.05초 표본의 source를 통과했으나27.683/28초에는 엄지 끝과 기타 root 형상 두 개에서1.085122/1.203464mm로 실패했다. 현재 오차를 매번 완전히 상쇄하는 이상적 증분식은 source를 통과했지만 실제 제출 손목 목표가 음수 등 원 범위를 벗어나 채택하지 않았다. 반복 적용 시 적분서보가 되는 문제도 별개다.

따라서 유한 관절 gain을 올리거나 범위를 바꾸는 대신, 고정오차 보정과 LH:thumb3 한 축의 작은 펴기를 먼저 별도 진단한다. 새 설계 후보는 기존 range/PD를 유지한다. 실제 baseline8 thumb3 native POSITION의 stiffness20Nm/rad, damping5Nms/rad, effort4Nm이며 이를 바꾸지 않는다.

## 이후 구현의 전제

새 thumb 정적 코드의 독립검수·RootACK·실제 조건부 평가가 끝나고, 지정된 작은 각도 하나가 모든 조건을 만족할 때에만 다음 구현에 연결한다. 원 thumb3 joint body-local axis와 초기 native DOF frame의 대조 및 G와 활성 nonadjacent 신체 source도 확인한다. 원 getter V2의 전체 종료1·이름 수 불일치는 그대로이며, 선택한 raw axis 자료만의 증거와 구분한다. 실제 새 힘/접촉/동적 추종 성공은 선취하지 않는다.

## 새 Motion의 최소 책임

원 Motion1의 RH distal6 타현·손가락21 고정·release/regrasp 수학은 상속한다. 새 변경은 gripped 구간의 LH arm12 유지와 thumb3의 한 축 목표다. parent.apply의 원 중간 결과를 보존하고 새 최종 요청·목표 소유권을 별도 기록한다. 기타 상태·base_target·native props·외부 시간·원 spec은 수정하지 않는다.

- 16초 실제 native wrist의 G상대 위치/방향과 e16=actual_arm12−직전 제출_arm12를 별도로 저장한다. actual10 원 참조는 해제 거리 등 기존 검증용으로 유지한다. 16경계 목표는held exact이며 IK를 호출하지 않는다.
- gripped 및 t>16에서 실제 q 기반의 desired-actual 손목 IK를 계산하고, command12=desired_actual12−e16을float32로 변환한다. desired-actual numerical fit10µm/.01도, 최종 command 원 bounds/qref±.8/principal160도·실제 제출/속도 제한을 구분한다. 실패하면 원자료를 남기고 중단하며 목표를 몰래clip하거나 상태를 바꿔 통과시키지 않는다.
- 고정 e16은 실제 추종 오차가 항상 같다는 보장이 아니다. 원 PD·힘 제한을 유지하며 실제 원자료로 검증한다. 현재 오차를 매번 더하는 이상적 fullstep 적분식을 생산 제어로 채택하지 않는다.
- 처음에는 기존 open/withdraw/free/approach/close/regrasp_hold의 arm IK를 유지한다. regrasp 구간을 새 gripped 제어 성공으로 소급 해석하지 않는다. 이후 실제 검증이 실패하면 새 버전으로 보완한다.

## 엄지 목표의 연속성

정적 후보 각도를 δ라고 할 때 새 thumb3 요청은 누적 덧셈이 아닌 원 nominal closed/open 경로에 대한 절대 보정이다. a=smoothstep(t,16,16.5)이며 원11..16 목표는 그대로다.

- gripped의 비경계: original_closed_thumb+δ·a. parent가 held를 반환하므로 이전 held에 δ를 반복해서 더하지 않는다.
- open의 비경계: 원 parent thumb 요청+δ·a·(1−opening_fraction).
- withdraw/released_hold/approach: 원 open 목표 그대로, 보정0.
- close의 비경계: 원 parent thumb 요청+δ·a·close_fraction.
- regrasp_hold의 비경계: original_closed_thumb+δ·a.
- 모든 parent phase 경계: 기존 제출 LH26 exact를 유지한다. parent가 이미 보정된 held를 반환할 수 있으므로 다시 δ를 더하지 않는다.

이렇게 해제·닫힘 경계에서 엄지를 원 closed로 순간 복귀시키거나 보정을 이중 적용하지 않는다. 다른 LH finger13과 나머지 고정7, 모든 RH finger21 목표는 원대로다. 엄지는 원14개 개방 축 중 하나이며 압현 검지 목표를 바꾸지 않는다.

새 metadata는 parent의 원 요청과 새 arm/thumb 요청, 보정 계수·nominal closed/open·실제 final target·16 reference·정적 선정 근거를 각각 저장한다. 기존 ownership=True를 그대로 전용하지 않고 parent 부분과 새 부분을 따로 확인한다.

## 검증과 진행 순서

새 Scene8의 oldBody9→새증분→Chest 가산 순서와 결합하되, LH 제어는 실제 q를 바탕으로 계산한다. 초기/목표/drive/실제 state를 같은 것으로 취급하지 않는다. 생성자 바인딩은 최소 범위에서 연결하고 정상·예외 복원 및 native/state/base 불변을 CPU로 확인한다.

CPU에서는16 및 각 open/withdraw/free/approach/close/regrasp 경계·엄지 보정 이중가산/경계점프·다른 finger/zero8/Rprox 변경·command bounds/미세변환·오류 기록을 검사한다. 새 runner/분석/source/manual/health/Root wrapper를 함께 독립검수·입력 봉인한다. 기존 source/static 선택의 False와 actual EPS0·solver cause 미확정은 보존한다.

이후 동일 후보로 정지5초 포함 baseline→반복 타현→완전해제15초→해제 타현→재접촉을 순서대로 실제 검증한다. 새 몸통과 왼손을 합친 동적 효과는 개별 정적 진단으로 보증하지 않는다. 통과 전77초/fresh/PPO는 실행하지 않는다. 실패나 미완료는 같은 자료 디렉토리에 새 버전으로 보존한다.
