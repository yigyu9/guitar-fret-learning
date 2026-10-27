# V7 실제시험: 남은Chest 0.31mm간격과목표8mm

V6(source4/Chest7mm) actual5초에서가슴접촉은107표본(0.05~.533333s) 유지됐으나.5375s Spine접촉으로교대해끝까지지속됐다. last1s Chestsourcegap .301918~.314984mm/rawhumanrequest약14.55N,전체최대18.24391N/20clip0. 전구간상체max4.6027745°,Grot1.311789°/넥1.008848°/양발gate통과. 유일실패는지속Chest지지다.

## 변경선택과한계
같은source4/worldright/하체/PD/caps에서virtualChestdepth7→8mm만비교한다. 추가same-state raw요청−2N이며초기일부가원래20Ncap에닿을가능성을그대로허용/기록한다. cap값은올리지않는다. 앞선3mm증분에서간격1.152mm감소,이번3→7mm에서1.418→약.312mm감소를관측했다. 7.5mm의예측감소.14~.19mm로는잔여.31mm를닫기부족할가능성이커8mm를선택한다. 상체max여유.397°가작으므로실제5°gate를그대로유지한다. 선형외삽을실제성공으로주장하지않는다.

원리/수식은검수runtime_v7그대로이고depth상수만.008이다. finitehuman normal task이며G직접힘/부착/고정/상태쓰기0,105/원0range8/하체16finite/Rootfixed/좌석과발제어불변이다.

- [ ] 문법·독립검수/새입력SHA.
- [ ] 실제native_static_v7(7번째5초), 기존전체15gate/Chest↔Spine교대/normalcap/상체·G·발을검사.
- [ ] 전체성공재현후압현·타현·해제;PPO0. 실패면추가깊이를자동정답으로채택하지않고다음원자료에따라결정한다.
