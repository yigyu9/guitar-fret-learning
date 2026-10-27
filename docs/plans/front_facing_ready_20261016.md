# 기타 연주 초기 자세 전체 조건 검증

## 목표와 보존

사용자가 2026-10-16 제시한 초기 자세 기준 전체를 수행한다. Root만 고정하고 하체16가동축은 유한 제어, 원래 영범위8축/105입력97비영범위를 보존한다. 기타 free/중력ON/strapOFF·원물성/shape filter·가슴/오른상완/허벅지 실제지지·발접지를 유지한다. 기타 고정/강제부착/직접 보조힘/매step 상태 덮어쓰기/PPO는 금지한다. 필요시 초기 자세/큐브의 새 버전 조정은 허용하되 먼저 현재 source9의 미해결 조건을 실제 검증한다.

기존 front_facing_pose_v1의 source9 정지5초/독립반복과 front_facing_strike_v1/native_strike_v6의14초/36gate·양측준비/삼중지지98.7513%를 입력으로 한다. 기존 소비 코드/계획/입출력/영상·최종검수·봉인은 전부 보존하고 새 package/자료 phase front_facing_ready_v1에만 구현·시도한다. 기존 right6 SO3/K60/20,D3/1,cap100/60·Chest0.5mm/K2000,D30,cap20·하체/발/기존 타현 spec을 유지한다. 새로운 left SO3/gain/목표속도 feedforward는 최초 버전에 추가하지 않는다.

## 왼손 사전검사의 정당한 범위

기존 release_preflight_v1의 full105 FK 10μm/.01° 실패와 eligible=false를 그대로 보존한다. 손가락2입력에 없는 미표현 회전이 있어 q105만의 정확한 손가락 형상 예측을 보장하지 못한다. 실제10초 상태를 FK zero에 흡수하거나 원문턱을 사후 완화하지 않는다.

새 wrist solver는 original-initial만으로 보정한 기존 FK를 사용한다. 이 solver의 실제 의존 chain(Pelvis/Torso/Spine/Chest/왼쇄골·상완·팔꿈치·손목/LH:palm)에 대해 같은10μm/.01°를 엄격 검사하고 손목41점 위치2mm/회전.02rad·원범위/float32/qref±.8/principal160°를 검사한다. 손가락은 원14named POSITION 목표의 개방/닫힘과 범위를 검사하며 독립 finger FK 정확도를 주장하지 않는다. 새 허용은 task-chain 진단 실행 자격이며 원 fullFK 성공으로 대체하지 않는다.

손 형상은 실제 native body pose와 정규화한 quaternion으로 원XML/모든 선언mesh를 배치해 별도로 검사한다. 미래 개방형상의 오차한계를 정지에서 관측한20μm로 대신하지 않는다. 완전해제 구간의 native240Hz 왼팔·손 raw contact0, 실제 손목60mm 이상 이탈, 사전선정 유효개방축의 signed 실제 개방을 모두 요구한다. 같은 구간의 실제60Hz LH전체+L_Wrist/L_Elbow 원source 활성형상 간격2mm 이상을 별도 요구하고 원nativefilter/XML충돌제외와 비활성겹침을 구분한다. 근위L_Thorax/L_Shoulder sourcegap은 진단이며 실제물리접촉은0이어야 한다. Source convex gap과PhysX cooked 접촉을 혼동하지 않는다.

## 구현과 단계

- [ ] 원입력·모든원XML/선언mesh·이전봉인을 실행전/후 SHA로 확인하고 초기보존/요구사항/계획을 새phase에 저장한다.
- [ ] 새단일 motion scheduler로 LH12+손가락14 해제/복귀와 Rdistal6 타현을 합성한다. Rprox6은2396step 실제최종목표 latch, R12 world IK는10초부터 중지한다. 기존 시간/step/cfg를 일시조작해 다른runtime을 재사용하지 않는다. 경계는 마지막제출 목표와 그FK pose에서 연속시작하고 새로운 관절·숨은축/상태주입을 만들지 않는다.
- [ ] finger open1초→손목G시작+X80mm world방향 withdraw2초, 완전해제15초를 검증한다. 열린손 재접근2초는 현재G에 실제10초의 손목 G-relative 참조를 옮긴 유한목표를 따른다. 닫기1초는 원2396손가락 목표로 보간하고 실제접촉을 확인한다. FK초기보정은 모든단계에서 unchanged다.
- [ ] Rstrike는 기존4초 왕복 궤적을 반복한다. 최초손방향G-Y−15° ramp는 한 번만 적용하고 이후 유지해 cycle경계 orientation reset/jump를 피한다. 검출기는 전체실행60Hz history를 유지하며 window별6→1/1→6와 양측실제준비(기존1mm깊이/3mm재무장/속도.05/lane)를 검사한다.
- [ ] 구현/CPU 계약·음성변조/독립code review 완료 후 baseline28초를 먼저 실행한다. 전체pass 전 action실행금지. 0..10초4raw는 기존 정지와 exact여야 한다.
- [ ] 별도 repeat22초(10/14/18 시작3왕복), release28초(10..13해제/13..28완전해제15초)를 통과시킨다.
- [ ] 별도 free_strike28초(해제15초창13..28 안의15/19/23 시작3왕복), regrasp36초(28..30접근/30..31닫기/31..36접촉안정)를 통과시킨다.
- [ ] 마지막 continuous52초:0..10준비·정지,10..22 세왕복,22..25해제,25..40완전해제15초와27/31/35세왕복,40..42접근/42..43닫기/43..48재접촉안정,48..52재파지후왕복을 같은실행/상태초기화없이 수행한다.
- [ ] 실제결과/실패·원자료·영상·권장README/영상색인/자세경로를 새phase에 보존하고 독립최종검수 완료·동결SHA 확인 후 root가 봉인한다.

## 원판정 유지와 새필수 판정

전체 기타이동30mm/회전5°/넥3°/좌우20mm, 몸통5°/오른3°/Spine5°, 원양발95%/네발바닥 기준, 실제Chest+R_Shoulder+한쪽Hip 동시95%를 준비5..10과 각 동작창에 모두 적용한다. 새 타현근위 상대회전1°는 각왕복 시작의 실제부모-자식 상대회전 대비로 검사하고 10초대비누적량도공개한다. 요청/최종prox목표는전행constant여야 한다. 단지32축허용집합만 검사하지 않고 각phase별 실제목표소유권·나머지불변/원rate/원caps/원zero8/POS48·모든N=240T 실제행을 검사한다.

재파지는 닫기후5초창에서 물리기타 neck과 실제LH 손가락의 양의접촉95%와 한손가락이상의 actual close 복귀/실제손목 graspG10 참조2cm 이내·원기타/발/몸통/삼중지지를 함께 요구한다. 여전히 왼손하중만으로기타안정성을대신하지못하며 직전15초완전해제와해제중타현을 별도로 통과해야 한다. 접촉 lambda를 보정된N이나압현력·현진동·음향으로주장하지않는다. 각가설/판정/수치가 최초실패 뒤 바뀌면 기존 결과를 보존하고 새leaf/source버전으로 진행한다.
