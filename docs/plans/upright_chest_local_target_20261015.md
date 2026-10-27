# 허리 유지·가슴만 국소 전경하는 유한 목표

현재전신오른쪽기울기는크게줄었으나Chest실제접촉0으로복합지지미달이다. source9안전초기는그대로두고Torso/Spine방향은초기약3.3/3.6°유지,Chest만앞8°/옆0°의목표를비교한다. 기존target2에서Spine이먼저닿아Chest간격이남는관측을구분한다. 양손worldpose와Head방향/lower24/zero8/모든범위는유지. 강도·물성·형상변경없이기존유한controller11/scene8/rate/토크cap으로만실행한다.

원사용자는정확한각도를지정하지않았다. 이전단계의Torso와Chest모두total5°자체목표와구분해,새후보의사전허용기준은Torso total5°/Chest total8.5°/모두right3°다. 실제각도가5°를넘으면이사실과국소전경타협을명시하고이전기준통과라고표현하지않는다. 기존analyzer결과도그대로보존한다. Chest/RShoulder실제positivecontact가1초후95%초과,모든좌표/안전gate통과한정지5초후에만15초해제. 기존자유기타/Root고정/하체유한/105채널97비영/8축0/strapOFF유지,PPO없음.

- [ ] upper_target4 원범위·손·Head/lower24 검사
- [ ] 같은source9로native 정지5초 비교
- [ ] 새허용기준과기존5°기준을나란히기록
- [ ] 지지까지통과시에만왼손15초
