# 장기 학습 초기 경과

관측 시각(UTC): 2026-10-18T15:54:03.256325+00:00

실행 중 초기 prefix다. 2시간 완료·정책 개선·결정적 평가 결과가 아니다. 원자료는 early_status_v1.json이며 이후 실시간 경과와 구분한다.

Supervisor 경과 379.7초. 양손 returncode는 [None, None](종료 전). host 최소 여유 13.62GiB, 최신 13.77GiB, GPU peak 7603MiB.

## left

이번 실행 수락 업데이트 4회, 표본 7680개, 완료 episode 16회, 물리 실패 0회. 역할별 품질 성공 0 / 16, timing-only 성공 16 / 16.

완료 에피소드의 steps=[420], task_time_s=[7.0], 종료 이유={'timeline_complete': 16}. 다음 열린 episode=[{'worker_id': 0, 'episode_id': 1, 'ticks': 60, 'last_time_s': 1.0}] (대표 worker). 마지막 수락 KL=0.000553, actor LR=1.5625e-07, 마지막 retry=0.

음 구간 clean 접촉 후보 평균 100.0%, 해제 완료 0회, 해제 지연 누계 범위 [2.5478000000000005, 2.5478000000000005]초. 목표 접촉은 되지만 끝까지 누르는 문제가 남았다. 압력/음향 성공을 뜻하지 않는다.

## right

이번 실행 수락 업데이트 4회, 표본 7680개, 완료 episode 16회, 물리 실패 0회. 역할별 품질 성공 0 / 16, timing-only 성공 15 / 16.

완료 에피소드의 steps=[420], task_time_s=[7.0], 종료 이유={'timeline_complete': 16}. 다음 열린 episode=[{'worker_id': 0, 'episode_id': 1, 'ticks': 60, 'last_time_s': 1.0}] (대표 worker). 마지막 수락 KL=0.001615, actor LR=6.25e-07, 마지막 retry=0.

준비 후 수락 통과 합계 15, extra 합계 15, unprepared 합계 0, wrong-native-eligible 합계 15, 종료시 recovery 15회. 원시 잘못된 통과와 extra는 다른 분류이므로 합산 실패 횟수로 취급하지 않는다.

초기 두 손의 역할별 품질 성공은0이며 단순 실행 완료와 구분한다. 이미 학습한 모델에서 시작한 첫 배치이므로 이를 이번 장기 학습으로 얻은 개선이라고 설명하지 않는다. 반복 reset과 전체 구간이 실제 연결됨을 확인한 뒤 기존 예산대로 계속 실행한다.

생산169파일 및 실행입력6파일 SHA 재확인: {'source_pins_v1.json': {'count': 169, 'mismatches': []}, 'long_execution_pins_v1.json': {'count': 6, 'mismatches': []}}. 기존 실행과 모델은 보존했다.
