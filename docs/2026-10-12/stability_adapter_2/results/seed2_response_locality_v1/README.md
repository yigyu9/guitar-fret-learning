# Seed 2 음의 방향과 결합 heldout 응답

2026-10-08에 새 초기화로 세 조건을 각각 5초 실행했다(3 init/3600 physics step). 별도 과거 결과 네 개는 그림의 저장 참조로만 다시 사용했다. 모든 조건에서 시작 81개 관절 자세, 기타 목표 위치·회전, 절대 strap 길이 1.1018469719600776 m, PD와 solver는 공통이다. root와 하체는 물리 고정, 기타는 중력 아래 자유 상태, self-collision은 ON이고 몸통 9개 목표를 유지했다. 최종 66개 제어 인터페이스는 유지됐으며 기타 고정 부착·상태 덮어쓰기나 runtime 기타 feedback은 없었다.

새 실행 두 개는 각각 `L_Shoulder_y` 또는 `L_Wrist_z` 제출 목표에 −0.002 rad를 요청했다. 세 번째는 이전 heldout의 6축 목표 편차를 절반 요청했다. 실제 float32 목표비율의 최소제곱 추정은 0.500009933989였고 축별 비율은 완전히 같지 않다. 세 새 실행의 기타 step 0–24, 총 25개 위치/자세 관측(24 physics step)은 저장된 기준과 exact 일치했다.

| 조건 | 5초 최대 p (mm) | 최대 q (°) | 종료 p (mm) | 종료 q (°) |
|---|---:|---:|---:|---:|
| 저장 기준 | 26.772807 | 8.323296 | 23.188748 | 7.413329 |
| 저장 +Shoulder Y | 27.568926 | 8.307683 | 23.497272 | 7.527566 |
| 신규 −Shoulder Y | 26.684900 | 8.116260 | 22.883315 | 7.338493 |
| 저장 +Wrist Z | 26.814406 | 8.191182 | 23.136911 | 7.415853 |
| 신규 −Wrist Z | 26.725074 | 8.377872 | 23.233159 | 7.370746 |
| 저장 full heldout | 26.774777 | 8.124454 | 23.108978 | 7.388837 |
| 신규 half heldout | 26.938437 | 8.182551 | 23.198611 | 7.400524 |

−Shoulder Y는 기준 대비 최대·종료 위치와 회전 오차가 모두 작아 유망한 진단 후보로 남았다. −Wrist Z의 최대 회전 오차는 기준보다 컸고 half heldout의 최대 위치 오차도 커졌다. 이 세 조건으로 안정성 성공이나 새 설정 채택을 선언하지 않는다.

![세 신규 조건과 네 저장 참조의 기타 오차 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts/seed2_response_locality_curves.png)

실선은 새 −Shoulder Y, −Wrist Z, half heldout 3회이고 점선은 저장 기준, 저장 positive 축 probe 두 개, 저장 full heldout이다. 모든 곡선은 저장된 기타 위치 오차(mm)와 world SO(3) 회전 오차(도)의 전체 0–5초 sample이다. 과거 네 참조는 새 native 실행 수에 포함되지 않는다.

![세 신규 run의 실제 Gym 손 카메라 시작·종료 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts/seed2_response_locality_hands_camera.png)

2×3 배열의 각 열은 새 조건이며 윗행은 step 0, 아랫행은 step 1200/t=5초다. 실제 Isaac Gym 손 카메라에서 저장한 frame을 조합했으며 run별 영상은 151 frame, 30 fps, ffprobe stream duration 5.033333초다. 이는 MuJoCo나 source geometry 재구성이 아니다. 각 run의 [initial values와 full capture](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native>) 및 초기값 파일: [−Shoulder Y](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native/negative_shoulder_y/initial_values.json>), [−Wrist Z](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native/negative_wrist_z/initial_values.json>), [half heldout](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native/half_heldout/initial_values.json>).

