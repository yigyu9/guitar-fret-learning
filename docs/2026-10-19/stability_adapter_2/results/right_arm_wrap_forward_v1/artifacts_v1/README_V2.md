# 기타 앞쪽으로 이동한 오른손 native 비교

비교 기준은 [right_arm_wrap_upright_v1/native_wrap55_static](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/native_wrap55_static/report.json)이고, 선택 run은 `native_elbow10_static`이다. 추가 오른팔 목표 wave 없이 78개 frozen initial q 중 몸통·Thorax·Shoulder·손목 scalar·손가락·왼팔·머리는 기준과 같게 유지했다. 오른쪽 팔꿈치의 세 DOF만 초기 q 목표가 달라졌으므로, 그 아래 전완·손의 world 위치와 팔꿈치 방향은 기준과 같지 않다. support body full state, 기타 39개 rigid body 초기 상태, two-block configuration은 baseline과 exact match다. 기타 root/head 방향은 유지하고 기타를 옮기거나 직접 힘을 주지 않았다.

## t=0 전신 비교 및 기존 손 카메라 범위

기존 아래 손·기타 확대 그림은 왼손/넥 쪽을 보는 native 카메라라 오른쪽 분홍색 손을 보여 주지 않으며, 오른손 이동을 판독하는 자료로 쓰지 않는다. 오른손을 확인하도록 같은 전신 카메라의 같은 native 원프레임 영역을 자른 추가 비교를 아래에 둔다. 두 source PNG는 캡처 메타데이터 SHA와 일치한다. 비교는 실제 픽셀 crop 확대이며 손 위치를 합성하거나 옮기지 않았다. 초기 오른손바닥의 고정된 기타 전면 방향 이동 9.9418199mm(표시 9.94mm)를 시각자료 캡션에 표시했다.

![동일 native 전신 프레임의 오른팔·손 crop 비교. 왼쪽 이전, 오른쪽 새 초기](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/right_arm_initial_comparison_v1.png)

[오른팔 추가 비교 입력·출력 해시 provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/provenance_right_arm_v1.json) · [추가 비교 native-pixel producer](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/build_right_arm_comparison_v1.py)

## t=0 전신과 손·기타 확대 비교

![기준과 elbow10 선택의 native 전신 t=0 캡처. view/projection 카메라 행렬 모두 일치](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/initial_whole_comparison_v3.png)

![기준과 elbow10 선택의 native 손·기타 t=0 캡처. view/projection 카메라 행렬 모두 일치](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/initial_hands_comparison_v3.png)

시작 팔꿈치 관절 원점의 차이는 float32 연산에서 59.605nm였고, native 검증 허용치 1µm 안이다. 이를 0 오차 또는 byte exact로 표현하지 않는다. 시작 손바닥의 고정된 world 기타 전면 방향(+Y 근사) 이동은 9.9418199mm, 손목은 8.531274mm다. 팔꿈치 방향은 2.0847° 달라졌다. 이 방향은 처음 정한 guitar-front 수평축 기준이며, 이동 중인 기타에 대한 상대 변위나 접촉력을 뜻하지 않는다. 5초 동일 시각의 손바닥 전방 차이는 8.562639mm다.

## 선택 run native 0·2·5초

![전방 elbow10 선택의 전신 native 원프레임 0,2,5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/selected_whole_0_2_5_v3.png)

![같은 native 전신 프레임에서 동일 ROI를 자른 상체 확대 0,2,5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/selected_upper_crop_0_2_5_v3.png)

ROI는 원본 전신 프레임 `(x=390..930, y=125..555)`다. 0,2,5초 패널은 native frame 0,60,150에서 왔다. 별도 카메라 합성이나 가상 움직임은 넣지 않았다.

## 거절된 전방 5mm partial

![전방 5mm 거절 후보의 확보된 시작·실제 종료 native 프레임. 이후 시점은 만들지 않음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/rejected_forward5_available_frames_v3.png)

`native_forward5_static`은 152 physics step/38 control step, 물리 0.633333초에 guitar safety displacement로 중단됐다. 영상은 원본 20 frames/0.666667초다. 5초 길이로 늘이거나 비어 있는 후속 프레임을 생성하지 않았다.

## 5초 결과와 한계

선택 run은 1200 physics step/300 control tick, 5초를 완료했다. 기타 bounding-box 중심 최대 이동은 34.011512mm, 최대 SO(3)는 16.513982°다. baseline은 34.001197mm/16.502623°로 약간 작았다. 같은 시각 비교에서 추가 최대 기타 변화는 1.323156mm/0.555192°였고 그 최대 회전차는 5초에 발생했다. 선택은 기타 이동/회전 모든 지표에서 baseline을 개선한 결과가 아니다.

오른 Hip waist 접촉은 1198/1200, 후기120/120이며 왼팔·손 기타 접촉은 1189/1200, 후기120/120이다. 오른 R_Shoulder 전체 body-contact presence 및 positive raw lambda는 1196/1200, 후기120/120이다. 별도 상완 축 0..1 구간 projection subset은 181/1200이며, 이는 전체 상완 접촉 수나 근위 30/45% 접촉 수가 아니다. endpoint-clamped sphere cap이 전체 body-contact 표본에 포함되므로 관측 표현은 팔꿈치 가까운 상완 끝부분 접촉으로 제한한다. Chest/trunk, Thorax, 오른 전완·원위팔, 머리 접촉은 각 0/1200이다. 두 블록 또는 겨드랑이의 지지, 왼손 없는 수동 안정, 음악/연주 성공을 주장하지 않는다. raw lambda는 힘 N이 아니다.

strap OFF, root/하체 고정, 기타 자유, self-collision ON이다. 제어는 full81 목표 중 33 EFFORT+48 POSITION이다. finite human virtual caps는 Thorax 10N/4mm, Shoulder 20N/8mm이며 이는 가상 명령 한계이지 측정 접촉력 값이 아니다. 기타 힘·부착·runtime pose overwrite, checkpoint 연결, 학습은 없다.

## 여섯 native 영상과 provenance

[기준·선택·거절 partial 전신/손 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/INDEX.md) · [원본/복사 SHA, ffprobe, frame metadata](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/manifest_v3.json) · [입력·producer SHA 전후 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/provenance_v3.json) · [최종 산출물 builder](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/build_artifacts_v3.py)

이번 최종 builder는 baseline 두 MP4와 NanumGothic 글꼴까지 실행 전 입력 SHA에 포함했다. baseline 원본 영상 SHA도 이전 upright phase의 artifact inventory/native report와 대조했다. 중간 builder v1/v2는 사전 경로 검증에서 멈춰 이미지·영상·manifest를 생성하지 않았으며, 실행 이력을 보존했다. 이번 배치에는 새 physics trial이나 영상 재인코딩이 없다.

- [arm final 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/arm_final_v2.json)
- [timelines/contact 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/timelines_final_v1.json) · [waist 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/waist_final_v1.json) · [guitar same-time 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/guitar_comparison_v1.json)
