# 현재 고정LA 조건의 관절→기타 6D 응답 재측정

## 목적과 판단

직전 joint_only_fixed_strap_v1은 후기변화.257786mm/.051003°로 작지만 초기최대
14.084223mm/2.920042° 이탈이 남았다. 이전seed2 Gfeedback의 empirical secant는
초기33각/몸통gain/손목명령이 달라 현재로 승계할 수 없다. 실제G오차를 읽는 보정에
앞서 현재 조건의 signed 목표각 반응을 측정한다. 전체66권한을 단일축으로 제한하는
최종설계가 아니며 작은 입력/응답 진단이다. 이전goal turn은 실제5초·17분석·보존감사를
완료해 다음방향을 바꾼 progress로 분류한다.

## 현재 한 단위

1. 직전 고정LA 관절18후보를 저장 기준으로 사용한다. 동일 초기81각·기타p/q·LA
   1.1018469719600776m·body9 PD×2·고정root하체·physics·collision·손목±.005rad1Hz를
   유지한다. 몸통9/손가락/right targets도 그대로다.
2. L_Shoulder_y의 유지목표 offset만 각각−.008/+ .008rad 바꾼 새trial/proposal을 선언한다.
   실제float32 최종목표의 변화량을 재계산하고 모델/기존offset±.3rad 범위와 양 wrist
   파형극값에서 clipping이 없는지 확인한다. 나머지80개의1200목표를 기준과exact대조한다.
   초기q·source_state는 그대로이며 각 실행 fresh native14 admission을 통과해야 한다.
3. frozen run_palm_witness_initial_diagnostic를 수정 없이 두 조건에 순차 재사용한다.
   조건별한초기화/1200step/초기값·전신/손151frame actualstrap영상을 저장한다.
   실패는 partial로 보존하고 정상5초로 표시하지 않는다. 추가actor/학습0이다.
4. G초기world오차 e=[p−p0, Log(R R0^-1)]의0~.1/.1~.5/2~5/4~5초 평균과 전체
   초기최대·종료·2초기준 후기변화를 비교한다. 4~5초 평균e의 central/forward/backward
   secant를 실제float32 delta로 계산한다. 위치m/회전rad의가중W=diag(1,1,1,.1,.1,.1)는
   분석용lever이며 최종보상가중치가아니다. rank/부호/양·음불일치·국소잔차를 명시한다.
   작은한축 반응을 즉시Jacobian/66관절 제어가능성/접촉력 또는 자유기타복원성공으로
   확대하지 않는다. 유효반응이면이범위안의새Gfeedback계획, 비선형/무응답이면다른
   관절/다축응답계획으로 다음행동을 정한다. 기존j/게인/box를자동채택하지않는다.

## 보존·산출물

소스/메인계획은stability_adapter_2에, 실행/이미지/그래프/영상은
/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1에 저장한다.
실행전 원문·SHA/입력/명령을복사하고 출력·로그·exit/전후SHA를보존한다.
소비원문수정·기타고정·손부착·지속pose덮어쓰기·기타목표외력은없다.
Source거리와PhysX cooked접촉의한계·palm상향·rawλ단위를구분하고기존자료를보존한다.

- [ ] 두새입력·float32 목표·closure 준비/검수.
- [ ] 실제두5초·freshgate·두시점이미지·4영상.
- [ ] 초기/후기·6D signed응답분석·다음보정방향/그림설명·독립검수·봉인.
