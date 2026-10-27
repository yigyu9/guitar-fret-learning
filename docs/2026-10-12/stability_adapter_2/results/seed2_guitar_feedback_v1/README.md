# Seed 2 기타 오차 feedback 진단

2026-10-08에 새로 초기화한 세 조건을 각각 5초 실행했다(3 init/3600 physics step). 이전 저장 기준 두 조건은 그림 비교용 참조이고 이번 실행 수에 포함하지 않는다. 세 신규 run의 초기 자세, 기타 목표 위치·회전, 절대 strap rest length 1.1018469719600776 m, PD·solver는 같다. root와 하체는 물리 고정이고 기타는 중력 아래 자유 상태이며 self-collision은 ON이다. 몸통 9축 목표를 유지했고 최종 66축 제어 인터페이스도 보존했다. 기타 고정 부착, 기타 상태 덮어쓰기, 학습은 없었다.

| 저장 곡선 / 신규 조건 | 목표 변화 | 5초 최대 위치 오차 (mm) | 최대 회전 오차 (°) | 종료 위치 오차 (mm) | 종료 회전 오차 (°) |
|---|---:|---:|---:|---:|---:|
| 저장 기준 | — | 26.772807 | 8.323296 | 23.188748 | 7.413329 |
| 저장 Shoulder Y −0.002 | −0.002 rad | 26.684900 | 8.116260 | 22.883315 | 7.338493 |
| 신규 constant 0.008 | Shoulder Y −0.008 rad | 25.929259 | 7.900654 | 22.182777 | 7.114842 |
| 신규 constant 0.016 | Shoulder Y −0.016 rad | 25.280921 | 7.753357 | 21.989056 | 7.096635 |
| 신규 guitar feedback | actual guitar error feedback | 26.950260 | 8.210682 | 21.953773 | 7.096483 |

표의 constant 0.008 종료 위치 오차는 원자료 22.182776609 mm를 소수점 여섯째 자리 기준으로 반올림한 22.182777 mm다. 위치 오차는 기타 목표 대비 world 위치 오차 norm이고 회전 오차는 world SO(3) log norm이다. 세 조건 모두 첫 0.1초의 최대 오차는 5.107730 mm / 0.969008°였고, 기준 원자료와 step 0–24의 25개 위치·자세 관측이 exact 일치했다. 이 exactness는 기록된 관측이지 그림 생성 통과조건이 아니다.

![저장 기준 두 개와 신규 세 조건의 기타 오차 및 Shoulder Y 제출 목표 offset](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/artifacts/seed2_guitar_feedback_curves.png)

위 두 패널은 0–5초 기타 위치(mm)·회전(도) 오차다. 세 번째 패널은 신규 run만의 `L_Shoulder_y` 목표 offset을 요청값과 실제 float32 제출값으로 표시한다(mrad, 300개 60 Hz update). constant 조건의 computed rate는 실제 목표에 적용되지 않았고 그 두 조건의 목표 offset은 일정했다. 따라서 이 패널은 계산된 rate가 적용된 rate를 뜻하지 않는다. Feedback run은 0에서 시작해 −0.016 rad 경계에 도달했고 180 update가 bound에 기록됐다. feedback 요청 rate는 최대 0.1051752932474102 rad/s였고, rate-limited 요청은 최대 0.008 rad/s였다. 실제 float32 목표 변화율 최대는 0.008003711700439453 rad/s다. 상수 조건에서는 계산 rate가 적용되지 않았다.

![신규 세 조건의 실제 Isaac Gym 손 카메라 step 0 및 1200](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/artifacts/seed2_guitar_feedback_hands_camera.png)

