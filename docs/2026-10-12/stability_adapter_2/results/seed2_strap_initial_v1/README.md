# Seed 2 strap 초기조건 5초 비교

이 단계에서는 동일한 Seed 2 자세·제어 조건으로 current, taut, 초기 strap law 5 N 세 조건을 각각 새로 실행했다(3회 초기화, 총 3600 physics step). `current`의 저장된 5초 원자료 다섯 배열은 이전 Seed 2 기준 실행과 정확히 일치한다. 이 일치 확인은 이번 실행 수에 추가되지 않는다.

| 조건 | 절대 rest length (m) | 초기 route (m) | 첫 0.1초 최대 기타 위치/회전 오차 | 5초 최대 위치/회전 오차 | 종료 위치/회전 오차 |
|---|---:|---:|---:|---:|---:|
| current | 1.1018469719600776 | 1.0866096862014567 | 5.108 mm / 0.969° | 26.773 mm / 8.323° | 23.189 mm / 7.413° |
| taut | 1.0866096862014567 | 1.0866096862014567 | 3.545 mm / 0.505° | 35.020 mm / 7.543° | 35.020 mm / 7.542° |
| 초기 law 5 N | 1.0857763528681235 | 1.0866096862014567 | 3.197 mm / 0.428° | 35.293 mm / 7.516° | 35.292 mm / 7.516° |

처음 0.1초에는 taut와 5 N 조건의 최대 오차가 더 작았다. 5초 최대 이동 오차는 두 조건에서 current보다 커졌지만 최대 회전 오차는 current보다 조금 작았다. 종료 위치·회전 오차는 current가 두 조건보다 작았다. current는 이번 세 조건에서 5초 최대·종료 위치 오차가 가장 작았다. 이는 이 세 설정의 기록 비교이며 안정화 또는 연주 성공 판정은 아니다. 주요 제어 66축과 몸통9 PD 목표는 유지했고, 기타는 자유롭게 움직이며 humanoid root와 하체는 고정했다. 몸통9의 실제 좌표 최대 편차는 current/taut/5 N 순으로 4.223°/4.282°/4.293°였다.

초기 pose는 같고 세 조건의 초기 route는 모두 1.0866096862014567 m다. current의 rest length는 route보다 길고, taut는 route와 같으며, preload 조건은 route보다 약 0.833 mm 짧다. `initial_values.json`과 실제 trial 설정은 preload 길이 1.0857763528681235 m를 사용했다. 소비된 [leaf 계획 문서](/home/ajou/yigyu/3/stability_adapter_2/SEED2_STRAP_INITIAL_PLAN.md:1)는 마지막 자릿수가 1 ULP 다른 1.0857763528681234 m로 기록한다. 표는 실행 당시 `initial_values.json` 값을 쓴다.
![세 조건의 5초 기타 오차 및 strap law scalar 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v3/seed2_strap_initial_curves.png)

그래프 아래 패널은 native force sensor가 아니라 strap law의 제출 scalar를 나타낸다. 시간은 각 law 입력 구간의 시작 시각이다. 첫 제출값은 current 0 N, taut 0 N, preload 조건 약 5 N이지만 이는 실행 내내 일정한 힘을 뜻하지 않는다. 최대/종료 제출값은 각각 current 21.026/0 N, taut 4.976/2.724 N, preload 6.768/2.713 N이다.

![실제 Gym 손 카메라의 t=0 및 t=5초 저장 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v3/seed2_strap_initial_hands_camera.png)

2×3 배열의 윗행은 step 0/t=0, 아랫행은 step 1200/t=5초이며 열은 current, taut, 초기 law 5 N이다. 이미지는 이번 물리 실행 중 저장한 Isaac Gym 카메라 프레임에서 골랐다. 초기 pose와 초기 route 길이는 세 조건에서 같지만 absolute rest length만 다르다. strap mesh는 camera render에 표시되지 않으므로 이미지로 LA 차이를 구별할 수 없다. 두 시점 사이의 자세 변화량을 픽셀 차이로 해석하면 안 된다.

여섯 부위가 모두 3 mm 이내여야 하는 통합 초기 source 접근 조건은 세 조건 모두 미달했다. raw named-body 기록은 넥의 접촉면을 분류하지 않으며, raw lambda는 뉴턴 힘이나 지속 지지를 뜻하지 않는다. current에서는 LH thumb3/index3/middle3의 양의 lambda 기록이 step 1200까지 있었고 palm은 마지막 양의 기록 step 121, 마지막 접촉행 step 134였다. taut에서는 thumb step 74/index step 145, 초기 law 5 N에서는 thumb step 78/index step 147이 마지막 양의 기록이었다; 두 조건 모두 palm과 middle의 양의 기록은 step 1200까지 남았다. 이 샘플 기록만으로 연속 지지나 넥 면 접촉을 인증하지 않는다.

각 조건의 [초기 설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/current/initial_values.json), [taut 초기 설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/taut/initial_values.json), [5 N 초기 설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/preload5n/initial_values.json), [analysis](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/analysis.json), [v3 artifact 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifact_execution_v3.json), [v3 입력·출력 SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v3/artifact_manifest.json), [v3 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifact_execution_v3.log)를 보존했다. 조건별 실제 영상은 [current 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/current/whole_body.mp4), [current 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/current/hands.mp4), [taut 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/taut/whole_body.mp4), [taut 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/taut/hands.mp4), [5 N 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/preload5n/whole_body.mp4), [5 N 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/preload5n/hands.mp4)에서 확인할 수 있다.

각 run은 151개 프레임(0–5초, 30 fps)을 저장했다. producer는 저장된 곡선과 카메라 프레임만 읽어 그림을 만들었으며 native simulation을 실행하지 않았다. v3 producer의 919개 입력(분석·brief·실행 메타데이터·원본 프레임·Nanum 폰트 포함)은 읽기 전후 SHA가 모두 일치한다. 출력은 PNG 두 장이며 manifest에 SHA를 기록했다. v1의 [원 출력 디렉터리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts), [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts/artifact_manifest.json), [producer 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts/producer.py)를 보존했다. v1 곡선은 마지막 law sample(4.995833 s)을 잘랐으므로 v2에서 세 패널 x축을 0–5초로 맞췄다. v2의 [출력 디렉터리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v2), [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v2/artifact_manifest.json), producer도 보존했으며 [v2 producer 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v2/producer.py)는 당시 v2 manifest의 producer SHA와 일치한다. v3에서는 full-5s 재현 boolean이 true인지 gate하지 않고 boolean 형식만 검증한다; 이 관측값은 그림 생성 조건이 아니다.

재생성은 빈 출력 디렉터리에서 실행한다. 출력 경로가 이미 비어 있지 않으면 producer는 덮어쓰지 않고 중단한다.

```bash
MPLCONFIGDIR=/tmp/seed2_strap_initial_reproduction_mpl MPLBACKEND=Agg \
  python /home/ajou/yigyu/3/stability_adapter_2/make_seed2_strap_initial_artifacts.py \
  --out-dir /tmp/seed2_strap_initial_reproduction
```

다음 계획인 [Seed 2 시작 목표각 검토](/home/ajou/yigyu/3/stability_adapter_2/SEED2_STARTUP_TARGET_PLAN.md:1)는 아직 실행하지 않았다. 이 비교만으로 길이 후보를 최종 채택하지 않는다. 독립 검수는 완료됐으며 남은 Critical/Warning/Suggestion은 없다. [검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/review.md:7)과 [최종 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/final_verification.json)을 확인한다.
