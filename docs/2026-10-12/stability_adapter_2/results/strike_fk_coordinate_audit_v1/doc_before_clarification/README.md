# 저장 native81 궤적의 FK 좌표 감사

기존 timed EXIT native 실행에서 저장한 관절 상태 151개(physics step 0–1200, 8 step 간격)를 사용해 XML joint-axis basis와 Cartesian identity basis의 parent-relative 회전 예측을 비교했다. 새 물리 실행이나 native 초기화는 없었다. 입력 6개의 실행 전 SHA는 [inputs_before.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_fk_coordinate_audit_v1/analysis/inputs_before.json:1>)에 있고, [inputs_after.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_fk_coordinate_audit_v1/analysis/inputs_after.json:1>)은 `unchanged: true`, `changed: []`를 기록한다.

## 결과

| 비교 | 최대 오차 | RMS 오차 |
|---|---:|---:|
| 8개 관절 그룹, XML B basis | 0.00003862° | — |
| 8개 관절 그룹, Cartesian I basis | 62.88158864° | — |
| full Chest-aligned FK, RH:pick body origin 위치 | 0.31645194 mm | 0.16108144 mm |
| full Chest-aligned FK, RH:pick body origin 회전 | 0.30028313° | 0.15288278° |

그룹별 최대치는 다음과 같다. 각 RMS와 표본별 오차는 [summary.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_fk_coordinate_audit_v1/analysis/summary.json:1>) 및 [group_rows.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_fk_coordinate_audit_v1/analysis/group_rows.json:1>)에 보존했다.

| Native 관절 그룹 | XML B 최대 오차 | Cartesian I 최대 오차 |
|---|---:|---:|
| R_Thorax | 0.00001360° | 12.78360973° |
| R_Shoulder | 0.00002257° | 24.83342207° |
| R_Elbow | 0.00003363° | 62.88158864° |
| R_Wrist | 0.00002222° | 60.89680504° |
| L_Thorax | 0.00000833° | 0.51644275° |
| L_Shoulder | 0.00003862° | 7.82748088° |
| L_Elbow | 0.00002740° | 3.38978670° |
| L_Wrist | 0.00002000° | 0.55633963° |

이 관측 궤적에서 XML basis를 사용한 회전 예측은 저장된 parent-relative 회전과 매우 가깝고, Cartesian identity 대조는 일부 오른팔 그룹에서 크게 벗어난다. Chest 정렬 FK도 RH:pick body origin 궤적과 최대 0.31645194 mm, 0.30028313° 안에서 일치했다. 이 검증은 관측된 자세 궤적의 좌표 일관성에 한정된다. 방문하지 않은 방향에 대한 Jacobian 정확도나 미분의 증명은 아니며, 음악·연주 성공을 뜻하지 않는다.

## 원 실행 설정과 자료

감사 입력은 기존 [timed EXIT native 실행 README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/README.md:1>), [native 초기값](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/initial_values.json:1>), [native report](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/report.json:1>), [controls](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/controls.json:1>) 및 [151표본 trace](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/trace.json:1>)다. 아래 이미지는 감사 중 새로 렌더한 것이 아니라 원 실행에서 저장한 Isaac Gym native camera frame이다.

| 원 실행 시각 | 전신 frame | 손 근접 frame |
|---|---|---|
| 0초 | ![원 timed EXIT native 전신 frame 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/whole_body/00000.png) | ![원 timed EXIT native 손 frame 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/hands/00000.png) |
| 2초 | ![원 timed EXIT native 전신 frame 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/whole_body/00060.png) | ![원 timed EXIT native 손 frame 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/hands/00060.png) |
| 5초 | ![원 timed EXIT native 전신 frame 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/whole_body/00150.png) | ![원 timed EXIT native 손 frame 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/frames/hands/00150.png) |

![감사 입력에 사용한 원 timed EXIT 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/whole_body.mp4)

![감사 입력에 사용한 원 timed EXIT 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/hands.mp4)

## 재현 근거와 범위

[분석 코드](</home/ajou/yigyu/3/stability_adapter_2/analyze_strike_fk_coordinates.py:19>)는 XML의 관절 축 행렬을 열로 쌓아 B basis를 만들고, 저장 native 상태만 사용해 8개 그룹과 full FK pick 위치를 비교한다. FK calibration 구현은 [underneck_initial_search.py](/home/ajou/yigyu/3/stability_adapter_2/underneck_initial_search.py:28)에 있다. [감사 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_FK_COORDINATE_AUDIT_PLAN.md:1)은 수정하지 않았다.

분석은 표본 수·81개 DOF·step coverage·유한 오차를 확인하고 여섯 입력의 SHA를 실행 전후 대조했다. 수치 결과 원본은 `analysis/` 아래 JSON에 보존했다. 이번 감사는 저장 궤적에 대한 FK 대조이며 새로운 native trial, 제어 변경, 실제 힘 측정은 포함하지 않는다.
