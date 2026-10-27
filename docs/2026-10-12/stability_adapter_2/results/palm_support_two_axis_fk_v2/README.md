# 실제 관절각–손바닥 FK 대조와 손가락 두축 가설

이번단계는완료된몸통PD×2의actual0~5초저장자료를읽은offline분석이다. 추가native초기화/physics/trial0이다. 손바닥·팔FK는실제상태와잘맞았지만손가락까지포함한전체손FK의기존gate는네가설모두미달했다. 기존FK로손가락각을바꾼미래형상을인증하거나제어를바로실행하지않았다.

## 초기값과 실제 실행 출처

[이분석의실제초기81각/G p·q/PD·LA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/initial_values.json), [원실행trial](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_patch_priority_diagnostic_v1/palm_wide_near17.json:1)을사용한다. 기타최대14.052228mm/2.884291°·palmcontact0의기존실행이며다른실행을한것으로집계하지않는다.

![분석대상 기존실제Gym 손·스트랩0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/hands.mp4)

완료된native영상출처다. 주황실선/옅은점선은actualpassive strap 경로이며새source모델/아래그림을Gymrender로표현하지않는다.

## t0 calibration을 유지한 runtime FK

[최초runtime대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_runtime_fk_v1/analysis.json)는t0의relative transforms/q0를한번만calibrate했다. Step0/24/120/1200의actualq를입력하고actualChestpose변화로world변환했다. 각시점finger/armrelativepose를다시fit해정답을강제로만들지않았다.

Palm sourceanchor의실제점대조오차는최대0.000157460mm였고normal도매우잘맞았다. 그러나약지1의회전오차가손끝으로누적돼5초ring_top 원점오차1.221470mm·최대body회전0.017248rad가됐다. 기존전체body gate0.1mm/0.001rad는실패다. t0의거의0오차는calibration결과이며runtime정확성증명과구분한다.

## 두좌표 회전의네가설과heldout 대조

Same-body두좌표에만exp(sum),XML순서product,역순product,quaternion벡터basis×tan(q/2)·scalar1의정규화map을비교했다. 다른3좌표·1좌표와t0calibration은유지했다. 마지막가설은순수수학가설이며PhysX의확정계약으로설명하지않는다. 원인도아직확정하지않는다.

4시점0/24/120/1200과별도20heldout시점의동일native parent–child상대회전/전체chain을대조했다. 추가fit과gate완화는없다. V1세가설/source/wrapper/로그를보존하고V2네가설로추가했다. [V1결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v1/analysis.json)·[V2결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2/analysis.json)에원자료를둔다.

| 두좌표 가설 | heldout20 최대body위치오차 | 최대body회전오차 | 전체손gate |
|---|---:|---:|---|
| exp(sum) |1.222811mm|0.017266rad|미달|
| XML순서product |0.835770mm|0.010405rad|미달|
| 역순product |1.727665mm|0.025484rad|미달|
| tangent-half quaternion |1.277136mm|0.017688rad|미달|

![실제저장24시점에대한source FK 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2/artifacts/whole_hand_FK_hypotheses.png)

위는왼팔·손각body원점오차의최대mm,아래는body SO(3)상대회전오차의최대mrad다. DOF좌표drift와다르다. 빨간선은기존0.1mm/1mrad대조기준이며모두미달했다. 선은표본연결이고연속오차측정이아니다. Source geometry/FK 그림이며native영상이아니다.

## 정확히확인된palm/팔범위와미실행각제안

[범위평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2/palm_scope_assessment.json)에서24시점palm body원점최대0.000312034mm·회전6.383681×10⁻⁷rad,팔body원점0.000278428mm·회전6.380717×10⁻⁷rad였다. Palm/arm은기존기준안에들어오지만전체손실패는그대로유지한다. 이는해당24저장시점의좌표예측근거이며모든자세/PD목표/접촉응답을인증하지않는다.

![5초시점palm 위치미분과네시점기하각제안](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2/artifacts/palm_J_and_geometric_proposals.png)

위열은왼팔12·행은world XYZ이며±0.0001rad source FK미분을mm/rad로표시한다. Native정적한계에접근한축은one-sided,actualq가한계밖이면unconstrained source미분이라고원자료에명시했다. 아래는position-only damped least-squares λ0.01m/rad의기하dq이다. Native한계∩actualq±0.05rad안에서제안하며이값은제출한PD목표/실제motion이아니다.

목표점은actualG의요청palm patch에서Gy/Gz를3.1mm안쪽으로clamp한plane점+outward unitnormal0.1mm다. 정확평행강제는없고normal미분은진단만계산했다. 대표source점오차0/0.1/0.5/5초0.759395/7.162044/16.045099/16.727384mm가가상각변경후0.000582/0.065918/0.334887/0.362148mm로예측됐다. 이것은기하계산이며nativePD로같이개선됐다는뜻이아니다. Wholehand겹침/상향조건/실제접촉은다음단계에확인한다.

기존81목표에이dq를더한float32목표의native한계와initial66offset±0.3rad는네시점계산에서통과했다. Actualq를기존base목표로치환하지않는다. Actualnativeangle은R_Thorax_x가전체1201표본중3step에서정적한계를최대0.000099935rad(0.005726°)넘었다. 목표의한계통과와actual물리상태를구분하고원자료를숨기지않는다.

## 다음방향과검증범위

[다음계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_MEASURED_POSE_RESIDUAL_PLAN.md:1)은미실행이다. Actualfingerbodypose의source형상에검증된palm/팔12기하변화를적용해1/0.5/0.25배제안의겹침/상향을먼저확인한다. Finger21의미래q→pose를가정하지않고현재sensorpose를읽는방식이다. Physics body/joint/guitarstate에는쓰지않는다. 안전한방향후기존81목표+bounded/rate-limitedpalm residual의한actual5초실행계약을정한다.

Finger21/R팔손/몸통9목표는다음소단계의비교중유지하지만최종66연주권한을제한하지않는다. 기타initial worldp/q복원·유지,thumb후면/다른손가락전면/palm옆면지지와연주안정화는미완료다. 제어합성관계/실제물리반응뒤학습구조를정하고WAIT→REACH→GRIP→TRANSPORT를연주필수선행과정으로만들지않는다.

4runtime검사·3가설V1/4가설V2각5검사·범위4검사와source/실행SHA를확인했다. Root가실제PNG와원자료·native프레임출처를대조했다. Luna/독립change-reviewer 도구threadlimit으로root산출물/자체검증이며독립검수는보류다. [변경파일절대경로·실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2/CHANGED_FILES.md:1)을따른다. 이전FK/helper/계획/물리실행은변경하지않았다.
