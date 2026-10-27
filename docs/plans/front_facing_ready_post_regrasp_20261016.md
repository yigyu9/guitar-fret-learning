# 재파지 후 재해제까지 포함하는 최초 연속77초·fresh77초 — 설계 제안

2026-10-16. 설계만 작성했다. 이 문서에 따른 구현·설정 생성·native·실제 후처리 실행은0이다. Root가 후보와 실행 순서를 선정한 뒤 새 버전 구현 및 독립 검수를 진행한다.

## 권고와 선행 조건

**동일 후보의 단독5단계가 모두 통과하면, 최초 연속 시험을 직접77초로 하고 동일 초기조건의 fresh77초를 한 번 수행하는 총2 episode를 권고한다.** 아직 실제 continuous59 자료가 없으므로 별도59초 실행을 선행 조건으로 추가하지 않는다. 단독5단계는 baseline/repeat/release/free_strike/regrasp이며, 각각 원 core·발·미디어 및 적용되는 추가 형상·수동·건강 조건을 충족해야 한다. 단독 결과들을 합쳐 연속 성공으로 표현하지 않는다.

현재 후보의 통과 여부를 이 설계가 인증하지 않는다. 설명되지 않은 제한초과 등 최종 불채택 조건이 남으면, 숫자 budget 통과만으로 위 선행 조건이나 최종 채택을 충족했다고 판정하지 않는다. 실패 시 원 자료를 보존하고 다음 episode를 자동 실행하지 않는다.

기존 `design_post_regrasp_release_v1.md`의58→76 설계와 protocol3의59초 계획·미실행 상태를 보존한다. 본 제안은 Root 선정 시 향후 실행 순서를 대체하는 새 계획이며, 과거59초 literal PASS나 실패 자료의 소급 성공을 만들지 않는다. 원76 설계의 source 계약 검사도 새77 구현의 검증으로 전용하지 않는다.

## 절대 일정과 비교안

|절대 시간(s)|왼손|오른손|
|---|---|---|
|0..16|원 초기화·준비·보정, 보정 완료 후11..16 정지5초|원2396 latch 유지|
|16..28|기존 grip|16/20/24 시작3왕복|
|28..31|opening28..29, withdrawal29..31|마지막 제출 distal6 hold|
|31..46|첫 완전 해제15초|33/37/41 시작3왕복,45..46 hold|
|46..55|approach46..48, close48..49, settle49..50, dwell50..55|hold|
|55..59|재접촉 grip 유지|55 시작1왕복|
|59..62|두 번째 opening59..60, withdrawal60..62|마지막 제출 distal6 hold|
|62..77|두 번째 완전 해제15초|64/68/72 시작3왕복,76..77 hold|

첫59초의 **계획된** 목표 경로·기존 물리 수학과 시간은 유지한다. 총10왕복이며 지정 현 통과는 각6 down+6 up, 총120 event다. 각 방향 준비·깊이·속도·순서·유한 segment/zone/lane 등 기존 기준을 그대로 적용한다. 76..77은 동작 후1초 hold이며 새5초 정지 성공으로 부르지 않는다.

대안67초는 첫59초 후 release59..62/free62..67/R63..67 한 왕복이다. 최초31..46의15초 요구는 유지되므로 이를 완화하는 안은 아니다. 다만 두 번째 재해제 내구성이5초이고 마지막 타현 후 hold가 없어 후속 하중 비의존성 근거가 약하다. 채택한다면 두 번째5초 전용 판정을 새로 정의해야 하며 원 free15 게이트를5초로 통과시키면 안 된다. 구현은 우선77안 하나만 선정하는 것이 최소 범위다.

## 고정 조건과 목표 소유권

동일한 원105 초기값·모델·chair/G 배치·원 root 고정·하체16 유한 제어·원0ROM8과105채널의 구분·gain/cap·solver/substeps·원 POSITION48/상태 보존을 유지한다. 기타는 자유 강체·중력ON·strapOFF다. 새 기타 힘/고정/부착/매 step 상태 덮어쓰기/중간 reset을 도입하지 않는다. 선택된 Scene의 Body9→기존 Chest 등 목표 가산 순서와10..10.5 ramp, 기존 SO3/Chest preload·제어 수학을 그대로 상속한다. substeps 진단을 정규 조건에 자동 채택하지 않는다.

LH26과 RH distal6 외 목표는 원 소유권을 유지한다. 타현 목표 변경은 R_Elbow/R_Wrist6뿐이며 proximal6 목표는 원 latch 그대로다. 실제 proximal 각 cycle1도 기준과 전체 누적 변화는 구분한다. RH finger21 목표는 원2396부터16..77까지 exact, 실제 변화·pick 상대기하도 기존 기준으로 전 구간 검사한다. 손가락이나 proximal arm을 새 타현 자유도로 쓰지 않는다.

