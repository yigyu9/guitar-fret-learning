# 자유 기타 V3: 인체 Chest 유한 normal 목표 깊이 비교

V2 actualstatic5초에서는 전체G회전1.268647°/중심이동5.027164mm/넥.498299°/총상체4.070321°/side1.517444°로모든변위·각도·양발gate를통과했다. 유일한실패는settle1..5초Chest actualpositive0(위팔100%)이다. V2와입력/코드/결과를보존한다.

## 단일 변경
같은source1/오른팔initialworld/성공발제어/gain/cap에서 Chest 가상normal목표의기존surface안쪽3mm를6mm로변경한다. K2000N/m,D30Ns/m,cap20N은변경하지않는다. 같은최근접형상normal·실제G속도·인체point/Jacobian을사용한다. 기존rawnormal에서2000*(.006-.003)=6N만더인체누름방향으로요청하고기존unilateral[-20,0]cap를적용한다. super의Chest JTF를정확히차감/새항가산해upper33만재clip한다. G직접force/가짜상태/attachment/지속statewrite는0이다. 이는가상인체목표이며source기하침투/실제접촉이나측정힘을대신하지않는다.

## 검증 체크리스트
- [ ] source1/Gworld/하체/PD/cap 동일 입력 대조 및 독립검수.
- [ ] actual5초 실행, Chest rawnormal의before/after/request, 가상goal,actualpoint와실제nativecontact 함께보존.
- [ ] 전체0..5 G각도/상체와1..5 Chest+upperarm/양발 및last1soles를이전15gate 그대로판정.
- [ ] 정지전체성공시같은cfg재현후압현·타현. 실패시면적·몸통·Spine접촉경쟁을읽고새버전으로진행.

기준을완화하거나settle구간만으로전체회전통과를대체하지않는다. 상체total5°/side3°를유지해야하며cap포화나상체실패시'더큰gain'으로대체하지않는다.
