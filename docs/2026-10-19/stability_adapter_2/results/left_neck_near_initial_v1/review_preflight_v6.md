# 사전 검수 — 양팔 EFFORT와 왼팔 중력 보상

요약 판정: **문제없음. 미결 Critical 0 / Warning 2 / Suggestion 0.** 실행 전 발견한 constructor reference 불일치는 새 config/reference로 해결되었다. 해당 설정으로 초기 필수 검증을 거친 5초 진단 진행을 막는 사항은 없다. 실제 native 결과는 아직 인증하지 않는다.

해결한 Critical — [왼 모드 전환:44](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v1.py:44)이 왼12를 EFFORT/0/0으로 바꾸지만 기존 reference는 POSITION이므로 [LearningScene:34](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:34)의 exact 비교에서 중단되는 문제를 보고했다. 새 [config](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/config_v1/config.json:1)는 native_reference와 그 SHA만 바꿨다. 새 reference에서 정확히 왼12의 driveMode/stiffness/damping만 3/0/0으로 바뀌었으며 나머지69행 및 기존 다른 필드는 exact다. candidate와 초기 상태를 변경하지 않았다. EnvironmentContract의 81개 순서·모델 한계·60/240Hz 검증도 직접 통과했다.

- [construction:40](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v1.py:40)는 실제 mode 변경 전 stiffness/damping을 복사해 외부 왼 scalar K/D로 보존한다. 오른 construction은 기존 경로를 호출하고, 초기 readback은 requested 전체와 exact 비교한다. scene의 property/GraphicsGym 계층은 지원 guard 클래스만 양팔24로 교체하며 기존 기타 물성 처리·runtime setter 제한을 유지한다.
- [합산 제어:100](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v1.py:100)는 기존 오른 제어를 한 번 계산한 뒤 같은 81벡터의 왼12에만 `gravity + Kp*(scene.target-q) - Kd*qdot`를 넣고 native effort 한계로 clip한다. 중력 보상 부호는 `-Σ J_COMᵀ m g`다. 새 기타 힘·손 task force·상태 덮어쓰기는 없고 기존 step_physics가 actor effort를 물리 tick당 한 번 제출한다.
- [guard:20](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v1.py:20)는 human actor/81 finite/양팔24 이외0/effort 한계/owner window를 검사한다. [step:65](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v1.py:65)는 나머지57 POSITION readback exact와 전체 native 상태 불변을 유지하고 단일 target 제출 뒤 4 physics step을 실행한다. 손가락21은 POSITION이다.
- [기록:113](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v1.py:113)에 actual 합산81·왼 요청/제출·target/K/D/중력을 저장하고 기존 오른 contribution은 별도 보존한다. encode는 기존 EndpointRecording 경로를 사용하여 이전 POSITION69 표기를 재사용하지 않는다. runner3의 초기 PD 검사는 선언된 왼 모드 변경만 허용하며 K/D 원값 및 mass exact 검증을 유지한다.

Warning 1 — 원 K/D 숫자 재사용은 PhysX implicit POSITION drive와 동일한 동역학을 뜻하지 않는다. 240Hz 외부 PD·중력 보상·effort clip 전환 효과가 함께 바뀐다. 따라서 결과를 중력 보상 단독 인과 효과로 해석하지 않는다. [계획V7](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_PLAN_V7.md:1)이 이 범위를 명시한다.

Warning 2 — 왼 중력 계산은 기존 오른 native 점 속도 검증이 선택한 동일 actor Jacobian COM/origin frame을 재사용한다. 왼 frame·전체 Jacobian·중력 모델을 독립적으로 인증한 것은 아니다. 새 reference의 historical native_initial_state도 현재 장면 측정값으로 부르지 않는다. 실제 초기값·좌측 각/속도·면 간격·접촉·유한 토크와 기타 변화를 후속 native 기록에서 확인해야 한다.

코드 diff·계획V6/V7·새 config/reference 필드/SHA·Python AST 및 CPU 계약 생성만 검토했다. 추가 native/정책추론/학습은 실행하지 않았으며 이 새 리뷰 외 원본 파일은 수정하지 않았다.

검수 SHA256:

- helper: `b63c3ae6d82b8b1cf93224024e65a6fcaaf51cddaee527ceaee8ab109b7c0dbf`
- scene: `7377936a1113c9770078ba26fd97c61b1664bf53ab86e8656017da6e8157f76e`
- runner3: `f665b013bf72cab5c9e257215c9307f23d351600f21ef03aea655224cdde54f0`
- 계획V6: `63cc918ba65cb22fcfeb02c3680ede7186a3190a4fdb20a97656170f42d8ce31`
- 계획V7: `fa72bf8a8ac633be91af44719051120fa3d02d25a3841b95494caa21be148c64`
- config: `d84373d7a56800987de903bd57a43b0d2428d80c0de01f3e8b6702ddf0ca72b3`
- reference: `f37b07393780aec86e10cd6138ee7d36963f657e4c33f06864dfddecc843f544`
