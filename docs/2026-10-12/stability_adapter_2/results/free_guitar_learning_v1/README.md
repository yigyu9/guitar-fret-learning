# 자유 기타 학습 환경 — 1단계 결과

현재035/v14 초기 자세에서 새 정책으로 제어권을 넘기는 환경 기반을 구현했다. 준비 자세 재현, 실제 관절 목표 전달, 움직이는 기타의 기하 관측을 확인했다. 음악 보상·압현/타현 성공 판정·PPO 학습은 다음 단계다.

## 이번에 구현한 것

- 기존 준비 절차를 실제로22초 수행한다. 저장된22초 상태를 simulator checkpoint처럼 주입하지 않는다.
- 정책의39개 정규화 행동을 준비 완료 시점의 최종 목표 주변 변화로 변환한다. 왼팔·왼손33개와 오른팔꿈치·손목6개다.
- 상체의 비정책42개 목표는 유지하고, 하체24개는 기존 발 유지 제어가 조절한다. 원105채널·비영범위97축·영범위8축을 보존한다.
- 원래의 position/effort 혼합 제어, 인체의 유한한 지지 피드백과 힘 제한을 유지한다. 별도PD를 중복 적용하지 않는다. 기존 왼손IK가 정책39개 목표를 다시 덮어쓰는 경로는 우회한다.
- 기타는 자유 강체·중력ON·스트랩OFF다. 고정 기타용 환경의 중력 해제·관절 상태 재주입 경로는 가져오지 않았다.
- 매240Hz 실제 상태에서 기타 좌표계의 줄·프렛·피크를 계산한다. 각 시각의 기타pose를 사용하고, 상대속도에는 기타 회전과COM/원점 차이를 반영한다.

[권장 환경 코드와 사용 범위](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/README.md) · [구현 범위와 기존 가정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/IMPLEMENTATION_SCOPE.md)

## 실제 연결 시험

새 초기화 두 번으로 총47초를 실제 실행했다. 첫 실행은 준비22초와 기존 유지1초, 두 번째는 준비22초와 정책 행동0의1초, 작은 비영 행동1초다. 마지막 두 구간은 같은 두 번째 실행에서 순서대로 수행했다. 음악 시계나 곡 연주는 아직 연결하지 않았다.

- 첫 준비22초의 실제 native 상태는 보존된 기존 준비22초 상태와 정확히 일치했다. 새 두 실행의 준비 상태도 서로 정확히 일치했다. 이는 준비 상태 재현의 결과이며 기존 전체V3시험이나83초 연속 수행을 다시 검증한 것은 아니다.
- 행동은39개 모두0 또는0.25였다. 시험용 최대 변경 범위는±0.002rad이고, 비영 행동의 최종 관절 목표 변화는 최대 약0.00050002rad였다. 이 작은 범위가 실제 압현·타현에 충분하다고 판단하지 않는다.
- 상체 비정책42개 목표의 준비 목표 대비 변화는0이었다. 하체는 원래 발 유지 제어를 사용했다. 금지된 native 호출 기록은 없었다.

아래 이동·회전은 각 실행의 **준비22초 기타root 상태**를 기준으로 계산했다. 위치는3차원 이동거리, 회전은 상대SO(3) 각도다.

| 조건 | 원 실행 시각 | 실제 물리 표본 | 최대 이동 | 최대 회전 |
|---|---|---:|---:|---:|
| 기존 유지 계속 |22–23초|240|0.004625mm|0.000579°|
| 정책 행동0 |22–23초|240|0.004004mm|0.000481°|
| 작은 비영 행동 |23–24초|240|0.016866mm|0.002974°|

이 비교는 짧은 연결 확인이다. 비영 행동 구간은 행동0 구간 뒤에 이어지므로 독립 초기화한 동일 시각 대조 실험이 아니다. 악기 지지·양발 접지·관절 건강의 모든V3세부 조건, 장기 안정성이나 음악 성공을 새로 인증하지 않는다.

[원 준비 상태와 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/prepared_original_comparison_v1.json) · [관측 수치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/native_analysis_v1/result.json)

## 기록 오류와 복구 범위

실제 실행에 사용한runner v6는 모든 물리 구간·원자료 저장·native 영상 인코딩 뒤, 사후import 목록을 정리하는 단계에서 namespace 모듈의 `__file__=None`을 처리하지 못해 **종료 코드1**로 끝났다. 원 실행 폴더의report.json은 생성되지 않았으며 새로 채워 넣지 않았다.

별도 읽기 전용 복구 감사에서 세 구간의 연속240Hz표본, 제출 목표, 실제 영상과 원 입력1502개의SHA불변을 확인했다. 추가 물리 실행은 하지 않았다. 원 프로세스의 실제 사후import 목록은 복구할 수 없으므로 전체 사후import 검증이 완료됐다고 주장하지 않는다.

runner v7은 해당 목록 처리만 수정했고, namespace 관련CPU회귀2개를 통과했다. v7으로 물리 시험을 다시 실행하지 않았다. 환경CPU8개·기하CPU4개도 통과했다. 기존 파일럿의보상·정책 가중치를 불러오지 않았고 PPO갱신은0회다.

[복구 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/native_recovery_v1/report.json) · [원 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/native_smoke_v1.log) · [CPU검사·실행 명령·수정 이력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/implementation/implementation_result_v1.json)

## 실제 영상과 원자료

다음 영상은 실제Isaac Gym 카메라 녹화다. 두 번째 실행의22–23초는 행동0,23–24초는 작은 비영 행동이다.5fps로 시작·종료 프레임을 포함하므로 영상 길이는 실제 실행보다0.2초 길다. `hands`는 기존 측면 보조 시점 이름이며 손의 확대 화면은 아니다.

![정책 제어 인계 시험 — 실제 native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/native_smoke_v1/media_handoff/whole_body.mp4)

[기존 유지 대조 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/native_smoke_v1/media_baseline/whole_body.mp4) · [실제 초기 상태와 원자료 폴더](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/native_smoke_v1)

## 남은 구현

다음은 실제 손가락–넥/프렛 접촉과 유지·해제를 측정하는 압현 판정이다. 이후240Hz타현 검출·목표 시각 매칭, 실제 관측 벡터·보상/비용, PPO수집을 순서대로 연결한다. [세부 순서와 주의점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/NEXT_STEPS_v2.md).