원 task-chain10µm/.01도와 실제 native 손 형상 검사를 유지한다. 원 full105/finger FK false와 zero8의 실제 미세잔차를 숨기지 않는다. 엄격 task-chain 통과가 미래 손가락 FK 오차의 상한이나 실제 압현 성공을 보증하지 않는다. 넥 grip·압현 준비 기하와 실제 현힘·선택현 압현·진동·음향은 별개이며 후자는 이 계획의 인증 대상이 아니다. 새 PPO는 시작하지 않는다.

## Motion1 재사용과 두 번째 latch

원 `motion_v1.py`의 `apply`는 한 release/approach/close만 읽고, RH는 `strike_starts`를 순회한다. 새 Motion을 상속해 전체 계획에 seconds77, 미래 R starts64/68/72, post_release/post_free를 추가하고 case는continuous로 유지할 수 있다. 원 apply가 읽지 않는 미래 필드는59 이전 분기를 바꾸지 않는다. 이것은 정적 설계 판단이며 실제 새 코드의 동등성 검사는 별도다.

59 이전에는 원 parent.apply를 직접 호출한다. 59 이후에는 LH 유효 뷰만 release=[59,62], free=[62,77], approach/close/settle/dwell=None으로 선택해 동일 parent.apply를 호출한다. RH starts/case/절대 clock은 전체 계획과 동일하다. `finally`에서 `self.plan`의 원 전체 계획 객체를 복원한다. cfg dictionary·native 상태·시각을 임시 변경하지 않는다.

다음 두 종류의 anchor를 분리한다.

- 59초 actual LH q/wrist/G는 두 번째 해제의 실제 시작 진단 및 원 release_delta=현재 G_R·[.08,0,0]에 사용한다. 60초 withdrawal 원점은 기존 방식의 current q+직전 제출 LH12 FK다.
- phase_start26과59 경계 목표는 **직전 제출 LH26**을 exact 유지한다. 원 closed→open 식을 재사용하려면59 직전 제출 finger14가 원 closed reference와 exact인지 확인한다. 실제 손가락 q로 closed 목표를 바꾸면 안 된다.

`started`, `initial_left`, actual10 grasp_G/rotation_G, 원 initial FK·qref·bounds는 유지한다. actual10 기준 손목 이격/개방 판단도59로 재보정하지 않는다. `first_strike=16`, orientation_start/final_palm과 기존16..16.8 단일 orientation ramp를 유지한다. 기존 cycle6 이후 새 cycle7/8/9는 원 정상 분기에서만 새 current-G pick anchor를 잡는다. 59..64 및76..77에는 마지막 distal6을 hold하며2396으로 되돌리지 않는다. phase/started를 초기화하거나 경계에서 실행을 재시작하면 안 된다.

이 plan 선택만으로 Motion의 두 번째 해제 경로를 재사용할 수 있지만, 단일 release를 가정하는 분석기·source 감사·protocol guard까지 자동 호환되는 것은 아니다. 원 q-domain solve_wrist·float32·bounds/qref/principal 및 reach 조건을 유지하고, 실제 미래 상태에서 infeasible이면 중단한다. 아직 없는 actual59 상태로 사전 도달성을 보증하지 않는다.

생성자는 현재 Controller6 체인을 상속하고 원 effort 본문은 복제하지 않는 방식을 우선한다. 새 protocol/schedule과 새 Motion 연결을 생성자 범위에만 한정한다. 가능한 현 체인은 외부 runtime6의2 binding+runtime1.Motion1개, 내부 runtime5의2개, runtime1/motion1의3개로 **총8 attribute binding**이다. 구현 시 실제 목록과 정상·예외의 원 객체/내용 복원·native 불변을 검사한다. apply의 self.plan 복원도 별도다. 실제 Scene/Controller/Motion class명은 정직하게 기록한다.

## 첫59 경로 동등성과 실제 재현은 별개

실제59 reference가 없으므로 `literal59_passed`를 만들지 않는다. CPU에서는 동일 state/held-target 입력을 제공한 원 planned59 경로와 새77 경로의 첫59 목표·phase 수학을 비교한다. 시각0,4,..14156의 target3540행과 주요 경계·원 parent.apply 호출을 검사하되, cfg 길이/새 class·protocol provenance 차이를 숨겨 모든 metadata가 동일하다고 주장하지 않는다. 실제 native/foot IK를 실행하지 않는 adapter라면 그 범위를 명시한다.

