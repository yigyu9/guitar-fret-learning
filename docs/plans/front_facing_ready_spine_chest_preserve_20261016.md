# Chest 전체 pose 보존·Spine source 분리 여유 — 정적 가설 v1

2026-10-16. 담당 범위는 새 `diagnose_spine_chest_preserve_candidate_v1/`와 본 leaf다. 원 소비 코드·기록·모델·gain·native·PPO를 변경하지 않는다. 코드 작성과 작은 schema/수학 CPU까지만 진행하고, 코드 동결·독립 검수·Root ACK 전에는 optimizer main이나 전행 sweep를 실행하지 않는다.

## 관측과 가설

원 `.15mm` 후보 `native_repeat_v8`의 source scan은1381시각 중368시각에서 부족했다. worst는 step6524(27.1833333333s), `human/Spine/0`–`guitar/G:body/55`, g=−0.0010543345401829995m다. 원 수치 QP의 primal/dual gap 약1.53e−16m는 해당 numerical hull의 근거이며 cooked 침투나 exact arithmetic 최적성의 증명이 아니다. 원 source FAIL은 유지한다. 원 core29 PASS와 `--baseline` 누락에 따른 expected30 비교 미완료도 별개이며 본 진단이 대신 닫지 않는다.

가설은 현재 Body9 상수에서 작은 추가9벡터를 찾아, **현재 FK(q)의 Chest full world pose6를 보존하면서 Spine source를 원 worst 법선 방향으로 이동**하는 것이다. Chest 전체 pose 고정이 후손 R_Shoulder/L_Wrist/Head FK world pose도 보존하는지는 실제 계층과 계산으로 별도 검사한다. 팔 전체의 실제 고정·접촉 하중·동적 안정 성공으로 표현하지 않는다.

추가로 확정된 LH grip source FAIL(1381시각×1602쌍 중544부족, worst index1–guitar root g=−1.176551591mm@step6644)은 별도 문제다. Chest 보존이 이 실패를 고친다고 가정하지 않으며 LH goal/손가락/원 문턱을 변경하지 않는다. 이번 가설은 Spine 한 표본에 한정한다.

## 고정된 입력과 좌표

원 initial state/q_ref로 구성한 `controller_horizontal_v4.full_fk`를 그대로 사용한다. 현재 actual state로 FK zero를 재보정하지 않는다. 설계점은 원 worst step6524의 native q105이며 기타의 native world pose/vertices와 원 source 형상을 고정한다. 법선은 실패 source summary의 unit world normal을 직접 대조한다.

g(n)=min(Spine source projection)−max(G source projection)이다. Capsule은 원 axis 두 점의 최소 projection에서 radius를 빼고, G는 원 vertices 최대 projection을 쓴다. 원 frozen source primitive/compiled placement를 재사용하며 큰 Minkowski hull이나 새 법선 탐색은 하지 않는다. 법선을 고정했으므로 이 계산은 명시된 방향의 source certificate와 그 변화다.

`g_native`, `g_FK(q)`와 그 차이를 먼저 기록한다. 새로운 값은 `Δg_FK=g_FK(q+δ)−g_FK(q)`이며 `g_native+Δg_FK`는 **동일 기타 pose·기존 오차 유지·완전 추종을 가정한 조건부 예측**이다. native 새 gap이나 실제 추종 관측으로 부르지 않는다. FK before/after와 native 값을 섞어 하나의 실제 측정처럼 쓰지 않는다.

## 문제와 사전 기준

변수는 Torso/Spine/Chest xyz의 추가δ9다. 현재 static Body9 및 기존 Chest+.005를 포함한 총목표와 추가항을 분리해 기록한다. 목적함수는 ½||δ||²이며 공통 작은 해를 우선한다. 각 추가축 검색은±.03rad 및 원 actual/target bounds의 교집합, principal<160도다. 이 bounded search 실패를 전역 불가능으로 주장하지 않는다.

동등식7개는 Chest 위치차3(m), `Log(R_Chest_before⁻¹ R_Chest_after)`3(rad), 고정법선 Spine Δg(m)다. 위치/Spine은 m, rotation은 길이척도.1m를 곱해 mixed-m residual/Jacobian을 구성한다. SVD singular values·rank·FD1e−5/1e−6/1e−7 차이·linearized residual을 기록한다. 형식상7식이라도 실제 rank7이라고 가정하지 않는다. rank 부족/중복·비선형 제약의 불가능·optimizer 실패를 보존한다. tilt/heading은 작은 norm과 명시 부등식으로 제한하며 추가 동등식은 도입하지 않는다.

