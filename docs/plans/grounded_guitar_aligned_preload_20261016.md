# V6 실제시험: 팔 정렬 상태의 bounded Chest 목표7mm

V5(source4+worldright+Chest3mm)는5초/모든무결성·각도·위치·발gate통과했으나Chest지속접촉0. 종료Chest sourcegap1.418mm,Spine−.246mm,전체상체max4.0566°. 팔정렬만으로는해결되지않았다. 실제Rhipy는목표bias−.01rad보다더음수로처져종료qref대비−.026344rad였다. R_Hip_y 원래range[-π/2,0],qref=0이므로초기목표를+.016rad로옮기는보상은원래limit위반이며채택하지않는다. suffix를world축으로해석하지않는다.

## 근거 있는 작은 비교
성공한발제어와하체·Root/의자·source4팔/Gpose를유지한다. 유일제어변경은Chest virtual normal goal3→7mm. gain2000/30,cap20N,원본jointcaps와worldright를그대로유지한다. 기존V2→V3에서3mm목표증분은실제로gap약1.152mm감소/상체max+.412°의유한반응을보였다. 현재1.418mmgap에는4mm증분이약1.54mm감소를줄가능성이있고상체max예측약4.61°로5°이내다. 이는서로다른초기팔/기하에서의선형추정이므로성공보장이아니며동일전체gate로실측한다.

새runtime_v7은검수된runtime_v3의동일Jᵀnormal항치환수식과상수깊이.007m만사용한다. same-state raw요청증분은−8N이며actualsteady변화·접촉은별도측정한다. virtualgoal침투7mm를실제G침투7mm나측정힘으로설명하지않는다. G직접force/state쓰기/constraint추가0,finitehumanpress만쓴다.

- [ ] 신규runtime/wrapper/analyzer문법·독립검수 및입력pin.
- [ ] native_static_v6(실제여섯번째5초) +기존15gate로판정. source3rejected는물리0이라실제count에포함하지않는다.
- [ ] 전체성공시동일설정재현→압현/타현/해제. 실패면contact/body기하별잔차를다시읽고하체성공설정을무리하게바꾸지않는다. PPO0.
