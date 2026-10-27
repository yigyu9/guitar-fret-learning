# Body-side lean axilla · 두 native 조건 기록

두 실행은 확정된 동일 full native initial state에서 각각 5.0 physics초 완료된 진단입니다. 두 MP4는 151프레임·30fps로 인코딩되어 재생 길이는 5.033333초입니다. root/lower body는 고정, strap OFF, 기타는 자유, 왼손 grip 없음, 기타에 직접 힘을 가하지 않았습니다. 기존 source v5 candidate는 그대로 보존했습니다. 방향은 사용자가 확인한 정의인 player-right = 정면 화면 왼쪽 = 기타 몸통 쪽이며, 몸통 추가 회전은 Chest 4°, Torso 1°, Spine 2.5°입니다.

![동일 방향 표기의 초기 native 장면 두 조건](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/initial_native_pair.png)

![두 조건의 실제 native 전신 0·2·5초 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/native_timeline_0_2_5s.png)

| 관측값 | 전완 motor-point · native1 | 전완 + 상완 motor-point press · native2 |
|---|---:|---:|
| body bbox 중심 최종 이동 | 48.051 mm | 47.501 mm |
| 초기 대비 전체 SO(3) 회전 | 52.174° | 47.662° |
| neck G+Y elevation 최종 | −15.921° | −10.019° |
| 2→5초 body 중심 이동 / 회전 변화 | 0.310 mm / 0.317° | 0.316 mm / 0.494° |
| 오른 상완 접촉 표본, 240 Hz endpoints | 968/1200 | 256/1200 |
| 오른 전완 접촉 표본, 240 Hz endpoints | 1191/1200 | 1149/1200 |
| 왼팔·Head 접촉 표본, 각각 | 0/1200 | 0/1200 |
| R_Shoulder, 60 Hz pre-control presence 표본 | 242/300 | 64/300 |

Neck G+Y elevation은 몸통에서 넥 방향으로 향하는 축의 world 수평 기준 부호 각도이며 전체 SO(3) 크기가 아닙니다. 60 Hz pre-control contact 표본은 별도 관측이며 240 Hz의 1200 after-step endpoint 표본과 합산하지 않습니다. Contact/raw lambda는 접촉 빈도 기록이지 측정힘이 아닙니다.

두 조건 모두 2→5초 변화는 작지만 이미 잘못된 자세 방향으로 이동한 뒤 정착한 상태입니다. 따라서 안정된 초기 자세 유지나 연주 성공으로 판단하지 않습니다. 상완 motor-point 요청은 사람 관절 effort를 통한 상완의 목표 접근이며 실제 측정 힘이 아닙니다. 상완 접촉 감소와 함께 neck elevation·전체 회전이 남아 있어 상완 지지가 해결됐다고 단정할 수 없습니다. Source 기하·capsule 간격은 cooked PhysX 접촉/여유를 증명하지 않습니다.

두 영상의 각 장면은 실제 Isaac Gym native camera입니다. 6현은 물리 추가가 없는 시각 overlay이며 gauge·진동을 모델링하지 않습니다. [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/INDEX_V1.md) · [source/copy SHA 및 ffprobe](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/manifest_v1.json)

- [결과 summary](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/result_summary_v1.json)
- [native1 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/analysis_v2/verification.json) · [native2 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/analysis_v3/verification.json)
