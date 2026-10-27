# 엄지 후면·네 손끝 전면의 전체 형상 접근

33좌표의12 source후보를78.037820초/exit0으로완료했다. 모든후보는최종source조건을통과하지못했다. old_near17과best_sliding25는human–guitar/비인접왼손/양손의source교차0이지만엄지대표점패치여유·후면witness방향이부족했다. 대표점오차는각각thumb7.682393/palm1.853464mm,thumb6.262113/palm7.114912mm였다. 임의균일seed로각도범위만넓히는것이grip을완성하지못했다.

새variant는기존33bounds/old81T/other48/G p·q/LA/gain과hardgate를유지하면서다음source잔차를더한다. 실제actor/물리외력/PD/solver는변경하지않는다.

- Thumb3 활성source convex hull의최대GZ가넥후면−8mm에서0.3mm바깥에있도록부드럽게선호한다. 단순lateral escape로SAT분리만만족하는해를줄인다.
- Index3/middle3/ring3/pinky3 hull의최소GZ가source전면최외곽11.230006mm에서0.3mm바깥에있도록선호한다. 모든선택지점의XY는기존전면허용영역안에서움직일수있다.
- Palm 전체hull은넥+X옆면의정규화평면에대해최소signedcoordinate가0.3mm바깥에있도록선호한다. 양손의최종66권한과몸통9목표를유지한다.
- 위잔차의계수는50,000/m이다. 실제접촉에사용하는constraint/외력이아니라초기검색의softobjective다. Hull전체halfspace선호는충돌형상proxy이며해부학적pad인증이아니다. 기존point/patch거리/witness/up hemisphere/교차gate는변경하거나완화하지않는다.
- 직전자료에서관측된11개비인접왼손겹침쌍에SAT분리0.1mm선호항을더한다. 마지막에는기존전체LP로재검사한다. Seed는LP교차0인old_near17/best_sliding25와엄지점가장가까운uniform_0의기존최적화결과3개다. 겹친seed는native로실행하지않는다.
- source통과최대2개만fresh native초기/FK검사와actual5초/1200step·초기값/전신·손151frame을진행한다. 통과0이면새native0을기록한다. 아직유지제어/학습을시작한것은아니다.

이전source실행/입력/출력은예상SHA대조후exact복사해보존한다. 독립검수도구의thread limit은이번단계에서도보류상태이며root검증과구분한다. Root하체물리고정/자유기타·중력·충돌·수동strap/기타고정·손부착·반복pose덮어쓰기·기타목표힘금지는같다.

- [ ] 기존source보존/33bounds 및softplane방향·단위 사전검증
- [ ] 새source3후보와통과최대2 actual5초
- [ ] 이미지·설명·재계산/보존/독립검수상태
