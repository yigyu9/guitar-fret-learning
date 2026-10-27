# 오른손 형상 개선 후 남은 지지·타현 깊이 보완

## 실제 근거와 분리할 원인

native_strike_v4는14초완료/첫10초4raw exact/기존자유기타·하체유한제어·몸통/발안정성·말단6목표권/근위상대1°를통과했다. native RH손접촉은0이지만타현동시세지지는52.758%로실패했다. 따라서RH약지충돌을제거해도가슴지지는회복되지않는다. 깊이2.5mm/손G-Y−12°에서내려치기는4·1번줄만원깊이1mm기준을충족했고올려치기는6줄을통과했다. 동적목표–실제추종차이와cooked지지여유문제를분리한다. 원판정기준을완화하지않는다.

## 한 단계: 기존강도 안의 유한 지지 목표와 충분한 타현 깊이

- 손모션solver/관절K·D/effort cap/원물성/하체/어깨·손가락목표는그대로다. source에서이미41점검사한깊이4mm/G-Y−15°한조합만241점으로검사해활성쌍2mm여유/원도달·원범위/float32/q_ref±1rad/principal160°를재확인한다. source적합이실제성공을뜻하지않는다.
- 가슴의실제유한human spring preload는동작중약18N이며원상한20N보다작았다. source capsule gap음수만으로native양의지지접촉을보장하지못했다. 원K2000N/m·D30Ns/m·cap20N을유지하고,10..10.5초smoothstep으로human Chest 가상지지목표깊이에0.5mm를추가한다(최대추가요청1N,실제전체요청은원20Ncap). 이는gain/cap증가나기타힘명령이아니다. 몸통/어깨의요청관절목표도바꾸지않는다. 실제몸통은원유한제어아래조금움직일수있으며기존5°/오른3°/Spine5°기준으로판정한다.
- 새토크는현재human Chest지점의native Jacobian 전치로몸통9EFFORT채널에만분배한다. 기타 actor/하체/손가락/오른말단직접강제힘은추가하지않는다. scalar관절목표가새로바뀌는것은타현6채널뿐이다. 모든실제토크는원cap으로다시clip하고하체·POS48·zero8은기존출력과비트단위동일하게유지한다.
- 기존기본Chest기록과추가항을모두보존한다. 분석은원Chest항의이전row복원후기존엄격계산을검증하고,새항은실제native상태·원source geometry·native COM/속도·기록Jacobian으로힘/JTF/clip을독립재구성한다. 원상체33전체합산/원하체16 stablePD/모든목표소유권검사도유지한다. 추가항의구성/상한/다른분기0/state불변을전960행검사한다.
- 새정지대조와타현각14초를검사한다. 둘다같은0.5mm유한가슴지지목표를사용하며타현만6축모션을추가한다.0..10초는기존reference와4raw exact,새대조/타현prefix도exact여야한다. 모든원95%지지/발/기타/몸통/실제6줄왕복/양측준비/근위1°gate를그대로유지한다. 정지대조미달이면타현하지않는다.

## 파일·보존

새source_clearance_v4.py/prepare_v4.py/runtime_v4.py/run_v4.py/analyze_v4.py/support_margin_math_v1.py만생성하고기존모든버전은보존한다. motion_v2는동일코드를사용한다. inputs/baseline_v5.json·strike_v5.json,source_clearance_v4/preflight_v4/native_baseline_v5/native_strike_v5를새로생성한다. 완성전초안/tmp,독립검수·원모델모든mesh/새계획/code/입력/실제실패원자료의사전SHA확인후실행한다. Root만고정,하체16유한/원zero8·기타자유/중력ON/strapOFF·기타고정/부착/지속상태주입금지·PPO미실행을유지한다. 추가작은유한지지목표도실제삼중지지를회복시키지못하면성공으로채택하지않고접촉여유/체간제어문제를기록해다음진단으로넘긴다.
