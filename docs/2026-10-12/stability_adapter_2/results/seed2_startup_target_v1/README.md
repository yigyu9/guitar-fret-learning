# Seed 2 왼팔 초기 목표 편차 비교

2026-10-08에 세 조건을 각각 새로 시작해 5초씩 실행했다(3 init, 3600 physics steps). 공통 초기 인간 관절값, 기타 위치·회전 목표, strap 절대 rest length 1.1018469719600776 m와 초기 route 1.0866096862014567 m, PD/solver는 유지했고 왼팔 12축의 시작 목표 편차 크기만 달리했다. 초기 관절값은 세 조건에서 모두 같고 0/0.5×/1×는 첫 제출 이후 유지되는 상수 목표 offset의 배율이지 초기각 변경이 아니다. 주 제어 인터페이스 66축, 몸통 9축 목표, 손가락 42축, root와 하체 고정 조건은 같으며 기타는 자유롭게 움직였다. 아래 표의 편차는 초기 관절값에서 목표까지의 최대 절대 좌표 차이다.

| 조건 | 시작 목표 편차 최대 | 첫 0.1초 기타 위치/회전 최대 오차 | 5초 기타 위치/회전 최대 오차 | 종료 위치/회전 오차 | 왼팔 12축 실제 좌표 드리프트 최대 |
|---|---:|---:|---:|---:|---:|
| OFF | 0° | 33.015 mm / 4.619° | 158.088 mm / 26.355° | 157.513 mm / 26.145° | 18.427° |
| 0.5× | 8.505° | 12.365 mm / 1.919° | 120.157 mm / 21.524° | 120.157 mm / 21.523° | 12.256° |
| 1× | 17.010° | 5.108 mm / 0.969° | 26.773 mm / 8.323° | 23.189 mm / 7.413° | 12.444° |

실제 좌표 드리프트는 각 저장 시점에서 왼팔 12개 native scalar 좌표 각각의 `|q(t)-q(0)|` 중 최댓값이다. 표의 목표 편차 최대와 실제 좌표 드리프트 최대는 각각 집계한 별도 최댓값이며, 둘 다 관절별 `q-q_target` tracking 오차가 아니고 관절 묶음의 SO(3) 회전 오차도 아니다. 기타 회전 오차는 별도 SO(3) 오차다. 몸통 9축의 목표는 유지됐지만 실제 좌표 드리프트 최대는 OFF/0.5×/1×에서 각각 3.444°/4.286°/4.223°였다.

1×는 이 세 조건에서 5초 기타 최대 오차가 가장 작았지만, 기타 이탈이 남아 `stability_success`는 false다. 승인된 판단에 따라 full bias/current LA를 다음 진단의 기준으로 유지하며 안정화 성공이나 일반적인 새 설정 채택으로 해석하지 않는다. 최대 목표 변화는 L_Shoulder_x의 17.010°다. 이번 실험은 왼팔12 bias 묶음을 바꾼 비교이므로 결과의 원인을 특정 관절 하나나 중력 효과로 분리하지 않았다. 초기 source 접근 통합 조건(여섯 부위 모두 3 mm 이내)은 세 조건 모두 충족하지 않았고 개별 gap은 혼합되어 있다. 이 조건은 cooked collider clearance 인증이 아니다. 저장 접촉자료에서 세 조건의 오른손-기타 접촉행은 0이다. full에서는 thumb3/index3/middle3의 양의 raw lambda 기록이 step 1200까지 있었고 palm의 마지막 양의 기록은 step 121, 마지막 접촉행은 step 134였다. half에서는 palm/pinky3의 양의 기록이 step 1200까지 남았지만 기타 위치 오차는 120.157 mm였다. 접촉은 면·지속 지지를 분류하지 않으며 raw lambda는 뉴턴 힘이 아니다. 분석의 8개 검사는 모두 통과했고, native PD 목표 clipping은 없었으며 upward-proxy 위반도 없었다. 이 검사들은 기타 안정화 성공을 뜻하지 않는다.

![세 조건의 기타 오차와 왼팔 목표 편차·실제 좌표 드리프트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifacts/seed2_startup_target_curves.png)

![실제 Gym 손 카메라의 각 조건 t=0 및 t=5초 저장 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifacts/seed2_startup_target_hands_camera.png)

두 번째 그림은 위 행이 t=0, 아래 행이 t=5초인 2×3 배열이다. 실제 Gym 카메라 저장 프레임이며 세 조건의 절대 strap rest length가 같고 strap mesh는 렌더되지 않는다. 이번 full(1×)의 처음 24 step과 전체 5초 원자료 다섯 배열은 직전 seed2_strap_initial_v1/current와 정확히 일치했다. 이는 관측 기록이며 추가 실행으로 세지 않았다.

세 조건의 실제 전신 및 손 영상과 초기값은 다음과 같다.

- OFF: [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/native/off/initial_values.json), [whole body video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/native/off/whole_body.mp4), [hands video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/native/off/hands.mp4)
- 0.5×: [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/native/half/initial_values.json), [whole body video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/native/half/whole_body.mp4), [hands video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/native/half/hands.mp4)
- 1×: [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/native/full/initial_values.json), [whole body video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/native/full/whole_body.mp4), [hands video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/native/full/hands.mp4)

원자료는 [검증된 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/analysis.json), [승인된 분석 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifact_brief.json), 각 조건의 `report.json`, `capture.json` 및 위 초기값 파일에 있다. 5초 수치는 세 조건 각각의 저장 실행에서 읽었다. 이 산출물 단계에서는 native 실행을 하지 않았다. 후처리는 두 번 실행했다. 첫 시도의 그림 범례에서 NanumGothic이 U+2212 minus 기호를 표시하지 못해 초안과 로그를 보존하고 ASCII 표기로 바꿨다. [첫 시도 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifact_execution_attempt_v1.json)과 [보존된 첫 산출물·producer·manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifacts_attempt_v1/)를 참조한다. 두 후처리 시도 모두 native 실행 0회다.

그림 생성은 [producer](/home/ajou/yigyu/3/stability_adapter_2/make_seed2_startup_target_artifacts.py)가 저장된 데이터만 읽어 수행했다. [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifact_execution.json), [실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifact_execution.log), [입력·출력 SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifacts/artifact_manifest.json)를 참조한다. 재현하려면 새 빈 출력 폴더를 사용한다:

```bash
MPLCONFIGDIR=/tmp/seed2_startup_target_reproduction MPLBACKEND=Agg python /home/ajou/yigyu/3/stability_adapter_2/make_seed2_startup_target_artifacts.py --out-dir /tmp/seed2_startup_target_reproduction/output
```

다음 단계인 [기타 응답 식별 계획](/home/ajou/yigyu/3/stability_adapter_2/SEED2_GUITAR_RESPONSE_PLAN.md)은 아직 실행하지 않았다. 독립 검수 완료 — Critical/Warning/Suggestion 없음. [검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/review.md:7)과 [최종 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/final_verification.json)을 확인한다.
