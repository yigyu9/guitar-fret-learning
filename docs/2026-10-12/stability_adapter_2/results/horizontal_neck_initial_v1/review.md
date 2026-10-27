# 넥 수평·앞판 정면 초기 회전 사전 검수

요약 판정: **문제없음(PASS, 순수 계산 및 정적 native 촬영 코드 사전 검수 범위)**. 다른 담당자 파일과 이전 봉인 자료를 수정하지 않았으며, renderer/native/physics main을 실행하지 않았다. 두 신규 Python 파일은 Python3.8 AST 검사에 통과했다. Critical/Warning에 해당하는 실행 blocker는 없다.

[계획:9](/home/ajou/yigyu/3/stability_adapter_2/HORIZONTAL_NECK_INITIAL_PLAN.md:9)과 [helper:13](/home/ajou/yigyu/3/stability_adapter_2/horizontal_guitar_pose.py:13)은 local +Y 넥을 world `[-cos(a),0,sin(a)]`, local +Z 앞판을 world `[0,1,0]`로 두며, local +X=`neck×front`를 사용한다. 이를 열벡터로 쌓은 행렬은 오른손 정규직교 회전(det+1)이고 0° 넥은 수평이다. [root 위치 계산:16](/home/ajou/yigyu/3/stability_adapter_2/horizontal_guitar_pose.py:16)은 바디 중심에서 회전된 local 중심 `[0,-.4,-.0217]m`를 빼므로 actor-root 고정 회전과 달리 바디 중심을 보존한다.

순수 helper의 −10/0/+10°를 독립 축·중심·정규직교 검산했다. 중심은 `[.1695845416630602,.06501234519615091,.6759729753888915]m`이며 0° root는 `[-.23041545833693983,.08671234519615091,.6759729753888915]m`, quaternion xyzw `[.5,-.5,-.5,-.5]`다. 세 조건의 중심·넥·앞판·정규직교 오차는 모두 4.45e−16 이하이고 det≈1이다. [computed_poses.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/computed_poses.json:1)의 13검사, 세 pose·기준 SHA 및 후보 파일 존재와 독립 계산을 대조했다. `native_captured=false`와 물리 요청0을 그대로 유지한다.

[renderer:28](/home/ajou/yigyu/3/stability_adapter_2/render_horizontal_guitar.py:28)은 기존 static Editor를 strap=False/viewer=False로 재사용한다. [기존 NoPhysicsGym:40](/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:40)과 [step_physics 금지:60](/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:60)는 적분/힘 호출을 차단한다. [install_pose:140](/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:140)는 static EDIT 상태에서 기타만 배치하며 human body 상태와 step0을 검사한다. 기존 recorder는 촬영 전후 native 상태를 비교하고, [신규 추가 카메라 검사:57](/home/ajou/yigyu/3/stability_adapter_2/render_horizontal_guitar.py:57)는 human body/DOF exact·render readonly·물리 차단 호출0·앞판 방향·중심·넥 상승각을 확인한다. 새 출력 디렉터리와 JSON은 overwrite 방지 방식이다. 기존 손·팔 상태를 바꾸지 않아 왼손 높이차가 남는다는 계획 범위, 정적 시각화와 실제 초기화 채택·관통/지지/자유기타 안정성 미검증의 구분이 명확하다.

검수한 canonical SHA-256 및 source_before 사본 byte exact:

- horizontal_guitar_pose.py: `685a4fa50a0e5e3ad55ce39ede6fc392f3b4f11b0fb0c856a157943ac1afd188`
- render_horizontal_guitar.py: `3e54405b5e8c5ba392e6bb9c0970103a01c8bb96ae10191654ad644eb40c1561`
- HORIZONTAL_NECK_INITIAL_PLAN.md: `4696b8afed646b32c297d42511aa54fa0980730428210062c34ef6f721199e0d`

현재 판정은 native 이미지 성공을 선언하지 않는다. GPU 부재 조건의 bounded ONE 촬영 시도와 실패 원문 보존은 root 담당이며, 실패 시 계산 pose만 제공하고 이미지 생성 성공으로 표현하지 않는 계획과 일치한다. 실제 실행 결과·미디어·최종 문서는 후속 검수 대상이다.


## 실제 정적 native 3배치 및 PNG 검수

요약 판정: **문제없음(PASS, 저장 native 배치·사진 범위)**. Renderer/native/physics를 재실행하지 않았다. [native comparison](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/comparison.json:1)의 3배치·aggregate2검사와 각 배치7검사 전체 True, physics_steps0을 확인했다. 11개 renderer 직접 입력의 현재 SHA와 기존 신규 source_before 사본이 그대로다. 각 pose의 초기81각·PD81목표는 원 quiet 기준과 exact이며, 저장 initial_state의 실제 human81각도 기준과 exact·속도0·step0이다. Capture는 각각 t0 한 프레임·render_preserves_states=True이고, 기존 recorder의 두 사진 및 추가 front/side 두 사진을 합한 **12PNG**는 기록 SHA와 현재 파일 집합이 전부 일치한다. Human exact 및 render readonly는 저장된 native guard 결과이며, 저장하지 않은 촬영 이후 raw 상태를 별도로 재측정했다고 주장하지 않는다.

세 actual quaternion으로 축과 중심을 독립 계산했다. 요청 넥 상승각 대비 최대오차 **3.2183212841374598e−6°**, world+Y 앞판 벡터 오차 **8.429368273470525e−8**, 중심 위치 오차 **5.510987575065124e−8m(약 .0551µm)**다. 각 aggregate row의 중심/상승각도 actual pose 재계산값과 일치한다. 0° native quaternion `[-.5,.5,.5,.5]`는 순수 계산 `[.5,-.5,-.5,-.5]`의 부호 반전이며 같은 회전이다.

