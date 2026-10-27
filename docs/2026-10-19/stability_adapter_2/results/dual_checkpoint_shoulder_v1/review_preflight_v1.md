# 사전 검수 — 현재 어깨 자세의 Fret·Strike 동시 연결

요약 판정: **문제없음.** Critical 0 / Warning 1 / Suggestion 0. 현재1cm 어깨 자세에서 factor0 pair 단일 native 진단을 차단할 사항은 없다. 실제 연결·음악 성공·PREP 궤적 exact와 물성 readback 결과는 후속 실행 검수 대상이다.

- [scene:51](/home/ajou/yigyu/3/stability_adapter_2/dual_shoulder_scene_v1.py:51)의 Parent는 EffortScene→strap factory→DualMusicScene이며, [runner:70](/home/ajou/yigyu/3/stability_adapter_2/run_dual_checkpoint_shoulder_v1.py:70)의 patched EnvironmentContract(CFG)가 실제 constructor에 적용된다. OM PropertyGym의 construction mass/COM/inertia readback·cache 경로와 GraphicsGym 내부 explicit ArmEffortGuard→후속 StrapForceGuard 계층을 유지한다. current reference right12 PD는 EFFORT3/stiffness0/damping0으로 LearningScene 초기 검사와 맞는다. runtime property setter window와 force 소유권을 새로 우회하지 않는다.
- [effort:103](/home/ajou/yigyu/3/stability_adapter_2/dual_shoulder_effort_v1.py:103)의 posture 목표는 `env.target`이다. EffortScene.step은 한81 목표에 contract model/rate codec을 적용해 target을 갱신하고4 physics를 실행하므로 source right9 목표가 실제240Hz 인간 torque 계산에 들어간다. 다른69 POSITION/readback/state·right12 selected actor/owner/cap·child J열 guard와 인간 상완 초기world점cap10N/gravity/posture 합산은 기존과 같다. forearm pointforce0, 기타 직접힘/부착/state overwrite 없음.
- [runner:109](/home/ajou/yigyu/3/stability_adapter_2/run_dual_checkpoint_shoulder_v1.py:109)은 두 source30 action 채널의 비중복과 source/native 유효범위 교집합을 확인한다. 한 native snapshot을 두 view에 복사하고, frozen actor deterministic 요청을 한81 desired로 합쳐 한 scene.step만 호출한다. Fret/Strike post-physics evaluator의 기존 AST/SHA seam은 source 전체 step/simulation을 제외하므로 중복 물리를 만들지 않는다. source goal/hand/profile/grip/layout 계약 및 weights frozen 검사는 재사용한다.
- [runner:125](/home/ajou/yigyu/3/stability_adapter_2/run_dual_checkpoint_shoulder_v1.py:125)는 recording의 기존240Hz endpoint/contact observer를 먼저 호출한 뒤 음악 관측을 수행한다. Endpoint→Head/contact→music chain을 보존하며 초기 view 생성/갱신의 native state 불변 검사도 유지한다. 60Hz 정책/240Hz 물리/2초 PREP·tick120에서 공통PLAY0, 원first-source-done 또는 full horizon 종료 구분이 유지된다.
- 순수 contract 검사에서 PREP neutral81 normalize→targets/rate의 최종 q_ref float32 exact를 확인했다. 실제 PREP에서는 actor 목표 적용 없이 기존초기값을 유지하고, PLAY에서만 source 요청이 들어간다. 잘못된 factor는 [runner:32](/home/ajou/yigyu/3/stability_adapter_2/run_dual_checkpoint_shoulder_v1.py:32)에서 출력 디렉터리/native 생성 전에 거절한다. exception 때 [runner:241](/home/ajou/yigyu/3/stability_adapter_2/run_dual_checkpoint_shoulder_v1.py:241)의 partial music 파일 보존이 추가돼 사전 지적을 해결했다. Python3개 AST 통과.

Warning 1 — [runner source scope](/home/ajou/yigyu/3/stability_adapter_2/run_dual_checkpoint_shoulder_v1.py:154)의 원action-scale/EMA/inverse helper clip과 source COM ABI, 원source 안전종료 및 conservative240Hz bracket 판정은 기존 고정기타 checkpoint 실행의 정확한 성능 재현이나 학습용 detector 인증이 아니다. 요청30→범위교집합→rate된 실제81→posture/effort를 구분해야 한다. 오른9는 POSITION target readback이 실제 actuator 명령이라는 뜻이 아니라 EFFORT posture의 목표다. 왼팔 parked 초기값에서2초뒤 정책으로 전환하므로 실제 전환 실패/first done을 숨기지 않아야 한다. 동시 연결을 곡 완주·연주 성공으로 확대하지 않는다.

검수 범위는 새3파일과 기존 source/native interface의 변경 연결·수식·권한 및 순수 PREP codec/reference 검사다. 추가 native/정책추론/학습/소스 수정0. root가 시작하는 실제trial 결과·전체초기 및2초trace·force/target/log/영상·입력SHA 보존은 별도 후속 검수 범위다. 소유한 새 리뷰만 작성했다.

검수 SHA256:

- 계획: `8fa5eb0e951ddf267b42ad442ac7ffd65c2de5a76a921d1a89d28a749de4986a`
- effort helper: `3cf72c384f913ccc83d432e4ca7326e9ad25ede741924e5449721b98f04d09ba`
- scene helper: `f19dcb65f83bad0c9dba2dbcd219cfc78447d6d9d1da3e325e247f7f79044def`
- 최종 runner: `d9bf29f3709e2805cd088596daf84d3af3b5a9e2b634f73371442054996ed2cc`
- 현재 shoulder10 config: `460551a2cf4fe082b72637ebca391b528624d02cfa7d5e9afaddccc0e66f6943`
- 현재 shoulder10 candidate: `32b8312ebdcc0295f71b1a6d12e91267c7a6661a847620df586a42b745221509`
