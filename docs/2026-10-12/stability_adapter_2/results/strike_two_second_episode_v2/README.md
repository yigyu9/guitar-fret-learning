# 2초 준비 후 Strike 종료까지 녹화

실제 Isaac Gym에서 **0~2초 준비 → 정확히2.00초 체크포인트 제어 시작 → 3.55초 원본 실패 종료**를 확인했다. 고정5초 cap은 제거했다. 이번 영상은42개 이벤트 완주 영상이 아니라, 잘못된 타현4회로 끝난 에피소드의 시작부터 종료 상태까지다.

| 항목 | 실측 결과 |
|---|---:|
| 준비 제어 | 120회 / 2초 / actor 미적용 |
| 체크포인트 제어 | 93회 / 1.55초 |
| 물리 실행 | 852steps / 3.55초 |
| 적시 타현 / 물리 타현 / RELEASE | 1 / 1 / 4 |
| miss / 잘못된 타현 | 1 / 4 |
| 기타 최대 이동 / 회전 | 46.354mm / 7.095° |
| 종료 이동 / 회전 | 33.342mm / 5.239° |
| 각 영상 | 108frames / 1280×720 / 30fps / 3.600초 |

물리 타현은 원본의 가상 피크 교차 판정이며, 손가락의 실제 접촉 횟수가 아니다.2.85초에 새끼손가락–기타 body 접촉 후보1행이 있었으나 raw lambda는0이었다. 저장된60Hz 접촉 표본에서 양의 lambda를 가진 오른손–기타 접촉은 없었다. 표본 사이 순간 접촉이나 mesh 간격을 전수 인증한 결과는 아니다.

## 전체 영상과 실제 장면

![2초 준비부터 원본 실패 종료까지 전체 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/native/data/images/whole_body.mp4)

[손 확대 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/native/data/images/hands.mp4). 마지막852step이30fps 격자 밖이라 실제 종료 상태를 한 프레임 추가했다. 영상 표시 길이3.600초와 실제 종료 시각3.55초를 구분한다. 종료 후 물리나 연주 제어를 계속하거나 정지 장면을 반복 추가하지 않았다.

![2초 전환 직전 실제 준비 자세](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/native/data/images/frames/whole_body/00060.png)

2초 장면은 마지막 준비 물리 상태다. 이 상태에서 기존 손 조건·준비 거리17.874mm를 확인하고 체크포인트를 적용했다. 기타는 자유 상태이고 스트랩은 없으며 root/하체는 고정 링크다.

![3.55초 원본 실패 종료 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/native/data/images/frames/whole_body/00107.png)

종료 frame에는 원본 `done=True` 직후 상태가 담겨 있다. 무동작 구간을 물리 평형이라고 설명하지 않는다. 원본 종료 이유는 `wrong_crossing_count_termination=True`; `goal_finished=False`다.

## 첫 시도의 준비 실패와 작은 진입 여유

[v1 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v1/README.md)는 최소2초 뒤 원래 Euler box를 충족하지 못해10초 준비 타임아웃/actor0회였다. v2는 위치 box를 유지하면서 진입 판단에만 원래 허용 회전 reference로부터0.1° 여유를 적용한다. 이는 원래 범위의 작은 물리 확장이며, 부동소수점 오류 수정이나 범위 완전 준수라고 표현하지 않는다.

2초 실제 자세는 원래 strict box 밖이고, bounds 안 reference [90,92.837746612,179.783932105]°와의 회전 차이는0.028954°였다. 원래 strict 결과와 여유를 적용한 entry 결과를 각각 저장한다. bounded 최적화가 찾은 허용 reference와의 거리이며 전역 최근접 해 인증은 아니다. 이 판정은 기타 상태를 변경하지 않는다.

## 검증과 다음 작업

모든 실행 체크와1127개 소비 입력의 실행 중 SHA 불변을 확인했다. v1/v2의 준비0~2초 native trace61개, 전환 전 control120개, 카메라 prefix61회×2시야는 동일했다. 두 시야는 전체 화면과 손 확대이며 별도 실험 횟수가 아니다. 보존 감사와 최종 검수는 별도 파일에 기록한다.

기존5초 결과의 적시 타현4회보다 이번2초 준비 전환은 적시1회로 악화됐다. **이번 완료 항목은2초 준비·종료까지 녹화 기능이며 연주 문제 해결은 아니다.** 다음 제어 실험은2초 준비 상태에서 연주로 넘어갈 때 오른팔 방향·피크 위치·목표 전환을 점검한다. 원본 타현 성공/실패 기준을 완화하지 않았다. CPU PhysX·실제 Isaac Gym 카메라이며 GPU 실행 동등성은 미검증이다.

[초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/native/data/initial_values.json), [원자료 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/native/data/report.json), [가변 길이 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/analysis/summary.json), [사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/pre_review.md).
