# 검지 candidate 중 DIP 추가 굽힘 억제: 단일축 진단 계획

상태: **root 계획 검토 후 scoped 구현/CPU준비를 승인했다. GPU/native 실행0.** 소유는 이 새 폴더뿐이며 현재 B producer/1267핀/모델/실제분석·baseline·다른 작업자의 자료를 수정하지 않는다.

- [x] DIP 증가 방향의 현재 source/형상 및 기존 native 기록을 CPU로 확인한다.
- [x] 단일 개입·정체성·검증 범위·전체 분모를 사전 고정한다.
- [x] root 계획 검토/최소 구현 승인.
- [x] 승인된 최소 wrapper/CPU 회귀를 구현·검사했다. 기존B load/eval/128cap 경로를 재사용하며 새GPU/성과는0이다.
- [ ] 독립 준비검수/최종봉인 상태는 별도review.json/preparation_seal.json에 기록한다(준비 이후 이 계획 동결).
- [ ] 그 뒤 root만 두 조건의 GPU 실행 및 실제 분석/독립 검수를 수행.

## 방향 근거: 증가를 source 기준 굽힘으로 부를 수 있는가

현재 `guitar_learning/assets/tab2body/assets/smpl_mpl_hands_body.xml:192–196`의 `LH:index3`는 parent `LH:index2` 아래의 **단일 +x hinge**이며 range는 −5..90.0002도다. index3의 source rest rotation은 identity이고 끝점 `LH:index_top`은 `[0,-0.019169357657432556,0]`에 있다. `<inertial quat>`는 질량 관성축이며 body rest rotation이 아니다. 이 자산은 `gpu/scene.py:123`의 native asset loader를 따르며 임의 변환 자산을 새로 만들지 않는다.

`gpu/finger_reward.py:_verify_source_frames`(323)와 `source_finger_frame_contract`(351)는 parent chain·identity rest·전방 −y·굴곡축 +x를 검사한다. 실제 자세 정의는 parent−child 상대회전으로 `(0,-1,0)`을 돌린 뒤 `atan2(-z,-y)`이다(`finger_posture_reward:138–143`). 단일 Rx(θ)는 전방을 `(0,-cosθ,-sinθ)`로 보내므로 현재 DIP 범위에서 이 정의의 굽힘각은 θ이다. `tests/test_gpu_finger_reward.py:test_signed_actual_angles_and_source_axis_sign`(251)도 이 부호를 검사한다. MCP2축이나 press-normal Jacobian으로 일반화하는 주장이 아니다.

추가 GPU 없이 기존 **B300 env0 221개의60Hz 기록**에서 index2→index3 상대 quaternion의 위 굽힘각을 재계산했다. 저장 native `q[LH:index3]`와 최대 차이는 **5.6186856767e−7rad**, native q 범위8.688113..89.217560도, body 굽힘 범위8.688110..89.217548도다. 따라서 이번 단일축의 양의 q/target 방향을 source 기준 굽힘 증가로 사용하는 근거는 있다. 이는 인간 생리학적 굴곡·압현 방향·접촉 하중의 단조성을 인증하지 않는다. 양의 목표를 억제해도 실제각은 관성/기존PD오차로 더 굽혀질 수 있다.

읽은 근거와 SHA:

- XML: `62d3483c19d04624168c834ebfe12d029a91579553b6d6f621162c1030549778`.
- `../low_effort_index_zero_cost_init_v1/evaluation_000300/trace_env0_episode0.npz`: `521fa39f7798d2fc3b7482ed1b6e8c81284c8e61a9be853a8be08df53e7e3629`.
- 같은 폴더 `trace_metadata.json`: `2cec974c84ef8ce44d25a9ab4236a42e2ab79c0138368787f61c96735e63825d`.

## 정확히 두 조건과 최소 seam

같은 B300 `../low_effort_index_zero_cost_init_v1/train/final.pt`를 원 strict 경로/fresh=False로 평가한다. large·seed7·128환경·검지 target4·원2초ramp/3초onset·221tick 상한·fixed 기타·private finger16 effort0.25Nm·원105개 native 속성/90 collision pairs를 유지한다.

1. `passthrough`: 새 진단 wrapper를 거치되 target을 전혀 바꾸지 않는다.
2. `candidate_dip_no_positive_increment`: **현재 유효 candidate이고 wrong이 아닌 행에서 DIP의 추가 양의 target 증분만0**으로 한다.

