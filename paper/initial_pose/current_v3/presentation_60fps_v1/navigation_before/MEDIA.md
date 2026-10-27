# 현재 자세의 이미지와 영상

기존 native v14 물리 실행에서 기록한 화면이다. Root 고정·하체 유한 제어·자유 기타·중력 ON·스트랩 OFF 조건이다. 영상은 5fps이며 원래 물리 기록은 240Hz다. 전신 영상의 주요 시간대 프레임과 MP4의 보조 시점을 확인했다. 영상 외관만으로 접촉력·현 통과·음향을 판정하지 않는다.

## 준비 완료 자세

baseline 실행의 **22초, physics step 5280**이다. 준비 정지 구간 17–22초의 끝이며 출발 candidate의 0초 화면과 구분한다. 아래 세 이미지는 저장 원본과 바이트가 동일하다.

![준비 후 22초 전신, baseline v14](/home/ajou/yigyu/3/paper/initial_pose/current_v3/images/prepared_22s_whole_body.png)

[측면 보조 시점 — 원래 이름 hands](/home/ajou/yigyu/3/paper/initial_pose/current_v3/images/prepared_22s_hands.png) · [발 시점](/home/ajou/yigyu/3/paper/initial_pose/current_v3/images/prepared_22s_feet.png) · [같은 실행·시각의 실제 관절 및 바디 상태](/home/ajou/yigyu/3/paper/initial_pose/current_v3/pose/prepared_state_baseline_v14_22s.json)

## 해제 상태 타현

주요 관찰 구간은 **27–39초**, 세 왕복 시작 시각은 27/31/35초다. 왼손·왼팔 전체 해제 판정 구간은 25–40초다. 여섯 줄 통과는 별도 기하 측정에서 확인했으며 실제 발음 검증은 아니다.

![해제 상태 타현 전신 영상, native_free_strike_v14](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/free_strike_whole_body.mp4)

## 넥 재접촉과 준비 복귀

주요 관찰 구간은 **40–49초**다. 접근 40–42초, 닫기 42–43초, 정착 43–44초, 준비 유지 44–49초로 구분한다. 왼손 손가락–넥 접촉률은 마지막 준비 유지에서 100%이며 재접촉 전체 구간의 100%를 뜻하지 않는다.

![넥 재접촉과 준비 복귀 전신 영상, native_regrasp_v14](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/regrasp_whole_body.mp4)

## 전체 영상 목록

`hands`라는 원래 영상명은 보존했지만 실제 화면은 측면 보조 시점이며 손의 확대 영상으로 해석하지 않는다. 모든 영상 링크는 같은 이름의 원본을 가리킨다. 0초와 마지막 시각 프레임을 모두 포함하므로 인코딩 길이는 실제 실행보다 0.2초 길다.

| 시험 | 실제 길이 | 주요 구간 | 전신 | 측면(hands) | 발 |
|---|---:|---|---|---|---|
| 정지 | 28초 | 17–22초 준비 유지 | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/baseline_whole_body.mp4) | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/baseline_hands.mp4) | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/baseline_feet.mp4) |
| 반복 타현 | 34초 | 22–34초, 세 왕복 | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/repeat_whole_body.mp4) | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/repeat_hands.mp4) | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/repeat_feet.mp4) |
| 왼손 완전 해제 | 40초 | 25–40초 해제 유지 | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/release_whole_body.mp4) | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/release_hands.mp4) | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/release_feet.mp4) |
| 해제 상태 타현 | 40초 | 27–39초 타현 | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/free_strike_whole_body.mp4) | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/free_strike_hands.mp4) | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/free_strike_feet.mp4) |
| 넥 재접촉 | 49초 | 40–49초 복귀 | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/regrasp_whole_body.mp4) | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/regrasp_hands.mp4) | [보기](/home/ajou/yigyu/3/paper/initial_pose/current_v3/videos/regrasp_feet.mp4) |

## 추가 대표 이미지

| 이미지 | 실제 실행과 시각 |
|---|---|
| [해제 상태 타현 중](/home/ajou/yigyu/3/paper/initial_pose/current_v3/images/free_strike_29s_whole_body.png) | free_strike v14, 29초 |
| [재접촉 시작 경계](/home/ajou/yigyu/3/paper/initial_pose/current_v3/images/released_40s_whole_body.png) | regrasp v14, 40초 |
| [준비 복귀 후](/home/ajou/yigyu/3/paper/initial_pose/current_v3/images/returned_49s_whole_body.png) | regrasp v14, 49초 |

각 이미지의 원본 경로·실제 시각·physics step·SHA는 [출처 목록](/home/ajou/yigyu/3/paper/initial_pose/current_v3/manifest.json)에 기록했다. 저장된 프레임과 영상은 자세·동작을 설명하는 자료이며 전체 성공 판정은 [RESULTS_v2](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/practical_criteria_v3/RESULTS_v2.md)를 따른다.
