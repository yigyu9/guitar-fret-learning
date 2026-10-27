# 유한 관절 경로 재생으로 접촉 후 목표 유지 효과를 분리

V3는14초를완료하고국소좌표예측오차를줄였으나2mm실제하강과Chest+상완95%를통과하지못했다. 기존모든코드·입력·실패를보존한다. 새후보는V1에서실제압현에이미도달했던finger4의유한목표경로를명시적으로사용하여새FK와접촉hold를동시에바꾼이전비교보다작게검사한다. 일반기하IK나임의프렛의해결로주장하지않는다.

1. 원V1 raw targets60에서step2396의rest target과2400..3116의finger4 requested/final을기록한새spec/table을만든다. joint순서/원범위/원Scene rate/기존각row의당시sourceIK3mm통과와코드·입력SHA를사전검증한다. 런타임은originalrequested4를원Scene.command에넣고,hold전final4가원recordedfinal4와exact인지확인한다. 실제q/qd/body상태는주입하지않고기타직접force/고정/부착도추가하지않는다.
2. 실제10초를기준으로원press geometry+index3↔physicalG positivecontact의60Hz관측기간≥.1초,marker G-Z하강≥2mm,실제finger4 maxabs q변화≥.02rad인최초targettick에서**직전이미제출된target4**를한번capture하여13초까지유한유지한다. 60Hz관측과240Hz실제dwell은구분하며원분석이후자를그대로판정한다. table은13초까지이며13초에capture가없으면실패중단한다. 임의연장/가짜capture/깊게재추종하지않는다.
3.13..13.5초에는capture된jointtarget4에서step2396 resttarget4로선형보간하고14초까지유지한다. 원rate/cap/한계를유지한다. 13초첫목표는직전hold목표와exact라명령jump가없어야한다. 원rest target복귀와실제marker/mesh pose복귀는구분해측정한다. 손가락IK는새run에서실행하지않으므로evaluated=False/error=None로명시하고과거referenceIK오차를새계산처럼기록하지않는다.
4. 새press-only는실제capture step=k까지원V1 state/contact0..k inclusive,effort0..k−1,numeric105 requested/final/readback target0..k−4가exact여야한다. stepk요청부터의차이는실험개입이다. combined는타현이분기되므로원press1과이prefix를요구하지않고기존first10 exact와자체onlinepredicate/원26개실제기준을검사한다. 원actual2mm/관절변화/contact·dwell/Chest+상완95%/기타·몸통·발/제한의기준은완화하지않는다.
5. source/table·runtime·raw재구성·독립검수후새14초press/combined를실행하고성공4case인증후완전해제13..28초15초로진행한다. 실패시새버전으로기록한다. Root고정·하체finite·8zero axes/105입력·기타자유/중력ON/strapOFF·원물성/gain/cap을유지하고PPO0이다.

- [ ] table/source·독립검수
- [ ] actualpress·combined·4case인증
- [ ] 완전해제15초·보존감사