최초77에서는 첫59의 event·물리·접촉·목표 소유권·제어 수학을 새 actual raw에서 직접 평가한다. 오래된 summary의 passed를 전달하거나 raw를59로 잘라 새 cfg를 임시59로 바꾸지 않는다. 실제 두77 episode 각각 원 baseline과 첫10초 raw exact를 확인한다. 두77 전체의 bit-exact는 사전 보장/필수 조건으로 추가하지 않고, 각 episode의 모든 조건 통과와 동일 초기 재시작을 실제로 증명한다.

## 전행·구간 표본 계약

외부240Hz, 목표60Hz와 기존 표본 시각을 유지한다. N=77×240=18480이다.

|자료/구간|기대 수와 끝점|
|---|---|
|전체 states/contacts|각18481, step0..18480, 마지막 상태 별도 final_state와 exact|
|전체 efforts|18480, physics_step_before0..18479|
|전체 targets|4620, physics_step_before0,4,..18476|
|계획 첫59 경계|states/contacts14161, efforts14160, targets3540; 실제59 reference는 없음|
|tail59..77|경계 포함 states/contacts4321, efforts4320, targets1080|
|첫 free31..46|step7440..11040, raw240 각3601/source60 각901|
|둘째 free62..77|step14880..18480, raw240 각3601/source60 각901|
|prepared5..77 실제 source60|4321, 전체 목표 시각+마지막 끝점|

누락/중복/순서·시각 오류/NaN/잘린 JSON/최종 endpoint 부재는 거부한다. 두15초를 합산하거나 한쪽 접촉률로 다른 쪽을 평균하지 않는다. 5fps capture를 그대로 사용하면 view당386 frame, 기존30Hz telemetry는2311 표본이다. 실제 적용 capture 설정과 step grid를 우선 검사하며 인코딩 길이를 raw sequence 증거로 대체하지 않는다.

## 분석기 재사용과 반드시 추가할 판정

원 analyze8의 measure/contact/sole·strike detector·readiness·N가변 duration_math_v2 및 margin→SO3→Chest→base 복원 수학은 재사용한다. 새 main은77 protocol/class/map과 전체18480 effort를 검사해야 한다. 기존 게이트를 제거하거나 빈 집합을 통과시키면 안 된다.

1. 원 left_evidence는 첫 release/free/approach/close/settle/dwell 뷰로 호출한다. 두 번째는 release59..62/free62..77이고 재접촉 필드가 없는 독립 판정 뷰로 호출한다. 둘 다 원 actual10 참조와 전체 absolute raw를 사용하고 각각 free15/raw3601/geometry901을 AND한다. raw LH–physicalG contact는 λ0까지 포함해0이어야 하며 양성0으로 대체하지 않는다. actual 손목-G60mm·signed opening·활성 source2mm도 각각 전행 판정한다.
2. ownership은 원 단일 release anchor/phase 사전을 그대로 전체77에 적용할 수 없다. 새 독립 절대 phase cursor가 첫째/둘째 anchor를 구분하고, 원 Body9/Chest 요청 복원 순서·other 축·phase 경계26 연속·R cycle10개와 metadata를 전행 검사해야 한다. actual10 reference 교체·cycle 중복·59 reset 오염 반례를 거부한다.
3. 각 준비/해제/완전해제/재접근/닫힘/settle/dwell/10개 strike/후속 hold와 전체5..77에 원 지지·발·전신 기준을 적용한다. 삼중 양성 지지95 기준은 각 창에서 독립이며 raw 접촉 존재와 구분한다. LH 비손가락 양성 접촉 금지도 기존 적용 창을 확장한다. 재파지 시 finger 접촉이 허용된다는 사실을 하중 비의존성으로 해석하지 않고, 이후 두 번째 완전 무접촉15초를 행동 근거로 사용한다. 하중분담률을 측정했다는 주장은 하지 않는다.
4. source 감사의 support/RH/Spine·Torso는5..77 전체 실제60Hz를 검사한다. LH grip1mm는 두 free의 **strict interior를 모두 제외**한2523시각이며 각 경계는 포함한다. 각 free2mm901표본은 별도로 유지한다. 기존 단일 free 선택기/old43 고정 scanner를 그대로 호출하면 안 된다. 원 compiled placement·source vertex·physical shape·활성/비활성 정책과 정밀 fallback을 보존한다. source 방향 분리 예산과 cooked 침투 깊이를 혼동하지 않는다.
5. RH event10왕복은 고유 event를 중복 소유하지 않게 하고6→1/1→6 및 방향을 곱한 signed speed 등 원 수식을 보존한다. RH21 실제 변화·pick-parent/palm·proximal 실제 각 cycle 기준과 full16..77 누적 변화를 모두 기록한다.
6. q105/dq/원zero8·요청/최종제출·sensor·cap·고주파 health는 전체77과 원 창 정의로 검사한다. 원 eps0 false/solver cause false 및 비단조·장시간 미설명 잔차는 budget와 별개로 보존한다. 짧은 substeps/PD 진단으로 장시간 문제를 소거하지 않는다.

