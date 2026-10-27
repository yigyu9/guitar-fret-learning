# 현재 기타 지지 관계 추종 v2

## 결과

v1과 같은 초기 자세 및 2초 준비를 사용했다. 무스트랩이며 root·하체 고정, 몸통 유지, 내부 충돌 조건이다. 손가락 21개는 정책이 계속 제어하고 checkpoint 가중치는 고정했다. 왼팔 9관절 목표는 준비 마지막에 제출된 PD 목표 ±0.1 rad와 초기 자세 기준 ±0.3 rad 및 native 범위 안에 두고, 변화율을 0.3 rad/s로 제한했다. 매 시점 기타의 현재 위치·자세에 맞춰 2초 시점의 손목–기타 상대 위치를 따라가며 부드러운 방향 목표를 썼다. source 손목 anchor를 명령하지 않았고, 기타나 사람 상태를 직접 덮어쓰거나 손바닥 접촉을 강제하지 않았다.

2초 시점의 상대 손목 위치는 기타 좌표계에서 `[0.060837, -0.021318, -0.100343] m`였다. source 손목 목표 `[0.075000, 0.112313, -0.022700] m`와의 거리는 155.2 mm다. 이 제어는 기타에 대한 손목 상대 위치 오차를 공통 2–11.133초 구간 평균 52.902 mm에서 49.746 mm로, 최대 62.413 mm에서 55.841 mm로 낮췄다. 최대 기타 회전 변화도 47.863°에서 19.408°로 줄었다.

반면 같은 구간 기타 root 최대 이동은 73.190 mm에서 126.888 mm로 커졌고, ON의 위치 상자 초과는 68.363 mm였다. source 손목 goal과 같은 548개 시점의 평균 오차는 ON에서 3.354 mm 증가했다. 646개 goal/time 표식의 평균 거리는 ON에서 32.480 mm 증가했으며, 표식 거리 크기는 압력이나 접촉 증거가 아니다. 기타의 현재 움직임을 따라가는 것만으로 기타가 허용 위치 안에 머물거나 손목이 source 손목 목표에 가까워지지는 않았다.

ON은 시뮬레이션 경과 11.133333초(2,672 physics step, 548 actor step, 335 프레임)에서 source의 wrong-press 종료로 끝났다. 영상은 t=0 프레임을 포함해 335/30 = 11.166667초 재생되며, 종료 후 시뮬레이션을 이어 실행한 시간이 아니다. `episode_goal_finished=false`, `episode_success=false`; 물리 프레스·프레스 성공·안정 프레스 성공률은 0이고, 지속 성공은 21개 이벤트 중 0개다. 17개 native 검사는 통과했고 최적화 표본 모두 수렴 판정을 받았다. 사전 검사는 root 소속 7개와 독립 reviewer 20개가 통과했다. 검증 분석 검사 16개 및 입력 2,229개 전후 해시 비교도 통과했다. 학습 업데이트는 0회다. 따라서 지지 관계 추종은 실제로 연결됐지만 안정화나 프렛 연주 성공은 달성하지 않았다.

다음 단계에는 기타 허용 위치 범위를 복원하는 지지 목표 교정과 연주 준비 초기 자세가 필요하다. 이 v2에서는 학습된 교정은 구현하지 않았다.

## native 녹화

아래 ON 영상은 Isaac Gym native COLOR camera 원본 프레임으로 기록했다. OFF 전체 및 손 영상은 같은 v1 보존 기준 기록이다.

![ON native 전체 몸 녹화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/ON/data/images/whole_body.mp4)

![ON native 손 녹화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/ON/data/images/hands.mp4)

[OFF native 전체 몸 녹화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/OFF/data/images/whole_body.mp4) · [OFF native 손 녹화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/OFF/data/images/hands.mp4)

## 같은 시점 native 비교 그림

각 PNG는 OFF와 ON의 동일 시각 raw native 프레임을 좌우로 놓는다. 아래 이미지는 위에서부터 2초, 3초, 공통 기록 끝 11.133초이며 각 쌍에 전체 몸과 손 화면이 있다. 렌더 위에 압력·접촉 표식을 합성하지 않았고, 시각만으로 접촉을 판정할 수 없다.

![2초 native 전체 몸 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/whole_body_480.png)

![2초 native 손 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/hands_480.png)

![3초 native 전체 몸 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/whole_body_720.png)

![3초 native 손 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/hands_720.png)

![11.133초 native 전체 몸 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/whole_body_2672.png)

![11.133초 native 손 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/hands_2672.png)

검증 분석 시간선의 위 패널은 **source 손목 anchor 오차**이며 지지 상대 위치 오차가 아니다. 그래프가 쓰는 wrist target 오차와 상대 지지 오차는 서로 다른 측정량이다. 분석은 고정된 Fret21 checkpoint를 쓰지만, 손가락 21개는 각 시점에 정책으로 계속 제어한다.

[검증 분석 시간선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/timeline.png)

## 원자료와 감사

- [analysis_verified/summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/summary.json), [interpretation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/interpretation.json), [matched_goals.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/matched_goals.json)
- [ON/data/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/ON/data/report.json), [ON/data/terminal_info.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/ON/data/terminal_info.json), [tests_pre.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/tests_pre.json)
- [analysis_verified_audit/inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified_audit/inputs_after.json): 검증 분석 단계에서 기록한 직접·재사용 입력 2,229개의 전후 변경은 없었다. 전체 phase 입력을 포괄하는 최신 SHA 주장은 아니며, 실행 전 소비 소스와 실행 뒤 추가된 진행 갱신본의 구분은 최종 감사 기록을 따른다.
- 독립 검수가 완료됐다: [review_final.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/review_final.md). 보존 감사와 소비한 소스 스냅샷·실행 후 진행 갱신본의 구분은 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/final_verification.json)에서, 전체 파일 목록과 SHA는 [artifact_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/artifact_inventory.json)에서 확인한다. 보존된 최종 소스: [source_final/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/source_final).
