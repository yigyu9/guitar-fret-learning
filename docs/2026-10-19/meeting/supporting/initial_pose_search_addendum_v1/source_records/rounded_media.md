# 분산 전경·왼손 초기 목표 native 비교

## 조건과 범위

네 조건은 **분산 전경 3°·왼손 철수**, **분산 전경 9°·왼손 지지**, **분산 전경 9°·왼손 철수**, **분산 전경 12°·왼손 철수**입니다. `상완 고정` 조건으로 부르지 않습니다. 9°/12°는 몸통 segment 목표가 누적된 조건이며, 이를 연속 척추 mesh 변형으로 해석하지 않습니다. 초기 body world 목표 차이는 9° 조건에서 Torso 2.25°/Spine 5.625°/Chest 9°, 12° 조건에서 3°/7.5°/12°입니다.

v2의 `predicted_upper_arm_source_plane_gap_mm` (mm)은 분산 전경 3°·왼손 철수 0.50359291, 9°·왼손 지지 0.50332533, 9°·왼손 철수 0.50332533, 12°·왼손 철수 0.50316475입니다. 이는 원본 FK의 오른쪽 상완 capsule 지지점과 기타 상단 평면 사이 signed gap 예측이며, PhysX cooked 형상의 실제 최단거리나 native contact 결과가 아닙니다. v1의 위 8 cm·뒤 3 cm 후보는 overlap 판정으로 거절된 상태로 보존했고, 이 비교는 선택된 v2 네 native 실행만 포함합니다.

모든 조건에서 원래 strap ON 법칙과 rest length를 유지했습니다. strap을 끄거나 runtime에서 해제하지 않았고, 음악 policy·checkpoint·학습도 사용하지 않았습니다. 고정 초기 `q_ref`를 PD target으로 계속 제출했고, root 하체는 고정했으며 실제 움직임은 물리에 맡겼습니다. 9°·12°의 Torso/Spine/Chest 분산은 초기 관절 목표 구성입니다. 왼손 철수도 reset 때 초기 LH palm 목표를 앞쪽 8 cm·아래쪽 3 cm 옮긴 배치이며, 동적 손 놓기 동작이 아닙니다.

Root native 검증은 33/33 checks 통과입니다. 네 실행은 모두 5.0초, 1,200 physics steps, 300 control steps를 완료했습니다. 각 MP4는 30 fps, 151 frames, 5.033333초 재생입니다.

## 실제 native frame 패널

아래는 각 조건의 실제 native capture에서 0초(frame 0), 2초(frame 60), 5초(frame 150)를 가져온 전신·손 패널입니다. 글자는 NanumGothic을 사용했습니다.

![분산 전경·왼손 조건별 native 전신 frame, 0초·2초·5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/artifacts_v1/native_whole_body_frames_v1.png)

![분산 전경·왼손 조건별 native 손 frame, 0초·2초·5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/artifacts_v1/native_hands_frames_v1.png)

## actor-root 위치와 quaternion 회전

위치 변화는 각 조건의 초기 actor-root world 위치로부터의 거리이며, SO(3)는 각자의 초기 quaternion 대비 각도입니다. actor-root 값은 body-center 자연범위 판정이 아닙니다. 후기 2–5초 변화는 실제 trace의 2초 위치/quaternion을 기준으로 다시 계산했습니다.

![actor-root 위치와 SO(3) 변화, 전체 0–5초 및 후기 2–5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/artifacts_v1/root_motion_traces_v1.png)

| 조건 | 5초 초기 대비 actor-root 위치 변화 | 최대 위치 변화 | 5초 초기 대비 SO(3) | 최대 SO(3) | 후기 2→5초 위치 변화 | 후기 2→5초 SO(3) |
|---|---:|---:|---:|---:|---:|---:|
| 분산 전경 3° · 왼손 철수 | 36.2371 cm | 37.1854 cm | 88.1609° | 90.1569° | 0.9081 mm | 0.177405° |
| 분산 전경 9° · 왼손 지지 | 10.8434 cm | 10.8435 cm | 18.9736° | 18.9740° | 0.04784 mm | 0.008496° |
| 분산 전경 9° · 왼손 철수 | 33.5360 cm | 35.9682 cm | 83.3055° | 91.0003° | 5.42628×10⁻⁴ mm | 0.000078° |
| 분산 전경 12° · 왼손 철수 | 33.2864 cm | 35.5503 cm | 83.4143° | 90.7531° | 2.68040×10⁻⁴ mm | 0.000037° |

후기 움직임이 작아진 세 왼손 철수 조건도 그 전에 기타가 크게 이동·회전했습니다. 특히 3° 철수는 종료 시 36.237 cm·88.161°, 9° 철수는 33.536 cm·83.305°, 12° 철수는 33.286 cm·83.414° 변했습니다. 이는 초기 기타 자세 유지나 안정화 성공을 뜻하지 않습니다. 9° 지지도 종료 시 10.843 cm·18.974° 변했으므로 초기 자세 보존 판정이 아닙니다.

## Contact query 관측

Contact는 control 주기 직전 60 Hz에서 300회 query한 결과입니다. 이는 240 Hz physics 모든 substep을 검사한 연속 비접촉 인증이 아닙니다. Raw λ는 native 원시값이며 Newton 힘으로 환산하지 않습니다.

| 조건 | 왼팔·손 합계 | LH palm | R_Shoulder | R_Elbow | Chest | Spine | Torso |
|---|---:|---:|---:|---:|---:|---:|---:|
| 분산 전경 3° · 왼손 철수 | 0/300 | 0/300 | 0/300 | 0/300 | 0/300 | 0/300 | 0/300 |
| 분산 전경 9° · 왼손 지지 | 299/300 | 263/300 | 284/300 | 15/300 | 0/300 | 0/300 | 0/300 |
| 분산 전경 9° · 왼손 철수 | 0/300 | 0/300 | 0/300 | 4/300 | 0/300 | 0/300 | 1/300 |
| 분산 전경 12° · 왼손 철수 | 0/300 | 0/300 | 0/300 | 6/300 | 0/300 | 0/300 | 0/300 |

세 왼손 철수 실행의 왼팔·손 contact query는 모두 0/300이었고, 9° 지지 실행은 299/300이었습니다. 철수 실행에서는 오른쪽 어깨 query도 0/300이었습니다. 전완 R_Elbow contact는 철수 3°/9°/12°에서 각각 0/4/6회, 9° 지지에서 15회 관측됐습니다. 9° 철수의 Torso contact 1회는 0.7초 표본 하나입니다. 접촉 query 0은 전체 물리 시간 동안의 비접촉이나 지지 안정성 증명이 아닙니다.

## 자료 및 provenance

- [8개 원본/보관 SHA와 ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/rounded_spine_no_left_v1/manifest.json)
- [네 조건 전신·손 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/rounded_spine_no_left_v1/README.md)
- [native 검증 33개 항목 및 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/verification_v1.json)
- [선택된 v2 초기 조건](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/search_v2/selected.json)
- [v1 위 8 cm·뒤 3 cm overlap 거절 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/search_v1/rounded3_left_away_audit.json)
- [그림 생성기: sealed native frame/trace만 사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/artifacts_v1/make_rounded_spine_figures_v1.py)
- [산출물 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/artifacts_v1/provenance_v1.json)
