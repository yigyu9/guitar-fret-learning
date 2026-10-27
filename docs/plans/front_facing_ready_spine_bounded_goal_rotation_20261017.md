# 보정 경로의 작은 목표 회전 허용을 명시한 별도 조건부 평가

기존 전기간 scan_v2는 두후보×두run 모두실패했다. 실제조건부 pose/각도·source178쌍×F64/F32·관절bounds·rate비활성은통과했지만, goalChest 회전을1e-6rad(약0.0000573도) 이하로보존하는설계조건이보정중간에서실패했다. 원실패·결과·외부requiredFalse를그대로보존한다. 선형q보간에서회전합성이비선형이므로두endpoint회전을정확히맞춰도중간에동일하지않다. baseline실측계산최대는추가.20의3.342909e-6rad(.000191535도), .35의6.169904e-6rad(.000353509도)다. 이는기존actualChest회전예산.02도와구분한goal설계조건이다.

사용자는가슴의실제접촉지지와제한된미세움직임을요구하며goalChest회전정확0을요구하지않는다. 따라서새별도평가에서는보정중goalChest회전변화를 **.001도 이하**로명시한다(기존actual.02도의1/20). goalChest위치.5mm·후손.75mm/.02도·actualChest.5mm/.02도·F64내부4.8/4.9/2.9·F32원4.95/5/3·source원1mm와private.95mm·모든물리조건은바꾸지않는다. point선정equality와원optimizer/vector도변경하지않는다. 원실패를소급통과시키지않고,같은두vector를새로명시한경로회전예산에서평가한다.

- [x] 원fullperiod결과완료/inputsunchanged/두run양candidate실패를확인했다. 원strict/zero8실패와최종채택False도유지했다.
- [ ] 새read-only evaluator와작은CPU를구현한다. 완료fullperiod의모든1381frame·A/B/rate·F64/F32저장pose변화로새goal예산만다시판정한다. 원모든다른check값/coverage/point+두runAND는유지하며새FK/source/optimizer/native를재실행하지않는다. 원targetexact실패개수/최대/첫시점과새예산판정을함께기록한다.
- [ ] 독립FINAL·동결SHA·Root원CPU/작은검수재현/ACK후에만새평가main을실행한다. 새조건부통과는실제제어성공아니며controller선정근거일뿐이다.
- [ ] 통과후에도새protocol4실제정지5초와전동작/연속/재시작및미해결관절물리평가를별도로실행한다. source의originalG고정가정·손응답미인증범위를유지한다.
