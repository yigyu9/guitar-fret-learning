# 손가락 구동 힘 상한 단일 비교

현재 원본 손가락 native effort 상한은 축마다20Nm다. 검지 grid21개 달성 후보에서도 첫마디 음중평균합력이38.8~88.3N로 남았다(탐색적 전체분포이며원선정115는그대로). 첫마디 한쌍 충돌을제외하면큰힘이index2로옮겨가압현은0/4였으므로,원래90쌍을유지한제어요인분리가필요하다. 큰상한이원인이라고확정하지않고한변수실험으로본다.

가설: 목표를향해부딪힌손가락과비선택B가서로밀때큰PD토크를계속허용한다. 손가락운동비용을추가하거나가동범위/충돌을없애지않고native구동상한만줄였을때목표도달·시간·하중이얼마나변하는지확인한다. **0.25Nm는사전정한공학진단값이며실제인체의정답값으로주장하지않는다.** 기하학적접촉력상한을보장하지도않는다.

1. [ ] 최소CPU준비: 새support안의진단subclass에서GpuScene생성중에만prepared contract의개인사본을써검지~소지16축 native_PD_properties.effort를20→0.25Nm로바꾼다. 엄지5·팔/나머지89축·전체범위/PD K/D/가속/질량/형상/90collision쌍/속도·codec/wristv3/음길이/보상·종료는같다. 원source·prepared JSON·states를수정하지않고본래loader검증이끝난사본만변경한다. 원contract SHA·16필드전후·진단schema/다른105속성동일성과native readback을명시한다. 원상태는035경계reset만하며지속state주입금지.
2. [ ] 재사용/검수: 기존grid reproduction의document/collect/acceptance/정해진index115·middle114/각4firstattempts를재사용한다. baseline20Nm는독립검수한원4시도재현을그대로기준으로사용하며같은실행으로가장하지않는다. 따라서이probe는cap0.25조건두새scene만GPU실행한다. NN/체크포인트없음·동일seed7·2초ramp/3초onset/tail·다른변수불변. wrapper복원/예외·분모·기존출력거부/핀/장면닫기·기존계약과새effort의차이를숨기지않는지CPU검수.
3. [ ] rootGPU직렬: 원20Nm재현실제종료/검수뒤index,middle순. native105 effort/K/D/drive mode/범위읽기검증및같은target요청·실제각/속도·손목/하중·원성공을수집. 기존60Hz세마디순힘은접촉쌍압력·240Hz극값이나motor단독토크인증이아니다. DOF total force sensor는구동과constraint를구분하지못하면motor torque상한증명에쓰지않는다.
4. [ ] 실제분석/독립검수:4시도달성/clean/wrong/실패와각도추종·양쪽손가락마디별힘을비교한다. 하중만줄고도달을잃으면채택하지않는다. 효과있어도기본변경은별도아카이브/회귀·무접촉양방향이동·유지/해제·다른finger/자유기타검증뒤판단한다. 임의의여러cap/gain탐색·현재판정완화·움직임비용추가는이번범위가아니다.

GPU는root만. 현재는계획이며active구현변경0. 다른준비/원결과/봉인보존·진단자료정리제외유지. 원20Nm재현검수와pair실제검수를기다리며새CPU도구만준비할수있다. 전체goal미완료.
