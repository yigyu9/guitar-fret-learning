# 초기 자세 적격성 비교 — 문서 v2

정지 지지 초기 후보는 유망하지만, 완전한 양손 연주 reset으로 채택하지 않는다. 먼저 왼손 해제 동작과 관절 움직임 여유를 해결·검증해야 한다. 기존 기본값은 변경하지 않았다.

| 조건 | 실행 | 실제 완료 구간 | 최대 BB 중심 변화 | 최대 SO(3) 회전 | 왼팔·손 접촉 | 초기·마지막 3-up |
|---|---|---:|---:|---:|---|---|
| 기준 자세 | native_baseline_v2 | 10.000 s · 완료 | 2.811 mm | 0.693° | 145/2400 표본 무접촉 | [0초 PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/baseline/three_views_00000.png) → [10초 PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/baseline/three_views_00300.png) |
| 정적 분리 | native_static_v3 | 10.000 s · 완료 | 2.719 mm | 0.826° | 2400/2400 표본 무접촉 | [0초 PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/static/three_views_00000.png) → [10초 PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/static/three_views_00300.png) |
| EW6 타현 | native_strike_v2 | 5.000 s · 완료 | 6.145 mm | 4.237° | 1159/1200 표본 무접촉; 접촉 41/1,200, paired thumb+other 0 | [0초 PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/strike/three_views_00000.png) → [5초 PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/strike/three_views_00150.png) |
| 왼손 사이클 (보호 중단) | native_left_cycle_v2 | 7.283 s · 보호 중단 | 115.508 mm | 30.527° | 1084/1748 표본 무접촉; B 도달 전 actor-root 한계 초과 | [0초 PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/left_cycle/three_views_00000.png) → [7.26667초 PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/left_cycle/three_views_00218.png) |
| 초기 G world Z +3 mm | native_z_plus3mm_v2 | 10.000 s · 완료 | 5.181 mm | 0.958° | 2400/2400 표본 무접촉 | [0초 PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/z_plus3mm/three_views_00000.png) → [10초 PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/z_plus3mm/three_views_00300.png) |

왼손 사이클은 16초 의도에서 7.283333초에 보호 중단됐다. actor-root 이동은 0.203189 m로 0.20 m 한계를 넘었고, 기타 BB 중심 변화는 115.508 mm, 회전은 30.527°였다. **회전 35° 중단은 아니다.** B 지점에 도달하지 않았으며, 마지막 카메라 프레임은 7.266667초로 물리 종료보다 1/60초 앞선다. MP4는 219프레임/30 fps, 표시 7.3초이며 마지막 문구는 중단 직전 장면이다. 이를 정지 평형이나 16초 성공으로 읽지 않는다.

### 왼손 사이클 비교 범위와 접촉 보충

이 보호 중단 실행에서 오른손 엄지3/중지3 접촉은 181 physics step 동안 6.345833–7.095833초 관측됐다. 이는 EW6 타현 5초 실행의 오른손 접촉 0과 구분한다. actor-root가 20 cm 한계를 처음 넘은 시각은 240 Hz 기준 7.279167초이며, 60 Hz 보호 표본에서 7.283333초에 중단했다.

이전 16초 cycle과 이번 실패를 몸통 자세만의 비교로 볼 수 없다. 이번 실행은 초기 관절값, 기타 초기 위치, 제어 참조와 손목 station을 함께 재기준화했다. 새 A 손목 목표는 이전 A보다 기타 좌표에서 (-1.170, 42.048, -0.034) mm 이동해 이전 B 분리 위치에 가까워졌으며, 이전 실행이 이전 B 분리 자세에서 시작했다. 따라서 실패 원인을 몸통 자세로 단정하지 않는다. [station 비교 원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/left_station_comparison_v1.json).

