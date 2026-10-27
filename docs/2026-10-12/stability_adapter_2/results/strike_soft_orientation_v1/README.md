# Strike soft orientation 진단

이 phase는 기존 POSITION timed-wait-rebase의 policy+PI 조건에 기타 기준 RH:pick 방향 선호 residual 5 mm/rad를 더한 5초 native 진단이다. 기준 방향은 PREPARE의 existing relative pick rotation이며, 실제 pick 회전을 anchor로 현재 Chest 변화와 calibrated FK 회전을 합성해 방향 오차를 계산했다. 위치·방향·관절 규제는 공동 soft cost이고, ±0.15/±0.3 rad 및 native/rate 한계는 별도 bounds로 유지됐다. 접촉이나 손 부착을 강제하지 않는다. [실행 코드의 cost 구성](/home/ajou/yigyu/3/stability_adapter_2/run_strike_soft_orientation.py:177), [방향 reference·weight와 기록 항목](/home/ajou/yigyu/3/stability_adapter_2/run_strike_soft_orientation.py:208).

**결과: NOT ADOPTED.** 실행은 1,200 physics steps, native camera 151 frames, contract checks 21/21로 5초 완료했고 native input closure 1,088개 변경 0, 분석 입력 7개 SHA도 before/after 동일하다. PREPARE/PLAY/HOLD는 49/251/0 control samples였다. 저장 trajectory에서 actor는 251 step 실행했고 source motor phase는 `[0]`뿐이었다. 따라서 실제 저장 trajectory에는 source phase 1 APPROACH나 phase 2 RECOVER가 없었고, phase-1 native damping quarter 전환도 없었다(PD switch 0). 이 단계는 native POSITION mode였고 EFFORT command는 없었다. learned finger 21축은 계속 frozen policy 소유였으며, 학습 update는 0이다.

READY success와 target hit/physical target hit/accepted release/physical release는 각각 0, miss 10, wrong crossing 0이었다. 종료까지 source terminal은 없었고 마지막 running Strike F1 및 tip-ready success는 0이다. 최소 PLAY policy pick-to-READY 거리는 0.006379423 m였지만 READY success로 이어지지 않았다. 기타 회전 변화는 최대 45.290342°·종료 43.959132°, 위치 변화는 최대 46.353646 mm·종료 31.995380 mm였다. playable region에 든 표본은 전체 control 52/300, PLAY policy 6/251이다. 접촉 여부는 저장된 native 접촉 기록이고 readiness flag는 상태·source 조건에서 계산한 값이므로, 둘 다 기타 이동 원인을 인증하지 않는다.

이 결과는 5 mm/rad 방향 선호를 추가한 해당 saved trajectory에서 타현 성공이 없었음을 기록한다. 원인이나 단독 인과효과를 증명하지 않으므로 채택하지 않는다. [순수 회전 anchor 수학검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/rotation_anchor_check.json)는 100개 회전 사례의 quaternion 일관성만 확인했으며, native 물리·전체 FK 추적 인증이 아니다. 접촉/비접촉 표본도 인과 진단으로 확대하지 않는다. 본 phase에서는 별도의 속도 또는 미관측 방향 미분 주장을 하지 않는다.

## 실행 및 분석 자료

- [Native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/report.json), [native input closure](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/inputs_after.json): 실행 길이, 21 checks, 영상 수, closure 1,088개 unchanged.
- [Analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/analysis/summary.json), [analysis SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/analysis/inputs_before.json), [after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/analysis/inputs_after.json): pulse·phase·region·자세 지표 및 7개 입력 SHA unchanged.
- [Initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/initial_values.json), [initial audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/initial_audit.json), [Native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/report.json): native mode와 PD switch count(0) 기록.
- [Checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/checkpoint_connection.json): 303 observation, 30 action, frozen checkpoint 연결 및 학습 0.
- [Controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/controls.json), [native trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/trace.json): 300 control records와 151 native state samples.
- [Pre-review](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/pre_review.md), [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_SOFT_ORIENTATION_PLAN.md:1): 사전 수학 검수의 범위는 anchor/world rotation 순수 수학이며 full native certification이 아니다.

## 저장된 native 전신 및 손 영상

아래 0·2·5초 정지 이미지는 native camera capture이고, 두 영상은 각각 151 frames, 30 fps, 5.033333초다.

| 시점 | 전신 | 손 |
|---|---|---|
| 0초, 초기 상태 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/images/frames/whole_body/00000.png) | ![손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/images/frames/hands/00000.png) |
| 2초, PLAY | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/images/frames/whole_body/00060.png) | ![손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/images/frames/hands/00060.png) |
| 5초, 기록 끝 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/images/frames/whole_body/00150.png) | ![손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/images/frames/hands/00150.png) |

![전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/images/whole_body.mp4)

![손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/native/data/images/hands.mp4)
