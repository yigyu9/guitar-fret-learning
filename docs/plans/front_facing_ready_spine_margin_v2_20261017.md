# 가슴의 작은 위치 변화를 허용한 두point 추가 여유 진단

원leaf와 result_v1은 보존한다. .20/.35mm 모두 SLSQP 국소해 실패였으며, source 여유만 좋아진 결과를 채택하지 않는다. currentactual/goal·원initialFK·두anchor5060/6330과held6328·추가δ만적용·actualG고정의반사실범위는같다.

사용자 필수조건은 가슴의 실제 접촉 지지다. 가슴 world 목표 위치를0.1µm까지 그대로 보존하는 것은 이전 설계 보조조건이며 사용자 필수조건이 아니다. 새 계산은 작은 가슴 이동을 허용한다. 실제 접촉·기타 지지는 후속 물리 검증에서 계속 필수다. 원source1mm/Spine5도/gain/cap/상태주입금지/왼손해제기준은 변경하지 않는다.

## 새 문제 정의(계산 전 확정)

- 추가gap .20/.35mm 두후보, search±.03rad/축과 actual/goal 양anchor bounds 교집합 유지.
- equality4:5060 goalChest 회전3 보존 + actualSpine 고정법선 추가gain1. 위치보존 equality3은 새 문제에서 제거한다.
- goalChest 위치 변화는 두anchor 각각≤0.5mm. 회전은 기존1e−6rad strict 유지. actualChest는≤0.5mm/.02도, R_Shoulder/L_Wrist/Head는≤0.75mm/.02도 보조상한이다. 목표 위치를 옮겨도 실제 지지가 유지된다는 뜻은 아니다.
- F64actual/goal 모두 Spine4.8/TorsoChest4.9/right2.9 내부 설계 상한 유지. actualpose16+tilt20에 goal위치2를 추가한38개 부등식이다. F32는 별도로 원strict4.95/5/3 및 새선언pose상한을 검사한다. 원105EPS0/zero8실패를 숨기지 않는다.
- 목적함수 `0.5*(δ9·δ9 + ||50*(goalChest위치변화_m)||²)`로 목표 위치 변화도 최소화한다. 50은 이 반사실 설계의 위치 비용 가중치(각도 환산50rad/m)이며 물리 힘이나gain이 아니다. 추가항에 맞게 gradient를 재계산하거나 수치미분한다. 이전jac=x를 그대로 사용하지 않는다.
- 최적화가 부등식 경계에 놓이는 수치실패를 피하려고 각38개 부등식에서 양의 내부reserve1e−5를 미리 요구한다. tilt성분은1e−5도, pose정규화성분은 그 상한의1e−5 비율이다. 최종판정은 원래 부등식≥0이며 사후epsilon을 더하지 않는다.
-5060 gain잔차≤1e−7m와 F64/F32 g≥−.95mm, 모든route AND 유지.6330 projection은 진단만, 전source통과로 해석하지 않는다. 두후보 모두 실패하면 불가능성 증명이 아닌 결과·잔차를 보존한다.

작은CPU(새4×9rank/FD/목적함수gradient·기존source수식 동일성·신규pose/내부reserve 경계반례)와 독립FINAL/RootACK 후 새result_v2에서 두point만 계산한다. 후보가 있어도 전기간/ramp/source와 실제정지5초·반복 전에runtime/native진입하지 않는다. 이번변경은판정후기준완화가아니라원실패를보존한새목표위치설계다.
