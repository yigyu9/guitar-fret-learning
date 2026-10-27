# 어깨 Y 목표 보정의 크기와 실제 기타 오차 feedback 비교

seed2_response_locality_v1의 실제3init/3600step을 완료했다. 같은초기81q/G/LA/PD에서
L_Shoulder_y -.002rad가 최대p/q26.684900mm/8.116260°, 종료22.883315mm/7.338493°로
기준26.772807mm/8.323296°, 종료23.188748mm/7.413329°보다 모두 작았다.
L_Wrist_z -.002rad는 최대회전8.377872°로 커졌고 half-heldout의 최대이동26.938437mm도 커졌다.
어깨Y -.002를 크기 탐색의 후보로 보존하며 원seed2/full/currentLA를 공통진단기준으로 둔다.
손바닥의 마지막양λ118/124/123과전체행134/133/134 이후소실은 해결되지 않았다.
세조건R_Hip–기타는1200개step전부양λ행이있었다. body기록이며면별지지/뉴턴힘/관통인증이아니다.

last1s의 양음끝점6×2차분은잠정rotationlever.1m 가중rank2/조건수4.805다.
0각보간잔차는Shoulder_y .135093mm/.026051°, Wrist_z .148227mm/.026527°다.
half의oldJ예측잔차 .481436mm/.084446°와full기반보간잔차 .104851mm/.014643°가 남았다.
정확한 runtime Jacobian 또는 최종66축 제어가능성의 증명으로 쓰지 않는다.

## 다음 작은 단위: 새3init/3600step

같은초기q/G/LA1.1018469719600776m/PD/solver/selfcollision에서 각각새5초를 실행한다.
원trial/proposal/producer는보존하고새phase/code/trial을사용한다.

1. L_Shoulder_y 상수 residual -.008rad(약-.46°).
2. L_Shoulder_y 상수 residual -.016rad(약-.92°).
3. 실제G오차를읽는목표 residual: δ(0)=0, δ∈[-.016,0]rad, |δ_dot|≤.008rad/s.
   모든실행은 기존왼팔12 supportbias를 유지한다. 새보정은Shoulder_y 하나에만 더한다.
   q_play는이번진단에서초기q지만 최종연주66인터페이스는 유지한다.
   몸통9와왼팔외69 목표는기존초기값을 유지한다. 상태를강제로고정하지않는다.

## 기타오차 feedback의 진단식과 제어권

e=[p_current-p_goal, Log(R_current R_goal^-1)]를world에서 m/rad로읽는다.
W=diag(1,1,1,.1,.1,.1)는이번실험선택용잠정가중치다. 성공허용범위가아니다.
j는이번음의Shoulder_y probe의last1s backward derivative 저장값(6×1)이다.
60Hz마다 v=-1.0/s * ((Wj)^T We)/((Wj)^T Wj)를요청하고
v를±.008rad/s로제한해δ_next=clip(δ+v/60,-.016,0)으로갱신한다.
이는측정된작은범위의방향을검증하는1축 feedback진단이며정확한행렬역제어로주장하지않는다.
소스j와W·gain·rate·bounds를입력으로봉인하고각갱신의e/projection/v/δ/실제float32목표를저장한다.
코드검수에서분모유한·양수와부호/시점/합성native한계/상태불변을확인한다.

최종목표는q_play66+지지bias+δ_stabilize다. 이번1축범위는진단용이며33/1축최종제한을만들지않는다.
연주목표변화와안정화의우선순위/잔여범위/변화율은이후연주입력시험에서검증한다.
학습구조는이번실행의물리효과와제어권검증후판단한다.

## 최소제약과 검증

합성offset±.3와native목표한계를확인하고 clipping된목표를요청각으로해석하지않는다.
fresh source/FK/초기81q/초기손바닥상향proxy/중첩검사를확인하고실제root/하체불변을측정한다.
feedback중손바닥proxy가상향반구를벗어나면residual갱신을보류하고이유를기록한다.
마지막안전한목표를유지하되물리는계속5초기록하고안정화성공으로표시하지않는다.
기타고정·손강제부착·pose/state덮어쓰기·기타목표로당기는힘은사용하지않는다.

각초기값/전신·손0~5초151frame30fps/영상container5.033333초를저장한다.
scalarp/q의최대/종료와G6벡터·타깃변화·손바닥/손가락/R_Hip/RH·몸통9실제편차·passive strap법칙을대조한다.
상수2조건과feedback의과도응답/목표포화/제약위반/예측오차를분리해분석한다.
물리/API오류나사용자중단은partial로그/확보영상을보존하고정상5초완료로표시하지않는다.
이계획은아직실행하지않았다. 기타의초기p/q복원·유지및연주중안정화의성공도아직없다.
