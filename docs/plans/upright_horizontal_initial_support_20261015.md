# 첫 rightIK 지지점 목표 차이 분리

V5추종감사에서초기palm계산오차거의0임에도rightjoint최종목표가t0최대.049969rad변했다. 가상RShoulder목표점은기존source표면보다G안쪽을향하며,IK도그점을목표로삼아시작과동시에팔모양을바꾼다. 실제palm은첫step.0943mm/.19194도오차,전체최대19.283mm/3.157도이며계산IK오차1.24e−7m와구별해야한다. 원인전체를이한항목으로확정하지않는다.

새static6는static5에서rightIK의지원점reference하나만바꾼다. 초기실제RShoulder local materialpoint를G좌표로저장해이점의상대위치와넥방향보정palm을IK목표로사용한다. 원래3mm안쪽가상목표와20Ncap의240Hz사람지원task는그대로유지하므로finite접촉압력을제거하거나기타에명령을추가하지않는다. t0rightIK는원qref의palm과supportpoint를함께만족해추가자세변화가거의없어야한다. neck보정pivot도동일한새IK지원점이며nativecontactwitness가아니다.

source4/원uppertarget/즉시Hipbias/모든gain·rate·cap/Root·의자고정/원zero8/105채널·97비영범위/기타freegravityON/strapOFF동일. initial q0/초기righttarget차이/実FK를확인하고같은전체5초기준(넥3도/좌우20mm/body5도·옆3도/1초후ChestRShoulder동시95%/안전)을판정한다. 새결과의불완전성도보존. 통과전15초/PPO없음.

- [ ] initial materialpoint reference·기타금지API·finite경로 확인
- [ ] 초기righttarget qjump 및실제추종 전표본 확인
- [ ] native5초배치·접촉判定/독립리뷰/자료봉인
