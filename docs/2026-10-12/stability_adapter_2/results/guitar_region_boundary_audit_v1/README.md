# 기타 playable-region 경계 감사

저장된 native 상태와 control 기록의 **동일 physics_step·동일 time_s만** 대조했다. false는 네 trial 모두 위치 범위 실패가 아니라, 원래 함수가 검사하는 두 일반 Euler branch의 roll/yaw 조건 실패였다. 기록 flag와 원래 함수 재계산 불일치는 0이다. box·threshold·controller·A·raw는 변경하지 않았고 물리 실행은 없다.

| trial | 동일시각 표본 | true / false | PLAY true / false | 최대 초기 대비 SO(3) 회전 |
|---|---:|---:|---:|---:|
| timed_wait_rebase_v1 | 151 | 143 / 8 | 82 / 7 | 7.095455° |
| free_finger_curl_v1 | 150 | 118 / 32 | 46 / 31 | 9.229756° |
| waypoint_velocity_v1 | 150 | 110 / 40 | 80 / 39 | 9.242948° |
| ready_incremental_v1 | 151 | 143 / 8 | 74 / 7 | 7.095455° |

각 controls는 300행, trace는 152행이다. control의 before_physics_step(4 step 간격)과 trace의 physics_step(8 step 간격 + terminal)을 정확히 결합했다. curl step816, velocity step1152의 중복 trace는 동일 p/회전임을 확인해 한 표본으로 셌다. unmatched control 149/150/150/149행의 판정 원인은 추정하지 않는다. 인접 표본 변화량은 표에 표시된 두 저장 시각 사이의 차이이며 보간·연속 최대치가 아니다.

원래 조건은 [prepared_strike_start.py:6](/home/ajou/yigyu/3/stability_adapter_2/prepared_strike_start.py:6)의 함수다. 위치는 x∈[−.50,−.15], y∈[−.15,.15], z∈[.65,초기 Chest z] m이다. Chest 상한은 .8837383985519409 m이며, frozen [run_strike_timed_exit.py:80](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/source_before/stability_adapter_2/run_strike_timed_exit.py:80)에서 초기값으로 잡고 [같은 파일:205](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/native/source_before/stability_adapter_2/run_strike_timed_exit.py:205)에서 현재 G p/q와 함께 검사한다. 분석은 initial Chest z와 checkpoint_connection의 상한이 같음도 확인했다.

동일시각 표본의 위치 조건 실패는 전부 0이다. 가장 작은 z 하한 여유도 rebase10.421491, curl9.559786, velocity6.090498, READY10.731435 mm로 양수다. 위치 상한을 넘어서 반환된 false는 없다.

## 초기 horizontal은 +90° Euler 특이점

[underneck_pose_trial_v5.py:69](/home/ajou/yigyu/3/stability_adapter_2/underneck_pose_trial_v5.py:69)는 [candidate_1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/search_v1/data/candidate_1.json)의 guitar p/q를 초기 생성 목표로 사용한다. source p=(−.2304154634,.0867123455,.7009729981) m, xyzw=(−.5,.5,.5,.5)이다. 저장 native 초기 z=.7009729743 m이며 source와 차이는 0.000023842 mm다. 네 native 초기값은 같다.

정규화한 초기 회전행렬은 [[0,−1,0],[0,0,1],[−1,0,0]]이다. cy=√(R00²+R10²)=0이므로 함수의 cy<1e−7 특이점 분기로 간다. positive pitch(+90°), roll−yaw=−90°라 허용 구간[−135,−45]를 통과한다. 동일 회전의 XYZ Euler (67.5,90,157.5)°는 roll45–90/pitch50–100/yaw135–180의 각 숫자 구간 안에 있고, 재구성 SO(3) 오차는 1.10e−14°다. 초기 위치도 box 내부다. **pitch 상한100°에 놓인 것은 아니며, Euler +90° 좌표 seam에 정확히 놓여 있다.**

일반 상태에서 함수는 principal (x,y,z)와 동등 alternate (x+180,180−y,z+180)을 모두 검사하고 roll/yaw를 %360 처리한다([원래 함수:17](/home/ajou/yigyu/3/stability_adapter_2/prepared_strike_start.py:17)). 모든 검사 branch의 회전 재구성 오차는 최대1.50e−13°다. 단순히 principal만 검사해서 alternate를 놓친 결과가 아니다. ±360°는 같은 회전을 만들지만 roll/yaw는 이미 modulo로 검사하며, 이 pitch 구간에 들어오는 일반 해는 두 branch에서 확인된다. 특이점에서는 roll/yaw가 따로 결정되지 않으므로 함수가 그 차이의 가능한 구간을 별도로 검사한다.

