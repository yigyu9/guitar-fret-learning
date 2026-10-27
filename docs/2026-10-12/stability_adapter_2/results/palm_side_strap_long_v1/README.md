# Palm-side strap 0.5초 저장 비교

네 개의 0.5초 실행에서 고정 rest length와 초기 tension-law를 비교했다. 초기 자세·제어 조건·수동 장력 법칙은 같고 고정 rest length만 달라 초기 장력이 달라진다. 4개 실행의 trace·normal task·contact·report 외에 current 조건 카메라 실행 1개가 포함되어 총 5 initialization / 600 physics steps다. 앞선 0.1초 자료와 첫 24-step raw prefix는 일치하지만, 각 실행은 별도 저장 run이며 curve들을 이어 붙이지 않았다.

| 조건 | 고정 rest length (m) | 초기 law (N) | 기타 최대 위치 오차 (mm) | 기타 최대 회전 오차 (°) | PRESTEP 장력 최대/종료 (N) | palm 접촉 행/step |
|---|---:|---:|---:|---:|---:|---|
| Current | 1.101846972 | 0 | 53.538626 | 6.994315 | 35.845525 / 2.378894 | 7 / 1–2 |
| Taut | 1.080474113 | 0 | 60.944152 | 9.231735 | 2.590060 / 1.993052 | 7 / 1–2 |
| Initial 5 N | 1.079640780 | 5 | 60.592216 | 9.327781 | 5.000000 / 2.189099 | 11 / 1–3 |
| Initial 10 N | 1.078807446 | 10 | 60.019756 | 9.534431 | 10.000000 / 1.575029 | 15 / 1–4 |

각 접촉행은 초기 몇 step에만 관측됐다. Current·Taut·5 N의 palm raw `lambda`는 0이고, 10 N은 step 1의 한 행만 양수(`0.6697399`; 단위 보정 없음)다. 행 수나 raw 값은 하중·지속 지지의 증거가 아니다. 0.1초에 보인 기타 오차 감소는 0.5초까지 유지되지 않았다. 이 비교로 rest length를 채택하거나 안정화·연주 성공을 선언하지 않는다.

![0.5초 네 조건의 기타 p/q 오차, 저장 PRESTEP strap 장력, palm 추적점 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/artifacts/palm_side_strap_long_curves.png)

네 번째 축은 source palm 추적점 오차 크기(mm)다. tension 곡선은 `last_applied_tension_n`의 PRESTEP 기록으로, trace 시각 `t_k`에는 step `k` 직전(`t_(k-1)`)에 적용된 값이며 `t=0`은 첫 step 전에 장력이 아직 적용되지 않은 상태다. Rest length는 run 중 고정됐지만 tension은 시간에 따라 변한다.

아래 정지 패널은 이 네 조건의 비교 baseline인 current camera run에서 기존 Isaac Gym native frame step 0/120을 재사용한다. Current는 이 제한된 비교의 기준이지 전체 실행 중 선택된 최상 조건이나 성공 결과가 아니다. 청록 표시는 target polygon, 주황 점은 같은 저장 pose에서 변환한 source facet 추적점이며 cooked 접촉점이나 압력 중심이 아니다. 별도의 31시점 front/side camera 저장 프레임을 나란히 연결한 영상도 함께 제공한다. 실시간 재생은 60 fps에서 31개 frame(0–0.5초, 0.5167초 파일), 느린 재생은 6 fps의 같은 31개 frame(0.1×, 5.1667초 파일)이다. 영상은 저장된 native camera frame의 replay이며, 후처리에서 새 simulation이나 camera render를 하지 않았다.

![current 조건 native camera step 0과 120, front/side](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/artifacts/palm_side_strap_long_camera.png)

- [저장 camera frame 실시간 재생, 60 fps](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/artifacts/palm_side_strap_long_realtime.mp4)
- [동일 frame 느린 재생, 6 fps / 0.1×](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/artifacts/palm_side_strap_long_slow.mp4)

결과는 한정된 0.5초 진단이다. 기타 오차와 손 위치 지표만으로 접촉 하중·안정 상태를 판정하지 않았다. Source gap 및 palm-up proxy는 cooked clearance나 해부학적 지지 인증이 아니다. 추가 rest length 채택이나 forced attachment를 결정하지 않았다.

Current 조건의 native DOF 좌표 성분 `L_Shoulder_x`는 종료 actual−target이 +24.218°이고, 종료 actual 좌표는 시작 actual 좌표보다 +7.029° 달랐다. 이는 단일 DOF 좌표 차이며 전체 관절 SO(3) 오차나 원인·중력·힘 응답의 인증으로 해석하지 않는다.

실행 명령·환경·ffprobe 결과는 [plot_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/artifacts/plot_execution.json), 사용 입력/producer/output SHA는 [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/artifacts/plot_manifest.json), 전체 경로와 실행 기록은 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/CHANGED_FILES.md)에 있다. [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/review.md:7)는 완료됐고 남은 지적은 없다.
