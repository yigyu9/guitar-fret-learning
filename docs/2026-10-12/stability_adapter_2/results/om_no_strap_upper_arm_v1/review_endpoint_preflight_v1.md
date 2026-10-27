# 240Hz endpoint 접촉 관측 사전 검수

판정: **문제없음. Critical 0건, Warning 0건, Suggestion 0건.** 새 진입점/계획과 기존 callback·제어 경로를 읽기 전용 확인했다. 추가 물리·학습이나 다른 파일 수정 없이 이 리뷰만 작성했다. 후보의 실제 접촉·안정성은 후속 native 결과 범위다.

[callback 연결:19](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v2.py:19)은 기존 after_physics 객체를 저장하고 먼저 호출한 뒤 native state/contact를 읽는다. [기존 적분 경로](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v4.py:165)는 fetch_results·steps 증가 뒤 callback을 한 번 호출하므로 정상 완료 시 새 기록은 physics1..1200의 post-physics endpoint다. 새 힘·target·state setter·physics step은 추가하지 않고, 새 관측 전후 native_state exact를 검사한다.

왼쪽 필터는 L_Thorax/Shoulder/Elbow/Wrist 및 LH: 전체와 모든 guitar body의 조합이고, 오른쪽은 R_Shoulder–G:body다. presence·양의 raw lambda 집계를 위한 원 contact를 그대로 보존한다. body pose 저장도 동일 endpoint 기준이다. 기존 constant neutral_action·60Hz 제어 전 contact/support·151영상 경로와 실제 strap OFF는 유지된다.

[patch:35](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v2.py:35)는 base가 보존한 원 factory/draw 함수/save를 사용한다. metadata→base.save_metadata→base.original_save 경로에 재귀를 발견하지 않았으며 leafV3 SHA는 attempt의 공유 closure에 추가되어 종료 검사에도 포함된다. 새 endpoint JSON은 배타 save이며 기존 기준 실행/출력을 변경하지 않는다.

[계획 V3](/home/ajou/yigyu/3/stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V3.md:7)는 기존 기준의60Hz 결과와 후보의 추가240Hz 증거를 구분한다. endpoint는 적분 완료 뒤 표본이며 solver 내부 substep/연속 시간의 비접촉이나 힘0 인증이 아니다. 기준을 재실행하지 않고 공통60Hz 결과를 비교한다는 범위는 타당하다.
