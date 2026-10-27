# 오른손 초기 자세 탐색과 짧은 native 비교

작성일: 2026-10-06. 고정된 guitar +5 mm 초기 목표와 절대 strap rest length `1.1010801317960974 m`에서, 승인 범위 내 오른팔 12개 초기각만 탐색한 185개 static source-shape 평가와 네 개의 0.1초 native run을 정리한다. 왼팔 p08, fingers 42, torso 9, C02 하체, humanoid root, native gains/solver 및 나머지 held target은 유지됐다. feedback은 사용하지 않았다.

## static search와 0.1초 native 결과

Search key 이름은 호환성을 위해 `palm_neck`로 남아 있지만 검색 pair는 `RH:palm / G:body`다. nominal 3 mm unsigned source convex-hull distance로 정렬했고, 위쪽 방향 gate와 soft tie-break는 LH proxy에만 적용됐다. 오른손 +Z 제약은 새로 추가되지 않았다. 후보 행은 선택된 search IDs 180, 166, 149에 대응한다.

| 조건 | search ID | RH:palm–G:body unsigned source hull (t0 → 0.1 s, mm) | 최대 기타 위치오차 (mm) | 최대 기타 회전오차 (°) | native R_Shoulder × guitar 행 |
|:---|---:|---:|---:|---:|---:|
| reference | 0 | 100.306 → 106.523 | 6.878 | 1.521 | 0 |
| candidate_01 | 180 | 3.230 → 23.201 | 15.556 | 3.495 | 2 |
| candidate_02 | 166 | 7.044 → 27.712 | 15.542 | 3.492 | 2 |
| candidate_03 | 149 | 7.180 → 27.233 | 15.534 | 3.491 | 2 |

최소 초기 right-palm hull 거리를 가진 candidate_01도 세 후보 모두 0.1초 기타 오차가 reference보다 컸다. 가까운 초기 unsigned source-hull proxy는 지속적인 손 접촉이나 지지를 보여주지 않는다. 네 조건 모두 native LH/RH hand contact 행은 0이고, 각 조건의 `human/R_Hip` 접촉 행은 23이다. 각 후보의 native `human/R_Shoulder` 접촉 행 2개는 step 3 (`0.0125 s`)과 step 4 (`0.016667 s`)에 기록됐다. step 3 raw `initialOverlap`은 약 −4.092 mm이며, 이는 원시 field 그대로이며 보정된 관통 깊이로 환산하지 않는다. 접촉 행 수만으로 지지력이나 오차 변화 원인을 결론내릴 수 없다.

전체 240 Hz physics samples에서 계산한 LH palm up-dot proxy의 최소값은 네 조건 모두 0.926703584였다. 최대 native main-joint scalar-limit violation은 reference 0.02907°와 후보 약 0.03054°로 작은 위반이 남았다. 이 proxy와 source-hull 거리 모두 PhysX cooked-shape clearance 또는 해부학적 손 방향 인증이 아니다. `comparison_v2.json`에서 long-run count는 0이며 prefix 검증은 `not_applicable_no_long_runs`; 따라서 장시간 유지에 관한 결과는 없다. reference는 이전 OFF 기록과 exact reproduction 확인을 통과했다.

## 그림 24. 짧은 native 기타 오차와 관측된 어깨 접촉 시점

![Reference 및 세 right-arm candidate의 0.1초 기타 위치/회전 오차 곡선, 접촉 sample 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_support_v1/images/right_support_v1_native_curves.png)

곡선은 각 trial의 candidate guitar goal 대비 saved native trace다. 세 후보에서 관측된 R_Shoulder × guitar 행 시점을 표시했으나 인과관계·지지력·안정성을 뜻하지 않는다.

## 그림 25. 오른손 palm과 기타 neck/body의 저장 source geometry

![Reference 및 candidate_01의 t=0과 0.1초 저장 pose, RH:palm/G:body witness 구간](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_support_v1/images/right_support_v1_source_geometry_v2.png)

파랑은 기타 넥/body source shapes, 초록은 오른팔/손 source shape, 주황은 comparison에서 저장된 RH:palm/G:body hull witness segment다. 동일한 world bounds와 카메라에서 saved native body pose를 원본 source shape에 재구성한 CPU 도식이며 Isaac/PhysX 렌더, contact image, cooked clearance 인증이 아니다. unsigned hull 거리 감소만으로 접촉이나 물리적 지지를 주장하지 않는다.

## 입력, 검증 및 재생성

네 개의 native trial은 모두 0.1초다. `comparison_v2.json`은 source/PD/initial-state audits와 search 계약을 확인했고 reference raw record가 이전 OFF run을 재현한다. 이번 자료에는 long trial이 없어 장시간 prefix 확인 결과를 주장하지 않는다. 보존된 `comparison.json`은 초기 후처리 기록으로 남기며, 플롯과 현재 요약의 입력은 `comparison_v2.json`이다.

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
MUJOCO_GL=disable MPLCONFIGDIR=/tmp/right_support_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_right_support \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_support_v1 \
  --out-dir /tmp/right_support_v1_reproduction
```

재생성 CLI는 지정 output directory 안에 기본 `plot_manifest.json`을 생성한다. 결과 폴더에 보관한 최신 provenance manifest는 별도 이름의 `plot_manifest_v2.json`이다.

[최신 plot manifest v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_support_v1/plot_manifest_v2.json)은 comparison/search와 run JSON, 최신 helper source, config, human/guitar XML 및 XML 참조 37개 mesh, canonical output PNG의 SHA-256을 기록한다. 기존 [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_support_v1/plot_manifest.json)과 기존 `right_support_v1_source_geometry.png`는 이전 G:body-only 캡션을 담은 보존 표시 초안이다. 새 source geometry 그림은 `right_support_v1_source_geometry_v2.png`이며 curve PNG는 픽셀 동일 확인 후 기존 파일을 그대로 사용했다. `source_manifest.json`의 17개 검색 입력/코드 snapshot SHA 검증도 통과했다. source-shape 그림 생성은 저장된 pose를 재구성하며 native simulation을 실행하지 않는다. 다음 palm-position feedback 제안은 별도 중요 결정으로 사용자 승인 대기 중이다.
