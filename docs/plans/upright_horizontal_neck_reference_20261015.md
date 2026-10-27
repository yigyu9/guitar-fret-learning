# 오른팔 IK의 수평 넥 방향만 비교

static4는initialworld오른팔IK로변경했으나Chest최대6.33도/옆6.24도,위팔접촉199/1201로악화했다. 초기world목표를좋은제어기로채택하지않는다. 기존실패는불변보존.

새static5는source4와static2의모든초기값/하체/상체목표/지원task/gain/cap/변화율을유지한다. 10Hz rightIK에서RShoulder목표점은실제기타의점을그대로따른다. 다만RH palm목표만현재기타neck의elevation을0으로돌리는최소world회전으로보정한다. 회전중심은그실제RShoulder지원목표점이므로그점이공간에서떠나지않는다. 기타의translation/yaw/neck축회전은원칙적으로따른다. 이는neck기울기에대한유한오른팔제어비교이며기타에직접명령/힘/고정/상태갱신을하지않는다.

수평회전은cross(neck,horizontalneck)와atan2로계산하고pitch보정은±10도로유한화한다. 실제nativeIK오차1cm/회전.05rad/지원점1cm기준및관절/rate/토크/속도안전기준유지. source4/zero8/105입력·97원범위유지. native5초전체neck3도/좌우20mm/body5도·옆3도/1초후동시ChestRShoulder95%판정과시각자료를기록한다. 접촉이0이면넥이개선돼도전체성공으로부르지않는다. 통과전release15/PPO없음.

- [ ] 최소회전/지원점중심/기타금지API독립확인
- [ ] 정지5초 실제판정
- [ ] 신규결과·실패·보존기록
