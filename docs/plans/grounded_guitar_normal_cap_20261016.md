# V9 실제시험: 기존20N normal cap 범위의 마지막 폐쇄 비교

V8 actual5초 schedule8→9mm는prefix/KD/나머지15기준중Chest외모두통과했다. Chest최후접촉1.3875s,settle동시접촉5.2029%,last1 Chest sourcegap.060393~.085125mm/rawhumanrequest18.06156~18.11195N(clip0),Spine접촉100%. 전구간상체max4.844598°는8mm startup과같고종료Chest4.53803°. 원래20Ncap까지약1.9N의유한여유가남는다.

source4/worldright/하체/PD/cap/첫0.75s 8mm는그대로다. .75..1.25s smoothstep의최종depth만9→10mm(증분1mm)로바꾸어원래20Ncap범위에서간격이닫히는지시험한다. same-state최종raw추가−2N,실제cap후약−1.9N이하이며기존cap20값은변경0. 이가상요청은human관절토크이며G외력/부착/상태쓰기0이다. damping은실제surface속도그대로/springpreload만schedule,K150D1유지.

이것은현재기하/자세에서normalcap여유를확인하는경계시험이다. 포화후depth를추가로키우는것은같은힘이므로후속해결책으로채택하지않는다. 실패하면상체자세·접촉지지공간의기하적분담이나상체제어좌표/질량진단으로돌아간다. 성공기준을완화하지않는다.

- [ ] 신규constant/leaf/exactclass/compile·독립검수.
- [ ] native_static_v9 실제5초, 기존15criteria+scheduleprefix총16gate. V7과t<=.75state/contact/command/targets 및K150D1정합.
- [ ] 정지전체통과재현후압현·타현·해제;실패보존/PPO0.