Strike는 5초 실행에서 EW6 타현 목표만 변경하고 다른 75개 목표는 유지했다(실제 상태는 움직일 수 있음). LH brief contact는 41/1,200 표본, 오른손목·손 접촉은 0이었다. V7 실제 타현 창의 raw detector에서는 6→1 하향과 1→6 상향 통과를 확인했다. legacy 상향 cutoff 집계는 보존하고 정정된 창은 [strike actual windows](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/strike_actual_windows_v1.json)에서 확인한다. 학습된 곡 연주 성공을 뜻하지 않는다.

![조건별 최대 기타 BB 중심 변화와 SO(3) 회전; 별도 단위 축이며 *는 불완전 실행의 관측 구간 최대값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/maxima_comparison_v2.png)

아래 두 native annotated 영상은 대표적인 정적 분리 결과와 보호 중단 결과를 본문에서 바로 보여준다.

## 정적 분리 실행

![native_static_v3 세 시야 annotated 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_qualification_v1/static/front_side_top.mp4)

## 왼손 사이클 보호 중단

![native_left_cycle_v2 세 시야 annotated 영상, 7.3초 부분 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_qualification_v1/left_cycle/front_side_top.mp4)

## 왼손 사이클 주요 시점

마지막은 peak나 평형 시점이 아니라 중단보다 1/60초 앞선 마지막 카메라 관찰이다.

![3.5초 · A 잡기 유지](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/left_cycle/three_views_00105.png)

![5.333초 · A 해제 진행 중](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/left_cycle/three_views_00160.png)

![6.5초 · A 분리 유지](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/left_cycle/three_views_00195.png)

![7.267초 · 중단 직전 마지막 카메라 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/left_cycle/three_views_00218.png)

## 조건·해석 범위

기준 near 10초는 최대 2.811 mm/0.693°였으나 LH arm/hand 접촉이 2,255/2,400 표본이라 독립 지지 비교가 아니다. Static v3는 2.719 mm/0.826°, 왼팔·손 무접촉 2,400/2,400, 오른손목·손 접촉 0이며 마지막 2초 변화는 0.01591 mm/0.006185°다. `native_static_v2`의 전역 guard는 실패했다. v3만 guard 통과 및 [5개 raw 결과 exact 재현](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/static_reproduction_v1.json)이 확인됐다.

Z+3 mm 조건은 reset 시 support motor local reference를 다시 계산했다. 고정 anchor에 대한 외란 복원력이나 강건성 실험으로 보지 않는다. 초기 scalar 한계 여유는 L_Wrist_y 0°, R_Thorax_y 약 0.000046°, L_Thorax_z 0.0012°다. 이는 모델 scalar bound이며 해부학적 world angle/인증이 아니다. 보호 중단 실행의 실제 joint bound overshoot 최대는 0.19815°이며 목표는 모델 한계와 변화율 안이었다. 상속된 near/axilla 호환 metadata는 새 접촉 인증이 아니다. LH는 시작 시 분리·후퇴하며 고정 palm 접촉을 요구하지 않는다.

다섯 실행 모두 자유 기타, strap OFF, 인위적 기타 힘 없음, root·하체 고정, self-collision ON과 유한한 active human support다. 이 결과는 passive equilibrium, force closure, 강건성, checkpoint 또는 music-ready success를 증명하지 않는다.

## 시각 자료와 원자료

기본 전면·옆면·위 순서의 세 view이며 조건별 개별 영상 3개와 합본 1개는 [전체 video index](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_qualification_v1/README_v2.md)에 있다. 3-up PNG와 MP4는 각 visual report의 해시와 대조해 바이트 보존 복사했다. 최대 변위와 최대 회전은 서로 다른 시점일 수 있다. [qualification summary](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/qualification_summary_v1.json) · [limit margins](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/initial_arm_limit_margins_v1.json) · [copy manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/copy_manifest_v2.json).


이 문서는 [영상 색인 v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_qualification_v1/README_v2.md)와 짝을 이룬다. 입력 SHA는 [새 before 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/artifact_before_v3.json)에, 생성 파일 SHA와 검증 결과는 [새 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/copy_manifest_v2.json)에 기록했다. 이전 README와 그래프는 보존했다.