원 `controller.targets(action,snapshot)` 호출 **전** `old_dip=self.controller.target[:, named_DIP]`를 복사한다. 호출 결과 `raw`가 같은 memory의 alias임을 확인하고 `raw_dip`를 보존한다. 원 판정 `candidate[:, selected_index] & ~wrong[:, selected_index]` 및 live first-attempt/유한 상태/비reset/기존 물리·손목 실패 없음인 행을 gate로 쓴다. candidate 자체도 positive & ~wrong이지만 명시적인 wrong 배제를 기록한다. force/J/각도에 새 문턱을 추가하지 않는다.

`gate & (raw_dip > old_dip)`이면 반환alias와 `controller.target`의 그 DIP값만 `old_dip`로 유지한다. 나머지는 원 `raw`를 그대로 둔다. zero/negative 증분은 gate가 참이어도 exact 통과한다. 따라서 MCPx/MCPz/PIP3축 및 외부101축, 합계104열은 **같은 snapshot에서 계산한 원 target과 exact**여야 한다. 이104열의 두 run 간 실제값까지 같다고 주장하지 않는다(개입 후 정책·팔feedback은 달라질 수 있음).

최소 hook은 `gpu/control.py:BatchedController.targets`(399/alias return418)의 **해당 인스턴스에만** 둔다. 원 함수와 active package는 수정하지 않는다. B `probe.execution_scope:103`/`initialization_scope:77`가 제공하는 cap검증·Btag·fresh=False를 유지한 뒤 얇은 진단 pool에서 hook을 설치/복원한다. `runner.ShortPool`과 `runtime.ShortPool` alias, 기존 두 `_pins` 경로의 superset 및 finally 복원을 보존한다. 엄지035/비선택B·팔teacher/손목v3의 순서나 계산을 바꾸지 않는다.

현재60Hz 제어 snapshot의 판정을 사용하며 영구 first-contact latch나 과거 source 시각을 gate로 쓰지 않는다. 접촉 상실에는 무하중뿐 아니라 기하 탈락·wrong 발생도 포함한다. gate가 꺼지면 **유지됐던 bounded memory에서** 원 제어를 재개한다. 억제했던 증가량은 저장/회수하지 않으며 재접촉 때 몰아서 제출하지 않는다. 네 물리substep 중간에는 새 target을 제출하지 않고 다음60Hz 경계까지 기다린다. 원 env0 첫candidate1.133333초를 모든 환경의 고정 개입시각으로 사용하지 않는다.

## 불변 계약과 정체성

- 실제 q/qd/body state/초기 상태를 덮어쓰지 않는다. target을 actual로 치환하거나 관절 비율을 결합하지 않는다. DIP 음의 증분과 다른 축의 제어를 막지 않는다. force cap/gain·PD·native 전체 범위·4rad/s·physics240/60·90pairs·원9보상·실패/비용식·LH21 움직임비용0을 유지한다. 새 실패가 생기면 원 비용을 기록하며 결과 비용을0으로 강제하지 않는다.
- 원 함수가 만든 native/action/rate 제한 목표 또는 기존 bounded 목표만 사용한다. 최종 DIP 변화가 `old±4/60`과 원 native/action bounds 교집합 안인지 확인한다. 범위를 좁히는 새 clamp는 추가하지 않는다.
- memory와 반환alias, `scene.target` 제출값, 다음 snapshot 및 observation의 `target_error=target−q`가 같은 변경 target을 가리켜야 한다. `GpuPool.step:81/100`의 원 제출·4substep과 `gpu/environment.py:1351`의 관측을 그대로 따른다.
- 원 NN 요청과 `ShortPool.last_executed_action`은 덮어쓰지 않는다. 현재 hook은 target 해석 뒤의 외부 개입이므로 원 action trace만으로 effective DIP증분이라고 부르지 않는다. sidecar에 raw/filtered target·실제증분·gate를 별도로 남기고 기존 action_change 등 보상 계산을 변경하지 않는다.
- B checkpoint의 original source SHA/metadata·contract·identity·전체 `trainer.load`를 유지한다. 새 control tag를 원 모델 contract에 넣고 strict mismatch를 우회하지 않는다. `initialization_declaration.fresh=False`, Bcost head 보존·모델/RNG/updates 불변을 감사한다. 별도 **execution_override** sidecar와 새 observer/helper/source핀 superset에 두 조건을 선언한다. 기존1267핀/봉인/모델/원보고서를 수정하지 않는다. 이는 frozen B정책+실행개입 진단이며 새 학습 checkpoint나 원 무개입 정책성과가 아니다. 향후 학습제어로 채택하려면 별도 새 controlcontract 검수가 필요하다.

