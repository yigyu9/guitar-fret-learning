# 파란 기타 측면 손바닥 추적 결과

이번 결과에서도 왼손 손바닥은 파란 넥 측면을 계속 지지하지 못했다. face-used palm facet의 source 표면 간격은 초기 약 **0.049807 mm**였지만, 세 0.1초 조건 모두 첫 physics step에서만 LH:palm–guitar 접촉 4행이 기록됐고 네 raw `lambda`는 모두 0이었다. step 2–24에는 해당 접촉행이 없다. 이는 연속 지지나 접촉력 인증이 아니다.

세 조건은 동일한 시작 자세와 기타 목표에서 비교했다. **OFF**는 손 목표 보정 없이, **bias**는 왼팔 12축의 startup 목표 보정만(그중 7축은 ±0.15 rad 포화), **tracking**은 그 보정과 bounded palm-task 추적을 함께 쓴다. 추적점은 face-used palm facet에서 고른 local point를 저장 native LH:palm 자세로 변환한 값이다. target은 기타와 함께 움직이는 파란 영역 중심에서 바깥 방향으로 50 μm 떨어진 점이며, 손–기타 초기 상대 회전은 유지한다. 이것은 source-derived 점 추적이지 PhysX cooked surface 쿼리나 접촉 압력 중심 측정이 아니다.

| 0.1초 조건 | 추적점 오차 최대/종료 (mm) | 추적 방향 오차 최대 (°) | 기타 위치 오차 최대 (mm) | 기타 회전 오차 최대 (°) | LH:palm–guitar 기록 |
|---|---:|---:|---:|---:|---|
| OFF | 71.909699 / 71.909699 | 10.182926 | 5.107730 | 0.969008 | step 1의 4행, `lambda=0`; 이후 0행 |
| bias | 49.465670 / 49.465670 | 5.228185 | 5.107730 | 0.969008 | step 1의 4행, `lambda=0`; 이후 0행 |
| tracking | 48.323668 / 48.323668 | 4.752099 | 5.107730 | 0.969008 | step 1의 4행, `lambda=0`; 이후 0행 |

Startup 보정 응답 교정은 6×12 행렬의 initial FK와 별도다. FK held-out 오차는 위치 0.683 μm, 회전 9.61×10⁻⁷ rad였다. 응답 교정의 위치 잔차는 0.848058 mm에서 선형 예측 0.384523 mm, 실제 bias 응답 0.379425 mm로 바뀌었고 회전 오차는 0.134891°에서 예측 0.101051°, 실제 0.106163°였다. 이 1-step 교정은 이후 추적 응답이나 지지 성공을 보증하지 않는다.

세 조건의 저장 기타 body 상태와 기타 위치·회전 오차 곡선은 서로 일치한다. 그 밖의 전체 trace는 route point, 속도, strap 길이, torso 항목까지 완전히 같지는 않다. 추적점 오차는 줄었지만 약 48.3 mm가 남고, 기타의 최대 오차도 5.108 mm / 0.969°다. 따라서 손 위치 추적이 개선된 관측을 기타 안정화나 지지 성공으로 해석하지 않는다.

## 그림

![세 조건의 손 추적점과 기타 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/artifacts/palm_side_feedback_metrics.png)

![저장 camera frame에 투영한 source facet 점과 target 영역](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/artifacts/palm_side_feedback_camera_comparison.png)

두 번째 그림은 이전 fixed-target 0.1초 frame, 신규 tracking의 0초와 0.1초 frame을 front/side camera로 나란히 놓았다. 청록 다각형은 각 이미지에 기록된 `target_polygon_W_m`를 해당 `camera_specs`의 look-at 방향과 horizontal FOV로 핀홀 투영해 덧그린 설명 표시다. 주황 점은 선택된 source facet local point를 각 이미지와 같은 시점의 native LH:palm 위치·회전에 적용해 투영했다. 표시 크기와 겹침은 물리 접촉을 나타내지 않는다. 카메라 이미지는 Isaac Gym native camera 저장 이미지다. GPU pipeline은 비활성화됐고 graphics device id는 0이며, graphics backend identity는 확인되지 않았다. MuJoCo render가 아니다.

## 원자료와 재현

최종 `analysis.json`의 14개 검사는 모두 통과했다. 그중 raw 길이·시간 범위·유한값 및 저장 camera 원자료 검사는 데이터 무결성 항목이다. 접촉 행과 기타 상태 일치는 결과 관측으로 별도 보고하며 성공조건으로 강제하지 않았다. 이 phase에는 FK·응답 교정, 세 짧은 조건, tracking 실행을 합쳐 **32회 native initialization / 110 physics step**이 기록됐다. 플롯 생성과 뒤이은 검증은 저장 JSON/PNG만 읽어 각각 0회/0 step 추가 실행했다.

처음 분석 시도는 SHA 함수에 문자열 경로가 전달되어 실패했고 로그에 남아 있다. 후속 분석은 완료됐다. 후속 preflight는 새로운 calibration/input hash coverage를 0회/0 step으로 확인했지만, 이전 production 단계의 누락 SHA를 과거로 소급해 증명하지 않는다. 이전 분석·그림 초안도 보존했다. 자세한 경로와 SHA는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/CHANGED_FILES.md), figure input/output SHA와 실제 재현 정보는 [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/artifacts/plot_manifest.json) 및 [plot_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/artifacts/plot_execution.json)에 기록했다.

읽기 전용 그림 재생성은 새 output directory로 실행한다.

```bash
MPLCONFIGDIR=/tmp/palm_side_feedback_mpl python3 stability_adapter_2/plot_palm_side_feedback.py \
  --phase docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1 \
  --out-dir /tmp/palm_side_feedback_reproduction
```

두 PNG 모두 저장된 결과로 재생성했을 때 pixel-exact였다. 별도 change-reviewer 검수를 완료했고 미해결 지적사항은 없다. [독립 검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/review.md:9).
