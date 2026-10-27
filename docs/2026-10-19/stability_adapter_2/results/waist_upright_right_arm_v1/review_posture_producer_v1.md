# 실제 자세 비교 producer 사전 검수 V1

요약 판정: **문제없음**. Critical / Warning / Suggestion 없음. 지정된 새 `analyze_posture_v1.py`의 전체 소스를 검수했다. 검수자는 producer를 실행하거나 원본을 수정하지 않았다.

- [analyze_posture_v1.py:19](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/analyze_posture_v1.py:19): baseline 실제 초기값·현재 initial/final/report·pose helper·자기 소스 SHA를 읽기 전 기록한다. canonical bbox 분석 JSON도24행에서 SHA를 먼저 기록한 후 읽고54행에서 전체를 재대조한다. helper 경로가 실제 프로젝트 파일로 해석됨을 확인했다.
- [analyze_posture_v1.py:27](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/analyze_posture_v1.py:27): Chest localZ를 baseline world 수평 앞축과 world up에 투영한 atan2 기울기이며 척추 scalar 또는 임상 굴곡각으로 설명하지 않는다. final 팔꿈치 거리는 해당 final 기타 pose로 이동한 bbox 중심을 사용하고 초기 요청 방향 투영/거리 감소는 baseline 고정 중심을 사용한다. bbox 중심을 질량중심과 구분한다.
- [analyze_posture_v1.py:38](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/analyze_posture_v1.py:38): parent inverse × child로 상대 회전을 만든 후 전후 SO3 각도 차이를 계산한다. 별도의 body9 최대 scalar 초기각 차이와 혼동하지 않는다. 실제 두 case와 baseline의 `q_ref_rad`는 저장 native 초기 DOF scalar와 exact하므로50행의 초기 scalar 측정에 일치한다.
- [analyze_posture_v1.py:41](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/analyze_posture_v1.py:41): baseline/current 초기 G39 pose의 위치와 회전 오차를 별도로 기록하고 기존 native 허용차로 검사한다. 완료 report와 동일 body 순서를 요구하며 원본 baseline 명령 재분석은 호출하지 않는다.

검증: Python AST 통과. helper·canonical bbox JSON 존재 확인. canonical `body_centre_G_m=[0,-0.4,-0.055937985]`를 확인했다. 검수 시 두 static report가 모두 completed/1200steps이며 두 초기값의 G body 수는39, 실제 초기 DOF scalar와 `q_ref_rad`는 exact였다. 이 확인은 producer 실행이나 최종 native 전체 검수를 대신하지 않는다.

source SHA256: `1c9220fb9ebcaca311a35b0db642540f0e3c3e70b841dba90bd802245bfeb1a0`.

완료 후 생성 JSON 값·입력 map·영상/native raw 및 접촉/명령 분석과의 대조는 최종 결과 검수에서 확인한다. 이 검수 파일만 생성했고 다른 담당자 파일은 수정하지 않았다.
