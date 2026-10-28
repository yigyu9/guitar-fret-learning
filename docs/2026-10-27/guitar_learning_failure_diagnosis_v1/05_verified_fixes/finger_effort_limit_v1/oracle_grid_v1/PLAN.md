# 낮은 구동 상한에서 같은 손가락 grid 재확인

원cap한변수실행에서index하중은줄었지만음악목표는실패했고middle은유지했다. 이전목표각은20Nm에서선정한drive target이므로새0.25Nm의actual자세와같지않다. cap변경이팔feedback/손목추종도바꾸며index손목오차약12mm가남았다. 손가락각도만의효과나동일실제wrist라고가정하지않는다. 이재확인은같은원음에서낮은하중조건의압현가능성을찾는유한예산이며기본cap채택이아니다.

1. [ ] root CPU최소구현: 원oracle225표/범위외사유/선정순위/2초ramp/3초onset/원음길이/tail/ShortPool/collect/원판정을그대로재사용한다. 검지135·중지180첫시도각1개. cap의원검증후private16effort0.25사본을scene constructor동안만적용한다. 원cap helper의4env hardassert는우회하지않고같은expected_properties/private_contract를이용한명시numenv별105readback검사를추가한다. 다른89축/PD/범위/90collision/엄지/비선택B/손목v3/보상·종료는불변.
2. [ ] 별도CPU검수: 새문서support만수정,active/원준비/원cap·grid소스동결. originalgrid.execute의pool import만constructor-scoped class로연결하고finally복원하며원_pins는새observer/helper/seal을추가한superset이다. NN/oldcheckpoint없음·출력기존/symlink거부·실제오류/닫기/후검증. 공식cap실제review PASS+모든reviewedSHA/raw연결은GPU전필수이며성능0/4도그대로둔다.
3. [ ] root GPU직렬2scene: 원20Nm grid와완전히같은315목표를각1첫시도로실행. 상세기준행+사전극값8행/원기존20metrics·6gate·selected3마디힘/손목오차·모든실패분모포함. 새native105readback/actualcaps/원source사본비변경/90쌍/장면닫기/실제exit검증.
4. [ ] 실제분석/독립검수:450선언표와315분모·원minperturbation순위를독립재계산하고원20Nm와새0.25전체결과를비교한다. 성공가능영역·힘·실제각·손목추종을같이보고한다. 동일target은동일actual이아니며source순힘을pair압력/240Hz최대/정상힘으로확대하지않는다.
5. [ ] 사전분기: eligible이있으면원순위의선정목표만새4시도재현하고압현/하중/자세를검토한다. 없으면같은변경에서캡·탐색범위를늘리는추가검색을하지않고wrist도달/팔bounds·비선택B간섭을근거로분리한다. 압현기준/곡목표/가동범위를완화하지않는다. 장기학습은미해결손가락에시작하지않는다.

root가이폴더구현을소유한다. 다른worker의cap actual분석/native video준비와공유원문은건드리지않는다. GPU실행은capactual독립검수후root직렬. 현재는계획/CPU단계이며새cap성공·생산반영은미확인이다. 진단자료정리제외유지.