## 누적 drift와 fresh 재현

원 initial-world G bodycenter 기준과 actual16 기준 Torso/Chest→G root6D를 전체5..77에 유지한다. 원30mm/5도 등 적용 기준을59에 다시 영점 잡지 않는다. 원 몸통·neck·lateral·발 높이/tilt/PTP/속도·actual16 발 회전·연속 접촉 누락 기준도 전체 창에서 유지한다. 접촉 소실과 실제 lift-off를 별도로 기록한다.

시각16/28/31/46/50/55/59/62/64/68/72/76/77의 G·몸통·발 잔차, 전 구간 최대와 최종 잔차,16→59와59→77의 증가를 남긴다. 59 기준 차분은 진단값이며 전체 기준을 대신하지 않는다. 최대 drift 외 누적 경로 길이는 진단으로 구분해 임의 새 합격 문턱을 만들지 않는다. 마지막76..77에는 원 지지/pose/발/무접촉/source/health를 유지해야 한다.

첫77 전체 후처리 통과 후에만 fresh77을 실행한다. 같은 config·source/model·초기q/body/properties·물리·gain·절대 일정, 새 process/출력/log/before map을 사용한다. constructor의 원 초기화 외 중간 reset은 없으며 첫 episode 최종 상태를 초기 상태로 이식하지 않는다. 각 episode를 독립 판정한 뒤 event 시각·support·G/발 drift·형상 여유·실측 제한잔차를 나란히 비교한다. 총2회 통과는 이 초기조건의 재현 근거이며 일반 성공률이나 모든 곡/프렛의 보장은 아니다.

## 후속 구현의 최소 파일과 검증 순서

경로명은 충돌 없는 새 버전으로 Root가 정한다. 필요한 책임은 다음과 같다. 기존 소비 파일은 수정하지 않는다.

- package: 새 protocol77, 새 Motion+생성자 wrapper runtime, 새 run guard, 새 analyze main/복수 phase 소유권 감사.
- read-only 감사: feet/media/manual/health/source의77 일정·두 free 선택 adapter. 기존 CLI가 길이/protocol을 거부하면 새 thin version으로 연결하며 감사 항목을 생략하지 않는다. 한 orchestrator로 묶을지는 실제 API를 보고 최소화한다.
- Root: 새 config producer(동일77 config를 두 episode에 사용), prospective closure, execute stage/fresh guard. 정확한 승인 source set·review/ACK·CPU 원문·모델과 actual expected maps를 전후 SHA로 닫는다. source map은 실제 flat/envelope schema와 충돌을 검사하며 새 glob로 과거 소비 범위를 소급 확대하지 않는다.

체크리스트는 아래 순서로 진행하며 **이 문서 작성 시 모두 미실행**이다.

- [ ] Root가77/67 및 같은 물리 후보·최종 건강 선행 조건을 선정한다.
- [ ] 새 코드 CPU: 원 planned59 경로 비교,59/60/62/64/68/72/76/77 경계, latch·한 번뿐인 orientation·8 binding/self.plan 정상/예외 복원, 대상/metadata 오염·두 번째 free의 λ0 접촉·누락·drift reset 반례를 검사한다.
- [ ] 독립 코드 검수 완료/frozen SHA·Root ACK 후 prospective closure/config를 생성한다.
- [ ] 동일 후보 단독5단계의 모든 필수 근거를 guard로 확인한 뒤 최초77만 실행한다.
- [ ] 최초77의 전체 core/발/media/manual/source/health 및 두15초를 실제 판정한다. 실패 보존·중단한다.
- [ ] 동일 초기조건 fresh77 한 번을 실행하고 같은 전체 조건을 독립 판정·비교한다.
- [ ] 결과 검수·문서/원자료 SHA 봉인 후에만 검증된 범위와 미해결 사항을 최종 보고한다.

이 설계 단계에서는 위 CPU나 실제 분석을 수행하지 않았다. 정적 근거로 읽은 source의 선택 SHA는 같은 자료 디렉토리 `post_regrasp_design_v1/source_inputs_v1.json`에 별도로 기록한다. 이 목록은 계획 작성 근거이며 미래77의 실행 before certificate가 아니다.
