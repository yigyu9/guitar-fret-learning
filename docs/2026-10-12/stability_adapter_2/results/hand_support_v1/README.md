# Initial hand–neck proximity and routed strap diagnostics

작성일: 2026-10-06. Sol이 확정한 10개 native-run 결과와 저장된 QP source search를 정리한 산출물이다. 초기 근접도는 실제 접촉/지지가 아니며 어느 설정도 안정 성공 또는 최종 후보로 채택하지 않는다. 현재 다음 joint-hold residual proposal은 별도 제안 단계이고, 이 결과에 feedback ON을 포함하지 않는다.

## 범위·변경·검증

시도 범위는 승인된 상체/왼손 초기 관절과 strap 길이 설정이다. 하체 초기 자세와 실제 하체 물리는 그대로 실행했고 이번 평가는 하체를 observation-only로 제외했다. humanoid root, torso9 목표, guitar 목표, main66/PD, 모델 assets와 solver 조건은 비교 audit상 유지됐다. 능동 strap/feedback/자동 동적 길이 변경은 없다. rest length는 각 run 동안 설정된 절대값으로 고정된다.

세 가지 run group의 10 trial 모두 0.1 s 또는 0.5 s trace/state를 보존했고 native/invariant checks가 통과했다. comparison check는 이전 C02 reference exact reproduction, coupling input hash, 0.5 s run의 short-prefix 일치가 모두 true다. 그림은 comparison·trace와 기록 pose만 읽는다. 이 보존·재현 통과는 물리 성공 판정이 아니다.

## Source query 탐색

처음 wide-cutoff signed backend query는 접촉/거리 sign이 불안정했다. `distance_cutoff_probe.json`의 baseline guitar neck geom 55는 cutoff 변화에 따라 다음 값을 냈다. 이 때문에 해당 v1 검색은 무효로 보존하고 선택 근거로 쓰지 않았다. 실패 검색 원본 `search/`, source snapshot의 script/input/trial 설정은 삭제·덮어쓰기 없이 보존했으며 이에 근거한 native 실행은 하지 않았다.

|Backend query cutoff|geom 55 raw signed output (mm)|
|---:|---:|
|0.1 m|+63.977|
|0.2 m|−94.407|
|1.0 m|−162.899|

`search_v2/search.json`은 159개 initial source case에 대해 6-variable SLSQP unsigned convex-hull distance를 사용했다. 20 mm backend signed-gap source gate는 별도 유지했다. baseline palm/neck hull distance는 64.025621 mm였다. selected QP IDs 70/72/79의 unsigned hull distances는 3.139057/3.269733/2.388134 mm였고 saved witness pair들의 계산 간격은 각각 해당 거리와 floating precision상 일치한다. p08은 valid search ID 69 (약 0.800 mm, 반올림)에서 골라 native 진단했다. 이 값들은 source convex-hull proximity proxy이며 penetration depth·PhysX clearance·contact force가 아니다. normal proxy의 anatomical sign도 검증되지 않았다.

## Native results (10 runs)

오차는 각 trace 전체에서의 최대값이다. QP hull distance는 source convex hull 간 unsigned 값이다. 0.5 s 이전 reference curve는 기존 `pose_strap_v1` comparison에서 읽은 참고선이며 이번 10개 trial 수에는 포함되지 않는다.

|Run|Initial route / absolute rest L (m)|Max guitar error pos (mm) / rot (°)|First / max applied tension (N)|Initial → final QP unsigned hull distance (mm)|LH guitar contact rows|Max main raw drift (°)|
|---|---|---|---|---|---|---|
|short / candidate_01 (0.1s)|1.101080 / 1.083374|24.216 / 8.612|106.236 / 106.236|3.139 → 26.205|0|6.641|
|short / candidate_02 (0.1s)|1.101080 / 1.083374|24.216 / 8.612|106.236 / 106.236|3.270 → 23.388|0|6.640|
|short / candidate_03 (0.1s)|1.101080 / 1.083374|24.215 / 8.611|106.236 / 106.236|2.388 → 25.091|0|6.644|
|short / reference (0.1s)|1.083374 / 1.083374|6.845 / 1.520|0.000 / 8.017|64.026 → 103.547|0|6.505|
|coupled_short / p08_load00 (0.1s)|1.101080 / 1.101080|6.878 / 1.521|0.000 / 6.818|0.800 → 33.873|0|6.642|
|coupled_short / p3_load00 (0.1s)|1.101080 / 1.101080|6.874 / 1.520|0.000 / 6.823|3.139 → 36.141|0|6.641|
|coupled_short / p3_load10 (0.1s)|1.101080 / 1.099413|6.916 / 1.693|10.000 / 10.000|3.139 → 35.172|0|6.641|
|coupled_short / p3_load20 (0.1s)|1.101080 / 1.097747|7.651 / 2.162|20.000 / 20.000|3.139 → 34.226|0|6.641|
|coupled_hold_05s / p08_load00 (0.5s)|1.101080 / 1.101080|61.483 / 8.877|0.000 / 15.938|0.800 → 146.550|0|18.314|
|coupled_hold_05s / p3_load00 (0.5s)|1.101080 / 1.101080|61.484 / 8.876|0.000 / 15.919|3.139 → 148.498|0|18.314|

