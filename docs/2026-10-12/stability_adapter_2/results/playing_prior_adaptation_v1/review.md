# root 자체 검토

독립 change-reviewer 호출은 `agent thread limit reached`로 실패했다.
아래는 root 자체 검토이며 독립 검수 완료로 표시하지 않는다.

- 기존 policy 관측은 현재 G frame이며 이동/회전 frame의 상대 속도 항이 이미 있다.
  연결 시 COM/root 속도 정의와 projected gravity의 Thorax frame까지 대조하도록 계획했다.
- 원본 action은 초기각 offset이 아닌 limit midpoint/half range 기반 절대 목표다.
  이름 매핑, 단일 EMA, 실행된 최종 목표의 history 회신을 명시했다.
- 두 source의 60관절과 현재 주요66의 차이는 Thorax6이다. 남은 native15는 목표 유지한다.
  기존105D arbiter를81D simulator 구현으로 오인하지 않는다.
- source 가중치뿐 아니라 정규화 buffer도 동결한다. 새 residual의 정규화는 별도다.
- checkpoint 예시의 계약 내부 SHA·buffer 유한성과 이름 대응만 검증했다.
  source 성능·asset 호환성·actuator 동등성·전체학습완료는 인증하지 않았다.
- Fret goal_pair 예시는 최종 연주 source로 선정하지 않았다.
- native POS와 원본 hybrid actuator 차이를 학습 이전 baseline에서 측정하도록 했다.
- 공동 보정이 기타 유지 때문에 연주를 멈추는 해를 택하지 않도록 연주 metric을 함께 둔다.
- 상태 강제 덮어쓰기/기타 고정/손 부착/동적 LA 조정을 도입하지 않는다.
- 기존 이미지·영상은 이전 작은 손목 시험으로 명시하고 새 연주 성능으로 표시하지 않았다.

남은 검증: 실제 source 선정, 후처리/EMA/history 잔차0 동등성,
현재 native API로 양손 관측 view 구성, one-simulator rollout, 학습 및 held-out 평가.
실행하지 않은 기능을 이번 완료 항목으로 표시하지 않았다.
