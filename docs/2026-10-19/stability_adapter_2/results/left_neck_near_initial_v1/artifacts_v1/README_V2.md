# 왼손을 기타 넥 가까이에 둔 초기 배치와 실제 실행 기록

이 자료는 앞서 수행된 native hold 네 조건과 두 체크포인트 연결 한 조건, 총 다섯 실제 native 실행의 기록을 정리합니다. 다섯 조건의 초기 native 전체 상태는 같았습니다. 이번 문서·미디어 정리 단계에서 추가 물리 실행은 0회이며, 새 모델 변경과 학습도 없습니다. strap은 꺼져 있고 기타는 자유 상태였으며 root와 하체는 고정됐습니다. 기타에 힘을 직접 가하거나 런타임 자세를 덮어쓰지 않았습니다.

## 초기 손 배치

사용자 요청은 왼손 손바닥을 기타 넥 쪽에 두되 손가락 면 방향을 구분하는 것이었습니다. `LH:palm`은 기타 G 기준 +X(넥 아래면 쪽), 엄지는 −Z(기타 뒤쪽), 검지·중지·약지·새끼손가락은 +Z(현 앞쪽)를 향하도록 놓았습니다. 이 표기는 초기 점과 면의 배치 방향이지 연주 가능한 그립 판정이 아닙니다.

시작 native 자세에서 선택된 source collision facet까지 계산한 signed plane gap은 아래와 같습니다.

| 시작 부위 | 선택된 면 | source facet gap |
|---|---|---:|
| 손바닥 | underside | 12.56884 mm |
| 엄지 | back | 11.14977 mm |
| 검지 | strings_front | 4.93175 mm |
| 중지 | strings_front | 7.95631 mm |
| 약지 | strings_front | 10.29301 mm |
| 새끼손가락 | strings_front | 6.81150 mm |

![hold4 시작 손과 넥의 native 이미지 crop](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/native_hold4_hand_close_crop_v1.png)

이 거리는 선택된 source facet의 평면 간격입니다. 손바닥 패드나 지지면 전체를 식별한 값이 아니며 PhysX cooked 형상의 전체 최단거리·관통 인증도 아닙니다.

## 네 가지 정지 관찰

| 실행 | 제어 변경과 실제 경과 | 손목·손 결과 | 해석 |
|---|---|---|---|
| hold_v1 | 기존 위치 제어, 5.0초 | 끝점 손바닥 오차 133.93 mm | 손이 처져 초기 근접 배치를 유지하지 못함 |
| hold_v2 | 높은 위치 제어 게인을 외부화, 1.833333초 | `L_Elbow_y` 속도 −100.095 rad/s에서 안전 검사 중단 | 부분 실행이며 5초 완료로 세지 않음 |
| hold_v3 | 낮춘 명시 게인, 5.0초 | 끝점 손바닥 오차 77.10 mm | hold_v1보다 작지만 넥 위치 유지에는 부족 |
| hold_v4 | 사람 손목 관절에 제한된 준비 과제 추가, 5.0초 | 손목 오차 끝 17.00048 mm, 최대 17.01819 mm | 이 과제의 정지 관찰만 개선. 기타 접촉/지지 성공은 아님 |

hold_v4 손목 task의 30 N은 인간 관절 토크 계산에 쓰이는 가상 힘 요청의 상한입니다. 원본 `virtual_force_request_W_N` 1200개 행의 벡터 norm을 직접 계산한 최대 요청은 16.962012 N(step 577)입니다. 이 값은 기타에 가해진 힘이나 실제 접촉력 측정값이 아닙니다. 종료점의 source facet 간격은 손바닥 31.53746 mm, 현 앞 손가락 약 14.45–17.49 mm, 엄지 3.36285 mm로 기록됐습니다. 왼손–기타 endpoint 접촉 표시는 1200개 표본 중 0개였습니다. 이는 기록된 표본 범위이며 모든 물리 substep의 연속 비접촉 증명은 아닙니다. 기타 바디 bounding-box 중심은 9.29564 mm 이동했고 전체 SO(3) 방향 변화는 2.834565°였습니다.

![hold4 손 카메라의 0, 2, 5초 실제 native 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/native_hold4_hands_t0_2_5_v1.png)

손 카메라 이미지는 Isaac Gym native 렌더입니다. 기타 줄은 깊이 테스트된 시각 표시이며 물리 현의 굵기나 진동을 표현하지 않습니다.

## 두 체크포인트 연결 점검

두 체크포인트를 등록해 연결한 조건은 같은 시작 상태에서 2초 준비 구간 동안 추론을 대기한 뒤 동시 추론을 시작했습니다. 준비 구간은 physics step 0–479(2.0초)였고, step 480부터 손목 tracking task는 비활성화됐습니다. 그 뒤 26개 paired inference tick을 거쳐 총 물리 2.433333초, 584 step에서 첫 source 종료 조건으로 멈췄습니다. 분석은 종료를 `wrong_crossing_count_termination`으로 기록하며, 종료 시 손목·finger-back 안전 표식은 false, Fret `goal_finished` false, 실제 press 및 target hit false였습니다. 기록된 공동 음악 평가의 정산 event는 2건이며 두 건 모두 `joint_success=false`였습니다. 현 crossing counter는 4건입니다. 따라서 이 실행은 음악 완주나 음악 품질 평가가 아닙니다.

![체크포인트 연결 실행의 시작·준비 종료·종료 native 손 화면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/native_pair_hands_t0_2_end_v1.png)

종료 시 기타 바디 bounding-box 중심은 33.0647 mm, 전체 SO(3) 방향은 11.2172° 변했습니다. 종료 직전 기록된 88.67049 mm는 step 583에서 비활성화된 손목 task의 초기 기타 G 기준 손목 목표에 대한 관측 이탈입니다. 활성 준비 과제의 추적 오차가 아니므로 hold4의 17 mm 추적 결과와 직접 비교하지 않습니다.

## 원본 영상과 세부 기록

각 조건의 전신 및 왼손·넥 방향 카메라 영상은 아래 두 파일에서 확인할 수 있습니다. 모든 MP4는 원본 byte 그대로 복사했으며 재인코딩하지 않았습니다.

![hold4 전신 native 영상 · 5초 정지 관찰](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v4/whole_body.mp4)

![체크포인트 연결 전신 native 영상 · source 종료까지](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/pair_v1/whole_body.mp4)

- [10개 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/INDEX_V1.md)
- [원본·복사본 SHA-256 및 ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/manifest_v1.json)
- [기준 분석 `native_analysis_v3.json`](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/native_analysis_v3.json)
- [연결 실행 보고서](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/native_pair_v1/report.json)

**해석 범위:** 다섯 조건은 짧은 초기배치·제어 진단입니다. hold4의 한 번의 5초 정지 실행을 반복 재현성, 연주 중 손 위치 유지, 힘 분담, 해부학적 패드 접촉 또는 cooked 형상 안전의 인증으로 해석하지 않습니다. 다음 후보는 오른쪽 pick을 현재 기타 G 기준 READY 위치로 옮기고 현 교차에 진입시키면서, 왼쪽 Fret 손의 음별 압현을 확인하는 것입니다. 이 후속 시험은 이 자료에 포함되지 않습니다.


V2는 소비된 V1 설명의 범위·좌표 방향·손목 요청 힘 표기·연결 종료 해석을 바로잡은 문서입니다. V1, 그림, 원본 실행 자료, 영상 사본 및 manifest는 보존했습니다.