p3/p08 상체 Thorax 변경으로 initial routed length가 기존 reference 1.0833741669597394 m에서 1.1010801317960974 m로 17.706 mm 길어졌다. 이를 그대로 old absolute L에 붙인 `candidate_01`에서는 첫/max applied tension 106.236 N, 24.216 mm/8.612°가 기록됐다. 이후 route length와 맞춘 absolute L에서 p3/p08 load00은 0.1 s에 각각 6.874/6.878 mm, 1.520/1.521°였다. preload10/20 조합은 개선되지 않았다.

0.5 s p3/p08 route-match 조건은 각각 61.484/8.876°와 61.483/8.877°로, 이전 reference 58.452/8.923°보다 위치 오차가 컸다. 둘 다 LH/guitar contact rows 0, max main raw drift 18.314°였고 final unsigned hull distance 148.498/146.550 mm로 멀어졌다. 따라서 더 가까운 초기 hand/neck geometry가 support/hold 유지로 이어지지 않았다.

## Figures and reproduction

![reference, p3, p08 initial source hand/neck witness geometry and p08 0.5-second saved pose](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/images/hand_support_v1_source_poses.png)

첫 그림은 reference/p3/p08 t=0 및 p08 t=0.5 s의 source pose reconstruction이다. 파랑은 기타 넥 형상, 초록은 왼손/손목, 주황 선·점은 table에 기록된 QP hull witness pair, 보라색 화살표는 palm normal proxy, 점선은 crop 안에서 보이는 저장 strap-route 부분이다. 같은 world bounds와 camera를 썼다. CPU source geometry이며 Isaac/PhysX renderer나 clearance validation이 아니다.

![old and route-matched absolute strap lengths at 0.1 s and p3/p08/reference guitar errors at 0.5 s](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/images/hand_support_v1_native_curves.png)

두 번째 그림은 0.1 s old-L/reference 및 old-L arm candidate와 route-matched p3/p08, p3 preload10/20, 그리고 0.5 s previous-reference/p3/p08의 position·rotation trace다. solid line은 mm 위치 오차, dashed는 각도 오차다. short old-L candidate는 새 Thorax pose에서 초기 route와 absolute L이 17.706 mm 어긋나 high tension을 유발했다.

기존 reference의 초기 왼손 palm convex-hull centroid는 local neck section 하단보다 82.533 mm 낮았고 normal proxy `palm_up_dot=0.869692`였다. p3/p08 자세는 이 source 관계를 바꿨지만 native contact/support는 만들지 못했다. 초기 20 mm-cutoff signed query의 음수 pair가 없더라도 손이 guitar에 닿거나 지지하는 것은 아니다. 0.5 s까지 양손/guitar contact rows는 없었고, QP/static geometry와 contact-row 기록은 support-force measurement가 아니다.

재생성은 새 출력 파일명을 사용한다. plotter는 기존 PNG 또는 manifest를 덮어쓰지 않고 중단한다. 실행 인자 예시는 다음과 같다.

```bash
cd /home/ajou/yigyu/3
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib MUJOCO_GL=disable \
MPLCONFIGDIR=/tmp/stability_adapter_2_matplotlib MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python stability_adapter_2/plot_hand_support.py \
  --comparison docs/2026-10-12/stability_adapter_2/results/hand_support_v1/comparison.json \
  --results-dir docs/2026-10-12/stability_adapter_2/results/hand_support_v1 \
  --previous-results-dir docs/2026-10-12/stability_adapter_2/results/pose_strap_v1 \
  --curve-output /tmp/hand_support_curves_fresh.png \
  --geometry-output /tmp/hand_support_geometry_fresh.png \
  --manifest /tmp/hand_support_manifest_fresh.json
```

`plot_manifest.json`은 플롯 코드, import helper, asset/mesh, comparison/search, native report/state/trace 및 두 이미지의 SHA-256을 담는다. 새 native rollout, 성공 기준, 후보 선택은 이 산출물에 포함하지 않는다.