## 검증 및 비교 계획

새 실행의 stdlib-only 선행 gate는 B의 preparation seal/review와 `analysis/results_v1/review.json`의PASS/findings[]·reviewed_sha256·verification의직접/검증입력SHA를 확인한다. B actual review SHA는 `49995b26e859c2cd4e4fafa0ffdafd8ef61c8af54e331fe0b0ff9b38e8a78e78`, verification SHA는 `4691201b19ef2117506c108c23f18d99a1370d8f459fbcd0abdcf5d313033532`다. 그뒤 원native import순서/기존strict B loader를 따른다.

CPU 구현 검수는 새 작은 wrapper에 한정한다. candidate+양증분 차단, candidate+음/0증분 exact 통과, candidate 없음/wrong/reset/failure/비유한 행 원 제어, 각 환경의 on→off→on에서 재누적 없음, 양의 action이어도 이미 상한이면 raw증분0인 경우, 입력 불변·alias/memory·native/rate box·나머지104열 exact를 검사한다. named_DIP는 `LH:index3`를 실제 joint_names/controller action mapping에서 찾고 선택4의 마지막 이름과 일치하는지 검사한다(숫자 index 고정 금지). 실제 native readback128×105/16cap/90pairs는 기존 검수 helper를 재사용한다. 생성/닫기 오류 보존과 alias/pins 복원, 기존 output/symlink 거부 및 gate의 native 전 검사를 유지한다.

root가 준비검수 후 GPU를 직렬 실행할 때 **2×128=256개 전체 첫시도**를 사전 할당하고 조기 실패도 분모에 포함한다. 두 조건 모두 같은 원 evaluator/초기화/시계/4substep을 사용한다. 기존 B300은 참조이며 새 passthrough가 원 평가와 정합하는지를 먼저 검증한다. 전체128의 원장/달성·clean·wrong·물리/손목실패·9보상·LH21 motion 통계는 모두 비교한다. env0 action/target/q/body/clock/gate/wrist와원 B300 trace의 exact 차이·최대잔차/발생시각을 남긴다. force 산술 차이 등 exact 불일치가 있으면 원값과 근거를 보존하고 동일하다고 과장하지 않는다.

각 조건의 모든 첫시도60Hz 제어에 대해 pre-control clock/candidate/wrong/gate/skip이유·old/raw/final DIP target·양증분 억제여부·나머지104열 최대변경·memory/scene/rate/bounds 잔차를 작게 기록한다. 접촉이 처음 생긴 시각과 실제 목표를 처음 바꾼 시각을 구분한다. 개입 연속/총 tick수·off후 즉시 재개·negative DIP증분 요청수와 exact 통과수를 보고한다. gate가 없어 저장된0을 실제0오차나 부하0으로 평균하지 않는다.

기존 env0 60Hz 상세/원128 episode motion으로 PIP/DIP actual/target·범위/추종차·상하한 체류·손목pos/rot/armbounds·손가락몸체1/2/3과엄지합력을 음전/음중/음후에 분리한다. 힘을 나머지127로 추정하거나 60Hz max를240Hz max·압력·접촉쌍으로 부르지 않는다. 음중 성공/힘뿐 아니라 자연스러운 DIP펴짐을 **차단하지 않았는지**를 요청/최종 증분 검사로 확인한다. 실제 펴짐의 즉시성까지 보장하는 검사는 아니다.

이 실험은 **closed-loop**다. 목표 변경 뒤 observation/NN행동과 팔teacher feedback 변화까지 포함한다. 과거 중지의 fixed-tape/loaded-normal projection 시험과 같다고 부르지 않는다. 이번에는128개 원 tape가 있는 것처럼 가장하지 않고 full-tape 생성·새 Jacobian 투영을 추가하지 않는다. 원음 판정/범위·힘·cost·성공문턱을 바꾸지 않고 두 조건의 전체 결과를 공개하며 유리한 환경/시점만 선별하지 않는다.

## 해석의 한계

B300 env0 첫candidate에서 DIP target36.565°/actual29.051°로 이미약7.514°차이가 있다. 추가 목표 굽힘을 막아도 기존 오차/관성/접촉·팔 움직임에 의한 실제 추가 굽힘은 남을 수 있다. 후반의PIP8.52°/DIP89.21°왜곡이 줄어들지, 음악기준을 유지할지 결과 전에 확정하지 않는다. DIP단일축의효과를 PIP 원인해결·인간자연성·해제/다음음·자유기타/J33 학습성과로 확대하지 않는다.
