# 손바닥 지지 우선의 유한시간 응답

이 phase는 **0.1초** 동안 왼팔 PD 목표의 작은 상수 보정과 기존 palm tracking을 분리해 비교한다. 평행에 가까운 정렬은 soft preference로 두고 실제 palm 지지와 기타의 초기 위치·회전을 우선한다. 실행은 native Gym 물리였다. 수치 표와 곡선은 저장 raw에서 계산했고, 카메라 그림은 실제 Gym capture에 source overlay를 더했다.

분석은 12개 계약을 모두 통과했으며 총 21회 초기화와 504 physics step을 집계했다. 기준 1회, 왼팔 축별 probe 12회, heldout 1회의 14개 측정에서 구한 보정은 기존 startup bias에 추가하는 제한된 상수 delta다. 0.1초 경로가 정적 FK나 무한시간 거동을 증명하지는 않는다. 조건별 기타 최대오차와 palm 작업 오차는 최종 분석 JSON과 해당 raw trace/task에서 대조했다.

## 고정 목표 조건과 기존 tracking 분리

초기 pose, 기타 초기 p/q, 절대 strap 길이, PD gain, 고정 root/하체를 유지했다. Constant 행은 보정 delta의 고정 목표만 사용하고, tracking 행은 기존 bounded PI를 유지하면서 같은 보정 크기만 적용했다. 이 둘은 별도 비교이며 tracking 조건을 constant 결과와 한 곡선에 섞지 않았다.

| 조건 | 종료 palm point 오차 (mm) | 종료 source normal gap (mm) | 종료 normal task angle (°) | 기타 최대 위치 오차 (mm) | 기타 최대 회전 오차 (°) | palm 접촉 기록 step | 양의 raw lambda step |
|---|---:|---:|---:|---:|---:|---|---|
| Constant baseline | 14.208452 | 13.909547 | 1.431640 | 5.107730 | 0.969008 | 1–2 | 없음 |
| Constant quarter correction | 11.093705 | 10.937180 | 1.002060 | 5.093169 | 0.968542 | 1–4 | 없음 |
| Constant half correction | 8.997563 | 9.028552 | 0.921828 | 5.526571 | 1.025444 | 1–5 | 1–2 |
| Constant full correction | 6.670577 | 6.612635 | 1.476742 | 8.219202 | 1.291844 | 1–8 | 1–4 |
| Tracking baseline | 12.186877 | 11.864499 | 1.280689 | 5.107730 | 0.969008 | 1–2 | 없음 |
| Tracking quarter correction | 9.712493 | 9.524164 | 0.939711 | 5.093149 | 0.968555 | 1–4 | 없음 |

`normal task angle`은 저장 3-vector의 norm을 0.08 m/rad로 나눈 값이지 전체 자세의 SO(3) 오차가 아니다. `source normal gap`은 source geometry 기반 기록으로 cooked clearance 인증이 아니다. Contact step은 접촉 기록의 존재만 나타내며 raw lambda를 힘 단위로 환산하지 않았다. 짧은 contact window나 양의 raw lambda가 지속 지지를 보증하지 않는다.

### Constant 목표 보정 곡선

![네 constant-target 조건의 기타·palm 저장 응답](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/artifacts/palm_finite_response_constant.png)

Full correction은 palm point 오차를 baseline 14.208 mm에서 6.671 mm로 낮췄지만, 기타 최대오차는 5.108 mm/0.969°에서 8.219 mm/1.292°로 커졌고 접촉 기록도 step 1–8에 한정된다. 따라서 낮은 palm task 값이나 방향각만으로 이 조건을 채택하지 않았다.

### 기존 tracking PI 조건 곡선

![baseline tracking과 quarter-correction tracking의 기타·palm 저장 응답](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/artifacts/palm_finite_response_tracking.png)

Quarter tracking은 baseline tracking보다 palm point 오차가 12.187→9.712 mm로 줄었지만, 기타 위치 오차 차이는 0.014581 mm, 회전 오차 차이는 0.000453°에 그친다. Baseline tracking의 palm contact 기록은 step 1–2, quarter tracking은 step 1–4이며 두 조건 모두 양의 raw lambda 기록은 없다. 이 작은 차이는 기타 개선이나 지속 지지를 인증하지 않는다.

### 저장된 Isaac Gym camera 비교

다음 이미지는 corrected-bias와 quarter-tracking 각각의 실제 Gym camera step 0/24를 front/side로 배열했다. 청록 다각형은 같은 시점의 source target polygon, 주황 점은 저장 pose로 변환한 source palmar-facet 점이다. Overlay는 캡처 뒤에 추가했으며 cooked 접촉점·압력 중심이 아니다.

각 montage는 위 행이 step 0, 아래 행이 step 24이며 왼쪽은 front, 오른쪽은 side view다.

![실제 Gym camera: corrected-bias 실행의 step 0/24](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/artifacts/palm_finite_response_camera_corrected_bias.png)

![실제 Gym camera: quarter-tracking 실행의 step 0/24](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/artifacts/palm_finite_response_camera_quarter_tracking.png)

Camera capture는 저장 PD 명령을 실제 Gym에서 다시 실행한 결과이며 pose 재생이나 MuJoCo 그림이 아니다. 이 phase는 장기 안정성·연주 성공을 판정하지 않았고 새 bias/strap 길이를 최종 채택하지 않았다. 다음 진단은 접촉이 생기는 경계에서 손과 기타 응답을 함께 측정해야 하며, 12개 작은 축 probe만으로 기타 p/q 제어 응답을 식별했다고 볼 수 없다.

## 재현과 검수

```bash
MPLCONFIGDIR=/tmp/palm_finite_response_mpl MPLBACKEND=Agg \
  python /home/ajou/yigyu/3/stability_adapter_2/plot_palm_finite_response.py \
  --out-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/reproduction_artifacts
```

Producer는 analysis, 선택 raw, 두 camera report/state, 28개 camera frame, facet input, overlay helper와 producer를 첫 데이터 읽기/helper import 전에 SHA 봉인하고 완료 후 같은 파일을 다시 확인한다. 실제 산출물 해시와 plot 실행 기록은 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/CHANGED_FILES.md)에 있다. [별도 change-reviewer 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/review.md:7)를 완료했고 Critical/Warning/Suggestion은 없다. 지속 지지·연주 성공은 미완료다.
