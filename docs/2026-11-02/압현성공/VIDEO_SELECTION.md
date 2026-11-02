# 대표 성공 영상

2026-11-01 정리 기준이다. 실험 유형별로 같은 모델·실행의 **손 확대1개·전신1개**를 남겼다. 실험의 성공 조건과 지원 조건이 서로 다르므로 아래 사례를 하나의 성공률로 합치지 않는다.

| 카테고리 | 대표 사례·해석 | 손 확대 | 전신 |
| --- | --- | --- | --- |
| 자유 기타 기하 재생 free_open | 검지3번줄4프렛. 관절각 명령 재생이며 학습 성과가 아님 | [손](video/free_open/index_s3_f4_hand.mp4) | [전신](video/free_open/index_s3_f4_full.mp4) |
| 실시간 손목 보정 기하 재생 free_live | 소지4번줄11프렛. 보정을 사용한 명령 재생 | [손](video/free_live/pinky_s4_f11_hand.mp4) | [전신](video/free_live/pinky_s4_f11_full.mp4) |
| 정렬된 팔 지원 학습 | 검지3번줄4프렛·100회. 팔 정렬을 정책이 학습한 결과는 아님 | [손](video/structured_press_v2/index_s3_f4_A_u100_hand.mp4) | [전신](video/structured_press_v2/index_s3_f4_A_u100_fullbody.mp4) |
| 준비 동작 개선 비교 | 중지·E4·100회. 해당 단일음 평가32/32 성공 사례 | [손](video/natural_press_v3_comparison_v1/review_seed7_E4_u100_hand.mp4) | [전신](video/natural_press_v3_comparison_v1/review_seed7_E4_u100_fullbody.mp4) |
| 전체33축 모델의 실행 해석 | 검지200회·seed7·요청 관절각 기댓값 실행. 기존 잠재 평균 실행과 구분 | [손](video/seven_hour_v1/full200_requested_angle_mean_hand.mp4) | [전신](video/seven_hour_v1/full200_requested_angle_mean_fullbody.mp4) |
| 전환 성공 유지 학습률 비교 | 보수 학습률·seed7·추가50회 모델. 촬영된 한 회의 두 음 전체 유지 확인. 모든 반복의 성공을 뜻하지 않음 | [손](../압현실험/동영상/16_성공유지학습률비교_conservative_best_seed7_추가50회_손확대.mp4) | [전신](../압현실험/동영상/16_성공유지학습률비교_conservative_best_seed7_추가50회_전신.mp4) |

실패 원인을 보여 주는 `video/learning/`, `target_transition_v2/`, `virtual_transition_v1/`는 성공 사례로 분류하지 않았다. 각 손가락별 두 영상 또는 기존 비교 진단을 보존한다. 별도 연구 입구의 번호별 영상은 목표·손가락·실행 방식별로 한 쌍이며, 학습률 비교 번호16의 중복 여섯 개를 정리했다.

원본 렌더는 보고서·SHA 검증 근거로 별도 보존했다. 공개 모음만 축소했으므로 원본 경로에 영상을 새로 복제하거나 보관 폴더로 숨겨 옮기지 않았다. 삭제 경로·SHA·문서 연결 변경은 [정리 원장](../../maintenance/video_selection_20261101/RESULT.json)에 기록했다. 현재6→8 연구의 동결 코드와 진행 중 산출물은 이 정리에서 수정하지 않았다.