세 run의 초기 여섯 부위 source 접근 통합 조건은 충족하지 않았다. 기준 source hull gap은 thumb3 5.831 mm, index3 1.459 mm, middle3 약 0.000007 mm, ring3 3.858 mm, pinky3 2.447 mm, palm 3.842 mm다. 이 간격은 cooked clearance 인증이 아니다. 세 신규 run 모두 thumb/index/middle의 positive raw lambda가 step 1200까지 관측됐고, palm의 마지막 positive step은 각각 118/124/123, 마지막 접촉행은 134/133/134였다. R_Hip named-body contact의 positive row는 각 run에서 1200개의 고유 step에 기록됐고 RH hand–guitar contact 행은 0개였다. 이는 인과나 하중·지지력·면을 판별하지 않는다. Raw lambda는 N이 아니고 sample 기록은 연속 contact 또는 stability 성공을 증명하지 않는다. `stability_success`는 세 run 모두 false다.

`L_Shoulder_y`와 `L_Wrist_z` 두 축의 양·음 endpoint secant로 만든 6×2 응답행렬은 0.1초 창에서 rank 0, 마지막 1초 평균에서 rank 2/condition 4.805(잠정 0.1 m 회전 lever)였다. 세 신규 run은 기준과 step 0–24의 25개 관측(24 physics step)에서 기타 위치·자세가 exact 일치했다. 따라서 0.1초 창의 영 secant는 이 저장 구간의 관측이지 일반적인 0.1초 물리 응답을 뜻하지 않는다. half-heldout에서 마지막 1초 old-J 예측 잔차는 0.481436 mm/0.084446°였고 목표 alpha 보간 잔차는 0.104851 mm/0.014643°였다. 이 회전 잔차는 world 회전오차 벡터 잔차의 norm을 도로 환산한 값이지 quaternion geodesic이 아니다. 이 secant는 runtime Jacobian이나 최종 66축 제어 가능성 인증이 아니다.

다음은 [SEED2_SHOULDER_GUITAR_FEEDBACK_PLAN](</home/ajou/yigyu/3/stability_adapter_2/SEED2_SHOULDER_GUITAR_FEEDBACK_PLAN.md>)에 기록된 후속 방향이며 아직 실행하지 않았다. 상세 분석은 [analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/analysis.json>), brief는 [artifact_brief.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifact_brief.json>)이다.

각 신규 run의 영상: [−Shoulder Y hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native/negative_shoulder_y/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native/negative_shoulder_y/whole_body.mp4>); [−Wrist Z hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native/negative_wrist_z/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native/negative_wrist_z/whole_body.mp4>); [half heldout hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native/half_heldout/hands.mp4>) / [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native/half_heldout/whole_body.mp4>). Historical curve references are [previous probe analysis](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/probe_analysis.json>) and [previous heldout analysis](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/heldout_analysis.json>).

저장 자료 후처리 재현 예:

```bash
MPLCONFIGDIR=/tmp/seed2_response_locality_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python \
/home/ajou/yigyu/3/stability_adapter_2/make_seed2_locality_artifacts.py \
--out-dir /tmp/seed2_response_locality_reproduction
```

출력은 비어 있거나 새 경로여야 한다. [artifact manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts/artifact_manifest.json>)는 실제 입력 21개와 결과 SHA를 기록하며 전후 입력 hash가 같았다. 실행 명령·환경·걸린 시간·exit code는 [artifact_execution.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifact_execution.json>), stdout/stderr는 [artifact_execution.log](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifact_execution.log>)에 있다. 첫 저장자료 plot 시도(v1)는 exactness 필드명을 잘못 참조해 렌더 전에 종료됐으며 producer·로그를 [v1 archive](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts_attempt_v1>)에 보존했다(0 native/0 physics step). 보존 producer SHA e0d922a92a108c95d1a26f430015dabbbed55f663ee03e523549a5ab919d1a12는 시도 metadata와 일치한다. 다음 후처리(v2)는 처음 성공했지만 step 0–24 exactness boolean을 true여야 하는 그림 통과조건으로 사용했다. 편집 직전 producer·출력·manifest·로그와 입력 closure 검증을 [v2 archive](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts_attempt_v2>)에 보존했다(0 native/0 physics step). 현재 canonical producer는 boolean 형식만 검사하고 그 값이 false여도 그림 생성을 허용한다. canonical PNG 두 개는 v2 출력과 byte-identical이다. 최종 기록은 [검증](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/final_verification.json>), [artifact inventory](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifact_inventory.json>), [source final manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/source_final_manifest.json>)를 참고한다.
