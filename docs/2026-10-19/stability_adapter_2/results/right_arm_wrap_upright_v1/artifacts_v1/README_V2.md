# 상체를 더 세우고 오른팔을 감싼 native 결과 — README V2 보완

기준은 [waist straighten 추가 8° 정지 run](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/native_add8_static/report.json)이며, 선택 결과는 `native_wrap55_static`과 동일 초기 자세의 `native_wrap55_elbow_wave`다. 전신 initial native 캡처의 view/projection 행렬은 기준과 선택 사이에서 일치한다.

## 기준·선택 초기 장면

![기준 waist_add8과 선택 wrap55의 동일 전신 카메라 초기 native 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/initial_whole_comparison_v1.png)

![기준과 선택의 native side 캡처 비교. G 상대 카메라 목표가 달라 같은 world camera 비교는 아님](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/initial_side_comparison_v1.png)

전신 이미지에는 기준과 선택 모두 t=0 native 프레임을 사용했다. side 이미지는 각 run에 저장된 `initial_support_side.png` 원본이며 두 장면 모두 물리 시점 t=0이다. 선택에서 기타를 humanoid 쪽으로 이동해 G 상대 side-camera target이 달라졌으므로 side view를 동일 world camera 시점으로 해석하지 않는다. 차이는 촬영 시점이나 물리 경과시간이 아니라 카메라 target이다.

기준 대비 Torso/Spine/Chest local-Z의 world 전방 기울기 proxy는 29.529/28.403/53.412°에서 16.529/11.403/33.412°로 감소했다. 각도는 local-Z 투영 proxy이며 임상적 척추각이나 관절 scalar 합이 아니다. 기타 목 방향은 유지했고 humanoid 쪽 기타 초기 translation은 world `[0.0009663, -0.0249813, 0.0010301] m`다.

![선택 static run의 t=0,2,5초 전신 원프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/native_wrap55_static_whole_0_2_5_v1.png)

![선택 static run의 같은 전신 프레임에서 자른 상체 영역 t=0,2,5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/native_wrap55_static_upper_crop_0_2_5_v1.png)

![팔꿈치 목표 wave run의 t=0,2,5초 전신 원프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/native_wrap55_elbow_wave_whole_0_2_5_v1.png)

![팔꿈치 목표 wave의 같은 전신 카메라 프레임에서 자른 상체 영역 t=0,2,5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/native_wrap55_elbow_wave_upper_crop_0_2_5_v1.png)

![팔꿈치 목표 wave의 손·기타 카메라 원프레임 t=0,2,5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/native_wrap55_elbow_wave_hands_0_2_5_v1.png)

타임라인 프레임은 원본 native frame 0, 60, 150이며 실제 시각은 0, 2, 5초다. 상체 crop은 전신 PNG에서 매 시각 동일한 `(x=390..930, y=125..555)` 픽셀 영역을 취했다. 별도의 가상 view나 재렌더를 만들지 않았다.

## 5초 실행과 접촉 범위

선택 static과 elbow wave는 각각 1200 physics step/300 control tick, 5초를 완료했다. 기타 바디 bounding-box 중심의 최대 변화는 34.001197mm, 최대 SO(3)는 16.502623°다. 2→5초 변화는 static 7.342286mm/3.344382°, wave 7.145638mm/3.259022°다. elbow 실제 scalar 범위는 10.101781°이며, static과 같은 시각의 wave 추가 변화 최대는 0.458126mm/0.200994°다. 첫 2.5초 trace는 두 조건에서 exact match다.

native wrap55에서 오른 Hip waist 접촉은 1198/1200, 후기120/120이고 왼팔·손가락 기타 접촉은 1189/1200, 후기120/120이다. Chest/trunk, Thorax, 오른 전완·원위팔·머리 접촉은 각각 0/1200이다. 오른 R_Shoulder 전체 body-contact 표본은 1196/1200이며 positive raw lambda 표본도 1196/1200, 후기120/120이다. 별도 `upper_full_raw_presence_steps=181`은 상완 축을 따라 정규화한 0..1 구간 안의 projection subset 표본으로, R_Shoulder 전체 body-contact 표본을 뜻하지 않는다. endpoint가 축을 넘어선 경우의 sphere cap 접촉이 clamped 전체 접촉 통계에 포함된다. 따라서 이를 상완 근위 30%/45% 접촉이나 Thorax 접촉으로 부르지 않으며, 시각 설명은 팔꿈치 가까운 상완 끝부분 접촉으로 제한한다. 두 블록/겨드랑이의 지속 지지나 왼손 없는 수동 안정으로 해석하지 않는다. raw lambda는 힘 N이 아니다.

## 일곱 native 실행 영상

[16개 영상 색인과 SHA/실제 프레임 정보](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/INDEX.md) · [machine-readable manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/manifest_v1.json)

일곱 trial 중 다섯은 기타 안전 변위로 부분 중단됐고, 색인·manifest에 실제 physics step, 프레임 수와 재생 시간을 각각 표시했다. 부분 영상을 5초로 늘리거나 정상 완료로 처리하지 않았다. 두 완료 run과 과거 부분 시도는 native 원본 MP4에서 byte-exact 복사했다. 비교 기준의 두 영상도 복사본과 원본 SHA가 일치한다. 다만 기준 영상 및 NanumGothic 폰트 파일은 이 artifacts builder가 시작 전에 기록한 입력 SHA 목록에서 빠져 있었다. 기준 영상의 동일성은 직전 `waist_straighten_v1`의 sealed inventory와 native report의 SHA 기록으로 대조했으며, 이번 provenance의 before-pin을 소급 완성한 것으로 취급하지 않는다. 글꼴은 `/usr/share/fonts/truetype/nanum/NanumGothic.ttf`를 사용했지만 해당 파일 SHA도 이 builder의 입력 목록에 없다.

## 원자료와 provenance

- [최종 posture/waist 요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/posture_final_v1.json) · [timelines/60Hz 및 접촉 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/timelines_final_v1.json) · [waist 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/waist_final_v1.json)
- [직접 읽은 입력·producer SHA 전후 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/provenance_v1.json)
- [산출물 producer](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/build_artifacts_v1.py)
- [기준 native 영상 SHA를 기록한 이전 phase sealed inventory](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/artifact_inventory_v1.json) · [기준 native run report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/native_add8_static/report.json)
