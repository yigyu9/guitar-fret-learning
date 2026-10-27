# 오른손 distal 미세각 비교 결과

작성일은 2026-10-06이다. 37개 초기 source-query 뒤 기준+후보 3개를 0.1초 native 실행하고, 후보 02로 PI OFF/ON 6개 native run을 수행했다(총 10 native run). 이전 c01의 PI 6개 run은 기존 저장 결과에서 읽었으며 재실행하지 않았다. 그림·문서는 이 저장 자료만으로 만들었다.

## 초기 후보 3개와 0.1초 비교

후보는 승인된 오른팔 초기각 범위에서 오른쪽 팔꿈치·손목 distal 각만 바꿨다. 기준, 후보 01/02/03의 절대 strap rest length는 모두 1.1010801317960974 m이고 기타 목표는 +5 mm 위치다. 왼팔, proximal 오른팔, 손가락, Torso 9개, C02 하체, root, 기타 목표, PD/solver는 유지했다. 후보 02의 변화는 기존 c01에서 `R_Elbow_x +0.01 rad`, `R_Wrist_x −0.005 rad`다.

| 조건 | RH palm/body 초기 unsigned source-hull 간격 (mm) | 최대 기타 위치오차 (mm) | 최대 회전오차 (°) |
|---|---:|---:|---:|
| 기준 | 3.936732 | 6.876050 | 1.519890 |
| 후보 01 | 2.200303 | 6.879917 | 1.520723 |
| 후보 02 | 2.256704 | 6.872016 | 1.519281 |
| 후보 03 | 2.313745 | 6.872551 | 1.519351 |

네 조건 모두 source query gate를 통과했고 0.1초 실제 run에서 손·어깨 contact 행은 0이었다. 후보 02의 RH palm/body source-hull 간격은 가장 작은 후보는 아니며, 기타 오차 차이도 작다. 양의 hull 거리는 초기 근접 지표일 뿐 native clearance나 지지 인증이 아니다. 각 run에서 R_Hip contact는 23행(22개 physics sample)에 기록됐다.

## 후보 02와 이전 c01의 저장 PI OFF/ON run

두 초기 자세에 같은 기존 joint-hold PI 설정을 적용했다. 아래 값은 각 run의 최대 기타 위치·회전 오차다.

| 기간 | mode | 이전 c01 위치 (mm) | 이전 c01 회전 (°) | 후보 02 위치 (mm) | 후보 02 회전 (°) |
|---|---|---:|---:|---:|---:|
| 0.1초 | OFF | 6.876050 | 1.519890 | 6.872016 | 1.519281 |
| 0.1초 | ON | 6.876050 | 1.519890 | 6.872016 | 1.519281 |
| 0.5초 | OFF | 54.500076 | 7.900382 | 54.280113 | 7.851534 |
| 0.5초 | ON | 35.847644 | 5.052139 | 34.975339 | 4.871416 |
| 1.0초 | OFF | 143.645622 | 35.962199 | 143.674455 | 36.215772 |
| 1.0초 | ON | 121.298052 | 29.759157 | 76.099207 | 14.183879 |

후보 02의 1초 ON에서 arm raw drift는 14.280032°였고 보정은 212개 physics sample에서 포화됐다. 공통 native scalar-limit 위반 0.030294°도 남았다. LH/어깨 contact 행은 없었다. 1초 ON에서 RH thumb3는 187행·69개 physics sample(첫 0.350000초, 마지막 0.666667초), thumb2는 6행·4개 sample에 나타났다. contact 행이나 첫/마지막 관측은 힘·인과·연속 접촉·지지를 입증하지 않는다. 큰 기타 오차와 포화가 남아 안정 연주 자세로 채택하지 않는다.

## 그림과 재현

첫 그림은 이전 c01과 후보 02의 0.1/0.5/1초 저장 OFF/ON trace를 비교한다. 두 번째 그림은 현재 기준과 후보 02의 저장 t=0 및 t=0.1초 pose를 같은 축 범위와 view에서 source collision 형상으로 재구성했다. 패널 제목의 간격과 주황 witness 선·점은 `comparison_v3.json`의 unsigned source-hull 값 표시이며 추가 측정·clearance 인증이 아니다. 그림은 Isaac/PhysX native 렌더가 아니며 cooked collision clearance를 인증하지 않는다.

![c01과 후보 02의 저장 기타 오차 trace 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/artifacts/right_distal_fine_v1_curves.png)

![기준과 후보 02의 저장 source pose 재구성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/artifacts/right_distal_fine_v1_source_poses.png)

후보 02 초기각과 기존 0 N rest-length 진단을 다음 기준으로 유지한다. 다음 각도 선택은 승인된 기존 범위 안에서 접촉 관측과 관절·기타 drift를 함께 검토한다. 새 controller, gain, gate 또는 palm-position feedback은 추가하지 않았고 사용자 확인 전 적용하지 않는다. 최초 `comparison_v2` 산출물은 당시 정적 비교 입력 수집기가 하위 artifact manifest까지 포함했고, 그 시점 manifest 원본은 보존되지 않아 현재 입력 provenance로 사용하지 않는다. 현 `comparison_v3`는 실제 search/source/native raw/helper 입력만 해시하고 산출물·문서는 제외한다. plot manifest에는 그 입력과 내장 source hash, plot/helper 코드, 설정 연계 XML/mesh, 출력 PNG SHA-256을 기록한다. 최초 플로터/그림은 [v1 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/artifacts_v1/source_plot_v1), provenance 입력 수집 수정 전 버전은 [v2 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/artifacts_v2/source_plot_v2)에 남아 있다.

재생성 예시:

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
MUJOCO_GL=disable MPLCONFIGDIR=/tmp/right_distal_fine_v1_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_right_distal_fine \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1 \
  --previous-results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_v1 \
  --out-dir /tmp/right_distal_fine_v1_reproduction
```
