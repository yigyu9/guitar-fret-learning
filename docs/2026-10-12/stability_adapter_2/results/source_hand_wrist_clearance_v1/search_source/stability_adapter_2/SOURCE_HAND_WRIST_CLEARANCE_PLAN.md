# 손 전체의 작은 손목 회전으로 초기 겹침을 해소하는 다음 단계

엄지 기저부 한 축4조건의 실제 native 초기 검사에서 모두 thumb2–guitar 교차가 남았다. 기준 손5관절 후보의 source LP 공통내접반경은4.288365mm였고 x−.05/y+.05/x−.10/y+.10rad에서는 각각5.193222/5.015440/6.079509/5.789207mm로커졌다. 모두15개 fresh검사 중 human–guitar 검사만실패했고4초기화·0물리스텝이었다. 후기 안정성이나 제어 성능은 측정하지 않았다. LP 반경은 PhysX 침투 깊이가 아니다.

다음에는 엄지를 더 굽히는 대신 손목을 통해 손 전체를 옮긴다. 기준은 변형하지 않은 fixed_strap_source_hand_initial_v1 실제 초기state다. 실패한 기저부 변화나 thumb2 ±.2rad를 승계하지 않는다. Finger1 다축 FK를 추정하지 않고 기준 실제 손 계층 상대변환을 유지한다. CoupledSnapshot의 arm12 변환은 과거 저장 native 표본에서 검증된 조건부 source 모델이지만, 새 초기각의 정확성·접촉은 fresh 실제 native로 다시 확인한다.

1. 같은 baseline에서 L_Wrist_x/y/z 각 한 축의0,±.05,±.10rad 총13source조건을 비교한다. 0은한번만평가한다. float32로조립한실제초기각delta를FK입력으로쓰고zeroidentity·기준HG재현·기타/오른손/상위팔/손가락상대변환보존을검사한다. 손목/손아래 모든 descendant body와 collision geom을 움직이는 집합에 포함한다. Static MuJoCo probe는 source형상query일뿐 새 Gym 영상이나 물리 실행이 아니다.
2. 한축 초기각만변경하고 기존 left33 offset은그대로유지한다. 현재 wrist의초기/held가다르므로 thumb1처럼offset0으로바꾸지않는다. 기존compose로전체81최종목표를재조립하고다른80초기각·목표exact,全81source/native/normalized교집합과손목sinusoid±.005rad양끝을검산한다. 몸통9목표/PD·기타초기p/q·root하체·LA1.1018469719600776m·나머지65주요제어권은유지한다.
3. 모든조건의human–guitar/cross-hands/self1188 source LP와palmar up proxy>0을검사한다. LH:palm과palm허용패치,thumb3와후면thumb패치의source거리하한/상한을기록한다. Palm proxy와넥옆면법선의평면정렬도는절대내적으로표시하되필수정렬제약으로두지않는다. 해부학적손바닥/실제접촉인증으로확대하지않는다.
4. Clear 후보 중 실제변경절대값이작은것을우선하고,동률은palm·thumb3의해당패치source거리상한제곱합이작은것,그다음평면정렬이좋은것,그다음고정축순서로선택한다. 후보가없으면native를실행하지않고팔꿈치·어깨를포함한손전체위치조정의새계획을정한다. 기존 gate나범위를삭제하지않는다.
5. 선택한한후보만실제native직접형상gate로검사한다. Gate통과면같은초기화에서1200step5초·전신/손151frame30fps스트랩영상과초기값을기록한다. Gate실패면0step시작이미지·partial영상과실제pair를보존한다. Source예측이actualnative와다르면변환오차를분석한뒤새단계에서수정하고같은입력을몰래재실행하지않는다.
6. 실제5초가확보되면기타초기이탈·후기완전1초창변화/손가락각·접촉·palm방향을기존quietbaseline과비교한다. 임시30mm/5°및후기5mm/1°기준은유지하되자연스러움·연주/학습성공으로선언하지않는다. 자유기타·중력·접촉·PD를유지하고고정/손부착/시작후pose덮어쓰기·인위적복원힘을사용하지않는다.

- [ ] 13조건 source·모델identity·범위·다른80보존·패치/정렬 기록
- [ ] 최소변경한후보의 fresh native 직접검사와통과시동일초기화5초
- [ ] 저장산출물·영상분류·독립검수·다음결정

이계획은아직미실행이다. 예정새결과경로는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1 이다. 이번기저부4조건의실패를엄지전체가동범위나모든자세의불가능성으로일반화하지않는다. 전체목표는자유기타초기이탈축소와이후물리관절제어에의한유지·연주전환이며13source조건의통과로대체하지않는다.
