# 스트랩 OFF·왼팔 철수·오른상완 접근 사전 검수

판정: **문제없음 — 지정 두 정상 PD 진단을 막는 Critical을 발견하지 않았다.** Critical 0건, Warning 1건, Suggestion 0건. 새 계획·검색/runner·저장 source 결과를 읽기 전용 대조했다. 추가 native·학습·원본 수정 없이 이 리뷰만 작성했다. 무왼손 유지·상완 지지 성공은 사전 승인 대상이 아니다.

[source 검색 v2:21](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v2.py:21)는 왼 palm을 초기값에서 world `[0,0.08,0.15]m` 옮기고 기존 방향을 유지하도록 왼팔12만 ±0.8rad∩native로 IK한다. v1의 왼Elbow–넥 교차 후보는 거절·보존됐으며 v2의 두 후보는 전체 source 간섭·capsule 최소0.2mm·왼 palm 2mm/1° 및 필요한 상완 접근 gate를 통과했다. 쌍의 공통 왼팔은 exact이고 후보 간 차이는 오른팔12뿐이다. 기타 p/q·body/head/finger/root/lower 초기값은 그대로다. source 입력 SHA739개는 현재 일치한다.

상완 후보의 근위 subset0..0.65 gap은1.000532mm, 기타 G 접점은 약 `[−0.184360,−0.458932,−0.004158]m`, 실제 오른 palm 이동은0.124825mm다. 전체 capsule–바디 최소 간격은0.498090mm다. 왼 palm 오차는 약1.52×10⁻⁸m/2.61×10⁻⁶°이며 왼/오른팔 최대 scalar 초기 변화는 각각0.507814/0.391480rad다. 근위 subset은 진단용 원 capsule 부분집합이며 물리 형상을 변경하지 않는다. source 양의 간격은 PhysX cooked clearance 또는 실제 지지력의 인증이 아니다.

[runner patch:58](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v1.py:58)는 원 factory 객체를 보존한 뒤 enabled=False로 호출하므로 재귀 없이 기존 scene/guard를 유지한다. 실제 env.strap_enabled=False도 검사한다. 내부 StringTrialRecording의 원 녹화기 alias만 GymTrialRecording으로 선택해 native raw 프레임을 사용하므로 strap route overlay를 그리지 않는다. 기존 6현 표시는 유지하며 OFF 배너는 픽셀 처리만 추가한다. disabled scene의 physics 분기는 strap 힘 API 제출을 생략한다. 실제 forcecall0은 native 결과에서 확인해야 한다.

[monitor:38](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v1.py:38)는 기존 constant neutral_action bound method를 저장·호출하고 60Hz 제어 전 native body state만 기록한다. PI·별도 목표 제출·physics step·상태 setter는 추가하지 않는다. side camera 및 capture/strap 읽기 전후 상태 exact 검사와 단일 contract.targets/기존 rate/4physics 경로가 유지된다. attempt의 공유 closure에 leaf V1/V2/searchV2 SHA를 추가해 종료 후 검사에도 포함한다. counterfactual cable 법칙과 실제 enabled 명령0을 구분한 로그 설명은 적절하다.

Warning 1건:

- [계획 V2의 무왼손 판정](/home/ajou/yigyu/3/stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V2.md:5): 실제 모든 L_팔/LH손–전체 기타 접촉을 집계해야 한다. 기존 query는 제어 전60Hz 표본이므로 positive raw lambda0이라도 모든240Hz 적분 시점의 비접촉·지지력0을 인증하지 않는다. 최종 보고는 검사한 표본에서 왼팔/손 접촉이 검출되지 않았다는 범위와 초기·최대·종료 기타 위치/SO3 및 상완 접촉을 함께 제시한다. raw lambda 빈도로 힘 분담을 확정하지 않는다.

Critical: 없음. Suggestion: 없음. 실제 상태/물성·하체 고정·목표 추종·속도·금지 API·forcecall·renderer·왼팔 접촉·상완 유지와 기타 이탈은 native 후속 검증 범위다. 정상 PD 초기 목표는 실제 팔 자세 강제 고정이 아니며 연주/왼손 철수 성공을 미리 주장하지 않는다.

검수 SHA256: runner `68c3a60fd7c07f64a8f19d9cc8706449799776a17e542014baae655685dfed7d`; 검색 v2 `db03b413238ff1c08dbb7785bdd8220f0016f2daef377002f48c81f2952972ea`; 계획 V2 `1eb8eb183af45b485bd713c410230725061512dcd33ee8e1fedaee132745ec7d`.
