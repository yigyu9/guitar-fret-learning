# 유한 접촉 압현 V3의 목표·복귀 경로 확정

[직전 설계](/home/ajou/yigyu/3/docs/plans/grounded_guitar_contact_press_20261016.md)는 보존하며 그 국소FK·60Hz관측·유한제출목표latch·.1mm/실제4q증분.05rad·원3mmIK/26기준·범위/rate/cap·금지조건을 그대로 따른다. source2의실제2mm하강이확인되지않은추가증거에근거하여아래두경로선택만새leaf로확정한다.

실제V2의최대하강은.647513mm로원2mm기준을충족하지못했다. 반면V1은11.283333초step2708에서실제하강2.005439mm,60Hz관측ready기간.125초,index3↔physicalG positive3개,Chest+상완동시접촉을확인했다. 따라서V3는실제압현이이미검출된 **source1의같은2번줄5프렛중점** XYZ를사용해새국소좌표/접촉hold를검사한다. source2 bar3.2mm marker여유를실제finger전체충돌여유나압현성공으로해석하지않는다. source2코드/실패는보존한다.

13초에는실제marker에서 **10초실제marker G좌표**로13.5초까지보간하여복귀한다. 기존V1의이동한Y에남는hover는최종.5초Chest접촉0이었으므로휴지상태로회복하는경로를선택한다. 이변경이접촉소실원인을확정하거나회복을보장하지는않는다. 개입전10..13의hover/down오프셋·시간,오른손타현과모든물성/제어gain/cap은유지한다.

source V3는새국소FK의현재anchor/원raw4step검증/nominal41도달과원right 재검사를닫고,13초복귀출발점은actualruntime에서capture하는것과source의nominalquery를명확히구분한다. requested/finaltarget−actualnorm및finaltarget 모델예측을따로기록한다. before-rate fullgoal IK3mm와작은 actual4step 예측gate는서로다른판정이다. 새물리실행에서성공을판정하며PPO0이다.

- [ ] source3·새motion/wrapper/분석·독립검수
- [ ] 압현V3·combinedV3 actual전기준
- [ ] 4case인증·완전해제15초