초기에서 최소 SO(3) 회전이 작다는 사실은 각 Euler 좌표가 작게 바뀌거나 해당 Euler box 안에 있다는 뜻이 아니다. +90° 근처에서는 roll/yaw가 작은 tilt 방향에 민감하다. 순수 수학으로 초기 회전에 world x축 ±.01°를 곱하면 위치는 같아도 두 branch 모두 실패하고, world y축 ±.01° 또는 world z축 ±.01°는 이 조건을 통과한다. 이는 저장 native 실험이 아닌 별도 회전행렬 계산이며, 초기 주변의 모든 작은 SO(3) 회전을 이 Euler box가 허용하는 것은 아니라는 확인이다. 이를 물리적으로 부자연스러운 자세나 잘못된 box라고 판정하지 않는다.

## native 반환값이 바뀐 대표 표본

아래 Euler는 동일 회전의 alternate branch (roll,pitch,yaw)이고 단위는 °다. principal도 실패한 경우에만 false가 반환된다. 위치는 각 행 모두 통과한다. Δp와 ΔSO(3)는 왼쪽 시각에서 오른쪽 시각까지의 정확한 두 저장 표본 차이다.

| trial / 시각 전환(s) | flag | 오른쪽 alternate Euler | 실패 조건 | 초기 대비 SO(3) | ΔSO(3) / Δp |
|---|---|---|---|---:|---:|
| 공통 0→.033333 | T→F | 96.431454,90.583767,186.863386 | roll>90, yaw>180 | .726187 | .726187° / 11.162872 mm |
| 공통 .033333→.066667 | F→T | 86.849247,90.907208,178.352915 | 없음 | 1.756131 | 1.125325° / 10.687390 mm |
| rebase 1.433333→1.466667 | T→F | 44.802519,95.303638,137.296480 | roll<45 | 5.860373 | .668438° / .423080 mm |
| curl 1.533333→1.566667 | T→F | 39.554763,95.626942,131.763576 | roll<45, yaw<135 | 6.044618 | .992825° / .148397 mm |
| velocity 2.400000→2.433333 | T→F | 44.857122,95.331706,136.665411 | roll<45 | 5.629799 | .208477° / .577646 mm |
| READY 1.233333→1.266667 | T→F | 89.097084,94.005050,180.057627 | yaw>180 | 4.118579 | .405837° / 1.357761 mm |

일반 alternate pitch의 전체 표본 범위는 rebase90.5838–95.7509, curl90.5838–98.4005, velocity90.5838–98.1293, READY90.5838–95.3195°로 모두 pitch50–100 안이다. false alternate의 실패 조합은 roll상한+ yaw상한, roll하한, roll하한+ yaw하한이며 velocity/READY에는 yaw상한 단독도 있다. 일반분기에서 roll/yaw 허용구간을 실제로 벗어난 것이다. 숫자 자체를 초기 Euler의 절대 차로 빼서 기타의 실제 회전량으로 해석하지 않는다.

## 재현·입력 보존 범위

[analysis.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_region_boundary_audit_v1/analysis.py)는 환경을 import하지 않고 원래 함수 한 개만 AST로 추출해 numpy/scipy 수학으로 평가한다. trial별 frozen 함수와 AST가 동일함을 확인했다. [summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_region_boundary_audit_v1/summary.json)에 전체 exact-match p/q, 양쪽 branch, 조건별 여유·실패, 모든 flag 전환, 원본 raw 경로·SHA256을 기록했다.

이 분석 실행은 모든 직접 입력27개를 **내용 decode/parse 전에 SHA256 수집 → 같은 byte cache 해시 대조 → 종료 재해시 대조**했고 모두 동일했다. 단, 실행 전 함수 위치를 찾은 underneck_pose_trial_v5.py의 최초 탐색 rg는 그 탐색의 SHA 수집보다 앞섰다. 그 최초 텍스트 탐색까지 사전봉인이라고 주장하지 않는다. 원래 함수는 앞선 탐색에서 별도 사전/종료 SHA를 확인했고, 수치 결론의 분석 입력은 이번 실행의 사전 SHA 수집 이후 범위로 검증된다. source/raw 원본의 이전 전체 이력까지 이 감사가 증명하는 것은 아니다.

재현: `/home/ajou/miniconda3/envs/rl38/bin/python /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_region_boundary_audit_v1/analysis.py`. 기존 성공한 analysis/summary는 소비된 산출물이므로 수정하지 않는다. 본 감사는 판정 조건을 분해했으며, 접촉 원인·controller 원인·연주 성공·box 변경을 판정하지 않는다.
