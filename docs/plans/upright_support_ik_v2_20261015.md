# 양 지지 확보 후 몸통 전경 보정 비교

V15는정지5초/실제Chest·RShoulder지속지지기준을통과하고Chestright최대1.156°/마지막1초.512°이나전체기울기최대5.505°로원5°기준실패다. 이를원5°성공이라고부르지않는다.

V16은동일source14/controller13/scene8/모든물성·gain·torquecap·rate·IK·하체목표를유지한다. body9축목표만target6=target5+.75*(qref14−qactualV15final)로추가보정한다. 관측된작은처짐에대한고정유한target이며실시간상태덮어쓰기아니다. 각변화량/원range/lower24/zero8/나머지96exact를기록한다.

사전기준Torso/Chest total5°/right3°/1초후Chest와실제RShoulder positive95%이상과모든안전gate를유지해새정지5초검증. 통과시에만같은초기/제어의15초왼손해제를실행하고0~2초prefix·5초후왼손무접촉·15초양지지/기울기를검증한다. PPO없음. 원자료불변.

- [ ] target6 관측식·범위·불변축 검사
- [ ] 같은제어/한target차이 정지5초
- [ ] 통과후15초·prefix·실제해제 검사
