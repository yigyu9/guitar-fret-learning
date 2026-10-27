# 오른손 distal 초기각의 고정 strap-load 비교

작성일: 2026-10-06. `right_distal_strap_v1`에서 같은 candidate_01 초기각에 초기 strap-law tension 0/5/10/20 N을 설정한 0.1초 네 조건과, 0/5 N의 0.5초 OFF/ON 조건을 비교한다. 이 보고서와 그림을 만들며 추가 native 실행이나 설정 변경은 하지 않았다.

## 고정 조건과 초기 rest length

오른손 distal 초기각은 candidate_01로 고정했다. humanoid root, torso 9, fingers 42, C02 하체, guitar +5 mm의 목표 pose, native PD/solver 및 기존 24 arm-joint PI 설정(±0.15 rad cap, 60 Hz update)은 유지했다. strap-law 초기 tension을 지정할 때 절대 rest length도 아래 값으로 초기화했으며, 각 run 중에는 그 rest length가 고정된다. 실제 strap tension은 상태에 따라 바뀌며 입력 load가 시간 내내 유지되는 것은 아니다.

| 초기 law tension | 절대 strap rest length |
|---:|---:|
| 0 N | 1.1010801317960974 m |
| 5 N | 1.1002467984627642 m |
| 10 N | 1.0994134651294307 m |
| 20 N | 1.0977467984627640 m |

## 0.1초 preload 비교

각 load에서 0.1초 기타 위치·회전 오차 곡선이 OFF/ON 간 정확히 겹쳐, 이 두 지표에서는 mode 효과를 관찰하지 못했다. 다른 humanoid 상태까지 동일하다는 뜻은 아니다. 5 N은 위치오차가 줄었지만 회전오차가 늘었다. 10/20 N은 두 지표 모두 0 N보다 높아졌다. 0.1초에서 위치와 회전 오차가 동시에 개선된 preload는 없다.

| 초기 law tension | OFF/ON 최대 위치오차 (mm) | OFF/ON 최대 회전오차 (°) |
|---:|---:|---:|
| 0 N | 6.876050 | 1.519890 |
| 5 N | 6.800005 | 1.558658 |
| 10 N | 6.915937 | 1.691500 |
| 20 N | 7.644348 | 2.158515 |

## 0.5초의 matched OFF/ON

| 초기 law tension | OFF 최대 위치 / 회전오차 | ON 최대 위치 / 회전오차 |
|---:|:---:|:---:|
| 0 N | 54.500076 mm / 7.900382° | 35.847644 mm / 5.052139° |
| 5 N | 54.519729 mm / 8.027734° | 35.572192 mm / 5.114377° |

PI ON은 각 load 안에서 두 최대오차를 낮췄다. 5 N과 0 N을 비교하면 OFF에서 5 N은 두 오차가 모두 더 컸고, ON에서는 위치오차는 낮지만 회전오차는 높았다. 양쪽 지표가 함께 개선되는 load를 보이지 않아 1초 연장은 진행하지 않고 0 N을 진단 기준으로 유지했다. 어느 조건도 안정 연주 자세로 채택하지 않는다.

LH/어깨 contact는 모든 run에서 0이다. 0.5초 `human/RH:thumb3` 행은 0 N OFF/ON에서 50/71개, 5 N OFF/ON에서 41/98개였다. 이는 contact row 총수이며 고유 physics sample 수와 다르다. 행 수나 raw signed gap은 접촉력, 지지, 원인 또는 관통 깊이를 확정하지 않는다. 새 controller, gain 변경, 동적 rest length, 학습은 적용하지 않았다.

## 그림 32. 0.1초 초기 preload 및 0.5초 0/5 N OFF/ON 곡선

![0.1초 0/5/10/20 N preload와 0.5초 0/5 N OFF/ON의 기타 위치·회전 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1/artifacts/right_distal_strap_v1_curves.png)

색은 초기 load, 실선은 OFF, 파선은 ON이다. 0.1초에서는 기타 위치·회전 오차의 OFF/ON 곡선만 load별로 완전히 겹친다. 다른 humanoid 상태가 동일하다는 뜻은 아니다. rest length는 run 동안 고정되지만 strap law의 적용 tension은 움직임에 따라 달라질 수 있다.

## 재현과 provenance

이 플롯은 comparison/search audit, strap 입력, commands 및 각 run의 저장 report/trace/contact/control JSON을 읽는다. source geometry를 렌더링하지 않아 geometry asset hash는 포함하지 않는다. 기존 CLI 출력 파일은 덮어쓰지 않는다.

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
MUJOCO_GL=disable MPLCONFIGDIR=/tmp/right_distal_strap_v1_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_fixed_strap \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1 \
  --out-dir /tmp/right_distal_strap_v1_reproduction
```

[Plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1/artifacts/plot_manifest.json)은 comparison, strap inputs, validation/commands, 12개 saved run의 report/trace/contact/control JSON, plotter와 출력 PNG SHA-256을 기록한다. 기존 `comparison.json` 및 원본 helper는 보완 전 기록으로 그대로 보존하고, 현재 표와 그림은 `comparison_v2.json`을 사용한다. 이전 plotter와 PNG/manifest 생성본은 [artifacts_v1/source_plot_v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1/artifacts_v1/source_plot_v1)에 보존했다.