세 가설은 추가 Δg=+.10/+.15/+.20mm뿐이다. 선택 기준은 모든 다음 항목의 AND다.

- optimizer success 및 Chest 위치잔차 norm≤1e−7m/회전잔차 norm≤1e−6rad, Δg 잔차≤1e−7m.
- actualq 반사실과 제출목표 반사실의 float64/float32 모두 같은 pose 잔차 기준을 만족한다. 실제 target에서는 목표 자체를 native q로 교체하지 않는다.
- 위 조건부 native 예측 g≥−.00095m. 원1mm 판정은 불변이며 이.95mm는 새 후보 설계 여유다. .10mm는 이상적인 선형 예측도−.9543345mm여서 이 여유를 못 채울 수 있다.
- Torso/Chest 전체 tilt≤5도·옆기울기 절댓값≤3도, Spine tilt≤4.95도. 4.95는 원5도보다 엄격한 후보 여유다. 어느 경로든5도를 넘으면 거부한다.
- 제출목표105의 원 bounds, actual 반사실의 수정9축 원 bounds, zero8 및 다른96 bit-exact 보존, Body9 principal<160도, finite. actual q의 기존 다른축 limit 잔차는 전105 eps0 결과와 변화/불변을 분리하여 보존하고 숨기지 않는다. 이는 actual 전105 bounds 성공 판정이 아니다.
- Chest 후손3체의 위치/회전 변화도 위 Chest 잔차 기준 이내인지 독립 검사한다. 해당 조건이 계층상 성립하지 않으면 실패/범위 제한을 기록한다.

세 후보가 통과하면 최소 ||δ||, 동률은 더 작은 요청 Δg 순으로 **정적 선별**한다. 하나도 없으면 후보 없음이다. optimizer success나 design 통과는 실제 source 전행/동적 성공·채택을 의미하지 않는다.

## 두 경로와 float32

actual q105+δ와 같은 시각 실제 제출목표105+δ를 별도로 FK 평가한다. 실제 목표는 원 current Body9→Chest+.005 계층 metadata와 대조해 현재 총 static9와 추가δ9를 분리한다. 제출목표에 더한 경로는 동적 controller를 다시 실행한 결과가 아닌 반사실이다. 두 경로 모두 δ 가산 전후와 float32 round-trip 후의 FK pose/g/tilt/bounds/zero8/other96를 기록한다. 원 control rate/cap 또는 목표를 더 크게 바꿔 합격시키지 않는다.

## 증거와 실행 범위

선택 input closure는 원 actual run attempt/config·report·initial/native properties·states240/targets60·source summary/원 source expected maps·원 primary 모델108(선언자산106+manifest2)·직접 소비 frozen helper/source·본 leaf/새 코드/CPU 원문을 사전 SHA 고정한다. flat/envelope map을 실제 schema로 추출하고 동일 path의 충돌은 거부한다. 과거 expected map의 선택 key를 검증하며 새 A glob로 과거 소비 범위를 확장하지 않는다. 새 source 전에 before를 기록하고 종료 후 same SHA를 확인한다.

최소 CPU는 실제 최상위 schema와 step6524 state/target 연결, 원 source compiled placement, unit normal projection 대조, FK initial 재구성·작은 FD/Jacobian, 합성7×9 minnorm/rank 부족/NaN·위조 SHA/외축변경 거부다. 이 CPU에서 실제 optimizer main과 전행 sweep를 실행하지 않는다. 작은 actual schema 검사는 실패 worst의 재측정/전행 인증이 아니라 코드 입력 계약 검사다.

- [ ] 새 코드·leaf·입력 before·최소 CPU를 동결한다.
- [ ] 다른 reviewer가 코드/CPU/조건부 해석을 검수하고 Root가 정확한 SHA를 ACK한다.
- [ ] Root가 새 output으로 세 후보 optimizer main을 한 번 수행한다.
- [ ] 정적 후보가 있으면 Root가 별도 승인된 전행 반사실을 설계/검수한다. 이 버전 자체는 worst 한 표본만 다룬다.
- [ ] 새 native는 이후 별도 계획/소스/독립 검수 없이는 실행하지 않는다.

본 가설은 기존 source FAIL·건강 eps0/cause false·원 first59/후속77 설계와 독립이다. 실제 전행 source 및 현재 하중제어·장시간 건강 검증을 대체하지 않는다. 후보 자동 채택과 새 PPO는 없다.
