# 다음 소단계: 실제 기타 오차로 손목 Y/Z 목표를 보정

Y/Z 두±.005rad 실제5초응답을확보했다. Zplus종료13.817638mm/2.895722°·후기1초.572182mm/.104704°는원기준13.819696mm/2.918277°·.648625mm/.115306°보다작지만위치개선은약.002058mm로극히작다. Zminus는종료13.829543mm/2.946758°·후기1.056584mm/.171364°로악화됐다. Yminus는종료두오차가줄었으나후기변화는조금커졌다. 이런미세변화를실패/성공의과도한절대기준으로삼지않는다.

comparison_v2.json의world6×2응답을사용한다. 위치.03m/회전5°로정규화했을때rank2·columncos−.728127296·조건수2.719646212다. 제한LS후보Y−.005/Z+.005는실제동시입력미측정이며13.635787mm/2.882135°는모델계산값일뿐이다. 6×2는임의6D복원권한이나순간Jacobian을보장하지않는다. 최초비교의보존목록참조KeyError는원소스/사전기록을보존하고v2에서baseline자체inventory를엄격대조하도록정정했다. 물리재실행은없다.

이번다음시험부터기타의현재p/q오차를관절목표에feedback한다. J는저장6×2world응답,S=diag(.03m,.03m,.03m,5°,5°,5°)다. 현재오차e=[p_goal−p_current, Log(R_goal R_current^-1)]로두며world좌표를지킨다. 정규화행렬A=S^-1J,오차b=S^-1e,gradient g=A^T b를계산한다. 상태delta는2초까지0이며그이후60Hz명령시각마다다음과같이갱신한다.

    rate = clip(kappa * g, -0.002, +0.002)  # rad/s, 각 축
    delta_next = clip(delta + rate / 60, -0.005, +0.005)  # rad
    q_final = q_hold + 기존 L_Wrist_x 사인목표 + delta(Y,Z)

clip은안정화보정자체의입력허용범위/변화율제한이며관절state/pose를덮어쓰지않는다. 기존compose로66offset±.3/native최종목표한계도엄격검사하고넘으면거절한다. delta상태자체를한계안에두어숨은integratorwindup을누적하지않는다. sourcecontrol/actor정규화공간의임의clip으로대체하지않는다. 두축동시작용은이실제ON시험에서처음검증한다.

kappa는원baseline t=2초(step480)오차의g_ref=[−.8247321000112535,+.4581455826792709]rad^-1로고정보정한다. max축rate .002rad/s가되도록kappa=.002/max(abs(g_ref))=.00242502989755426rad²/s다. 기준초기rate는Y−.002/Z+.001111016735429649rad/s다. 실제ON에서는저장기준오차가아니라매명령직전실제기타오차를쓰며gain은실행중바꾸지않는다. g가역전하면delta도되돌아올수있다. 이설계가폐루프안정성을증명하는것은아니며freshnative로확인한다.

원quiet초기81각·기타fullstate·LA1.1018469719600776m·원PD(몸통KP2/KD√2)·root하체고정·기존손목Xsin·손가락전체목표를유지한다. 주요66권한은유지하고이번안정화보정만양손목중왼Y/Z에한정한다. 시작후관절state/기타pose쓰기·기타인위적복원력·손강제부착·기타고정은없다. 몸통9목표held와실제관절각변화를구분해측정한다.

최대두actual초기화로OFF/ON각fresh15직접gate통과동일환경1200step/151frame/스트랩두영상을저장한다. 자동retry는없다. OFF는원baseline81목표전체·가능한전체native경로를직접대조한다. ON은처음484명령과앞2초nativeprefix·다른79목표/손가락전체·실제오차→g/rate/delta/최종PD목표·rate/angle제한·body9/고정하체·접촉/손바닥방향/실제관절한계초과를검사한다. 초기오차와후기변화는분리해보고자연스러움/전체성공을자동인증하지않는다. 조건부오류는partial과원자료로남긴다.

이단계에서는actor추론/학습을하지않는다. 이후 q_hold를fret/strike연주목표로바꾸어같은최종목표합성구조를재사용할수있어야한다. 원정책관측은현재기타frame을쓰나자유기타정책성능은미검증이며sourceprofile실제각과previousPD/history bridge표현조건은구분한다. 2초공통구간은진단용이며연주선행WAIT/REACH/GRIP/TRANSPORT과정으로승계하지않는다.

- [ ] Feedback OFF/ON새구현·목표/오차수학검산·독립검수
- [ ] 두actual5초/partial보존
- [ ] 초기오차·후기/제약·모델기여를분석해연주목표연결방향결정

아직구현·실행하지않았다. 예정결과 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1.
