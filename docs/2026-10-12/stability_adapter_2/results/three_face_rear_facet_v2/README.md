# 세 면 지지: 엄지 후면 facet 후보 V2

작성일: 2026-10-08. 이 문서는 저장된 source geometry 후보 검색과 승인 brief에 따른 정적 산출물을 기록한다. 검색은 네 후보를 완료했으나 **네 후보 모두 거절**, 승인 0, native 초기화 0, physics step 0이다. source-only 그림과 manifest는 아래 경로에 저장한다.

## 선택된 source 면과 범위

초기 LH 엄지의 활성 source triangle 중 G-root +Z 방향 내적이 0.75보다 큰 367개를 대상으로 가장 넓은 면을 선택했다. 선택 triangle은 index 323, 면적 4.433116826 mm², 초기 outward normal은 G에서 `(-0.050917, 0.559098, 0.827536)`이다. 이는 선택 규칙에 따른 source 면이며 해부학적 엄지 패드나 cooked PhysX 면이라는 뜻이 아니다. Native feature anchor는 별도 값으로 저장되어 있으며, 이 선택 centroid와 동일시하지 않는다.

엄지 대표점은 finite patch 밖에 남았으며, 각 대표점이 후면 patch 경계 밖으로 벗어난 거리는 9.21–10.55 mm다. source triangle 면적·법선·점 위치는 정적 형상 정보다. 그림의 Gx/Gy 및 millimeter 좌표는 analysis JSON에서 읽으며, source common radius는 물리적 깊이가 아니다. λ는 힘을 나타내지 않는다.

## 후보 비교

| 후보 | thumb radius (rad) | thumb target error (mm) | palm target error (mm) | source intersection 수 | 판정 |
|---|---:|---:|---:|---:|---|
| `thumb_0.1_clear_0.0003` | 0.1 | 14.047475 | 5.701879 | 3 | 거절 |
| `thumb_0.1_clear_0.0007` | 0.1 | 13.682516 | 4.772728 | 4 | 거절 |
| `thumb_0.2_clear_0.0003` | 0.2 | 14.499266 | 4.270202 | 2 | 거절 |
| `thumb_0.2_clear_0.0007` | 0.2 | 12.609899 | 1.810477 | 1 | 거절 |

마지막 후보의 palm 목표 오차 1.810477 mm는 네 후보 중 가장 작지만, source 교차가 남고 기타 조건을 충족하지 않아 승인되지 않았다. `thumb_0.1_clear_0.0007`의 palm QP는 `success=false`였지만, feasible distance bound 구간 `[4.281297407, 4.281297552] mm`로 판정됐다. 이는 feasible bound 판정이지 최적해 주장이나 후보 승인 근거가 아니다. 후보의 모든 거절 사유와 원 solver status는 proposal/analysis 원자료를 따른다.

V1은 첫 후보의 partial 기록 뒤 두 번째 후보 거리 QP 수치 중단으로 exit 1을 반환했다. 그 첫 후보의 q, anchor, source intersections는 V2 재실행 기록과 exact 일치한다. V2는 기존 81개 절대 target, 나머지 64개 관절, G 좌표계 및 LA 조건을 유지해 네 완료 후보를 기록했다. 복구 전 검수와 V1 보존 검수는 완료됐다. 이 결과 summary와 실제 새 PNG의 최종 독립 검수는 완료했다(C/W/S 없음).

## 그림과 재현

![후면 facet source 후보의 대표점·목표와 paired target-error 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/artifacts/rear_facet_source_comparison.png)

그림은 CPU source geometry의 정적 비교이며 native Gym 렌더·실제 접촉·cooked 형상·해부학적 지지 인증이 아니다. 이번 후보를 위한 새 5초 영상은 생성하지 않았다. 기존 저장 영상은 이번 후보의 경과를 나타내지 않으므로 여기에 반복 삽입하지 않는다.

```bash
python stability_adapter_2/make_rear_facet_artifacts.py
```

Producer는 `artifact_brief.json`, `analysis.json`, `proposal.json`, 실행/복구 검수 자료, 분석이 명시한 입력 SHA closure, producer 자체와 NanumGothic font를 실행 전후 대조한다. 출력이 이미 있으면 덮어쓰지 않고 중단한다. 생성 PNG와 SHA mapping은 `artifacts/artifact_manifest.json`에 기록한다.

## 파일

- 분석: [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/analysis.json)
- 승인 brief: [artifact_brief.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/artifact_brief.json)
- 검색 proposal: [proposal.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/proposal.json)
- 산출물 producer: [make_rear_facet_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_rear_facet_artifacts.py)
- 생성 manifest: [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/artifacts/artifact_manifest.json)
- 최종 독립 검수: [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/review.md)

그림 왼쪽은 넥 후면의 왼쪽 경계를 국소 확대했다. 같은 XY 목표는 한 기호로 표시하지만 GZ 목표는0.3/0.7mm 여유별로 다르며 오른쪽 오차는3차원 norm이다. 모든초기/후보점을표시하고label leader를분리했다. [root의 실제8거리구간 재계산](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/interval_data_verification.json)에서 source witness의hull/patch포함과상·하한을독립확인했다. [다음미실행catalog](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_FACET_CATALOG_PLAN.md:1)을진행한다.

검색9.785139초/exit0/native0, 그림생성5.638161초/exit0/native0을완료했다. [그림실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/artifact_execution.json)과전후11367입력/PNG SHA를manifest에기록했다. root는실제PNG의label/범례/좌표범위를확인했다. 전체기타초기복원·지속세면지지·연주안정화는미완료다.

[독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/review.md)는실제8witness·source교차LP·같은목표/초기각·summary와PNG/문서·입력SHA를대조했다. Source기하검증과actualGym접촉/지속지지는구별한다.

root의 37개 source/실행/거리/보존 검사를 완료했다. [최종 보존 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/final_verification.json)와 source_final에 현재 소스·문서를 봉인한다. 전체 목표는 계속 진행한다.
