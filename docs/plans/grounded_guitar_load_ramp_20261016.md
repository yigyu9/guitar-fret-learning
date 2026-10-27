# V8 실제시험: 초기8mm 유지 후 하중정착 구간9mm 목표

V7 actual5초에서Chest settle접촉4.1623%,last1s gap.123133~.142352mm,rawhumanrequest약16.20N. 최대상체4.844598°는.525s,종료4.41605°로과도추가.43°가있다. 기타와발등나머지14gate는통과. 힘cap20은원래그대로이며V7실제1표본clip.

## 채택하지 않은 감쇠 제안
상체D1→6 제안은실행하지않았다. nativeprops+XML의근사body9질량최소고유값.002921kgm²에서는240Hz explicit dtD/m가1.426→8.56,단순선형모드(dt²K+2dtD)/m가3.745→18.01로안정여유가없다. 이는couplednativeM인증이아닌경고계산이지만,감쇠를안전하다고가정해추가할근거가부족하다. 원D1/K150을유지한다.

## 선택한 최소변경
source4/worldright/발/상체PD/caps를그대로두고virtualChestdepth시간함수만변경한다. 초기0..0.75s에는검사된8mm그대로유지,0.75..1.25s smoothstep으로8→9mm,이후9mm. 최대기울기가난.525s의startup을바꾸지않고,hipload가정착하며남는.13mm간격만보상하려는유한인체목표다. V7은1초이후에도Chestpositive40samples가있으므로접촉소실이전증분을시작한다. source간응답은선형보장이없어동일15gate로실측한다.

same-state 최종추가raw요청−2N,cap20변경0. 1mm/.5s smoothstep 최대목표변화율3mm/s,raw요청기하증분rate최대6N/s. 초기7.5mm/8.5mm를새순간목표로넣거나몸통고정/상태쓰기/G직접힘을추가하지않는다. 실제source침투와virtualdepth를구분한다.

- [ ] 신규runtime_v9/wrapper/analyzer/입력pin/문법·독립검수.
- [ ] native_static_v8 실제5초(8번째). 기존15gate유지+perstep목표depth와원D1/K150기록. V7과0..0.75s state/contacts/제출105torque·finaltargets일치검사.
- [ ] 전체통과시동일cfg재현→압현/타현/해제. 실패는보존후관측에따라다음단계를정한다. PPO0.

정의보완: schedule은spring preload만시간에따라바꾸며damping은실제Gsurface와인체점의상대속도를그대로쓴다. −D*depthdot goal-velocity feedforward는추가하지않는다. 이는설정한제어법정의이며이를전체이동goal속도추종이라고설명하지않는다. prefix검사는t=.75 명령까지포함하여effort181/target46/state181/contact181행을대조한다. 기존15criteria+schedule/prefix/KD정합1gate(총16)를검사한다.
