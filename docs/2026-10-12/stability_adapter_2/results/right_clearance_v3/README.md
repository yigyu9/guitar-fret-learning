# 오른팔 초기각과 기타 주변 source 거리 진단

작성일: 2026-10-06. 이번 `right_clearance_v3` 입력의 10개 source-query recipe(기준 1개와 후보 9개) 및 native 0.1초 비교 4개(기준과 통과 후보 3개)를 요약한다. 이 보고서와 그림의 생성 과정에서는 추가 native 실행이나 설정 변경을 하지 않았다.

## 고정 조건과 source-query 선별

탐색은 승인된 초기각 범위 안에서 오른팔 12개 목표만 바꿨다. 왼팔 p08, finger 42, torso 9, C02 하체, humanoid root, guitar +5 mm goal, PD/solver와 absolute strap rest length 1.1010801317960974 m는 유지했고 feedback은 꺼져 있었다.

10개 recipe 중 기존 signed-negative gate가 후보 6개를 제외했고, 통과한 후보 3개와 reference만 0.1초 native diagnostic으로 이어졌다. 입력에서 RH palm/G:body unsigned source-hull 거리와 R_Shoulder/G:body 거리는 다음과 같다.

| 조건 | RH palm/G:body source hull (mm) | R_Shoulder/G:body source hull (mm) | negative pair 수 |
|:---|---:|---:|---:|
| reference | 100.306 | 35.395 | 0 |
| ty015_sx010 | 38.250 | 5.565 | 0 |
| ty0175_sx015 | 20.827 | 2.663 | 0 |
| ty0175_sx0175 | 12.065 | 2.910 | 0 |

이 unsigned QP source-hull 거리와 20 mm cutoff signed source query는 서로 다른 proxy다. signed-negative gate를 완화하지 않았으며, 양수 hull 거리만으로 native clearance나 접촉을 인증하지 않는다. 이전 v1 boolean 저장 실패 및 v2 중간 7-query 시도는 별도 이력으로 보존하며, 이번 10개 recipe나 4개 native run에 합산하지 않았다.

## 저장된 native 결과

| 조건 | 최대 위치 오차 (mm) | 최대 회전 오차 (°) | native hand contact 행 | R_Shoulder × guitar 행 | 종료 RH palm/G:body source hull (mm) |
|:---|---:|---:|---:|---:|---:|
| reference | 6.878064 | 1.520538 | 0 | 0 | 106.523 |
| ty015_sx010 | 6.875701 | 1.519469 | 0 | 0 | 56.265 |
| ty0175_sx015 | 9.867470 | 2.467039 | 0 | 2 | 40.294 |
| ty0175_sx0175 | 8.581359 | 2.157702 | 0 | 2 | 32.353 |

`ty015_sx010`과 reference의 차이는 2.363 µm 및 0.001069°다. 이 차이만으로 실질적인 개선이라고 판정하지 않는다. 두 `ty0175` 조건에서 shoulder contact 행이 각각 두 개 관찰됐으나, 행 수만으로 원인이나 지지를 입증하지 않는다. LH/RH hand contact 행은 네 run 모두 0이며 `human/R_Hip` 행은 각 23개로 관찰 전용이다. 하체 진단을 재개한 결과가 아니다. 네 run의 최소 LH palm up-dot sample은 모두 0.926703584다.

모든 run은 24 physics step, 0.1초다. 초기 RH palm source gap이 종료 때 네 조건 모두 증가했으며, 두 거리 proxy와 짧은 native 기록은 안정 유지 성공이나 후보 채택을 뜻하지 않는다. 연장 실행 및 최종 후보 선택은 하지 않았다.

## 그림 28. 네 native run의 기타 위치·회전 오차 trace

![reference와 통과 후보 3개의 0.1초 저장 native error 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_clearance_v3/artifacts/right_clearance_v3_native_curves.png)

보라색 step 3/5 선은 두 `ty0175` run에서 관찰한 R_Shoulder × guitar raw contact 행 시점이다. marker는 인과관계나 지지 여부를 뜻하지 않는다. 각 run은 고정된 guitar target 대비 최대 오차를 범례에 표시한다.

## 그림 29. reference와 ty015_sx010의 시작·종료 source geometry

![reference와 ty015_sx010의 t=0 및 0.1초 저장 source-shape 재구성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_clearance_v3/artifacts/right_clearance_v3_source_poses.png)

초록은 오른팔/손, 파랑은 기타 body/neck, 주황은 RH palm/G:body source-hull witness다. witness는 가독성을 위해 source surface 위에 겹쳐 표시했으므로 실제 앞뒤 가림 관계를 나타내지 않는다. 두 run의 시작 및 종료 저장 pose를 동일한 world bounds와 view에서 CPU로 재구성했다. native renderer 출력이나 cooked-clearance 인증이 아니다.

## 재현과 provenance

재생성은 `comparison.json`, `search/search.json`, 각 run의 report/trace/states/contacts, plotting/replay helper 및 source geometry 자산을 읽는다. native physics 실행은 포함하지 않는다. 기존 CLI 출력은 덮어쓰지 않는다.

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
MUJOCO_GL=disable MPLCONFIGDIR=/tmp/right_clearance_v3_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_right_clearance \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_clearance_v3 \
  --out-dir /tmp/right_clearance_v3_reproduction
```

[현재 plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_clearance_v3/artifacts/plot_manifest.json)은 raw JSON, helper, config, human/guitar XML, 37개 mesh와 두 PNG의 SHA-256을 기록한다. 이전 witness 가시성 수정 전의 그림·manifest와 정확히 일치하는 plotter snapshot은 보존용 [artifacts_v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_clearance_v3/artifacts_v1)에 두었다. 현재 그림은 `artifacts/`에 별도로 생성했다.
