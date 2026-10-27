# Submitted-goal Chest 보존과 Spine 분리의 조건부 정적 진단

현재Body9+.15 후보의 실제 repeat Spine source FAIL과 이전 actual-Chest 보존3후보 selected=None을 보존한다. 이전 .15mm actual-Chest 보존해도 submitted목표의 Chest pose가 약5.923µm/.00331° 달라 엄격보존이 실패했다. 제어할 실제 제출목표의 Chest pose를 보존하는 독립 가설을 검사한다. source1mm·Spine5° 원 기준을 완화하지 않는다.

새9변수는 Torso/Spine/Chest xyz의 추가증분이다. worst repeat step6524에서 submitted target FK Chest pose6 보존과 actualFK Spine 고정법선 Δg1의 총7제약을 최소norm으로 풀이한다. .12/.15mm 두 요구만 검사하며 .10mm의 사전 .95mm여유부족과 .20mm tilt경계 실패를 지우지 않는다. 원±.03rad bounded search와 strict targetChest 위치1e−7m/회전1e−6rad·Δg1e−7m 허용을 유지한다. actualChest 변화≤10µm/.01°, actual/target 후손 R_Shoulder·L_Wrist·Head 변화≤.1mm/.01°를 사전 보조한계로 둔다. 원 source private .95mm/Spine private4.95°와 Torso/Chest5°·right3°/원 bounds·principal160°/other96·zero8/F32를 분리한다.

새증분만16..16.5초 smoothstep으로 가산한다. 기존Body9의10..10.5와 별도Chest+.005 순서는 유지하며11..16 정지5초 및16초 경계는 변경0이다. 제출목표 두 가산경로는 Root와 정확순서를 확정하여 코드/CPU에 명시한다. 실제입력/목표각은 원 initialFK보정을 그대로 사용하고 actual시점 재보정은0이다.

한표본만으로 선정하지 않는다. main은 두 point해 각각에 대해 baseline_v8/repeat_v8 실제5..28 전60Hz+종료1381행씩 조건부예측을 수행한다. 각 actual Torso/Spine native pose에 FK(q+increment*ramp)·FK(q)^−1을 rigid delta로 적용하고 원G actual worldpose를 고정한다. 두부위×physicalG89의178 활성쌍 직접평면 g≥−.95mm와 pose/tilt/변경9bounds/목표F32·다른96·zero8를 전행 확인한다. 불충분한 certificate만 frozen QP/complete convex후보로 정밀화하며 대형self Minkowski는0이다. 원native g와 원FK g, anchored조건부g와 전기간원105 EPS0false를 따로 보존한다.

이 가설은 기타추종/실제동역학/손추종/현재 LH grip544FAIL을 개선했다는 증거가 아니다. 원initial-FK error표, 실제원결과와 sourceplane 판정은 보존한다. actual_dynamic_tracking_validated/fullself/cooked/final_adoption_eligible=False, native/gain/PPO/A변경0이다.

순서: 계획·사전SHA → 실제schema/원FD/two-space/순서/F32/ramp 최소CPU(optimizer sentinel, main0) → source동결 → 독립검수·Root ACK → Root의 optimizer+전행 main. ACK 전 optimizer/full sweep은 실행하지 않는다.
