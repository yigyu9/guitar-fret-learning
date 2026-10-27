# 전곡 목표 입력이 첫 음에 고정되는지 점검

`/root/reward_v2_warmstart`의 읽기 전용 점검이다. 소스 수정·추가 native 실행은 하지 않았다. [기존 모델의 실제 고정 평가 원자료](baseline_fixed_evaluation_v1/transitions.jsonl.gz)에서 마지막240Hz 표본의 `music.observation.priority_ids/target_ids/mask`를 확인했다.

| 정책 시각 | current priority | nearest strict deadline priority |
|---:|---|---|
| 0.0167초 | 없음 | note0,7프렛·2번현·약지 |
| 3.7000초 | note0 | note1,5프렛·2번현·검지 |
| 3.9833초 | note1 | note2,7프렛·3번현·약지 |
| 4.2000초 | note2 | note2 |

첫 future token도 note0→note1로 바뀐다. 두 priority 슬롯은 LH/RH 전용이 아니라 양 Actor가 함께 받는 현재 가장 일찍 끝나는 발음 목표와 미매칭 strict50ms 마감 목표다. 완화된 RH 성공과 strict50ms 매칭은 다르므로 skip 조건을 혼동하지 않는다.

- 매240Hz 표본의 실제 시계와 token 재생성: [task_measurement.py:132](/home/ajou/yigyu/3/guitar_learning/task_measurement.py:132), [task_measurement.py:169](/home/ajou/yigyu/3/guitar_learning/task_measurement.py:169).
- 이벤트는 onset≤now+4초, now≤end+.1초에서 제공되며 시간이 지나면 첫 음이 사라진다. priority도 strict매칭·마감·발음 구간에 따라 교체된다: [music_task.py:125](/home/ajou/yigyu/3/guitar_learning/music_task.py:125), [music_task.py:156](/home/ajou/yigyu/3/guitar_learning/music_task.py:156).
- state의 song.focus는 현재 또는 앞으로2초의 가장 가까운 목표다. 미래4초 정보는 별도64×24 이벤트 입력이다: [song/metrics.py:152](/home/ajou/yigyu/3/guitar_learning/song/metrics.py:152).
- 실제 builder가 token/priority를 복사하며 양 Actor가 attention과 직접 priority 경로로 소비한다: [observations.py:71](/home/ajou/yigyu/3/guitar_learning/observations.py:71), [policy.py:23](/home/ajou/yigyu/3/guitar_learning/policy.py:23), [specialist_policy.py:87](/home/ajou/yigyu/3/guitar_learning/specialist_policy.py:87).

기존 `test_song_task.SongTaskTests.test_overlap_and_token_capacity` 통과(0.047초). 파일 생성 없는 순수 token 계산에서도0~30.11초의 목표 교체와 strict매칭 후 deadline 이동을 확인했다. 따라서 관측이 첫 목표를 계속 명령하는 구현 문제는 발견되지 않았다. 바뀐 목표를 실제 동작으로 옮기는 능력, [행동 범위와 탐색](ACTION_AUTHORITY_AUDIT.md)을 구분해 검토해야 한다. 이는 모든 관측/정책 설계의 최적성을 입증하는 감사는 아니다.
