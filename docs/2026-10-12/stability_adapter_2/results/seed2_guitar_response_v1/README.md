# Seed 2 기타 응답의 국소 방향 비교

2026-10-08에 기준 실행, 왼팔 6개 단일 축 probe, 결합 heldout을 각각 새로 5초 실행했다. 총 8회 초기화와 9,600 physics step이며 저장 분석은 probe 8개 계약과 heldout 8개 계약을 통과했다. 시작 관절 자세, 기타 목표 위치·회전, 절대 strap 길이 1.1018469719600776 m, PD·solver는 공통이다. 기준의 처음 24 step 다섯 raw 배열은 이전 Seed 2 저장 실행과 exact였고, 몸통 9개 actual native scalar 좌표의 초기 q 대비 전체 조건 최대 편차는 4.228°였고, torso PD 목표는 held였다. 여섯 probe는 `L_Shoulder_x/y/z`, `L_Wrist_x/y/z` 중 하나의 초기 제출 목표에 +0.002 rad를 요청했다. 여덟 조건의 첫 0.1초 최대 위치/회전 오차는 모두 5.107730 mm/0.969008°였다. heldout은 이 순서대로 약 ±0.001 rad를 요청했다. 실제 float32 목표 차이는 일부 축에서 −0.00100004673 rad처럼 요청값과 미세하게 다르며, 자세한 요청·실제 차이는 [heldout 선택 기록](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/heldout_selection.json>)에 있다. 실험은 초기 목표만 바꾸며 runtime 기타 feedback이나 학습은 없다.

| run | 5초 최대 기타 위치 (mm) | 5초 최대 기타 회전 (°) | 종료 위치 (mm) | 종료 회전 (°) |
|---|---:|---:|---:|---:|
| 기준 | 26.772807 | 8.323296 | 23.188748 | 7.413329 |
| Shoulder X +0.002 | 27.259656 | 8.269204 | 23.387493 | 7.485885 |
| Shoulder Y +0.002 | 27.568926 | 8.307683 | 23.497272 | 7.527566 |
| Shoulder Z +0.002 | 26.951441 | 8.187234 | 23.363260 | 7.478110 |
| Wrist X +0.002 | 27.246571 | 8.252361 | 23.370459 | 7.452799 |
| Wrist Y +0.002 | 27.280403 | 8.266845 | 23.415952 | 7.443227 |
| Wrist Z +0.002 | 26.814406 | 8.191182 | 23.136911 | 7.415853 |
| 결합 heldout | 26.774777 | 8.124454 | 23.108978 | 7.388837 |

단일 축 여섯 조건은 모두 기준보다 최대 위치 오차가 컸다. 결합 heldout은 최대 위치 오차가 기준보다 0.001970 mm 늘고 최대 회전 오차는 0.198842° 줄었다. 따라서 heldout은 회전 응답을 살펴볼 진단 후보로만 남기며 안정화 성공이나 새 자세 채택으로 보지 않는다. 모든 조건에서 기타 이탈은 남았다.

![기준, 여섯 단일 축 probe, 결합 heldout의 기타 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifacts/seed2_guitar_response_curves.png)

그림은 저장된 trace의 기타 위치 오차(mm)와 world SO(3) 오차(도)를 0–5초 전체에서 보여준다. 점선은 heldout이다. 두 오차 곡선은 성공 기준이나 초기 조건 검사가 아니다.

![기준, Wrist Z probe, heldout의 실제 Gym 손 카메라 이미지](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifacts/seed2_guitar_response_hands_camera.png>)

2×3 이미지는 실제 Isaac Gym 손 카메라에서 저장한 프레임이다. 윗행은 각 run의 step 0, 아랫행은 step 1200/t=5초이며 각 영상은 151 frame, 30 fps로 저장됐다. 이는 MuJoCo 렌더가 아니며 strap mesh는 카메라에 나타나지 않는다. root와 하체는 물리 고정, 기타는 중력 아래 자유 상태, self-collision은 ON이었다. torso 9개 목표와 66개 최종 제어 인터페이스, PD/solver는 공통이며 기타 목표를 고정 부착하거나 상태를 덮어쓰지 않았다. 다른 5개 단일 축 조건의 영상도 아래 링크에 있다.

