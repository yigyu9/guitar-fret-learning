# 자유 기타 V4: Spine 여유5mm의 새 초기 기하

## 근거
V2 initialworldright: 실제5초 회전1.26865°/넥.4983°/발통과지만Chest0. V3 Chest가상depth6mm는gap2.365→1.212mm를줄였지만Spine받침과상체기울기4.4827°를증가시켰고Chest0이었다. 출력/gain을더키우기보다접촉공간관계를바꾼다. 기존초기Spinegap1.873mm는실제접촉전이에서소진되었다.

전human q/Root/좌석/발을고정한순수source탐색에서Gcenterlateral0을유지하며Chest.300/RShoulder.500/RHip.500/Spine5.000/PelvisSAT4.380mm가공존하는후보를찾았다. source1대비Gbody중심front+.498409mm,Z+1.228034mm,absolute neck1.008832°,neck-axisroll+.418103°,worldyaw−.536776°; G절대position[-.2447365785876299,-.09655313507325103,.6993953063818535]m, xyzw[-.5625349435745866,.37061248947047365,.6242474312322926,.39562098592708517]. 이는선택된순수source후보수치이며float32/전체형상/native성공은아직아니다.

## 단일 비교 범위
새source_v2에서위G초기pose만적용하고전human/발/Root/좌석/q는그대로둔다. 초기상대palm변화는직전source1대비L6.48/R2.47mm,회전.91°예상; 전체baselineFoot대비도별도기록한다. 이번손상대허용범위는명시적으로10mm/3°로검사하고손mesh완전형상인증은주장하지않는다. 실제native손접촉과안전gate필수.

제어는V2 initialworldright/원래Chest3mm의작은가상preload로돌아가geometry효과를V2와비교한다. 원본gain/cap,성공발제어,Rootfixed/Gfree+gravity/strapOFF/상태덮어쓰기금지는유지한다. V3와의비교에는기하와preload두변수가다르므로단일원인효과로설명하지않는다.

## 체크리스트
- [ ] 새source2 float32후allcaps/convex,allhumanBOX-Gbody/Pelvis,chair,ground,unchangedhuman/foot감사 및SHA before/after.
- [ ] 독립검수후run_v2의새config로native_static_v4(5초)실행.
- [ ] analyzer_v2의기존15gate/전구간변위각도/settleChest+위팔·발/last1soles로판정.
- [ ] 전체성공이면같은cfg재현,이어서5초prepare후압현/타현/결합. 실패면원자료접촉순서/부하를읽고새버전으로이어간다.

기존실패·코드·입력·leaf계획은모두동결한다. source Spinespace5mm를실제nativeclearance나지지성공이라고설명하지않는다.
