# 해제 시작 목표 연속성 교정

정지V16은전체기준을통과했다. 같은기존해제protocol의releaseV16은2.45417초Groot이동200.498mm로중단,qd최대2.834rad/s/회전20.99°여서속도제한50이나35°회전이직접중단원인이아니다. 2초이전상태prefix와요청목표를독립감사한다.

기존leftIK는기타초기G좌표의Wristanchor를2초부터currentG에다시붙여goal을계산한다. 이때기타는초기후약64mm내려앉았지만팔은기존관절목표를유지했다. 따라서해제시작의Cartesian requestedgoal에큰불연속이있다. 제출q목표는원rate제한을통과하므로실제상태를순간이동했다는뜻이아니다. 접촉중인손이움직이는G를따라가는경로는기타를더끌가능성이있으나단독원인확정은아님.

controller14는해제t=2초에실제nativeLWrist world위치·방향과그순간G기준이동방향을1회latched한다. 목표는world고정출발점에서연속적으로생성,현재G이동을따라출발점이계속변하지않는다. 손가락open2~3초/팔withdraw3~5초(기존deltaG .07,.08,0을latch순간world로변환)로순서를분리한다. 단지유한q요청/원rate·K/D·cap만사용하며기타/사람state덮어쓰기없음. source14/target6/rightIK/lower/물성/형상/zero8/105조건유지.

새정지V17을먼저검증하고통과후새releaseV17 15초를검증한다. static/release0~2초prefixexact/2초Cartesiangoal실제손오차/5초후LHraw0/Chest·RShoulder95%/TorsoChesttotal5/right3/모든안전gate유지. PPO없음. 이전실패코드/자료보존.

- [ ] release경로diff/문법·상태쓰기없음
- [ ] 정지V17 기존V16과동일경로검증
- [ ] 15초재시험과실제해제/지지/목표연속성
