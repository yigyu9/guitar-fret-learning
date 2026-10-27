# Palm-witness 초기 자세 후보: 실제 유지 시험과 source 거리 진단

이 phase는 기존 LA−2 mm 기타 초기 pose를 유지하면서 왼팔·손가락 초기 18각과 그에 대응하는 PD 목표만 바꾼 후보를 한 번 시험했다. 16개 저장 형상 배치의 source screen 중 6개가 접근 방향 검사를 통과했고, 새 후보 한 초기화에서 실제 Isaac Gym 1200 step을 실행했다. 이는 기타 지지 접촉이나 연주 성능 개선을 확정하는 시험이 아니다.

## 초기 조건 변경

| 변경 범위 | 변경 내용 |
|---|---|
| 초기 관절각 | 팔 12개 + 단일 hinge 손가락 6개, 총 18개. 실제 적용 최대 변화 `0.002616494894 rad` |
| 초기화 시점과 이후 PD target | 첫 native startup target은 측정 초기 q였다. 이후 유지 target은 기존 33개 offset을 보존하고 초기 18개 변화량만큼 이동했다. |
| 보존 | 기타 초기 p/q, root·하체, 나머지 63개 초기각/PD 목표, 기타 목표, 몸통9 목표, PD×2, LA 절대 rest length `1.0998469719600776 m`, 손목 파형은 유지 |
| 손목 파형 | `L_Wrist_x`, 진폭 `0.005 rad`, `1 Hz`, `0–5 s` |

Thorax 각도 변경으로 strap 경로와 초기 slack은 달라졌다. LA rest length가 같다는 사실만으로 경로와 slack까지 같다고 볼 수 없다.

## 형상 거리와 실제 유지 결과

아래 그림은 실제 native 두 trace를 연속선으로 비교하고, 별도 panel에서 source 형상의 네 저장 시점과 네 delta fraction을 점으로 표시한다. source 지점은 시계열로 연결하지 않았다. 원의 표식은 source 접근 screen 통과, 십자 표식은 미통과를 나타낸다. fraction 0은 접근 방향을 제안하지 않은 기준행이라 접근 gate 미충족으로 표시되며, 이것은 baseline 자체의 native 충돌 실패를 뜻하지 않는다.

![저장 native trace 비교와 이산 source whole-palm 거리 표본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/palm_witness_diagnostics.png)

| 측정 | 기존 LA−2 mm 기준 | Palm-witness 초기 후보 | 의미 |
|---|---:|---:|---|
| 초기 source whole-palm patch 거리 상한 | 0.421669522 mm | 0.109504850 mm | 저장 source pose의 feasible finite-patch 거리 |
| float32 적용 후보 인증 거리 상한 | — | 0.109512592 mm | witness/source quantization 후 계산 |
| 실제 native t=0 source 거리 상한 | — | 0.109523083 mm | 실제 초기 snapshot의 source 진단 |
| 기타 초기 위치 오차 최대 | 14.010555659 mm | 14.085147532 mm | 후보가 더 큼 |
| 기타 초기 회전 오차 최대 | 2.607664763° | 2.616524646° | 후보가 더 큼 |
| 2초 기준 이후 위치 변화 최대 | 0.363488152 mm | 0.373544434 mm | 후보가 더 큼 |
| 2초 기준 이후 회전 변화 최대 | 0.070088885° | 0.072412256° | 후보가 더 큼 |
| Strap 법칙 장력 최대 | 28.152161370 N | 27.358932455 N | 재구성한 법칙 scalar; 접촉 λ와 다름 |
| Strap 첫 양의 법칙 장력 step | 37 | 37 | 두 실행에서 동일 |
| `human/LH:palm` 양의 raw lambda step 수 | 0 | 0 | 두 실행 모두 palm 접촉 관측 없음 |

후보는 초기 source whole-palm 간격을 줄였지만 기타 유지 오차와 후기 변화는 모두 소폭 커졌다. 따라서 새 초기각을 채택하지 않고 기존 LA−2 mm를 작은 손목 파형 비교 기준으로 유지한다. 이 결과는 각 조건 1회 시험이므로 반복 변동이나 다른 동작의 우열은 판단하지 않는다.

Source 거리는 최적화된 유한 patch의 feasible distance upper bound이며, 정확한 최소거리 인증이나 PhysX cooked penetration/contact/support certificate가 아니다. LP common-radius 검사는 source 교차 screen이고, Cooked geometry의 접촉·지지력 측정과 별개다. 실제 native contact `lambda`는 양의 raw lambda가 관측된 step 수로만 해석하며 N 단위 힘으로 해석하지 않는다. 네 시점의 이산 점은 16 placement를 요약하고 중간 동작을 보증하지 않는다.

