# 보완 물리 유효성의 최종 후보 평가 기준

사용자 REQUIREMENTS_v2의 실제 상태·진동·형상 유효성을 검사한다. 기존32개 생산코드/원범위/모든 gain·cap/소비 leaf/원시자료·판정을 수정하지 않는다. 이 기준은 최종 후보 평가 전 추가 기준이다. 기존 actual eps0 범위 검사에서 관측한 초과를 삭제하거나 원범위를 넓히는 문서가 아니다.

## 상태와 설명 조건

- [ ] 원4/2 solver로 별도5초 재생을 먼저 확인한다. cfg는원baseline28/일정28 그대로,진단루프만1200step에서종료한다. 첫5초 states/contacts/efforts/targets 전체row exact와 원모델·초기값·제어명령을 확인한 뒤8/4만바꾼 별도5초를 비교한다. 제어강도·힘제한·Root·기타·초기화횟수는변경하지 않는다.
- [ ] actual97 nonzero축 및zero8의 초기/준비후잔차·부호·지속시간·각속도·목표·원bounds를비교한다. iteration변화와시간패턴에대한독립검수가 잔차를 유한 제약계산의 작고 제한된 오차로 설명할 수 있어야 한다. 단순히작다는이유·사후epsilon만으로 원인을확정하지않는다. 비교가설을지지하지않거나좌표불일치/발산이남으면최종미채택이다.

설명이성립한경우의별도건강예산은 다음과같다. 원eps0준수표의False는계속보존한다. 이예산을원native joint limit의새설정이라고설명하지않는다.

|항목|추가 기준|근거·범위|
|---|---|---|
|실제 nonzero97 원범위초과|전기간 각축≤.001rad|1m lever의단일축에서약1mm급이동에해당하는작은상태오차예산. 원목표는eps0범위내여야한다. 여러축합성·실제몸체이동은별도native pose/기하 gate로검사한다.|
|원zero8 실제q−원reference|전기간 각축≤.0001rad|같은lever에서약.1mm급의더작은예산. 원range0/목표0/명시effort0는그대로보존하며실제상태0을가정하지않는다.|
|실제native dq|전105축 전기간절댓값≤10rad/s|느린연주·자세유지후보의gross속도유효성문턱. 원native100rad/s속성/runner50rad/s안전중단과다른추가기준이다. 실제q차분과동일한양이라고가정하지않는다.|
|지속고주파진동|확인된정지2초창의각q채널10Hz초과RMS≤.001rad|linear detrend+Hann 에너지보정. .001rad의단일축은1mlever에서약1mm급이다. 의도된손동작과겹친창은정지판정에사용하지않는다. native dq와몸체운동·기존발gate를함께본다.|
|수치·명령유효성|q/dq/body pose/velocity/명령/가용센서 finite,제출명령원cap이내|센서반력과제출명령을같은양으로취급하지않는다. 초기step0 contact/DOFforce buffer의freshness는미확인이므로준비후지지/힘의근거로사용하지않고step1이후와분리한다.|

이 값들은 기존관측최댓값에맞춘epsilon이 아니라 기존mm급자세/기하정확도와느린연주후보의상태예산이다. 어떤예산도미설명좌표·제약오류를통과시키지못한다. 원래actual범위eps0미충족과설명/건강예산판정을같은표에남긴다.

## 동적 source 형상의 독립 보완

MuJoCo signed capsule–mesh 거리의음수가양수분리평면증명과모순되는표본을발견했다. primitive검사·실제vertex배치는맞았으므로음수를침투깊이로채택하지않는다. 기존양수LH거리판정도그대로보존하되새독립support-plane 검사를추가한다. 원자료/이전검사표를소급수정하지않는다.

- 모든대상shape를원XML·선언mesh·native shape filter와닫고,정규화된**실제native body pose**에배치한다. capsule은world axis endpoints a,b와r,convex mesh/box는전체worldvertices V를사용한다.
- 단위법선 n에대해 `g = min(a·n,b·n) − r − max(V·n)`를직접검사한다. 일반convex human mesh는`min(H·n) − max(V·n)`다. witness/수치최적화는n후보를구할뿐이며최종여유는원vertices/analytic support로재검사한다. 0법선·미해결pair·누락shape는통과시키지않는다.
- g>0이면그pair의분리가증명된다. g<0은침투확정이아니며,max(0,−g)는**그법선으로그pair를분리하는방향이동상한**이다. 여러piece의최대값을전체union의탈출거리/실제cooked침투깊이로해석하지않는다.
- [ ] 준비5초이후4support(Chest/R_Shoulder/L_Hip/R_Hip)×전체physicalG source shape를실제60Hz로검사한다. 모든활성pair의방향분리이동상한≤1mm. 원초기주요지지여유(.1~1mm)와같은mm급의보수적형상예산이며현재표본의.2~.3mm값그대로문턱으로삼지않는다. inactive쌍도별도공개한다.
- [ ] 각완전해제15초901개60Hz표본에서LH전체/L_Wrist/L_Elbow의모든native활성physicalG shape pair에 g≥2mm인분리평면을독립확인한다. 기존2mm source분리문턱을그대로쓴다. 그밖의왼팔source형상·inactive쌍은별도진단,전체왼팔손native raw contact0은3601개240Hz전행에서유지한다.
- [ ] 원본capsule/mesh 배치·단위법선·primitive·오염/누락거부·이동후투영·양수certificate와all-pair검사의CPU/독립검수를거친뒤전행producer를실행한다. 실제cooked형상침투량/시간연속clearance인증과source60Hz증거는구분한다.

## 채택 순서

정규v6 baseline/repeat/release/free_strike가core/발/영상으로통과했고regrasp42는실행중이다. solver진단첫entry는Scene전검증필드누락으로0step중단해원본보존/새V3보완중이다. 이사실을물리실패·진단완료로치환하지않는다.

regrasp42→continuous58의기존기준을먼저완료한다. 재파지후LH하중비의존을접촉normal/마찰만으로증명할수없으므로,그뒤동일초기조건의새76초조건(첫58보존/58..61재해제/61..76완전해제·R63/67/71)과fresh restart1회를별도계획/검수후실행한다. 두episode각기존기준+보완상대이동·접지·RH파지·건강·source평면검사를통과해야최종채택을검토한다. 지정압현준비와실제현힘은구분한다. 새PPO0.

소유권: Root는이기준/최종판단·실행/보존,구현담당은요청된새solver/76초entry,분석담당은요청된새health/source-plane 감사,reviewer는독립검수다. 새전행geometry producer나76초구현은확정brief/독립검수전에실행하지않는다. 기존소비파일은변경하지않는다.
