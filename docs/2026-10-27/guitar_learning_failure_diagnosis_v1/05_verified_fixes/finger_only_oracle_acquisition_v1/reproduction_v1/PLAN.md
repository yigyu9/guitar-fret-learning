# 사전 선정 손가락 목표의 새4시도 재현

부모grid의사전순위가선정한index115(0,0,+5,0도)와middle114(0,0,+5,−5도)만대상이다. 실제분석/독립검수에서분모·순위·성과가확인되어야GPU실행한다. 달성한225행에서아무행이나바꾸어고르지않는다. source/reference/selected 목표의차이를별도문서로명시한다.

1. [ ] 최소CPU준비: 현재활성 소스동결. 새support안에서parent probe.collect를재사용해각선정목표를4env에동일하게요청한다. ShortPool/settings/trajectory/기존판정·음길이/2sramp/3sonset/tail/범위/PD/속도/충돌90쌍/엄지035·비선택B불변. 실제state주입/NN/checkpoint없음. 원목표4각과gridoffset·최종각,기존sourceJSON과선정근거grid/eval/selection/봉인/실제종료/검수SHA를기록한다. 부모의reference를거짓수정하거나보존파일을덮어쓰지않는다.
2. [ ] CPU/별도검수: 각4개동일목표의서로다른env_id첫시도1개,실패포함,원성공원장/수집상한/close·SHA·실패전파. 원시trace는사전env0첫시도만60Hz,4개전부는관절/gate/세마디하중요약. 부모collect의grid_index중복을환경별시도ID와구분하고원후보ID는유지한다. 결과를225grid재실행이나4seed로설명하지않는다.
3. [ ] rootGPU한finger씩: 두원음/두선정target각4첫시도. 기존baseline0/4와이번선정재현을각조건으로보고한다. 압현통과사전기준은4/4달성·평균clean≥70%·wrong≤10%·물리/손목실패0. 실패시다른후보사후교체금지.
4. [ ] 실제검수/분기: 판정재현과안전/자연스러움·높은proximal하중을별도판단한다. 성공해도현재index73N하중문제해결로확대하지않고pairA/B및자세확인을먼저마친다. 불안정하면gate/실제각/하중을근거로고정wrist조건의학습대상을재검토한다. 원래범위/성공문턱완화·장기학습으로덮지않는다.

모든새도구/결과는이하위폴더에두고기존source/부모PLAN·원결과·봉인수정0. GPU는root만직렬실행하며전체실패진단goal미완료상태를유지한다.
