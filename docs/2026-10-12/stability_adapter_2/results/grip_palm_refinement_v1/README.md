# 손바닥 여유를 둔 두 초기 자세 refinement 비교

이 결과는 기존 seed 2 저장 실행과 새 refinement α=0.5, α=0.25 실행의 기록을 비교한다. baseline은 이번 단계에서 다시 실행하지 않았다. 새 조건은 각각 5초이며 합계 2회 초기화와 2400 physics step이다. 저장 분석의 여섯 검사 항목은 모두 통과했다.

| 조건 | 기타 최대 위치 오차 (mm) | 최대 회전 오차 (°) | 종료 위치 오차 (mm) | 종료 회전 오차 (°) | 초기 6개 source gap 최대 (mm) | 초기 source 접근 기준 |
|---|---:|---:|---:|---:|---:|---|
| 기존 seed 2 기준 | 26.773 | 8.323 | 23.189 | 7.413 | 5.831 | 미통과 |
| 새 α=0.5 | 29.575 | 8.691 | 29.567 | 8.689 | 2.869 | 통과 |
| 새 α=0.25 | 28.296 | 8.436 | 26.405 | 8.169 | 4.343 | 미통과 |

새 두 조건 모두 기타 최대·종료 위치 및 회전 오차가 기존 seed 2보다 컸다. 따라서 이 refinement 두 조건은 채택하지 않는다. α=0.5의 여섯 source gap은 각각 3 mm 이내였으나, α=0.25는 그렇지 않았다. 이 source-shape 간격 검사는 cooked PhysX clearance 인증이 아니다.
검색에서는 8개 source 후보 중 5개를 통과시켰다.

## 저장 곡선과 카메라 프레임

그림은 세 실행의 저장된 기타 위치·회전 오차를 시간에 따라 표시한다. 카메라 시트는 위 행이 t=0, 아래 행이 같은 실행의 t=5초이며, 열은 기존 seed 2(이전 실행), 새 α=0.5, 새 α=0.25 순서다. 이미 저장된 실제 Isaac Gym 손 카메라 PNG를 배열한 것이며 새 렌더링이나 시뮬레이션을 하지 않았다.

![저장 trace의 기타 위치·회전 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/grip_palm_refinement_curves.png)

![기존 seed 2와 두 새 조건의 실제 Gym 손 카메라 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/grip_palm_refinement_hands_camera.png)

## 초기 간격과 접촉 기록의 범위

| 조건 | 엄지3 | 검지3 | 중지3 | 약지3 | 새끼3 | 손바닥 | 세 면 초기 source 접근 |
|---|---:|---:|---:|---:|---:|---:|---|
| 기존 seed 2 (mm) | 5.831 | 1.459 | 0.000007 | 3.858 | 2.447 | 3.842 | 미통과 |
| 새 α=0.5 (mm) | 2.869 | 0.950 | 0.000036 | 2.171 | 1.448 | 2.130 | 통과 |
| 새 α=0.25 (mm) | 4.343 | 1.222 | 0.000001 | 3.038 | 1.966 | 2.981 | 미통과 |

분석에는 기타 body와의 named-body 접촉 기록이 들어 있지만, 기록만으로 넥의 뒷면·앞면·옆면을 구분할 수 없다. 양의 raw lambda가 마지막으로 기록된 step은 α=0.5에서 엄지 1200, 중지 1200, 검지 368, 손바닥 112였고, α=0.25에서 엄지 1200, 중지 1200, 검지 257, 손바닥 142였다. 접촉 행의 마지막 step은 각각 α=0.5 검지 487/손바닥 122, α=0.25 검지 350/손바닥 149였다. 이 sample과 raw lambda는 연속 지지나 뉴턴(N) 단위 힘의 증명이 아니다.

몸통 9개 PD 목표는 유지됐지만 실제 몸통 좌표의 최대 변화는 기존 seed 2 4.223°, α=0.5 4.235°, α=0.25 4.239°였다. 각 실행의 report는 안정성 성공을 인증하지 않는다.

## 재현 및 입력 자료

저장 자료만 사용하는 producer는 [make_grip_palm_refinement_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_grip_palm_refinement_artifacts.py)다. 새 출력 디렉터리로 재생성하려면:

```bash
MPLCONFIGDIR=/tmp/grip_palm_refinement_reproduction MPLBACKEND=Agg python /home/ajou/yigyu/3/stability_adapter_2/make_grip_palm_refinement_artifacts.py --out-dir /tmp/grip_palm_refinement_reproduction
```

실행에는 새로 비어 있는 출력 경로를 사용한다. [v4 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifact_execution_v4.json)과 [v4 input/output SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/artifact_manifest.json)가 최종 산출물 기준이다. 이전 산출물과 producer 사본은 `artifacts_attempt_v1`, `artifacts_v2`, `artifacts_v3`에 보존했다. v1 기본 글꼴의 한글 누락, v2 한글 글꼴 적용, v3 시트 여백 조정의 산출물과 producer를 보존했다. 전체 906개 카메라 PNG, producer, 폰트를 포함한 918개 입력을 생성 전에 해시하고 모든 capture의 step/time·두 view SHA를 대조한 v4가 canonical이다. 후처리 산출은 네 번 만들었으며 새 native 실행은 두 조건뿐이다.

새 조건의 [α=0.5 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p5/initial_values.json), [α=0.25 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p25/initial_values.json), 기존 기준의 [seed 2 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_2/initial_values.json)을 확인할 수 있다. 각 실행의 [α=0.5 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p5/whole_body.mp4), [α=0.5 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p5/hands.mp4), [α=0.25 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p25/whole_body.mp4), [α=0.25 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p25/hands.mp4), [기존 seed 2 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_2/whole_body.mp4), [기존 seed 2 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_2/hands.mp4)은 각기 다른 실행의 실제 Gym 녹화다.

다음으로 지정된 것은 seed 2 초기 strap 여유 비교 계획이며 아직 실행되지 않았다: [SEED2_STRAP_INITIAL_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/SEED2_STRAP_INITIAL_PLAN.md).

검수 상태: [독립 검수 완료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/review.md:7). 남은 Critical/Warning/Suggestion은 없으며 기타 안정화 성공을 뜻하지 않는다.
