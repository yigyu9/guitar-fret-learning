# 고정 중지4 tape의 target 누적 진단 — 구현 전 제안

상태: **root가 구현 방향 승인. CPU 구현·독립 검수 진행, GPU 실행 금지.** 활성517 Python·현재 A 입력·기존 봉인/probe/raw는 변경하지 않는다. root의 구현방향 확정은 내부 작업 조율이며 추가 사용자 승인이 아니다. GPU는 후속 root 인계까지 금지한다.

## 1. 같은 명령의 세 조건

각각 원래128환경 첫 시도·218 control/872 physics endpoint를 직렬 실행한다. 원래 corrected baseline final.pt를 strict 로드하며 선택4 입력만 `contact_load_probe/run_final300_policy/control60.npz`의 executed-action tape로 고정한다. 같은 actor를 달라진 관측에 적용한 새 행동 비교가 아니므로 **finite tape 진단**으로 표시한다.

| 조건 | target 처리 |
|---|---|
| ① original | 원래 누적 target 그대로: tape 자체의 무개입 재현 대조 |
| ② no_new_inward | A: 추가 안쪽 target 증분 억제 |
| ③ no_new_inward_and_relax | B: A + 이미 남은 법선 target−q 오차의 유한완화 |

첫480 physics endpoint/120 control(2초)는 전혀 개입하지 않는다. source baseline의 env별 clock480 최근접 reward-pad **body-local material point**를 사전 고정하고 이후 새 argmin을 선택하지 않는다. source index와 raw pose/world-point 역변환의 일치를 CPU 확인한다. 원래 reward nearest/any-sample 판정은 그대로다.

개입 gate: 첫 시도·clock≥480·기존 물리/손목 실패 없음·reset_body_snapshot=false·필요 pose/force/J finite·선택 distal signed press-normal resultant **>원래 loaded 문턱0.01N**. clock480 직후 control121부터 가능하다. stale J 행은 계산 전에 제외하며 gate 거짓이면 원래 target 그대로다. signed gate는 새 진단 조건이고 원래 norm-loaded/candidate/보상 판정은 바꾸지 않는다. candidate를 gate로 삼지 않아 wrong/깊이 때문에 candidate가 없어지는 하중도 관찰한다.

## 2. 권장 수학: rate/native box의 최소 변경 projection

원래 targets 호출 전 선택4 memory `t0`, actual `q`, 원래 반환 target `traw`, `δraw=traw−t0`다. 기존 COM→point Jacobian helper로 고정점 `J(3×4)`를 구하고 실제 guitar pose의 press outward normal로 `g=nWᵀJ`를 만든다.

```
L = max(native_lower−t0, action_lower−t0, −rate[native]/60)
U = min(native_upper−t0, action_upper−t0, +rate[native]/60)
m = max_box g·δ = Σ g_j * (U_j if g_j>0 else L_j)
βA = 0
βB = min(max(0, −g·(t0−q)), m)

δ* = argmin ½||δ−δraw||², subject to L≤δ≤U, g·δ≥β
δ(λ) = clip(δraw+λg,L,U), λ≥0
```

`0∈[L,U]`, 원래 rate=4rad/s를 assert한다. correction에 별도4/60을 더하지 않고 **최종 target 변화 전체**가 이 box 안이어야 한다. A는 새 안쪽 증분만 막고 기존 오차는 유지될 수 있다. B는 현재 tick에 가능한 outward 양m까지만 기존 오차를 완화한다. 실제 q/state로 target을 덮어쓰거나 큰 선형오차를 한 tick에 제거하지 않는다. m=0이면 완화 불가능을 기록한다.

이미 제약을 만족하면 raw 그대로다. 나머지는 단조 `g·δ(λ)−β=0`의 첫 root를 찾는다. **4축 finite clip breakpoint 정렬 + 구간별 affine root**를 권장한다. 일반형 최대8개, 현재 box 안 δraw와 λ≥0에서는 축당 outward bound 하나라 실제≤4개다. 외부 QP/일반 solver를 만들지 않는다.

미세수치: float64로 계산하고 `s=max|g|>0`이면 g와β를 s로 함께 나눈다. g=0은 vacuous constraint로 raw 통과, nonfinite/stale은 skip한다. 새 임의 force/J 크기 문턱은 없다. 최종 float32 target의 box/rate/halfspace는 dtype epsilon·4축 dot·원래 target scale에 근거한 numerical tolerance로 assert하고 실제 잔차를 그대로 남긴다. tolerance 내 미세 음수를 별도 nextafter 등으로 수정하지 않고, tolerance보다 큰 위반은 진단 실패로 보존한다. CPU에서 이를 검증하며 물리 문턱으로 해석하지 않는다.

joint Euclidean 최소 변경은 Cartesian 접선 보존이 아니다. `T=I−nW nWᵀ`로 `TJ(δfiltered−δraw)`를 측정한다. 접선 보존 제약이나 새 solver는 넣지 않는다. 큰 `g·(target−q)`는 국소 선형 외삽이고 실제 침투 mm가 아니다.

## 3. 최소 hook·기록·검증

explorer 확인: controller.targets는 self.target에 copy 후 **같은[N,105] float32 alias**를 반환한다. 호출 전 선택4 old를 clone하고 호출 뒤 `controller.active[spec.learned_action_indices]` 열만 수정한다(현재 middle action21..24→native60..63, 이름 assert). memory/반환 alias/scene 제출 target이 같아야 한다. advanced-index `.copy_()`의 사본 위험을 피한다. Scene.step에는 rate 검사가 없으므로 wrapper가 최종 rate를 assert한다.

기존 strict runner/evaluator/observational probe를 작은 tape/target-hook subclass로 감싸고 전체 평가기를 복제하지 않는다. 원래 source/checkpoint/teacher/자산 pin에 새 wrapper·manifest·tape·고정점 입력만 추가한다. base report/raw는 보존하고 실제 override는 별도 진단 계약에 명시한다. 같은 tick 팔 teacher/B/엄지035는 hook 전에 계산돼 유지된다. **이후 wrist feedback 혼입은 남는다.** previous_action도 override 역산값이 아니므로 원래 action/proposed/final target을 별도 기록한다.

추가60Hz 기록은 old/raw/filtered target4·g/J·gate/skip·signed force·β/m/남은 선형오차·normal/tangent 변화·memory/실제제출 오차, 팔12 요청/손목오차다. 기존 bounded240Hz 하중/pose/실패/9보상 관찰을 재사용한다. full-body240Hz/가중치 저장은 추가하지 않는다.

- CPU: feasible raw, inward A, B의 기존오차0/양/음, mixed/zero/tiny g, native포화/m=0, float rounding, 최종box/halfspace/최소변경, tape/env/clock480 경계, reset/first/failure gate, alias/제출/기존out 보호를 확인한다.
- native①: source tape 요청 exact와 원래 final 평가 JSON·q/target/pose/force를 실제 비교한다. 세 조건 첫480 endpoint도①/source와 비교한다. 불일치면 보존하고 matched 효과 해석을 보류한다.
- native②/③: 전체128 실패포함 성과와 실패 전 하중·원9지급·고정점 normal/tangent·실제 J velocity 잔차를 구분한다. 힘 감소·자연스러움·접촉쌍 압력·정책 단독 원인·새 힘 한계를 주장하지 않는다.
- 독립 change-review 후 root GPU 인계를 기다린다. **root가 위 동일 box+halfspace A/B를 채택하도록 승인했다.** 독립 CPU 검수 전 GPU 실행은 하지 않는다.
