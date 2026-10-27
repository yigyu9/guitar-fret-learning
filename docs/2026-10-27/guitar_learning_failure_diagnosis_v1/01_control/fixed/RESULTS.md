# 관절 제어 행렬 분석

기타 조건: fixed.

현재 저장된 실제 GPU 진단 자료의 CPU 분석이다. 새 학습·재시뮬레이션은 수행하지 않았다.

각 모드는21관절×양방향×2프로토콜=84행이다. 실패가 발생한 표본부터 제외하며, 미완료 구간을 통과로 세지 않는다. 동일 행·동일 명목 목표각 비교와 동일 출력값의 의미 차이 비교를 구분한다.

| 모드 | 실패/84 | 추종 완료 창/84 | 완료 창 중 p95≤10° | B 완료 행/84 | B 통과 손가락 검사/336 | 최대 목표속도(rad/s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| incremental | 0 | 84 | 84 | 84 | 336 | 0.969136 |
| position | 0 | 84 | 84 | 84 | 336 | 4.000003 |

추종 창은 목표궤적42행의3~4초 및5.5~6초다. 240Hz 끝점 포함 표본의 선택 관절 |실제−목표| p95를 계산한다. 이 기준은 공학 진단 기준이며 무접촉을 인증하지 않는다. B는11.5~12초의60Hz31프레임×4축을 손가락마다 합쳐 RMS≤10°·최대≤20°인지 검사한다. 엄지는 B에서 제외한다.

## 관절별 추종

| 모드 | 행 | 관절 | 부호 | 3~4초 p95(°) | 5.5~6초 p95(°) | 두 창 완전관측 |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| incremental | 0 | LH:thumb1_x | -1 | 0.000 | 0.070 | True |
| incremental | 1 | LH:thumb1_x | +1 | 0.030 | 0.009 | True |
| incremental | 2 | LH:thumb1_y | -1 | 0.021 | 0.049 | True |
| incremental | 3 | LH:thumb1_y | +1 | 0.033 | 0.101 | True |
| incremental | 4 | LH:thumb1_z | -1 | 0.036 | 1.979 | True |
| incremental | 5 | LH:thumb1_z | +1 | 1.980 | 0.078 | True |
| incremental | 6 | LH:thumb2 | -1 | 0.033 | 0.045 | True |
| incremental | 7 | LH:thumb2 | +1 | 0.034 | 0.112 | True |
| incremental | 8 | LH:thumb3 | -1 | 0.012 | 0.070 | True |
| incremental | 9 | LH:thumb3 | +1 | 0.010 | 0.090 | True |
| incremental | 10 | LH:index1_x | -1 | 0.370 | 1.509 | True |
| incremental | 11 | LH:index1_x | +1 | 1.502 | 0.396 | True |
| incremental | 12 | LH:index1_z | -1 | 1.297 | 3.311 | True |
| incremental | 13 | LH:index1_z | +1 | 3.300 | 1.315 | True |
| incremental | 14 | LH:index2 | -1 | 0.002 | 0.236 | True |
| incremental | 15 | LH:index2 | +1 | 0.214 | 0.026 | True |
| incremental | 16 | LH:index3 | -1 | 0.000 | 0.065 | True |
| incremental | 17 | LH:index3 | +1 | 0.040 | 0.027 | True |
| incremental | 18 | LH:middle1_x | -1 | 0.215 | 0.261 | True |
| incremental | 19 | LH:middle1_x | +1 | 0.234 | 0.241 | True |
| incremental | 20 | LH:middle1_z | -1 | 4.791 | 0.157 | True |
| incremental | 21 | LH:middle1_z | +1 | 0.141 | 4.785 | True |
| incremental | 22 | LH:middle2 | -1 | 0.001 | 0.025 | True |
| incremental | 23 | LH:middle2 | +1 | 0.002 | 0.027 | True |
| incremental | 24 | LH:middle3 | -1 | 0.000 | 0.013 | True |
| incremental | 25 | LH:middle3 | +1 | 0.000 | 0.013 | True |
| incremental | 26 | LH:ring1_x | -1 | 0.090 | 4.416 | True |
| incremental | 27 | LH:ring1_x | +1 | 4.402 | 0.116 | True |
| incremental | 28 | LH:ring1_z | -1 | 3.754 | 1.831 | True |
| incremental | 29 | LH:ring1_z | +1 | 1.835 | 3.770 | True |
| incremental | 30 | LH:ring2 | -1 | 0.004 | 0.010 | True |
| incremental | 31 | LH:ring2 | +1 | 0.000 | 0.018 | True |
| incremental | 32 | LH:ring3 | -1 | 0.001 | 0.107 | True |
| incremental | 33 | LH:ring3 | +1 | 0.093 | 0.014 | True |
| incremental | 34 | LH:pinky1_x | -1 | 2.602 | 0.016 | True |
| incremental | 35 | LH:pinky1_x | +1 | 0.002 | 2.599 | True |
| incremental | 36 | LH:pinky1_z | -1 | 4.442 | 4.265 | True |
| incremental | 37 | LH:pinky1_z | +1 | 4.253 | 4.458 | True |
| incremental | 38 | LH:pinky2 | -1 | 0.356 | 0.024 | True |
| incremental | 39 | LH:pinky2 | +1 | 0.002 | 0.375 | True |
| incremental | 40 | LH:pinky3 | -1 | 0.000 | 0.014 | True |
| incremental | 41 | LH:pinky3 | +1 | 0.001 | 0.015 | True |
| position | 0 | LH:thumb1_x | -1 | 0.000 | 0.070 | True |
| position | 1 | LH:thumb1_x | +1 | 0.030 | 0.009 | True |
| position | 2 | LH:thumb1_y | -1 | 0.021 | 0.049 | True |
| position | 3 | LH:thumb1_y | +1 | 0.033 | 0.101 | True |
| position | 4 | LH:thumb1_z | -1 | 0.036 | 1.980 | True |
| position | 5 | LH:thumb1_z | +1 | 1.976 | 0.077 | True |
| position | 6 | LH:thumb2 | -1 | 0.033 | 0.045 | True |
| position | 7 | LH:thumb2 | +1 | 0.034 | 0.112 | True |
| position | 8 | LH:thumb3 | -1 | 0.012 | 0.070 | True |
| position | 9 | LH:thumb3 | +1 | 0.010 | 0.090 | True |
| position | 10 | LH:index1_x | -1 | 0.370 | 1.509 | True |
| position | 11 | LH:index1_x | +1 | 1.502 | 0.396 | True |
| position | 12 | LH:index1_z | -1 | 1.297 | 3.311 | True |
| position | 13 | LH:index1_z | +1 | 3.300 | 1.315 | True |
| position | 14 | LH:index2 | -1 | 0.002 | 0.236 | True |
| position | 15 | LH:index2 | +1 | 0.214 | 0.026 | True |
| position | 16 | LH:index3 | -1 | 0.000 | 0.065 | True |
| position | 17 | LH:index3 | +1 | 0.040 | 0.027 | True |
| position | 18 | LH:middle1_x | -1 | 0.215 | 0.261 | True |
| position | 19 | LH:middle1_x | +1 | 0.234 | 0.241 | True |
| position | 20 | LH:middle1_z | -1 | 4.791 | 0.157 | True |
| position | 21 | LH:middle1_z | +1 | 0.141 | 4.785 | True |
| position | 22 | LH:middle2 | -1 | 0.001 | 0.025 | True |
| position | 23 | LH:middle2 | +1 | 0.002 | 0.027 | True |
| position | 24 | LH:middle3 | -1 | 0.000 | 0.013 | True |
| position | 25 | LH:middle3 | +1 | 0.000 | 0.013 | True |
| position | 26 | LH:ring1_x | -1 | 0.090 | 4.416 | True |
| position | 27 | LH:ring1_x | +1 | 4.402 | 0.116 | True |
| position | 28 | LH:ring1_z | -1 | 3.754 | 1.850 | True |
| position | 29 | LH:ring1_z | +1 | 1.835 | 3.768 | True |
| position | 30 | LH:ring2 | -1 | 0.004 | 0.010 | True |
| position | 31 | LH:ring2 | +1 | 0.000 | 0.018 | True |
| position | 32 | LH:ring3 | -1 | 0.001 | 0.107 | True |
| position | 33 | LH:ring3 | +1 | 0.094 | 0.014 | True |
| position | 34 | LH:pinky1_x | -1 | 2.602 | 0.016 | True |
| position | 35 | LH:pinky1_x | +1 | 0.002 | 2.599 | True |
| position | 36 | LH:pinky1_z | -1 | 4.442 | 4.265 | True |
| position | 37 | LH:pinky1_z | +1 | 4.254 | 4.457 | True |
| position | 38 | LH:pinky2 | -1 | 0.356 | 0.024 | True |
| position | 39 | LH:pinky2 | +1 | 0.002 | 0.375 | True |
| position | 40 | LH:pinky3 | -1 | 0.000 | 0.014 | True |
| position | 41 | LH:pinky3 | +1 | 0.001 | 0.015 | True |

## 지속 출력 편향

1~6초에 같은 부호의0.05를 입력했다. incremental에서는 unclamped1rad(약57.296°)의 누적 요청이고, position에서는 초기 참조와 부호별 native 범위에 의해 정해지는 고정 목표각이다. 동일 행동값은 동일한 물리 입력이 아니다.

| 모드 | 행 | 관절 | 부호 | 목표각 변화(°) | 실제각 변화(°) | 완전관측 |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| incremental | 42 | LH:thumb1_x | -1 | -0.000 | 0.000 | True |
| incremental | 43 | LH:thumb1_x | +1 | 40.000 | 39.990 | True |
| incremental | 44 | LH:thumb1_y | -1 | -31.607 | -15.511 | True |
| incremental | 45 | LH:thumb1_y | +1 | 57.296 | 55.612 | True |
| incremental | 46 | LH:thumb1_z | -1 | -0.165 | -0.165 | True |
| incremental | 47 | LH:thumb1_z | +1 | 57.296 | 17.369 | True |
| incremental | 48 | LH:thumb2 | -1 | -57.296 | -55.607 | True |
| incremental | 49 | LH:thumb2 | +1 | 22.644 | 22.610 | True |
| incremental | 50 | LH:thumb3 | -1 | -48.817 | -48.806 | True |
| incremental | 51 | LH:thumb3 | +1 | 46.183 | 46.173 | True |
| incremental | 52 | LH:index1_x | -1 | -57.296 | -53.241 | True |
| incremental | 53 | LH:index1_x | +1 | 49.446 | 27.072 | True |
| incremental | 54 | LH:index1_z | -1 | -54.868 | -32.656 | True |
| incremental | 55 | LH:index1_z | +1 | 5.132 | 1.803 | True |
| incremental | 56 | LH:index2 | -1 | -51.897 | -51.850 | True |
| incremental | 57 | LH:index2 | +1 | 38.103 | 30.519 | True |
| incremental | 58 | LH:index3 | -1 | -25.751 | -25.752 | True |
| incremental | 59 | LH:index3 | +1 | 57.296 | 54.708 | True |
| incremental | 60 | LH:middle1_x | -1 | -57.296 | -54.452 | True |
| incremental | 61 | LH:middle1_x | +1 | 26.673 | 18.914 | True |
| incremental | 62 | LH:middle1_z | -1 | -39.463 | -11.593 | True |
| incremental | 63 | LH:middle1_z | +1 | 0.537 | 0.393 | True |
| incremental | 64 | LH:middle2 | -1 | -38.352 | -38.353 | True |
| incremental | 65 | LH:middle2 | +1 | 51.648 | 45.197 | True |
| incremental | 66 | LH:middle3 | -1 | -0.063 | -0.063 | True |
| incremental | 67 | LH:middle3 | +1 | 57.296 | 55.867 | True |
| incremental | 68 | LH:ring1_x | -1 | -57.296 | -55.298 | True |
| incremental | 69 | LH:ring1_x | +1 | 42.756 | 26.034 | True |
| incremental | 70 | LH:ring1_z | -1 | -32.516 | -11.839 | True |
| incremental | 71 | LH:ring1_z | +1 | 7.484 | 5.642 | True |
| incremental | 72 | LH:ring2 | -1 | -57.296 | -55.949 | True |
| incremental | 73 | LH:ring2 | +1 | 0.674 | 0.670 | True |
| incremental | 74 | LH:ring3 | -1 | -0.000 | -0.000 | True |
| incremental | 75 | LH:ring3 | +1 | 57.296 | 55.178 | True |
| incremental | 76 | LH:pinky1_x | -1 | -57.296 | -32.731 | True |
| incremental | 77 | LH:pinky1_x | +1 | 0.473 | 0.470 | True |
| incremental | 78 | LH:pinky1_z | -1 | -9.174 | -4.426 | True |
| incremental | 79 | LH:pinky1_z | +1 | 50.826 | 25.478 | True |
| incremental | 80 | LH:pinky2 | -1 | -22.643 | -20.205 | True |
| incremental | 81 | LH:pinky2 | +1 | 57.296 | 54.975 | True |
| incremental | 82 | LH:pinky3 | -1 | -1.026 | -1.026 | True |
| incremental | 83 | LH:pinky3 | +1 | 57.296 | 55.868 | True |
| position | 42 | LH:thumb1_x | -1 | -0.000 | -0.000 | True |
| position | 43 | LH:thumb1_x | +1 | 2.000 | 1.969 | True |
| position | 44 | LH:thumb1_y | -1 | -1.580 | -1.582 | True |
| position | 45 | LH:thumb1_y | +1 | 2.920 | 2.922 | True |
| position | 46 | LH:thumb1_z | -1 | -0.008 | -0.008 | True |
| position | 47 | LH:thumb1_z | +1 | 4.492 | 4.495 | True |
| position | 48 | LH:thumb2 | -1 | -3.368 | -3.368 | True |
| position | 49 | LH:thumb2 | +1 | 1.132 | 1.132 | True |
| position | 50 | LH:thumb3 | -1 | -2.441 | -2.441 | True |
| position | 51 | LH:thumb3 | +1 | 2.309 | 2.309 | True |
| position | 52 | LH:index1_x | -1 | -4.028 | -3.726 | True |
| position | 53 | LH:index1_x | +1 | 2.472 | 2.190 | True |
| position | 54 | LH:index1_z | -1 | -2.743 | -2.332 | True |
| position | 55 | LH:index1_z | +1 | 0.257 | 0.227 | True |
| position | 56 | LH:index2 | -1 | -2.595 | -2.589 | True |
| position | 57 | LH:index2 | +1 | 1.905 | 1.893 | True |
| position | 58 | LH:index3 | -1 | -1.288 | -1.288 | True |
| position | 59 | LH:index3 | +1 | 3.462 | 3.458 | True |
| position | 60 | LH:middle1_x | -1 | -5.166 | -5.036 | True |
| position | 61 | LH:middle1_x | +1 | 1.334 | 1.299 | True |
| position | 62 | LH:middle1_z | -1 | -1.973 | -1.436 | True |
| position | 63 | LH:middle1_z | +1 | 0.027 | 0.021 | True |
| position | 64 | LH:middle2 | -1 | -1.918 | -1.918 | True |
| position | 65 | LH:middle2 | +1 | 2.582 | 2.583 | True |
| position | 66 | LH:middle3 | -1 | -0.003 | -0.003 | True |
| position | 67 | LH:middle3 | +1 | 4.747 | 4.747 | True |
| position | 68 | LH:ring1_x | -1 | -4.362 | -4.315 | True |
| position | 69 | LH:ring1_x | +1 | 2.138 | 2.021 | True |
| position | 70 | LH:ring1_z | -1 | -1.626 | -1.366 | True |
| position | 71 | LH:ring1_z | +1 | 0.374 | 0.316 | True |
| position | 72 | LH:ring2 | -1 | -4.466 | -4.466 | True |
| position | 73 | LH:ring2 | +1 | 0.034 | 0.034 | True |
| position | 74 | LH:ring3 | -1 | -0.000 | -0.000 | True |
| position | 75 | LH:ring3 | +1 | 4.750 | 4.750 | True |
| position | 76 | LH:pinky1_x | -1 | -6.476 | -4.695 | True |
| position | 77 | LH:pinky1_x | +1 | 0.024 | 0.023 | True |
| position | 78 | LH:pinky1_z | -1 | -0.459 | -0.232 | True |
| position | 79 | LH:pinky1_z | +1 | 2.541 | 1.285 | True |
| position | 80 | LH:pinky2 | -1 | -1.132 | -1.132 | True |
| position | 81 | LH:pinky2 | +1 | 3.368 | 3.368 | True |
| position | 82 | LH:pinky3 | -1 | -0.051 | -0.051 | True |
| position | 83 | LH:pinky3 | +1 | 4.699 | 4.699 | True |

## 초안 판단과 해석 한계

- incremental: 계획84개 추종 창 중 완전 관측84개, 그중 p95≤10°는84개다. B 검사336개 중 완전 관측과 각도 기준을 함께 만족한 것은336개다. 실패한 행도 전체 분모에 남겼다.
- position: 계획84개 추종 창 중 완전 관측84개, 그중 p95≤10°는84개다. B 검사336개 중 완전 관측과 각도 기준을 함께 만족한 것은336개다. 실패한 행도 전체 분모에 남겼다.

이 비교는 스크립트 목표 제어의 응답이며 학습 정책의 자연스러움·음악 성공·두 제어 방식의 학습 성능 비교가 아니다. raw0은 누적 제어에서 목표 유지, 위치 제어에서 준비 참조 목표 복귀이므로 별도 분석했다. 목표각 한계 체류와 실제각 한계 체류는 JSON에서 분리했으며 native 경계1e−6rad와 공학 근접1°를 같은 항목으로 세지 않는다. 60Hz 전손 관절 지표와240Hz 선택 관절 지표도 구분한다.

순힘 크기는 접촉 상대나 무접촉을 인증하지 않는다. 제출 effort_selected가0이어도 native POSITION drive의 실제 토크가0이라는 뜻이 아니다. 실제 모터 토크·effort 포화는 이 로그에서 측정하지 않았다. body_state는 환경0만 저장돼 다른83행의 충돌·몸체 자세를 이 배열로 주장할 수 없다. 실행기의 hard-failure 조건은 기타 변위/회전·속도·지지 방향 검사이며 전체 학습 종료 조건과 같다고 간주하지 않는다.

표본을 잃은 구간은 available-sample 수치와 complete 여부를 함께 확인한다. 240Hz 체류시간은 유효 표본 수/240의 이산 지표이며 보간한 연속 접촉 시간이 아니다. 상세값과 입력 SHA는 `analysis.json`, 행별 요약은 `analysis.csv`에 있다.

## 실제 수치에 근거한 해석

- incremental: 첫1초 선택축 추종오차 p95의 행별 최대는0.142°다. 목표궤적 실패0/42, 편향실험 실패0/42다. 마지막 B창 완전관측은84/84행이며 그 행들의 손가락별4축 RMS 최대는4.400°, 관절 최대 절대오차는8.360°다. 미관측 행을 빼고 전체 B 도달률을 주장하지 않는다.
- position: 첫1초 선택축 추종오차 p95의 행별 최대는0.142°다. 목표궤적 실패0/42, 편향실험 실패0/42다. 마지막 B창 완전관측은84/84행이며 그 행들의 손가락별4축 RMS 최대는3.765°, 관절 최대 절대오차는7.014°다. 미관측 행을 빼고 전체 B 도달률을 주장하지 않는다.
- 같은 양모드 완료 편향행42/42에서 목표각 변화 절댓값 중앙값은 누적41.378°, 위치2.069°다. 작은 지속 출력이 누적 제어에서 큰 각도 요청으로 변하는 구조를 확인한다. 두 모드의 동일0.05는 서로 다른 물리 입력이므로 학습 우열의 증거로 쓰지 않는다.
- 완전관측된 작은 목표궤적의 추종이 양호하더라도, 접촉 부하·큰 편향·여러 손가락의 B 동시 이동에서 기타가 이탈한 원인은 별도로 봐야 한다. B 미완료만으로 B 각도 자체가 도달 불가능하다고 결론 내리지 않는다. 자유/고정 대조와 관절 추종을 함께 해석한다.
- native 범위1e−6rad 초과 여부는 엄격 수치 진단이고1° 근접 체류와 다르다. 미세한 물리 범위 초과가 있으면 그 크기를 기록하되 이를 큰 관절 발산이나 코드의 목표각 범위 위반으로 확대하지 않는다.
