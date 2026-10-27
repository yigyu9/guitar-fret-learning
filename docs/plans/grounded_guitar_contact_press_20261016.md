# 실제 관절 자세와 접촉에 근거한 유한 압현 V3

압현V1은동작pass/가슴지지73.257%로실패,V2는12.4초에원3mm sourceIK gate로중단됐다. 모두코드·입력·원자료·분석을보존한다. 검지첫2DOF의native qxz만으로상대회전전체를복원할수없고, 실제rotvecY가0→.178rad로변하는데기존fixedFK는0으로가정했다. 이오차는index3까지~6mm누적된다. qd는child angular성분이며scalarq미분과같지않다. gain/한계/물성/기타직접제어를바꾸지않고다음후보를검사한다.

1. 매60Hz target시점 actual native palm/index1/2/3 pose와q로finger-only국소FK를만든다. index1은currentRrel·exp([wx,0,wz])의log[x,z]차이가요청q증분과일치하도록역변환하고hinge2/3는원축을쓴다. scene.q_ref/원팔·하체FK는변경하지않으며현재q에서actual marker와일치해야한다. 이는선택한유한경로의국소근사이며qxz로전체회전상태가유일하게정해진다는주장이아니다. 기존실제4step증분재생에서V1/V2 최대오차.0006367/.0002475mm인증거를핀한다. 새실제시험에서는이전anchor→현재actualq의palm상대marker예측오차≤.1mm와4finger실제4step증분norm≤.05rad를검사한다. raw actual world 추적오차도기록하되접촉이막는가상목표오차와FK좌표오차는구분한다.
2. 동일sourceV2의2현5프렛점·원hover/down offset/전체시간/right경로를사용한다. solve구간의원3mmIK gate와원joint bounds·Scene1.5rad/s target rate/cap을유지한다. down10.8..13초중60Hz에서실제geometry-ready+index3↔physicalG positivecontact가연속관측된기간≥.1초이고actualG-frame marker가10초대비2mm이상하강하며finger4실제q변화≥.02rad이면최초targettick에서**그직전이미제출된s.target4**를한번만capture하여13초까지유한목표로유지한다. 이60Hz관측은240Hz연속접촉dwell인증이아니며원240Hz분석이동작을별도판정한다. 접촉소실시깊게재추종하거나토글하지않고loss를기록한다. contacthold는IK 미실행으로명시하고오차0을기록하지않는다.13초actual marker에서원hover로13.5초까지연속복귀한다. 기타/인체실제상태를고정하거나덮어쓰지않는다.
3. 새fingerFK/motion/run/source/analyzer와입력·4step재생·41sourceReach를닫고독립검수한다. 실제14초새초기화에서원26개기준(동작/2mm하강·실제contact/dwell/Chest+상완95%/발/자세/제한)과새국소모델·targethold소유권을모두검사한다. baseline/strike는press분기를사용하지않은기존실제대조를재사용한다. 성공후combined,4case인증,완전해제15초28초시험을차례로실행한다. 실패시허용오차확대없이새버전진단한다. PPO0.

- [ ] 좌표진단동결·새국소FK/source/runtime독립검수
- [ ] 실제압현V3 전기준
- [ ] 실제combined·4case인증·완전해제15초
