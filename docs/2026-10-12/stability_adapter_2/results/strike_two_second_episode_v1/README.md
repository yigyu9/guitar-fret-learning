# 2초 준비 첫 실행: 기타 자세 범위 때문에 연결되지 않음

준비 최소 시간을2초로 변경한 실제 Isaac Gym 실행이다. 기존 손 조건·준비 위치·원래 기타 자세 범위를 유지하니2초 이후 기타의 Euler 범위 판정이 실패하여,10초에 `preparation_timeout`으로 종료했다. 체크포인트는 로드됐지만 actor 추론은0회이며 곡 시계도 진행하지 않았다. 에피소드 완주나 연주 실패 종료 영상으로 해석하지 않는다.

| 시점 | 준비 위치까지 거리 | 원래 기타 범위 | 초기 대비 기타 회전 |
|---|---:|---|---:|
| 1초 | 22.644mm | 안 | 4.052° |
| 1.5초 | 19.338mm | 안 | 3.098° |
| 2초 | 17.874mm | 밖 | 2.846° |
| 10초 | 17.088mm | 밖 | 3.046° |

2초의 위치 범위·왼손 손가락 접촉·손바닥 위쪽 방향·오른손 앞쪽/그립/비접촉·준비 거리 조건은 통과했다. 원래 허용 Euler [90,92.837746612,179.783932105]° reference와2초 실제 quaternion의 회전 차이는0.028954°였다. 후속v2는 진입에만0.1° 물리 회전 여유를 따로 기록하며 적용한다. 원래 strict 범위 판정은 계속 보존한다.

## 실제 장면과 영상

아래는2초 실제 native 카메라 장면이다. 기타 위치를 덮어쓴 설명 그림이 아니다.

![2초 준비 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v1/native/data/images/frames/whole_body/00060.png)

![준비 실패까지 전체 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v1/native/data/images/whole_body.mp4)

[손 확대 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v1/native/data/images/hands.mp4). 물리는0~10초/2400steps이며30fps 영상은301frames/10.033초다. 마지막 상태의 한 프레임 표시 시간을 포함한다. 모든 실행 체크와1122개 소비 입력의 실행 중 SHA 불변을 확인했다. CPU PhysX·실제 Isaac Gym 카메라이며 GPU 실행 동등성은 미검증이다.

[초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v1/native/data/initial_values.json), [원자료 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v1/native/data/report.json), [가변 길이 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v1/analysis/summary.json), [사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v1/pre_review.md).

기존 `analyze_strike_episode.py`는 부분 actor 행의 info 누락 처리에 검수 Warning이 있어 보존했다. 본 요약은 그 경우를 구분하는 새 `analyze_strike_episode_v2.py`를 사용한다. 분석기 실행은 native 재실행이 아니다. 기존 실험·공용 자산은 수정하지 않았다.
