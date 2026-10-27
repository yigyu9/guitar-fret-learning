# 다면 그립 초기 자세 비교 — v3

세 조건은 각각 5초, 1200 physics step으로 완료됐습니다(총 3 init/3600 step). 초기 변경은 왼팔 12축과 손가락 21축의 각도이며, 오른팔·몸통·하체, 기타의 초기 p/q, 스트랩 절대 길이 1.1018469719600776 m 및 PD 기준은 유지했습니다. 각 조건의 목표각은 해당 초기 각도에 따라 다릅니다. 분석 계약 7개가 모두 통과했습니다. v1의 source 탐색 후보 3개는 모두 거절되어 native 실행이 없었고, v2의 고비용 soft heuristic도 native 전에 중단됐습니다. v3 source fit 3개는 완료됐지만 원래 3 mm 기준은 통과하지 못했습니다. 이후 별도 full-hull source audit에서 “safe-incomplete”으로 분류된 두 seed를 선택해 baseline과 함께 실행했습니다. 세 조건 모두 요청한 세 면 초기 source 접근 조건은 만족하지 않았습니다. source 검사·native FK는 cooked collision clearance 보증이 아닙니다. 초기 잘못된 source-probe import는 exit -11로 남아 있으며 native 초기화 없이 종료됐습니다.

| 조건 | 5초 최대 기타 위치 오차 | 최대 기타 회전 오차 | 종료 위치 오차 | 종료 회전 오차 |
|---|---:|---:|---:|---:|
| baseline | 82.047 mm | 10.831° | 80.435 mm | 10.564° |
| seed 1 | 47.437 mm | 12.769° | 47.437 mm | 12.769° |
| seed 2 | 26.773 mm | 8.323° | 23.189 mm | 7.413° |

![세 조건의 저장 trace에서 계산한 기타 위치·회전 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifacts/multi_face_grip_curves.png)

Seed 2는 세 조건 중 기타 오차가 가장 작았지만 안정성 성공은 아닙니다. 세 조건 모두 엄지 후면·손가락 전면·손바닥 측면의 초기 source 접근 조건을 만족하지 않았습니다. 초기 palm / finger source gap은 다음과 같습니다. 단위는 mm이며 source 형상 간 거리입니다.

| 조건 | thumb3 | index3 | middle3 | ring3 | pinky3 | palm |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 47.175 | 75.165 | 95.291 | 90.157 | 68.654 | 0.050 |
| seed 1 | 1.411 | 0.438 | 1.030 | 1.653 | 1.469 | 11.679 |
| seed 2 | 5.831 | 1.459 | 0.000007 | 3.858 | 2.447 | 3.842 |

이 source gap은 cooked collision clearance나 접촉력 인증이 아닙니다. 실제 named-body contact와 raw lambda는 별도로 기록됐습니다. Seed 1의 엄지 양의 raw lambda는 마지막으로 step 63 (0.2625 s)에 관측됐고, palm/index 기록은 종료 step까지 있습니다. Seed 2의 thumb/index/middle 양의 raw lambda는 step 1200에도 기록됐으며 palm은 step 121 (0.5042 s)이 마지막입니다. 마지막 sample만으로 연속 접촉이나 지지 유지가 증명되지는 않습니다. Raw lambda는 N 단위로 보정되지 않았습니다. 접촉 body 이름만으로 넥의 뒤·앞·옆 면을 판별하지 않았습니다.

몸통의 실제 최대 좌표 변화는 baseline/seed 1/seed 2에서 4.227°/4.270°/4.223°였습니다. 이는 유지된 9개 몸통 목표와 구별되는 실제 상태 측정입니다. 세 조건 모두 안정성 성공으로 판정되지 않았습니다.

## 저장된 카메라 프레임

아래 2×3 그림은 실제 Isaac Gym 손 카메라에서 저장한 PNG입니다. 위쪽은 t=0 / step 0, 아래쪽은 t=5.0 s / step 1200이며 각 열은 baseline, seed 1, seed 2입니다. 이는 MuJoCo 렌더나 source-shape 재구성이 아닙니다.

![실제 Gym 손 카메라의 초기 및 종료 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifacts/multi_face_grip_hands_camera.png)

각 run의 [baseline 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/baseline/initial_values.json), [seed 1 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_1/initial_values.json), [seed 2 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_2/initial_values.json)을 확인할 수 있습니다.

| 조건 | 전신 실제 Gym 영상 | 손 실제 Gym 영상 |
|---|---|---|
| baseline | [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/baseline/whole_body.mp4) | [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/baseline/hands.mp4) |
| seed 1 | [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_1/whole_body.mp4) | [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_1/hands.mp4) |
| seed 2 | [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_2/whole_body.mp4) | [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_2/hands.mp4) |

각 영상은 151장의 30 fps 프레임(0–5.0 s)으로 생성되어 컨테이너 길이는 약 5.033 s입니다. 물리 실행은 5.0 s입니다. 실행은 CPU PhysX와 graphics device 0에서 기록됐으며, 그래픽 backend의 구체적 정체는 확인되지 않았습니다.

분석기는 frame별 두 camera view의 동시 존재 검사를 보완한 뒤 saved-data만으로 다시 실행됐습니다. 보완 전 두 분석본과 summary/curves가 exact했고, 추가 native 실행은 없었습니다. 최종 artifact manifest는 3조건의 전체 906 camera PNG와 실제 읽은 Nanum font를 포함해 926개 입력 SHA를 기록합니다. 이전 산출물은 [입력 범위 보완 전 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifacts_attempt_v1/)에 남겼습니다. Artifact 생성기는 저장된 분석 및 카메라 PNG만 읽었으며 native 실행을 추가하지 않았습니다. 입력·producer·출력 SHA256과 실제 표시된 프레임은 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifacts/artifact_manifest.json)에 있고, 실행 환경·명령·종료 코드는 [artifact 실행 정보](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifact_execution.json)에 있습니다. 출력은 새로운 빈 `artifacts` 폴더에 생성해야 합니다; 재생성 예시는 다음과 같습니다.

```bash
MPLCONFIGDIR=/tmp/multi_face_grip_reproduction MPLBACKEND=Agg \
  python stability_adapter_2/make_multi_face_grip_artifacts.py \
  --out-dir /tmp/multi_face_grip_reproduction/artifacts
```

초기 source 경로의 단계별 시행·검사 기록은 [IMPLEMENTATION_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/IMPLEMENTATION_FILES.md:1)에 모았습니다. 분석 원자료는 [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/analysis.json)입니다.