실제 native 결과는 초기화 1회, 물리 1200 step, 0–5초이다. 두 영상은 각 151 frame, 30 fps로 저장되어 파일 duration은 5.033333초다. 원자료 trace는 native timestep 기록이고, 장력 panel은 `last_applied_tension_n`(직전 step에 적용된 장력, N)을 나타낸다.

### 실제 손/전신 캡처

손 카메라의 `00000.png`는 초기 t=0 snapshot이고, `00150.png`는 1200번째 step 이후 t=5 s snapshot이다. 이는 실제 Gym 캡처이며 source 형상 미리보기가 아니다.

![실제 Gym 손 카메라, t=0 초기 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/native/frames/hands/00000.png)

![실제 Gym 손 카메라, t=5 s 마지막 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/native/frames/hands/00150.png)

실제 손 영상: ![실제 Gym 손 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/native/hands.mp4)

실제 전신 영상: ![실제 Gym 전신 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/native/whole_body.mp4)

## 다음 목표와 학습 상태

현재 기타 frame G에서 fret·strike 연주 목표를 맞추는 정확도와 초기 world G pose p/q를 유지하는 목표는 별도 측정값이다. 이후 의도는 기존 연주 기준 target과 초기 world-pose hold target을 함께 받아 한 공동 residual을 합성하는 것이다. 두 기준의 구체 계약과 평가 순서는 [연주 residual 평가 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:1), 이번 초기 자세 판단은 [초기 palm-witness 결정](/home/ajou/yigyu/3/stability_adapter_2/PALM_WITNESS_INITIAL_DECISION.md:1)에 정리했다.

이 phase의 새 실제 물리 실행은 초기화 1회와 1200 step이다. 산출물 생성·복구에서는 추가 native/physics 실행이 0회였고 actor 추론·학습도 0회다. 완전한 fret/strike 연주는 검증하지 않았다. 학습은 아직 시작하지 않았다.

## 재현 및 provenance

그림은 저장 JSON/JSONL과 실제 저장 frame을 읽은 Python 3 producer로 생성했다. 실행은 exit code 0, producer 내부 native call 0, physics step 0, inference 0, training update 0이다. 입력 전·후 SHA-256, producer SHA-256, 결과 SHA-256과 정확한 명령/로그는 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/artifact_manifest.json:1), [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/producer_execution.json:1), [stdout/stderr log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/producer.log:1)에 있다. 그림 생성기는 [make_palm_witness_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_palm_witness_artifacts.py:1)이다.

현재 검수 자료는 [review](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/review.md:1), [root verification notes](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/ROOT_VERIFICATION_NOTES.md:1), [artifact revision preservation record](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifact_revision_preservation.json:1)이다. 통합 보존 감사 결과는 봉인 단계에서 별도 생성되는 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/final_verification.json:1)에 저장한다.

### 산출물 버전 보존 기록

첫 그림을 고친 뒤 같은 `artifacts/` 경로를 재사용해 첫 생성 파일을 덮어쓴 일이 있었다. 이전 producer source는 영구 복구본 [make_palm_witness_artifacts_v1_recovered.py](/home/ajou/yigyu/3/stability_adapter_2/make_palm_witness_artifacts_v1_recovered.py:1) 및 [recovered_v1/producer_source.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/recovered_v1/producer_source.py:1)에 보관했고, SHA-256은 이전 기록값 `61ea48b82aed0f27d3c005c17bedfc9b3edec157d55b7f6cdc712a18b95161fe`와 일치한다. 동일 sealed inputs로 별도 경로에서 다시 만든 v1 PNG도 기록된 SHA-256 `db6c6964dacc0c816272be17179b33813144b6692bd97dde1b4b3f412bfde68f`와 일치한다: [recovered v1 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifacts/recovered_v1/palm_witness_diagnostics.png). 원 v1 실행 manifest/log/metadata 전체의 byte 복구는 검증되지 않았다. recovered v1 manifest는 복구 재생성 실행에서 새로 작성된 것이며 원 실행 manifest가 아니다. 현재 `artifacts/` 루트의 그림은 범례와 whole-palm upper-bound 라벨을 다듬은 revised 버전이며 v1과 별도다. 버전별 SHA와 보존 내역은 [보존 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/artifact_revision_preservation.json:1)에 있다.
