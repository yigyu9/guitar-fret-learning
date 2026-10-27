# 자연 오른팔 V6 시각 진단 사전 검수

요약 판정: **문제없음 — 수락된 한 후보의 native 시각 진단 진행에 코드 차단 사항 없음.** Critical 0 / Warning 0 / Suggestion 0. source 준비 코드·저장 후보·실행용 diff를 확인했다. native 실행·학습·최종 자세 채택을 인증한 기록은 아니다.

[계획 V6](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_RIGHT_ARM_REFERENCE_PLAN_V6.md:4)는 80mm가 단일 사진에서 복원한 치수나 확정 자연스러움 기준이 아니었음을 밝히고, 이번 시각 진단에서만 하강 60mm를 적용한다. [준비 코드](/home/ajou/yigyu/3/stability_adapter_2/prepare_natural_right_arm_v6.py:14)는 V5 front160mm 원래 결과를 선택해 다른 source 수락 조건·설계 box를 유지한다. 원본 행에서 변경된 키는 `accepted_for_native`와 `adoption_scope`뿐이다.

후보의 팔꿈치 하강 64.051mm, 외측 252.155mm, 손목 안쪽 74.319mm, 손 목표 오차 14.010mm를 확인했다. 전완 gap 1.315mm, 전체 검사 capsule 최소 gap 0.466mm, 전완 normal world Y 0.989이며 전체 source clear다. right12 저장 각도는 V5와 exact, 다른69도 기준과 exact이다. right12 설계 box 안쪽 최소 여유는 약 9.66e−8rad이며 모델 한계를 통과한다. source 값은 cooked/native 간격 인증이 아니다.

기타 초기 world 이동은 [8.052, 109.437, −19.842]mm이고 초기 회전은 유지한다. config 변경은 후보 경로와 후보 SHA 두 항목뿐이며 SHA가 실제 후보와 일치한다. [search V6](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/search_v6/search.json)의 입력 575개 현재 SHA 불일치 0개를 확인했다. V5 결과를 수정하지 않고 새 경로에 준비한다.

[runner V6](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v6.py:113)은 V5 대비 PLAN/search 경로만 변경한다. 초기 world human 전완 목표·목표 속도 0·task K3000/D80/요청 cap40N·posture K60/D8, right12 EFFORT/other69 POSITION, 단일 제출/owner window/금지 상태쓰기/Jacobian 속도 가드를 유지한다. 기타 고정·직접 기타 외력·strap을 추가하지 않는다. `safety_stopped`는 토크가 계속되는 이탈 감지 래치다. 실제 자연스러움·지지·왼 비접촉은 이후 native 이미지와 저장 접촉으로 별도 판단해야 한다.

검수 SHA256:

- 계획 V6: `097c04005f2a3aed4ff556b55ea7ffee4f4a82ce779162ee61fa18796f5bcb77`
- 준비 코드 V6: `55b8d4691a55fd8096667ec790e3d3b82c6a63fe6e870304e1b30d2a6a943edf`
- runner V6: `21188412ce8317ce746ed74db8ff45a1589c71a65dc8586b1a22b2dec957c44b`
- search V6: `deb543dbb48e75304ff2a556081bf452b5fcfd4e3dea9ea3cb47b3be75387ff4`
- 후보: `077ddd78562807651804cc989746ef55ae747d06100f18fcc80e846574a5cc4d`

이번 검수는 새 사전 리뷰만 작성했다. 기존 리뷰·코드·실험 출력은 수정하지 않았다.
