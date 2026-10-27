# Left-lean axilla · native1–3 비교

V2는 기존 V1을 보존하고, 완료된 native3 조건과 두 영상을 추가한 후속 문서입니다. Native1=pure left4°, native2=coupled left4_nearbody, native3=같은 coupled 초기 조건에서 기존 전완 motor-point 제어에 상완 motor-point press를 더한 조건입니다. Native2/native3의 initial81, joint q 및 기타 초기 상태는 exact match입니다. 세 실행 모두 1200 physics step·300 control·5.0 physics초 완료, training/policy/music 0, strap OFF입니다. Native3 상완 점은 사람 관절 effort로 작동하며 기타에 직접 힘을 가하지 않습니다. 이 비교는 순수 수동과 능동을 비교하는 시험이 아닙니다. Native2도 전완 controller가 활성화돼 있습니다.

![세 완료 native의 실제 0·2·5초 whole_body 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/native_timeline_comparison_v2.png)

![기준·native1·native2·native3의 초기 native 장면 정성 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/initial_pose_four_conditions_v2.png)

| 관측값 | native1 · pure left4° | native2 · coupled | native3 · upper press |
|---|---:|---:|---:|
| body bbox 중심 이동 | 187.876 mm | 205.134 mm | 203.862 mm |
| actor-root 이동 | 258.387 mm | 323.030 mm | 319.918 mm |
| 초기 대비 전체 SO(3) 회전 | 73.904° | 50.178° | 49.689° |
| 2→5초 body 중심 이동 / 회전 변화 | 0.614 mm / 0.237° | 35.083 mm / 13.212° | 32.609 mm / 12.603° |
| R_Shoulder 접촉 표본 | 0/1200 | 0/1200 | 0/1200 |
| R_Forearm 접촉 표본 | 173/1200 | 346/1200 | 351/1200 |
| Head 접촉 표본 | 782/1200 | 0/1200 | 847/1200 |
| 왼팔·손 접촉 표본 | 0/1200 | 0/1200 | 0/1200 |

접촉 수는 240 Hz endpoint 표본이며 힘 단위가 아닙니다. Native3의 상완 motor-point 최대 요청 norm은 21.392 N이며 point별 cap은 30 N입니다. 실제 R_Shoulder 접촉은 0/1200으로, 상완 motor-point 요청만으로 겨드랑이 접촉 지지가 확인된 것은 아닙니다. Head 접촉 847/1200 (positive raw lambda 846)과 전체 회전 49.689° 때문에 native3은 거절 조건입니다. Raw lambda는 N 단위 힘이 아닙니다. Native1은 Head 접촉으로 거절됐고, native2는 R_Shoulder 접촉 0/1200 및 큰 위치 이동으로 기타 유지에 실패했습니다. 어느 조건도 유지·연주 성공으로 판정하지 않습니다.

이 문서에서 방향 표기는 player-left=넥 쪽(정면 화면 오른쪽)으로 두며, 방향 표현에 대한 사용자 확인은 대기 중입니다. 상완점은 해당 초기 world target에 향하는 사람 관절 effort 점이고, 기타에 직접 힘을 가하지 않습니다. source gap은 source analytic 간격이며 cooked contact/clearance 인증이 아닙니다. 화면상 겹침 역시 cooked 관통을 증명하지 않습니다.

- [V1 source 비교와 이전 두 native 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/README_V1.md)
- [영상 색인 V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX_V2.md) · [6개 영상 SHA/ffprobe manifest V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/manifest_v2.json)
- [Native3 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v4/verification.json) · [native3 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/native_v3/left4_nearbody_upper_press/report.json)
- [V1 source gap comparison](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/source_gap_comparison.png)
