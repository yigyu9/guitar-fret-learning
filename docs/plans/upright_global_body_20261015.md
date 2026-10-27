# source14 실제 가슴 접촉 후 몸통 방향 좌표 비교

정지V13은가슴positive1161/1201표본,마지막1초241/241을얻었지만RShoulder마지막1초0이며Chest오른쪽기울기−5.16°/전체최대7.14°로실패했다. 기타root최대80.95mm이동. 양Hippositive는지속됨. source14초기전체audit13통과와동적성공을혼동하지않는다.

기존relative scalar qPD는각몸통joint의작은처짐이누적돼Chest절대기울기가커진다. controller12는Torso/Spine/Chest만목표FK의world절대SO3방향을오차로사용하고nativeangularJ의해당own3joint전치로유한토크에변환한다. K150/D1/토크cap/Chest20N/RShoulder20N/lower stablePD/목표rate를동일하게유지한다. 가동축suffix를world축으로가정하지않는다. 실제Jangular@qd와native각속도를매step .01rad/s검증한다. scalar원요청과새적용posture/토크/오차/축목록을따로기록. 기타직접힘/상태수정없음.

같은source14 초기에서새정지V14로좌표피드백변경만비교한다. Torso/Chest total5/right3/1초후Chest·RShoulderpositive95%/원안전gate를통과한후에만15초해제. 실패시손실원인보존,단순gain증가금지,PPO없음.

- [ ] 문법 및 원gain·cap·하체 동일성
- [ ] native각속도J gate와정지5초
- [ ] 실제양지지·기울기 판정
- [ ] 통과시에만15초해제
