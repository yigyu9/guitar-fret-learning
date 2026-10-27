# 음악 조건 공동 정책 구현 검수 v1

2026-10-15. change-reviewer의 독립 검수 기록이다. 구현 소스와 기존 결과는 수정하지 않았다.

## 요약 판정

문제없음. 검토한 수정본에서 B의 native 기준 실행과 계획된 scratch 16갱신×256전이 pilot을 막는 Critical은 발견하지 못했다. 이는 구현과 제한된 검증 실행에 대한 판정이며, 압현·타현 학습 성공이나 C/D 구절 수행을 인증하지 않는다.

## 검수 범위와 확인

- [구현 계획](/home/ajou/yigyu/3/docs/plans/fresh_music_implementation_20261015.md), [이벤트 입력](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/events.py), [native 환경](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/environment.py), [실행기](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/run.py), launcher 및 해당 세 테스트 파일을 확인했다. [모션 내보내기](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/export_motion.py)는 실제 상태 저장 경로와 형식 검증을 확인했다.
- 현재 소리가 이어지는 줄 목표가 미래 준비 목표에 덮이지 않는다. 서로 다른 프렛·손가락의 실제 가청 구간 충돌은 거부하며, 지원되지 않는 원본 이벤트 ID와 선택한 구간·시간 변환을 metadata에 남긴다. 원본 긴 press/release와 선택 음의 sustain을 구분한다.
- 움직이는 기타 좌표계에서 실제 줄 구간과 프렛 간격을 사용한다. 타현 후보는 240Hz 궤적의 유한 줄 통과이며, 압현이 필요한 경우 같은 프렛·할당 손가락의 접촉·기하가 통과 양경계에서 유효하고 직전 연속 준비시간이 0.1초 이상이어야 한다. 학습 허용창 ±100ms와 별도 ±50ms 집계가 분리되어 있다.
- 압현 유지의 분모는 선택 음의 onset부터 sustain/release의 이른 시점까지다. 준비 접근은 유지 실적으로 세지 않으며, 같은 소유자의 겹친 음은 각 음의 가청 구간에만 실적을 쌓는다. 줄별 dwell을 한 번만 갱신한다. 후보 유지·해제 완료는 실행의 정상 완료와 별도 필드다.
- 54개 행동의 단일 목표 경로와 나머지 27개 목표 보존 검사, root·하체 고정 및 금지 API 검사를 유지한다. 실제 native q81/qdot81과 기타 root body pose/twist를 전이에 저장한다. 내보내기는 기존 skeleton/assets를 필요로 하는 native 궤적이며 BVH/FBX retargeting 결과가 아니다.
- 정책은 신규 음악 관측 744차원에 맞춰 난수 초기화한다. 명시적 음악 checkpoint 재개만 허용하며 schema·네트워크/PPO 설정·음악/물리/관측/입력 SHA 계약을 대조한다. 종료는 terminal과 time truncation을 구분하고 reset 이전 최종 관측으로 bootstrap한다.
- 명령을 물리 step 전에 기록한다. 검증 오류는 fatal이며 미완료 rollout은 PPO 갱신에 전달되지 않는다. 중단된 optimizer 갱신의 checkpoint 재개는 거부한다. 평가 전이 수는 누적 학습 전이 수에 합산하지 않는다. 누적 갱신 목표와 현재 프로세스 실적을 구분한다.

## 검증

`python -m unittest stability_adapter_2.fresh_music_v1.test_events stability_adapter_2.fresh_music_v1.test_environment stability_adapter_2.fresh_music_v1.test_runner -v`: 22개 통과(events 7, environment 11, runner 4). 신규 Python 파일 AST 검사와 launcher의 `bash -n` 검사도 통과했다.

Critical 없음. 수정이 필요한 추가 Warning은 발견하지 못했다. 앞서 확인한 미래 목표 덮어쓰기, stale readiness/다른 손가락의 crossing 허용, 유지 분모와 중복 dwell, 평가 누적계수 문제는 수정본과 회귀 검사에서 해소되었다.

## 판정의 한계

이번 기록 시점의 판정은 정적 검수와 CPU 계약 검사에 근거한다. native 기준 실행·제한 학습·저장 정책 평가의 실제 수치와 입력 보존은 별도 실행 원자료와 root의 최종 감사로 확인해야 한다. 접촉은 할당 distal body와 기타 사이의 native 접촉 후보이며 실제 줄 압력·진동·음향을 검증하지 않는다. 기타 회전 비용은 허용 회전 집합까지의 인증된 정확 최단거리가 아닌 feasible upper bound를 사용한다. C/D 전체 시간축이 실행되더라도 음악 과제 성공과 구분해야 한다.
