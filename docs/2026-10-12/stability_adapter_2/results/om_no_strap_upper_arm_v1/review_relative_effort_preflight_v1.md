# 현재 기타 상대 effort·미세 간격 사전 검수

판정: **문제없음**. Critical 0 / Warning 2 / Suggestion 0. 실행용 v13/V14·source search v6·후보/config·material inspection 코드/원자료와 사전 SHA를 읽기 전용으로 검토했다. 추가 native 실행·학습·다른 파일 수정은 하지 않았다.

- [상대 제어:93](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v13.py:93): 현재 기타 root pose와 COM 선속도·각속도로 동일 기타-local 희망점의 world 위치/속도를 계산한다. 감쇠는 `−D·(motor_velocity−target_velocity)`로 상대 운동을 줄이는 부호이다. 요청 norm80N 및 native joint effort 제한을 유지한다. CPU에서 실제 제어 함수를 실행해 현재 G 목표/속도, COM 오프셋, 감쇠 부호,80N cap·나머지69 torque0을 확인했다.
- [latch:93](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v13.py:93): 20cm 또는35° 초과 시 마지막 world 희망점을 유지하고 희망점 속도0으로 둔다. 위치/회전 각각의 합성 반례와 원위치 복귀 후 latch 유지가 통과했다. actuator torque나 physics를 중지하는 조건은 아니다.
- [source 수락:26](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v6.py:26): 오른12 초기각만 최대 .005716443rad 변경됐다. 나머지69·기타 초기 p/회전·EFFORT reference는 유지되며 81D 계약이 통과했다. 저장 FK로 근위 상완 source gap .050000929mm를 재계산했다. source audit는 전체 clear이며 최소 capsule gap도 같은 값이다. 전체 source 충돌 검사를 독립 재실행한 범위는 아니다.
- [재료 읽기:25](/home/ajou/yigyu/3/stability_adapter_2/inspect_om_surface_materials_v1.py:25): 별도 imported actor의0physics/0surface-setter 검사이다. 저장 human L/R_Hip·Chest·R_Shoulder와 G:body shape friction은1.0이며 입력6개 SHA가 일치한다. 실제 시험 scene의 filter/contact-offset 적용 전 속성이므로 solver effective friction·측정 마찰계수·지지력으로 확대하지 않는다. 이번 trial은 실제 shape friction을 별도로 기록하며 재료를 변경하지 않는다.

guard·construction·factory(혼합 모드 step 포함)·Head callback은 v12와 AST가 동일하다. 전체 state 불변·POSITION69 exact·Jacobian 속도 guard·physics owner/effort window는 유지된다. 실제 metadata 함수를 연결한 CPU 검사에서 저장1회·재귀 없음·search_v6 SHA·최신 상대 제어 및 오른 POSITION ignored 범위 보존을 확인했다. source 입력550개·사전 입력8개 SHA가 현재 파일과 일치한다.

Warning 1 — [metadata:115](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v13.py:115): `current_initial_pose_plan`은 여전히 기본 배치 V10을 가리키지만 이번 오른팔 미세 수정은 V14/search_v6에 근거한다. 최종 설명에서 기본 배치 출처와 현재 수정본을 구분해야 한다. 후속 보완 시 `base_initial_pose_plan=V10`, `current_initial_pose_plan=V14`로 분리하는 것이 정확하다. 검색/현재 제어 SHA는 이미 별도로 저장되므로 이번 물리 실행 차단 사항은 아니다.

Warning 2 — [초기 간격 수락:26](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v6.py:26): 양수 source 미세 간격은 cooked/native 초기 관통 부재나 접촉 형성을 인증하지 않는다. 초기 간격·16mm 희망점·80N cap·상대 속도 감쇠가 함께 변경돼 결과를 한 요소의 인과 효과로 단정할 수 없다. 실제 결과는 초기 상태와 contact/Head/left·기타 이동/회전으로 별도 판단해야 한다.

[사전 입력 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/relative_effort_preflight_inputs_v1.json)의 핵심 검수 SHA-256은 다음과 같다.

| 파일 | SHA-256 |
|---|---|
| run_om_no_strap_upper_arm_v13.py | 37d0e4c94f1b8fe8f09edf6b3f0c63b1db0b333f6518a6aa2f89daa0bc92b79a |
| search_om_no_strap_upper_arm_v6.py | b1fde104abd06fdc9eb3e5f96a38e4a756120735afb58881c5898756adb984f3 |
| OM_NO_STRAP_UPPER_ARM_PLAN_V14.md | d574cde92ab14c579320ee43db039de8e0396c69a1b3b2cb7aea92a2642d4949 |
| search_v6/candidate.json | 0be6a73b792a6ece835ed0a4fe9b6cce9616a5f657a535c355bcd54cf78d4bcd |
| material_inspection_v1/materials.json | 8e2a61e5a2706a750d8d64a28ca0ee1241bf9ff92e03f3b7680a4b0c0c907760 |

실행 차단 사항은 발견하지 않았다. 이번 검수는 사전 코드·수식·저장자료 범위이며 실제 actuator/접촉력, 자유 기타 유지 성공, 관절/기타 pose 고정 또는 연주 가능성을 인증하지 않는다. 지정한 새 리뷰 파일만 작성했다.
