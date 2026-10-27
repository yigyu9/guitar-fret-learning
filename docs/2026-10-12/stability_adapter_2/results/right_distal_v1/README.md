# 오른손 distal 초기각 및 고정 joint-hold PI 진단

작성일: 2026-10-06. `right_distal_v1`의 65개 초기 source-query search, 0.1초 native comparison 4개와 동일 후보 초기각의 joint-hold PI OFF/ON 6개 저장 결과를 정리한다. 결과 판정은 안정적인 연주 자세 채택이 아니다.

## 초기각 선별과 0.1초 native 결과

초기 search 65개는 승인 범위(C02 ±0.3 rad와 native joint 범위의 교집합)에서 오른쪽 elbow/wrist 6개 목표만 바꾸고, proximal 조건 `ty015_sx010`을 유지했다. signed-negative gate, LH up-dot 및 local-neck 검사도 기존 조건 그대로 적용했다. 기준 대비 오른손바닥/G:body unsigned source-hull 거리는 아래처럼 줄었다. 왼손 p08, finger 42, torso 9, C02 하체, root, guitar +5 mm 고정 목표, PD/solver 및 absolute strap rest length 1.1010801317960974 m은 동일했다.

| 조건 | 초기 RH palm/G:body unsigned source hull (mm) | 최대 기타 위치오차 (mm) | 최대 회전오차 (°) | 최종 RH palm/G:body hull (mm) | hand/shoulder contact 행 |
|:---|---:|---:|---:|---:|---:|
| reference | 38.250 | 6.875701 | 1.519469 | 56.265 | 0 |
| candidate_01 | 3.937 | 6.876050 | 1.519890 | 21.824 | 0 |
| candidate_02 | 4.537 | 6.872301 | 1.519297 | 21.562 | 0 |
| candidate_03 | 5.797 | 6.876072 | 1.519909 | 23.099 | 0 |

짧은 0.1초 기록에서는 위치/회전 오차가 약 6.876 mm/1.52°였고 native hand·shoulder contact 행은 없었다. unsigned source 거리 감소는 접촉, 지지력, clearance 인증이 아니다.

## 기존 joint-hold PI를 적용한 6개 저장 run

같은 candidate_01 초기각에서 이미 승인된 joint-hold PI를 그대로 사용했다. OFF는 held target, ON은 기존 bounded actual-error correction이며 ±0.15 rad cap과 60 Hz update 설정을 바꾸지 않았다. `joint_hold/comparison.json`의 paired initial state, OFF short raw 재현 및 long-prefix checks는 모두 통과했다.

| 기간 | 모드 | 최대 기타 위치오차 (mm) | 최대 회전오차 (°) | 최대 arm raw drift (°) | 포화 physics sample 수 |
|:---:|:---:|---:|---:|---:|---:|
| 0.1 s | OFF | 6.876 | 1.520 | 6.619 | 0 |
| 0.1 s | ON | 6.876 | 1.520 | 5.832 | 8 |
| 0.5 s | OFF | 54.500 | 7.900 | 18.297 | 0 |
| 0.5 s | ON | 35.848 | 5.052 | 12.576 | 92 |
| 1.0 s | OFF | 143.646 | 35.962 | 20.981 | 0 |
| 1.0 s | ON | 121.298 | 29.759 | 14.280 | 212 |

포화 수는 240 Hz physics sample 기준이며 서로 독립인 60 Hz update 수가 아니다. 여섯 run 모두 native arm scalar-limit violation 0.030295°가 남았다. LH contact 행은 모두 0이고 LH palm up-dot proxy 최소는 여섯 조건에서 0.926703584였다. 1초 ON에서도 121.298 mm/29.759° 오차가 남아 안정 연주 자세로 채택하지 않는다.

### 관측된 contact 행의 제한

`decision.json`의 `human/RH:thumb3` 행은 0.5초 OFF/ON에서 50/71개(12/23 physics sample), 1초 OFF/ON에서 91/127개(34/44 sample)였다. ON의 `human/RH:thumb2`는 0.5초와 1초에 각각 1행이다. thumb3 첫 행은 OFF 0.454167 s/ON 0.358333 s, 1초 run에서 마지막 행은 두 모드 모두 0.591667 s였다. 첫/마지막 시각은 그 사이 연속 접촉을 뜻하지 않는다. contact 행 수나 raw signed gap은 지지력, 인과, 관통 깊이 판정이 아니다. `human/R_Hip` 행은 기록됐지만 하체 진단으로 해석하지 않았다.

다음 비교는 기존 승인 범위에서 candidate_01 초기각을 고정하고 strap preload 0/5/10/20 N의 matched short run을 보는 것이다. 이는 다음 탐색 방향이며 이 보고서에는 해당 실험 결과가 포함되지 않는다. 새 palm-position controller, gain 확대, 학습은 승인 전 적용하지 않는다. 이번 PI 결과도 후보 채택이나 안정성 성공을 뜻하지 않는다.

## 그림 30. 1초 joint-hold OFF/ON trace와 arm target 보정

![right_distal_v1의 1초 OFF/ON 기타오차, arm drift와 보정 포화 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_v1/artifacts/images/joint_hold_v1_1s_off_on.png)

## 그림 31. 저장 source geometry와 strap route

![right_distal_v1의 공통 시작 및 0.5초/1초 OFF/ON source pose 재구성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_v1/artifacts/images/joint_hold_v1_source_pose_comparison.png)

그림 파일 basename의 `joint_hold_v1`은 재사용한 `plot_joint_hold.py` 도구 이름이며 실험 run은 `right_distal_v1/joint_hold`의 6개 run이다. geometry 그림은 저장 pose의 source collision shapes를 CPU로 재구성한 것이며 Isaac/PhysX renderer 출력이나 cooked clearance 인증이 아니다. 손 normal 화살표의 해부학적 부호도 검증되지 않았다.

## 재현과 provenance

아래 명령은 저장된 `right_distal_v1/joint_hold` JSON, 기존 plot/replay helper 및 현재 geometry 자산을 읽어 그림과 manifest를 만든다. native physics를 실행하지 않는다.

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
MUJOCO_GL=disable MPLCONFIGDIR=/tmp/right_distal_v1_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_joint_hold \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_v1/joint_hold \
  --out-dir /tmp/right_distal_v1_reproduction
```

[Plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_v1/artifacts/plot_manifest.json)은 six-run JSON, plotting/replay helper, config, human/guitar XML, XML에서 참조하는 37개 mesh 및 두 PNG의 SHA-256을 기록한다.
