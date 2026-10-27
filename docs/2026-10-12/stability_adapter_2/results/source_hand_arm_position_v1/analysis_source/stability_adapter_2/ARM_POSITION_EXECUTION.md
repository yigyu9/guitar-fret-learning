# 팔 위치74제안의 실행 범위

SOURCE_HAND_ARM_POSITION_PLAN.md의74제안을유지하되숫자범위검사를geometry보다먼저수행한다. 원Thorax_x초기−.064633653rad/held−.065298341rad에서−.025/−.05rad는하한−.087266468rad를넘고,Thorax_y+.05rad는상한.174532935rad를넘는다. 두seed각3개,총6제안은예상범위제외다. 나머지68제안만source형상을검사한다. 실제범위교집합을全81初期/held/sin양끝으로검산하고예상숫자와다르면기록으로확인한다.

범위밖제안은원하는delta·조립한rawfloat32목표·위반관절과bound를보존하고source_evaluated=false/source_clear=false로기록한다. Source교차가없다는의미의빈결과로표현하지않는다. Initial/held목표를clip하거나범위를완화하지않으며실제native로전달하지않는다. Source팔조건의정적예측과freshnative직접검사를구분한다.

74제안·두seed·선택L2norm·원offset유지·최소변경한후보1개/같은초기화5초·기타/몸통9/root하체·고정LA/최종66·원본보존조건은원계획그대로다. 현재사용자지침에따라범위위반제안을제외하는필수검산을자율적으로수행하며별도승인대기는하지않는다. 실제결과와체크리스트갱신은mainREADME/PLAN에추가하고소비된원계획/소스는수정하지않는다.
