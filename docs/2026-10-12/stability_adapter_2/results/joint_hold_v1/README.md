# Joint-hold feedback paired diagnostics

작성일: 2026-10-06. 이 결과는 승인된 24-arm-joint actual-error target correction OFF/ON 조건의 저장된 여섯 native run을 비교한다. 각 기간은 240 Hz physics trace의 0.1, 0.5, 1.0초다. 하체·몸통·손가락 held target, 초기 상태, humanoid root, guitar initial pose/goal, strap 길이, native gain/solver는 유지했다.

## 시간별 최대 오차와 arm drift

표의 기타 오차는 각 run의 candidate guitar goal에 대한 최대값이다. `arm raw`는 저장 DOF의 actual angle과 변경 전 원래 목표각의 최대 절대 차이다. 접촉 gap은 초기/종료 source-hull proxy이며 PhysX clearance가 아니다.

| 길이 | 모드 | 최대 위치오차 (mm) | 최대 회전오차 (°) | 최대 arm raw drift (°) | 종료 palm–neck hull gap (mm) | 왼손–기타 접촉 행 |
|---:|:---|---:|---:|---:|---:|---:|
| 0.1 s | OFF | 6.878 | 1.521 | 6.642 | 33.873 | 0 |
| 0.1 s | ON | 6.878 | 1.521 | 5.850 | 29.409 | 0 |
| 0.5 s | OFF | 61.483 | 8.877 | 18.314 | 146.550 | 0 |
| 0.5 s | ON | 61.462 | 8.873 | 12.595 | 85.960 | 0 |
| 1.0 s | OFF | 264.207 | 48.065 | 20.997 | 270.835 | 0 |
| 1.0 s | ON | 196.035 | 33.994 | 14.314 | 156.395 | 0 |

## 그림 22. 1초 paired native trace와 제한된 joint-target correction

![1초 OFF/ON 기타 오차, arm drift, 목표 보정량 및 포화 physics samples](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_hold_v1/images/joint_hold_v1_1s_off_on.png)

ON은 1초 구간 최대 arm drift를 줄였지만 196.035 mm/33.994°의 최대 기타 오차가 남아 유지 성공이 아니다. correction은 최대 0.15 rad로 제한됐고 saturation/blocked-integral 상태는 각각 0.1초 8, 0.5초 92, 1초 212 physics samples였다. 이 수는 240 Hz trace에서 반복 기록된 held samples이며 독립적인 60 Hz controller update 횟수로 해석하지 않는다. 모든 run에서 왼손–기타 contact row는 0이고, 전체 물리 sample의 palm up-dot 최소값은 0.926704였다. up-dot은 해부학적 방향이 검증되지 않은 source geometry proxy다. arm scalar-limit violation 최대 0.029066°가 모든 paired 조건에 공통으로 남았다.

`decision.json`의 1초 ON raw contact 집계에는 `human/R_Shoulder` 65행, `human/RH:thumb2` 35행, `human/RH:thumb3` 78행이 있고, OFF의 세 부위는 각각 0행이다. 양쪽 `human/R_Hip`는 각각 239행이다. 이 값은 접촉 행 수일 뿐 지지력이나 drift 개선 원인을 말하지 않으며, 왼손 contact가 전 조건에서 0행이므로 LH 지지 성공도 아니다.

## 그림 23. 저장 pose의 손·기타 source geometry

![공통 초기 자세와 0.5초 및 1초 OFF/ON 저장 pose의 source geometry 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_hold_v1/images/joint_hold_v1_source_pose_comparison.png)

이 그림은 saved native states, convex source collision shapes, 저장된 strap route를 같은 world bounds/view로 CPU에서 재구성한 것이다. Isaac/PhysX renderer 화면이 아니며 cooked-shape clearance, contact, 지지력을 인증하지 않는다. ON target은 guitar-error feedback이 아니라 arm joint actual-error 기반 PI target-only 보정(`q_play` 기준, bounded delta)이다. guitar pose를 직접 제어하지 않고 FK task rejection과 rate limit도 구현되지 않았다. 모든 six-run checks와 paired initialization/long-prefix reproduction은 통과했고, controller 경계 검사는 4개 통과했다. 이는 trial 진단이지 안정성 성공이나 최종 후보 채택이 아니다.

## 재생성 및 원자료

재생성은 저장된 JSON과 source geometry만 읽으며 native physics를 실행하지 않는다. Python 3.8 `rl38` 환경이 필요하다.

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
MUJOCO_GL=disable MPLCONFIGDIR=/tmp/joint_hold_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_joint_hold \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_hold_v1 \
  --out-dir /tmp/joint_hold_v1_plot_reproduction \
  --manifest-path /tmp/joint_hold_v1_plot_reproduction/plot_manifest_v2.json
```

원본 `comparison.json`, 여섯 run의 report/trace/states/contacts/controls 및 플롯 helper hash는 아래 manifest에 기록했다. 기존 [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_hold_v1/plot_manifest.json)은 재구성에 읽힌 geometry asset의 fresh hash가 빠진 과거 기록으로 보존한다. 최신 검증 provenance는 [plot_manifest_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_hold_v1/plot_manifest_v2.json)이며 config, human/guitar XML과 그 XML이 참조하는 37개 mesh 파일의 SHA-256을 새로 계산했다. 별도 `/tmp` 재생성 그림은 기존 두 PNG와 픽셀 단위로 동일했고, 기존 PNG와 기존 manifest는 변경하지 않았다.
