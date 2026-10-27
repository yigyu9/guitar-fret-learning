# 새두point 후보의 기존 전기간 반사실 검사

새goalChest 위치설계의 result_v2에서 추가.20/.35mm 모두point설계통과했다. 이것은동적성공이나현재기타고정설정이아니다. 실제G는원기록을고정한계산뿐이다. 원V1 두실패및현재repeat10동적source실패는보존한다.

## 범위

- 기존native_baseline_v10/native_repeat_v10의5..28초 source60Hz+종료1381시점씩을읽는다. 새후속protocol의34/40/49초를예측했다고설명하지않는다.
- 현재Body9increment에추가δ를16..16.5 smoothstep으로가산한다. originalinitialFK를고정하고actualnativeTorso/Spine capsule에FK전후rigid delta를운반한다. actualG worldpose는원관측을그대로둔다.
-두후보각각F64/F32에서Torso/Spine×physicalG89=178활성쌍을모두검사한다. 원고정된AABB/projection/최적법선/complete-refinement helper수학을재사용한다. privateg≥−.95mm와원1mm를구분한다.
-actual수정9bounds/principal160/other96·zero8불변, 목표전체105bounds를확인한다. 원actual105EPS0/zero8실패는별도로보존한다.
-새선언goalChest위치≤.5mm/회전≤1e−6rad, actualChest≤.5mm/.02도·후손≤.75mm/.02도, F64내부Spine4.8/TorsoChest4.9/right2.9, F32원private4.95/5/3를전행검사한다. F32내부4.8은진단과분리한다.
-목표A=원finalF32+δ·ramp와목표B=원preIncrement→(기존increment+δ)·ramp→Chestlast의F64/F32를분리한다. δ0 B가원finalF32 Body9와같은지먼저검사하고, rate제한이활성화될수있으면실제새Body9 요청경로의.1rad/s이력을검사한다. 목표를단순히actualq라고취급하지않는다.
-기존source native g와FK/anchored g를분리한다. compiled source policy/model108 입력은실제expected맵을선택검증한다. 입력schema를추측하지않는다.

## 판정·후속

두point통과만으로자동선택하지않으며두run의전행AND를각후보별로기록한다. 전체신체/손가락/새LH-IK의동적반응을인증하지않는다. Body9변화에대해왼팔IK는실제실행에서재계산되므로oldarm상태를고정한LH형상계산으로새제어성공을선취하지않는다. baseline/repeat실제새source와왼손전체해제는필수로남는다.

새후속runtime는별도계획의정지17..22후action을사용한다. 본검사는oldstress16초action원기록의반사실이며새시작시각의실제성공이아니다. gain/cap/G상태/기존source수학변경0/PPO0. 작은CPU·독립FINAL·RootACK후새out에서검사하고,실제정지5초가통과한뒤새action진단을수행한다.