각 열은 신규 조건이며 윗행은 step 0, 아랫행은 step 1200/t=5초다. 이는 실제 Isaac Gym 카메라 저장 프레임이고 MuJoCo/source geometry 재구성이 아니다. 각 영상은 151 frame, 30 fps이며 ffprobe duration은 5.033333초다. 각 run은 실제 물리 5초 구간(step 0–1200)을 포함한다. [0.008 손 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/constant_0p008/hands.mp4>) · [0.008 전신 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/constant_0p008/whole_body.mp4>) · [0.016 손 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/constant_0p016/hands.mp4>) · [0.016 전신 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/constant_0p016/whole_body.mp4>) · [feedback 손 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/guitar_feedback/hands.mp4>) · [feedback 전신 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/guitar_feedback/whole_body.mp4>). 조건별 [initial values](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/constant_0p008/initial_values.json>), [초기 −0.016](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/constant_0p016/initial_values.json>), [feedback](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/guitar_feedback/initial_values.json>)와 hands/whole-body 영상 링크도 함께 보존했다.

초기 여섯 손 부위의 통합 source 접근 조건은 세 신규 조건 모두 미달이고, 이는 cooked clearance 판정이 아니다. 각 조건에서 thumb3/middle3의 positive raw lambda 마지막 step은 1200, index3은 각각 87/95/255, palm은 123/124/124였다. `R_Hip` positive contact는 각 run 1200개 고유 step에서 기록됐고 RH hand–guitar contact는 0행이다. 이 named-body 기록은 넥 면·연속 지지·힘을 판별하지 않는다. raw lambda는 N 단위가 아니며 contact 표본은 접촉 유지나 안정성 성공을 증명하지 않는다. `stability_success`는 세 run 모두 false다. 몸통 9축 목표는 유지했지만 실제 몸통 scalar 좌표 편차는 최대 약 4.22°였다.

상수 −0.016 rad는 진단상 비교적 낮은 오차를 보였고 feedback은 종료 오차가 낮았지만 최대 위치 오차는 저장 기준과 −0.016 조건보다 컸다. 어느 조건도 안정 연주 성공이나 최종 채택으로 판정하지 않는다. 다음 계획은 [Seed 2 support-pose warm start](</home/ajou/yigyu/3/stability_adapter_2/SEED2_SUPPORT_POSE_WARMSTART_PLAN.md>)이며 아직 실행하지 않았다.

상세 저장 분석은 [analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/analysis.json>), 조건 brief는 [artifact_brief.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/artifact_brief.json>), artifact 입력·출력 SHA는 [manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/artifacts/artifact_manifest.json>)에 기록했다. [실행 기록](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/artifact_execution.json>)에 명령·환경·exit code가 있고, [stdout log](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/artifact_execution.log>)에는 성공적으로 생성된 세 artifact 경로가 있다. 저장자료 후처리 producer는 21개 입력의 전후 SHA를 확인했고 native call은 없었다. 실행 시간은 metadata 조립 오류로 보존되지 않아 기재하지 않았다.

새 그림 producer는 이전 locality producer를 sealed `source_final_manifest.json`과 대조해 SHA 일치를 확인한 후 복사·수정했다. 원본 복사본은 [producer origin](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/producer_origin.json>) 및 [보존된 base producer](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/producer_origin/make_seed2_feedback_artifacts_base.py>)에 남겼다. 입력에는 실제로 사용한 저장 PNG와 Nanum 폰트 파일이 포함되며, 재생성 시 출력 디렉터리는 비어 있거나 새 경로여야 한다.

```bash
MPLCONFIGDIR=/tmp/seed2_guitar_feedback_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python \
/home/ajou/yigyu/3/stability_adapter_2/make_seed2_feedback_artifacts.py \
--out-dir /tmp/seed2_guitar_feedback_reproduction
```

이 단계의 구현 경로, 저장 trial, 비교 참조와 계획은 [CHANGED_FILES.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/CHANGED_FILES.md>)와 [IMPLEMENTATION_FILES.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/IMPLEMENTATION_FILES.md>)에 있다. 별도 검수 기록은 [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/review.md>)에서 확인할 수 있다.