선형 응답 분석의 0.1초 창 rank는 0이었다. 마지막 1초 창은 rank 6이지만 condition number 56,647이고 0.1 m 회전 lever를 가정한 진단값이다. heldout 선형 예측 잔차는 1초에서 0.423612 mm/0.146700°였고, 5초에서 0.792644 mm/0.155114°였다. 회전 잔차는 world 회전오차 벡터 잔차의 norm을 도 단위로 바꾼 값이다. 마지막 1초 평균 잔차 0.789333 mm/0.155463°는 기준 대비 실제 변화 벡터 0.152794 mm/0.028116°보다 크다. 이 국소 fit은 역행렬 runtime 제어기로 채택할 근거가 아니다.

초기 여섯 부위의 통합 source 접근 조건은 8개 run 모두 충족하지 않았다. 예를 들어 기준의 초기 source hull gap은 LH thumb3 5.831 mm, index3 1.459 mm, middle3 약 0.000007 mm, ring3 3.858 mm, pinky3 2.447 mm, palm 3.842 mm다. 이는 cooked PhysX clearance나 접촉 인증이 아니다. heldout의 RH hand–guitar 접촉 행은 0개였다. LH thumb3/index3/middle3의 마지막 양의 raw lambda는 모두 step 1200이었다. LH named-body 접촉행과 raw lambda는 저장됐지만, 손바닥은 양의 raw lambda가 step 117에서 마지막으로 나타났고 마지막 접촉행은 step 135였다. raw lambda는 뉴턴 힘이 아니며 named-body 접촉은 넥 면별 또는 연속 지지를 입증하지 않는다. 모든 run의 `stability_success`는 false다. 다음 진단은 [SEED2_RESPONSE_LOCALITY_PLAN](</home/ajou/yigyu/3/stability_adapter_2/SEED2_RESPONSE_LOCALITY_PLAN.md>)에 정리돼 있으며 아직 실행하지 않았다.

각 native run의 초기값은 [`initial_values.json`](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/base/initial_values.json>)에서 확인할 수 있다: [base](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/base/initial_values.json>), [Shoulder X](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/shoulder_x/initial_values.json>), [Shoulder Y](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/shoulder_y/initial_values.json>), [Shoulder Z](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/shoulder_z/initial_values.json>), [Wrist X](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/wrist_x/initial_values.json>), [Wrist Y](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/wrist_y/initial_values.json>), [Wrist Z](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/wrist_z/initial_values.json>), [heldout](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/heldout/initial_values.json>).

각 run의 저장 영상: [base hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/base/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/base/whole_body.mp4>); [Shoulder X hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/shoulder_x/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/shoulder_x/whole_body.mp4>); [Shoulder Y hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/shoulder_y/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/shoulder_y/whole_body.mp4>); [Shoulder Z hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/shoulder_z/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/shoulder_z/whole_body.mp4>); [Wrist X hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/wrist_x/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/wrist_x/whole_body.mp4>); [Wrist Y hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/wrist_y/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/wrist_y/whole_body.mp4>); [Wrist Z hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/wrist_z/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/wrist_z/whole_body.mp4>); [heldout hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/heldout/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native/heldout/whole_body.mp4>).

후처리 재현 명령은 아래와 같다. 출력 폴더는 비어 있거나 새 경로여야 한다.

```bash
MPLCONFIGDIR=/tmp/seed2_guitar_response_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python \
/home/ajou/yigyu/3/stability_adapter_2/make_seed2_guitar_response_artifacts.py \
--out-dir /tmp/seed2_guitar_response_reproduction
```

[artifact manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifacts/artifact_manifest.json>)는 입력·출력 SHA와 카메라 프레임 대응을 기록한다. 실행 stdout은 [artifact_execution.log](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifact_execution.log>), 실행 정보는 [artifact_execution.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifact_execution.json>)에 있다. source와 직접 읽은 분석/초기값/카메라 파일의 SHA는 생성 전후 일치했다. 이번 산출물 생성 작업은 저장자료 후처리이며 추가 native trial은 없었다. 각 실제 Gym 영상은 t=0–5초의 151 frame을 30 fps로 저장해 ffprobe에서 확인한 container duration은 5.033333초다.
