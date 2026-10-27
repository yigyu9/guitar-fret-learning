# 같은 수평·좌우 배치에서 상체 유한 목표와 Hip preload 시작 보완

static2는source4 initialRHipgap.4mm로바꿔종료neck1.17254°/lateral오차7.450mm로개선됐으나전표본neck6.35996°/Chest접촉0이라실패다. Chest최대4.4936°는5°이내였다. runtime sourceChestgap6.167mm/Spine−.791mm로종료. 초기근접만으로성공하지않았다.

새static3는source4 초기/G몸통좌우위치/넥0°/몸통3.5°/발/물성그대로. 상체의finite목표만Torso/Spine/Chest앞4.8°/옆0°로계산하고양손world위치·회전과Head방향은가능한원배치로refit해기존rate/cap으로제출한다. target의source음수gap은가상접촉목표이지초기관통이나실제지지성공이아님을기록한다.

controller_horizontal_v1은controller14에서R_Hip_x기존bias−.08rad의도달만smoothstep0~1초로완만히한다. 기존K/D/cap/최종목표/나머지3bias/오른팔10HzIK/Root/하체finite/자유기타/strapOFF/금지APIguard는유지한다. 두변경이있어단독인과는주장하지않는다. body목표원범위/lower24/zero8exact/양손5mm·2°/Head방향검사후native정지5초. 원계획의전표본neck3°/lateral±20mm/TorsoChest5°·옆3°/동시ChestRShoulder95% gate유지. 통과전왼손15초/PPO없음.

- [ ] uppergoal 범위/손/Head/lower/zero확인
- [ ] 원source4 초기·유한ramp경로 확인
- [ ] native5초 전표본배치/접촉판정
