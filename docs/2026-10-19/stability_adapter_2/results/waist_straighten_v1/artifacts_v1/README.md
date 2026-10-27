# 허리를 더 편 후보: native 전후 이미지와 영상

현재 4° 완화 기준(run `waist_upright_right_arm_v1/native_relief4_static`)과 추가 8° 후보(run `waist_straighten_v1/native_add8_static`)의 실제 Isaac Gym 캡처를 나란히 정리했다. 두 전신 카메라의 시작 프레임 view/projection 행렬은 정확히 일치한다.

## 초기 자세 비교

![현재 4도 기준과 추가 8도 후보의 동일 카메라 native 전신 초기 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/artifacts_v1/initial_whole_comparison_v1.png)

![동일 전신 native 프레임의 같은 픽셀 영역 확대 비교. 양쪽 모두 t=0](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/artifacts_v1/initial_closeup_comparison_v1.png)

확대 그림은 각 전신 캡처에서 같은 `(x=365..875, y=190..590)` 영역을 잘라 만들었다. 손·기타 카메라의 view 행렬은 두 run에서 일치하지 않으므로 그 카메라를 같은 view라고 표시하지 않았다.

초기 Chest local-Z의 world 전방 기울기 proxy는 현재 기준 61.412311°에서 추가 8° 후보 53.412323°로 줄었다. 선택 후보의 5초 종료값은 56.421877°다. 이는 local-Z 투영값이며 임상적 허리 굴곡각이나 관절 scalar 합이 아니다. 시작 뒤 Chest proxy가 약 3.010° 다시 커졌지만 현재 기준의 최종 63.364037°보다 낮다. 초기 기타 39 rigid body 위치/회전은 현재 기준에서 최대 9.9960e−8m/1.3009e−7rad 차이로 유지됐다.

## 선택 후보의 native 0·2·5초 프레임

![추가 8도 정지 run의 전신 원프레임 0초, 2초, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/artifacts_v1/add8_whole_body_0_2_5_v1.png)

![추가 8도 정지 run의 손·기타 원프레임 0초, 2초, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/artifacts_v1/add8_hands_0_2_5_v1.png)

각 패널은 실제 native frame 0, 60, 150을 그대로 사용한다. 30fps 기준 시각은 0, 2, 5초다. 프레임은 축소 배치했고 시점 표시는 이미지 바깥에 두었다.

## 정지 조건 결과

두 새 run은 각각 물리 5초·1200 physics step·300 control tick을 완료했다. 현재 4° 기준은 기타 bounding-box 중심 최대 이동 14.545447mm/SO(3) 8.012684°다. 추가 8° 후보는 12.882340mm/7.542856°이며, 2→5초 추가 변화는 기준 3.735037mm/1.650240°와 후보 0.381862mm/0.143808°다. 추가 4° 후보의 최대 회전은 7.353169°로 추가 8°보다 조금 작다. 더 펴진 자세와 작은 후기 변화를 근거로 추가 8°를 선택했으며 모든 지표의 종합적인 우위로 판단하지 않는다.

선택 조건에서 후기 120 step의 Thorax 접촉은 0/120, 근위 상완과 waist 접촉은 각각 120/120이다. 오른 전완·손의 기타 접촉은 없고 왼손 손가락 기여는 남는다. 따라서 두 블록의 지속 끼움, 왼손 없는 수동 안정, 반복 강건성이나 연주 성공을 주장하지 않는다. raw lambda는 힘 N이 아니다.

## 실제 영상과 provenance

네 native 영상 원본은 재인코딩하지 않고 복사했다. 영상별 원본/사본 SHA, ffprobe 크기·프레임·재생시간, 카메라 비교와 생성 이미지 SHA는 [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_straighten_v1/manifest_v1.json)에 있다. 5.000초 물리 경과와 5.033333초 영상 재생 길이를 구분한다.

- [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_straighten_v1/INDEX.md)
- [직접 입력 및 producer SHA 전후 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/artifacts_v1/provenance_v1.json)
- [이미지·영상 packaging producer](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/artifacts_v1/build_artifacts_v1.py)
- [확정 산출물 brief](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/artifact_brief_v1.md)
- [최종 자세 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/posture_final_v1.json)
