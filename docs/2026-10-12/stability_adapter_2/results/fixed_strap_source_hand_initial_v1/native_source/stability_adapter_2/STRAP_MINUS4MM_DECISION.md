# −4mm 결과 판단과 다음 지지 자세 단위

실제같은손목동작0~5초3조건비교에서original/−2/−4mm의maxG초기이동은
14.132608/14.010556/14.023529mm,회전은2.894328/2.607665/2.335921°다.
−4mm의회전은개선했지만−2mm보다2s기준후기위치변화.363488→.404326mm,
회전변화.070089→.079347°로늘었다. Peak lawT28.152161→28.097309N,
actual손목scalar진폭.147836→.149523°다. 목표파형소실로설명하지않는다.

−4mm를회전개선후보로보존하고−2mm를후기유지비교기준으로유지한다.
엄지양λstep수194→163,중지20→28,검지1155→1154이며오른허벅지1200이다.
Palm양λ0이라손바닥/엄지/전면finger의완전한세면그립은미완료다.
새길이의무동작정지를측정하지않았으며originalstatic의µm범위를승계하지않는다.

추가길이단축은이번결과만으로계속하지않는다. 다음에는기존
[팔12+손가락6연동계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_FINGER_COUPLED_SOURCE_PLAN.md:1)의
첫source검증을−2mm저장actual상태에서수행한다. 원본검증helper를보존하며
조건부6hinge와팔12의합성형상identity/차분을먼저확인한다. Finger1의실패한
FKmap은사용하지않는다. Whole-shape/palm옆면·front/rear와+Z반구를함께검사한다.
Source후보가유효해도native로검증하기전안전한그립/복원제어로판정하지않는다.

그다음PD목표보정은현재실제각으로base를치환하지않고원본유지목표에추가한다.
연주연결에서는[공동residual설계](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_PRIOR_ADAPTATION_PLAN.md:60)의
하나의최종PD목표와66제어권을유지한다. 작은동작시험과실제fret·strike학습은구별한다.
Root/하체고정·몸통9목표유지·자유G·passiveLA·자기충돌·상태overwrite금지는그대로다.

이번actual1회/1200step·두151frame스트랩영상과3조건13검사를완료했다.
독립검수는수정된analyzer/audit_v2에Critical/Warning0을보고했다.
Checkpoint조사Strike schema null은새v2출력으로보완하고원본증거를보존했다.
