# 접지 V5: 평탄 접촉과 수평 미끄럼을 분리하고 하체 목표를 일관되게 연결

2026-10-16. V4는5초완료/무결성통과,1..5초양발동시positiveground100%. 마지막1초4부위밑면−.006512..+.285670mm/tilt최대.160954°로높이·기울기통과. 그러나왼ankle원점ptp9.306866mm/Toe8.142065mm로3mm정지검사실패. 왼linear최대.01214m/s/angular.045rad/s. 오른발ptp.00354mm이하. 전체기타회전14.8846°/넥5.2183°/Chest0 실패도보존한다.

원인가설: V2~4는actualhip을고정입력으로두고lower10만height를맞췄고,XY는weight2의약한항뿐이라잔존hipy/z목표및평탄IK의yaw자유도가수평움직임과경쟁한다. staticflat접촉성공을정지성공으로부르지않는다.

새V5에서는양발Ankle/Toe의초기worldXY를동시에목표로삼고양쪽유효8축씩총16lower목표를일관된IK로계산한다. heightcornerweight2000은그대로,bodyoriginXYweight1000으로위치제약을명시하며gain/cap은변경하지않는다. hip3/leg5의원가동범위보존,hip은source각±.1rad로추가제한하고기타leg5는기존±.6. Hipregularization3,other.02. R_Hip_x는source−.01rad를선호각으로두지만충돌하는legacy목표를그대로강제하지않는다. originalzero8 제외,upper81/Rootfixed/Gfree원조건보존. 16목표는기존rotationalstablePD의유한피드백/원cap을그대로거친다. 매stepstate주입/ground나Gforce추가없음.

고정root에서lower16전체가IK변수이므로ramp종료후world발목표는일관된정지q목표가된다. 완벽한실제Cartesian고정이아니며ground접촉·friction·유한PD가얼마나유지하는지같은native5초/3mm정지gate로확인한다. 기존desiredZ+.5→−1.5mm/.5sec와1mm예측bottomspan/원범위·rate/actualsolegate그대로. 예측XY오차1mm hardguard추가해source도달불가를통과시키지않는다. actualfootgeometry/속도/동시접촉/정지gate완화없음. 새runtime/run/analyze_v5와static5_v5.json. 성공시동일설정새out반복검증. 이전시도는모두불변,새PPO/15초손해제없음.
