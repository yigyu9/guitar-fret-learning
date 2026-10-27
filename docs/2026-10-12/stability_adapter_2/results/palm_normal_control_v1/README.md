# 손바닥 normal-only 제어 짧은 비교

검증된 `analysis.json`은 11개 검사를 통과했다. 이 단계의 전체 실행 집계는 8 native initialization과 123 physics steps이며, 아래 곡선은 네 개 0.1초 저장 trace를 비교한다. 이번 단계에 포함된 Normal 0.30 camera 실행 1회와 이전 Full 0.15의 저장 frame을 비교한다. 그림 생성은 물리 실행을 추가하지 않았다.

| 조건 | 손 추적점 최대 오차 (mm) | source 법선 대향각 최대 (°) | 종료 signed source gap (mm) | 종료 접선 거리 (mm) | 기타 위치/회전 최대 오차 (mm / °) | palm 접촉 기록 |
|---|---:|---:|---:|---:|---:|---|
| Full 0.15 | 48.323668 | 4.750409 | 40.495078 | 26.445653 | 5.107730 / 0.969008 | step 1, 4행 |
| Normal 0.15 | 48.284051 | 4.800777 | 40.449147 | 26.443497 | 5.107730 / 0.969008 | step 1, 4행 |
| Normal 0.30 | 12.186877 | 1.280689 | 11.864499 | 2.989581 | 5.107730 / 0.969008 | step 1–2, 7행 |
| Normal 0.50 | 11.963341 | 1.434722 | 11.336725 | 3.966279 | 5.107730 / 0.969008 | step 1–2, 7행 |

각 조건의 palm contact 행은 모두 raw `lambda=0`이며 step 2 이후(0.15 조건) 또는 step 3 이후(0.30/0.50 조건)에는 기록이 없다. 접촉 행은 힘·지속 지지의 증거가 아니다. Normal 0.30은 법선각과 접선 거리가 0.50보다 작고, 0.50은 손 추적점 최대 오차가 조금 작지만 법선각·접선 거리는 더 크다. 0.30을 진단 기준으로 남길 수는 있어도 안정화나 연주 성공으로 판정하지 않는다.

첫 step에서 runtime cap 0.30의 실제 추적점 오차는 0.085002 mm였고 예측값은 0.00004393 mm였다. cap 0.50은 실제 0.100337 mm, 예측 0.00002599 mm였다. 이 짧은 startup 예측은 실제 추적점 오차를 크게 낮게 잡았으므로 정지 모델의 검증이나 후기 응답 예측으로 해석하지 않는다.

Full 0.15에서 Normal 0.15로의 1단계는 방향 task와 startup bias를 함께 바꾼 비교다. 이어지는 0.30/0.50 비교는 같은 초기 자세에서 normal-only task의 runtime target 범위를 넓힌 단계다. 조건 간 전체 기타 body state는 정확히 같고, 기타 위치·회전 오차는 네 조건 모두 같았다. 이는 전체 trace가 같다는 뜻은 아니며 torso와 route 등 다른 저장량은 다르다. torso 목표는 유지됐지만 actual torso drift는 조건별 최대 약 0.959–1.014°였다.

곡선은 저장 `normal_tasks.json`의 앞 3성분 norm을 mm로, 뒤 3성분 norm을 orientation scale 0.08 m/rad로 나눈 source 법선각을 도 단위로 표시한다. 법선각은 전체 SO(3) 차이가 아니다. 기존 source palm-up proxy 최소값은 네 조건 모두 0.963174였으나 해부학적 방향 검증은 아니다. 초기 50 µm source gap 및 이 곡선은 PhysX cooked surface, 실제 압력, 충돌 여유를 인증하지 않는다.

![네 조건의 손 추적점·source 법선각·기타 오차 저장 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/palm_normal_control_curves.png)

아래 3×2 panel은 위에서부터 이전 Full 0.15의 0.1초 frame, Normal 0.30의 초기 frame, 같은 Normal 0.30 실행의 0.1초 frame이다. 열은 front/side camera다. 청록 영역은 해당 시점의 target polygon 투영이고 주황 표식은 같은 저장 native palm 자세에 변환한 source facet 추적점이다. 표식은 cooked contact point나 접촉 압력 중심이 아니다. 이들은 Isaac Gym native camera가 실제로 저장한 frame이며 MuJoCo 재구성이 아니다.

![저장 native camera frame과 같은 시점의 source target/facet 표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/palm_normal_control_camera.png)

실행·입력·출력 SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/plot_manifest.json)와 [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/plot_execution.json)에 있다. 첫 초안은 Hangul font 표시 문제 때문에 `artifacts_v1/`에 보존했고 위 그림은 수정된 최종 producer 출력이다. 다른 native 실행은 추가하지 않았다.

설계 맥락은 [PALM_NORMAL_CONTROL_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_NORMAL_CONTROL_PLAN.md), 파일 경로와 줄 번호는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/CHANGED_FILES.md)에 있다. [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/review.md:7)는 완료됐으며 남은 지적은 없다. 지속 지지와 기타 안정화는 아직 달성하지 못했다.
