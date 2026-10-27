# 반복 타현10 실패의 읽기전용 추종 진단

기존 정지10의 모든 감사는 통과했지만 반복10은 Spine/Torso source1mm gate에서 실패했다. 목표 보정량을 실제 형상 개선으로 간주하지 않는다. 원 결과·문턱·gain·설정은 보존한다.

- [ ] 실제 원시 schema와 사전 SHA에서 작은 대표 표본을 추출한다.
- [ ] 몸통9 목표→실제 q/qd→scalar PD/중력/지지 task→제출 명령을 재구성하고 독립 검수한다. SO3 비교 오차는 진단이며 기존 제어를 바꾸지 않는다.
- [ ] 정지10과 반복10의 같은 시각을 비교한다. 기존 source frame의 여유·기타 세계/Spine/Chest 상대 자세와 실제 몸통 추종을 분리한다.
- [ ] 실패 시작17.7333초와 최악21.0833초의 근거 및 다음 수정 판단을 새 결과에 기록한다.

읽기전용이며 새 FK/최적화/source query/native/PPO는 실행하지 않는다. selected snapshots의 제출 명령은 step 직전, state는 같은 step 시점이다. endpoint는 이전 명령과 구분한다. source g는 방향 쌍 경계이며 cooked 침투량이 아니다. 실제 원시 파일의 expected SHA를 검증하고 원시 상태·명령을 바꾸지 않는다. 새 생산 main은 독립 FINAL/Root ACK 후 실행한다. 현재 후보로 왼손 해제에 진행하지 않는다.
