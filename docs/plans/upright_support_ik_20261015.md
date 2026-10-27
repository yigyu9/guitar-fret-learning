# 기존 유한 제어와 오른팔 접촉 추종·관측 처짐 보정

V14 globalownjoint방향servo는0.8초에몸통각속도약12rad/s/검증gate실패로중단됨. gain150/D1를유지했지만discrete동역학안정성이없었음. 좌표변환부호정합만으로안정성을주장할수없다. 이실패는보존하고controller11의검증된scalarupperPD/lowerstablePD로되돌린다.

V15는source14초기그대로, Torso/Spine/Chest target만V13종료관측처짐만큼반대로보정(qtarget=2*qref−qfinal). 이는유한q목표이며초기상태수정이나매step상태덮어쓰기가아니다. 원래joint범위/lower24/zero8는보존하고기존.1rad/srate를통과한다. 별도upper_target5에SHA와숫자기록.

오른팔은10HzsourceFK IK로현재G자유운동을따라원guitar-localRPalm위치·방향과상완skinpoint의기존virtualpressgoal을추종한다. 팔12joint범위내±.8rad/원rate·K·D·토크cap유지. IK위치1cm/방향.05rad/supportpoint1cm하드gate, 실제contact·tracking오차와구분. 기타직접힘/강제부착/상태덮어쓰기없음. 한실험에관측하중bodytarget과armIK두변경이있으므로단독인과분리주장하지않는다.

같은source14에서정지5초Torso/Chest total5/right3/실제Chest·RShoulder1초후95%/기존모든guard통과후15초해제. 실패원자료보존/PPO없음.

- [ ] bodytarget계산·원범위/lower24/zero8 및문법
- [ ] 오른팔sourceIK와유한목표·actual tracking 비교
- [ ] 정지5초실제양지지/기울기
- [ ] 통과후왼손15초