실제 0° [front PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/scene/candidate_001/front.png), [side PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/scene/candidate_001/side.png), [hands PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/scene/candidate_001/images/frames/hands/00000.png)를 view_image로 열었다. 넥은 수평이고 앞판은 정면을 향하며, 변경하지 않은 초록 왼손이 넥보다 높은 상태가 남아 있다. 이 사진은 실제 Gym camera 산출물이나 물리 적분·접촉/지지·자연 연주·초기화 채택을 인증하지 않는다. Visual geom 로드 오류 및 articulation 상태 제출 경고가 로그에 보존되어 있으며, 해당 경고가 없는 실행이라고 설명하지 않는다.

[runtime request](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/runtime_request.json:1)는 nvidia-smi exit9·NVIDIA device 없음·Mesa lvp Vulkan ICD·물리 요청0을 명시한다. 저장 결과는 GPU 부재에서 사진 생성에 성공한 상태와 일치한다. 닫힌 native 로그의 현재 SHA는 `d9203e77d30f21b0978dfd954aecfa908b8c5fc88d99b2fe583f214a40abbe4c`, native comparison SHA는 `3bc7ebde9656b623be1e5d1df577efe5cad0aefb34a6c36f9c9c750c5e16e4a1`이다. 이 검수 시점에 native_execution.json은 아직 없으므로 종료 exit0·walltime·실행 전후 closure metadata는 root 후속 기록 이후 대조한다. 이는 실제 사진/수치의 오류 판정이 아니라 남은 증빙 범위다. 최종 문서·비교표 및 보존 감사는 후속 검수 대상이다.


## 종료 metadata·v2 비교표·최종 문서 delta 검수

요약 판정: **문제없음**. 앞선 native/math/원본PNG 검수를 재사용하고 새 종료 metadata·비교표·보존 사본·최종 문서만 대조했다. 코드/native/renderer/그림 producer/감사를 재실행하지 않았으며 review.md 외에는 수정하지 않았다. Critical/Warning에 해당하는 미해결 문제는 없다.

앞서 남긴 종료 metadata 증빙 범위는 해소됐다. [native_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native_execution.json:1)은 실제 exit0·완료3배치·physics0을 보존하며 닫힌 로그/comparison/runtime_request SHA가 현재 파일과 exact다. wall_time_seconds=null은 측정하지 않은 값으로 남기며 실행 시간을 추정해 기입하지 않는다. 설정한 Mesa lvp ICD와 실제 graphics backend 식별자를 구별하는 README 설명도 적절하다. CUDA 자원 또는 동적 안정성 성공으로 확대하지 않는다.

[v2 비교표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/artifacts_v2/horizontal_neck_initial_comparison.png)를 view_image로 열어 3각×정면/측면/손근접의 9칸, 요청각/actual각, t0/physics0 제목과 캡션을 확인했다. 데이터 위에 문구가 겹치지 않고 음수 하이픈이 읽힌다. [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/artifacts_v2/artifact_manifest.json:1)의 **18입력 전후/current SHA·9mapping·4checks·producer/output SHA**를 확인했다. 각 1280×720 원본을 432×243으로 비율 유지 축소하여 crop/overlay 없이 배치한다. PNG SHA는 `0e2d2ace0f11306aac5e1c4bb8adc15c4e816bf90d638d32386d3054e4175d52`다. 원v1 source/PNG/manifest가 producer_attempt_v1에 보존되며 producer diff는 '−10°'→'-10°' 한 줄뿐이다. 원본 native PNG와 computed 자료는 변하지 않았다.

[최종 결과 README:13](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/README.md:13), [결정 메모:3](/home/ajou/yigyu/3/stability_adapter_2/HORIZONTAL_NECK_INITIAL_DECISION.md:3), [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/CHANGED_FILES.md:1), [main README:1402](/home/ajou/yigyu/3/stability_adapter_2/README.md:1402), [main PLAN:2226](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:2226), [VISUAL_REPORT:2212](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2212)의 방향·수치·36개 문서 링크 존재/줄 범위를 대조했다. 바디 중심을 보존하기 위한 회전 계산/root 이동과 이후 static UI의 actor-root pivot을 구분하고, native 0° q와 pure q의 부호 동치를 정확히 설명한다. 0°는 사용자 요청 방향의 우선 후보이며 ±10°는 비교 표본이다. 높은 왼손을 낮추는 다음 팔손 설계는 미실행이고 접촉·관통·자유 기타 유지·학습/기본 시작 pose 채택은 미검증이다.

[final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/final_verification.json:1)의 12checks 全True, source5개의 canonical/current/source_final 사본 exact 및 12nativePNG SHA, main3 원문 prefix SHA를 읽기 전용으로 대조했다. 최종 신규 source/원자료와 원v1 보존 기록을 수정하지 않았다.

검수 시점 최종 SHA-256:

- README: `f2c5d36bba0410fe6434dbe7db5665beaac0d55d05f2ed6621a12b1aaf503878`
- CHANGED_FILES: `b203781dece1a8b7c3fcbec4e955e952c758fc1511b970376440bb1a6fb58259`
- native_execution: `04948c68e29928f0d8391c92a3d6d291439c601ad0a7fae737ee42c3018562b0`
- final_verification: `a5436289b0a3a3c5e4a25da0425a928fb73cc6b84c5cab4bb9da85f6224a844a`
- v2 artifact manifest: `2e5a5df4c3073b662eb1140b5523e9d9c7e7da0776c370187ea2ed50317381e4`
- 결정 메모: `66015e3c5a683c0b365d288f37b6fe94e26dd299cb6ce517c00668abb9f45511`

최종 판정: PASS
