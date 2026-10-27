# Bounded lower-initial-pose search and native diagnostics

작성일: 2026-10-06. 이 결과는 승인된 제한 범위에서 초기 하체 관절각의 민감도를 살핀다. 초기 기타 Z +5 mm, 절대 strap rest length 1.0891851746440693 m, humanoid root, 상체 66개/몸통 9개 PD, 기타 자세 목표와 solver 조건은 네 native trial에서 동일하다.

## 조건 및 결과

정적 source-shape 탐색은 101개 조건을 평가했다. `search/`에는 자기 파일 SHA 기록을 넣기 전의 첫 실행을 그대로 보존했다. `search_verified/search.json`은 자기 SHA를 포함한 재검증 자료이며, `search_reproduction_validation.json`에서 두 탐색의 101개 결과 행과 선택 ID `[45, 58, 66]`가 동일함을 확인했다. 범위는 제한된 국소 5레벨 coordinate 탐색이며 모든 관절 조합을 배제하지 않는다.

|조건|관절 초기각 변경 (rad)|source 최소 바닥 gap / 음수 pair|native 최대 기타 오차: candidate 목표 (mm / deg)|공통 원본 목표 위치 오차 (mm)|하체 raw 최대 actual−target (deg)|native scalar 위반 (deg)|leg body 방향 변화 (deg)|첫 neck/knee contact|
|---|---|---:|---:|---:|---:|---:|---:|---|
|baseline|없음|−9.691 mm / 2|63.033 / 7.320|65.349|107.784|101.734|147.173|0.05 s|
|c01|R_Hip_z +0.025, R_Ankle_y −0.05|−9.443 mm / 2|63.139 / 7.236|65.420|99.176|96.528|136.111|0.05 s|
|c02|c01 + L_Hip_x −0.025 (−1.57079637 → −1.59579637)|−9.443 mm / 2|7.174 / 1.591|8.322|90.755|90.755|116.689|없음 (0.1 s 내)|
|c03|c01 + L_Knee_x −0.025 (1.39629996 → 1.37129996)|−9.443 mm / 2|63.741 / 7.400|65.889|96.428|96.428|134.115|0.05 s|

모든 초기 source guitar/human query에서 음수 pair는 0개였다. 초기 source-ground 최소 gap은 baseline 대비 0.248 mm 나아진 뒤 c01–c03에서 같았고, 네 조건 모두 바닥 음수 pair 2개가 남았다. 이는 CPU source-shape signed query이지 보정된 침투 깊이나 native PhysX clearance 인증이 아니다. 탐색의 1 mm 목표 여유에도 크게 못 미치며, 제한된 두 차례 탐색만으로 전 공간에서 해가 없다고 증명하지 않는다. 정적 case 29는 R_Hip_x −0.05 rad에서 바닥 gap +4.607 mm였지만 R_Hip/G:body source gap −9.071 mm여서 바닥 개선이 기타 겹침과 tradeoff임을 보였다.

c02는 0.1초 동안 기타 candidate 목표 최대 오차를 크게 줄였고 knee/neck 접촉 기록도 없었다. 그러나 공통 원본 위치 목표 오차는 8.322 mm이며 raw 하체 편차 90.755°, native scalar 위반 90.755°, leg body orientation 변화 116.689°가 함께 기록됐다. 이 수치로 Euler 표현만의 문제라고 추론할 수 없다. 따라서 이는 초기 관절각에 대한 기타 오차 민감도 개선이지 안정 자세 성공, feedback 준비, 또는 최종 선택을 뜻하지 않는다. 각 run의 strap 최대 applied tension 기록은 0 N이다.

## 그림과 재현

![native 기타 오차, 공통 원본 목표 오차, 초기 source-ground gap, 하체 최대 편차 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/images/lower_initial_pose_v1_comparison.png)

![c02 저장 native pose의 t=0과 t=0.1초 source collision shape 재구성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/images/lower_initial_pose_v1_c02_poses.png)

두 번째 그림은 c02의 저장된 native state step 0과 24에서 source collision shape를 재구성한 것이다. 기타는 파랑, pelvis/다리는 주황, 나머지 humanoid는 반투명 회색이며 두 패널은 같은 world bounds와 시점을 쓴다. 116.689°는 전체 0.1초 구간의 최대값(step 15, 0.0625초, L_Knee)이며 그림 오른쪽 끝 시점의 값이 아니다. 그림의 step 24에서 leg body 방향 편차 최대값은 L_Ankle의 90.608°다. 이는 PhysX/Isaac Gym renderer가 아니며 source geometry를 저장 native pose에 배치한 시각화다. 물리 실행은 추가하지 않았다.

위 그림은 report/trace 및 comparison JSON에서 읽은 실제 기록을 시각화한다. 곡선은 240 Hz CPU PhysX 24-step trial이며 source-ground panel은 초기 source-shape query다. 그림은 Isaac/native renderer 이미지가 아니며 signed gap은 cooked shape clearance를 보증하지 않는다. leg raw angle은 wrapping하지 않은 actual−target 차이다.

재생성 명령 (저장된 결과만 읽고 시뮬레이션하지 않음):

```bash
cd /home/ajou/yigyu/3
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib MUJOCO_GL=disable \
MPLCONFIGDIR=/tmp/stability_adapter_2_matplotlib MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python stability_adapter_2/plot_lower_initial_pose.py \
  --results-dir docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1 \
  --output docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/images/lower_initial_pose_v1_comparison.png \
  --pose-output docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/images/lower_initial_pose_v1_c02_poses.png
```

원자료는 `baseline/`, `c01/`, `c02/`, `c03/`의 report, trace, states, contacts 및 initial source geometry JSON이다. 검색 원자료, 보존된 초기 검색 실행, 재현 검증과 20개 테스트 기록은 이 결과 폴더에 함께 남겼다. 별도 change-reviewer 검수를 통과했다. 20개 테스트, 탐색 기록·선정 순위, 네 조건의 전체 native 상태/접촉/trace/torque와 두 그림이 독립 재현됐다. 남은 지적은 없다. [검수 기록](review.md), [변경 파일·실제 줄 번호](CHANGED_FILES.md), [원본 보존](protected_validation.json), [최종 소스 스냅샷 검증](source_snapshot_validation.json).
