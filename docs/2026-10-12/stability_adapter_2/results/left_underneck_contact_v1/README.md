# 왼손 넥 아래면·뒷면·전면 목표 영역

사용자가 요청한 배치 방향은 손바닥을 넥 아래 측면에, 엄지를 뒷면에, 나머지 손가락을 전면에 두는 것이다. 아래 그림은 기존 수평 기타 자세와 설명용 `grip_proposal` 영역을 바탕으로 목표 면과 법선을 월드 좌표로 옮긴 개념도다. 새 손 자세는 아직 만들거나 물리 시험하지 않았다.

## 현재 기준 장면

아래는 이전에 저장한 수평 넥 장면의 native Isaac Gym 이미지다. 현재 손 배치를 보여 주는 기준 참고 이미지이며, 새 접촉 영역에 맞춘 손 배치나 접촉 결과가 아니다.

![기존 수평 기타 장면의 손 참고 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/scene/candidate_001/images/frames/hands/00000.png)

## 설명용 영역과 검증 범위

![기타의 손바닥 옆면·엄지 뒷면·손가락 전면 목표 영역과 원하는 손 법선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_underneck_contact_v1/artifacts_final/contact_regions.png)

색면은 검증 자료의 `regions_W.*.polygon_W_m`를 그렸고, 색 화살표는 각 `desired_hand_normal_W` 방향이다. 축은 월드 X/Y/Z, 단위는 m다. 이는 원본 source 영역의 변환을 설명하는 그림이지 Isaac Gym 렌더나 cooked PhysX 표면이 아니다. 손 형상·새 손 자세·실제 접촉은 표시하지 않으며 접촉이나 지지력을 인증하지 않는다.

[verification_v2 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_underneck_contact_v1/verification_v2/verification.json)는 6개 판정이 모두 참이고, 단위 테스트 5개가 통과했다고 기록한다. 이 검사는 CPU 기하 변환이며 native 물리 단계는 0, 새 손 자세 설정은 false, 접촉 제어 구현은 false다. v1은 검사와 단위 테스트 5개가 통과했지만 `numpy.bool_` JSON 직렬화에서 결과 저장에 실패했고, v2에서 JSON boolean으로 변환해 기록했다.

구현은 [접촉 영역 변환 함수](/home/ajou/yigyu/3/stability_adapter_2/underneck_contact_targets.py:10), [5개 단위 테스트](/home/ajou/yigyu/3/stability_adapter_2/tests/test_underneck_contact_targets.py:8), [저장 자세 CPU 검증기](/home/ajou/yigyu/3/stability_adapter_2/verify_underneck_contact_targets_v2.py:20), [세 면 목표 계획](/home/ajou/yigyu/3/stability_adapter_2/LEFT_UNDERNECK_CONTACT_PLAN.md:1)에 기록되어 있다. 그림 생성 코드와 입력·출력 SHA는 [plot_contact_regions.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_underneck_contact_v1/plot_contact_regions.py:1) 및 [그림 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_underneck_contact_v1/artifacts_final/contact_regions.manifest.json)에 있다. 앞선 두 레이아웃 산출물은 별도 보존했으며, 보존된 생성 코드 SHA가 각 당시 manifest의 producer SHA와 일치하는지 확인했다.
