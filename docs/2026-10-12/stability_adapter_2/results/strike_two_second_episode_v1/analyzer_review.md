# 가변 길이 분석기 독립 검수

판정: **수정 권장**. 완료된 정상 실행의 집계·시간 표시는 정합하며, 실패 부분 행을 분석하는 경계에 Warning 1건이 있다. Critical / Suggestion: 없음.

**Warning** — [analyze_strike_episode.py:33](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_episode.py:33): 모든 `actor_used` 행의 `info` 존재를 가정한다. [runner:315](/home/ajou/yigyu/3/stability_adapter_2/run_strike_two_second_episode.py:315)는 actor 기록 후 `view.step`을 호출하므로 이 호출의 예외로 보존된 마지막 행에는 `info`가 없을 수 있다. 실제 집계 AST에 해당 부분 행을 넣으면 `KeyError('info')`가 재현된다. 실패/부분 자료도 요약하려면 새 variant에서 미완료 actor 행을 별도 집계하고 pulse는 `info`가 있는 완료 행에서 합산하도록 권고한다. 현재 정상 실행 결과 분석을 차단하는 지적은 아니다. 소비 중 원문은 수정하지 않는다.

확인 범위:

- Python 3.8 AST 문법, `[bool]` 및 `[float]` pulse 집계의 실제 AST 계산을 확인했다. target-hit/physical-target-hit/release/miss/wrong count는 구분되며 물리 contact·음악 완주로 재해석하지 않는다.
- report의 episode outcome·정상/실패 종료·녹화 완료를 그대로 전달하며, `goal_finished`와 모든 음표 정확도·체크포인트 전이 성공을 구분한다.
- 고정 5초 가정 없이 report의 물리 step·duration, 실제 capture frame 수/마지막 step, 영상 ffprobe metadata를 전달한다. MP4 재생 길이를 물리 종료 시각으로 바꾸지 않는다. trace 위치 m→mm 변환과 회전 deg 집계는 맞다.
- 실제 입력은 **원자료/metadata 7개 + 분석기 자체 1개 = 8개**다. JSON 내용 읽기 전에 SHA를 저장하고 종료에 같은 목록을 재대조한다. 이는 직접 소비 파일 봉인이며 native 입력 closure와 영상/프레임 자체의 독립 재검증은 아니다. 영상 정보는 report metadata를 전달한다.

검수 SHA256: `72c605156bd93ae9d6be9745c23a690159f09a9199f925a6605b0bd7237b5aaa`. 읽기 전·후 변경 없음 확인. 검수 중 native 초기화·물리 실행·원자료/코드 변경은 0이다. 실제 완료 raw·영상·문서와 최종 수치는 후속 결과 검수 대상으로 남긴다.
