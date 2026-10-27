# 누락12부위–기타 source 방향상한 감사 계획

Root 승인 범위: 기존 source14 감사와 소비 자료를 보존하고, 새 readonly 감사만 만든다. 초기/동역학/제어/모델/gain/PPO 변경은 없다. 현재 Body9+.15 후보의 repeat Spine 실패는 계속 실패다.

- 대상은 Pelvis, L_Knee, R_Knee, L_Ankle, R_Ankle, L_Toe, R_Toe, Neck, Head, R_Thorax, L_Thorax, L_Shoulder의 원 source geom 각1개다. native filter와 XML policy상 활성 physicalG89개와의 1,068쌍을 전부 검사한다. inactive LH pad, disabled visual, proxy/range와 무geom marker는 이 범위가 아니다.
- 실제 run의 준비 후5..T 전60Hz target 대응 state와 종료점에서 각쌍의 원 vertices/analytic capsule 직접 unit-normal projection g≥−0.001m을 요구한다. 값에 맞춘 epsilon은0이다. AABB6방향이 충분하면 즉시 certificate, 부족한 쌍만 frozen normal/QP/complete convex fallback을 재사용한다. 누락·잘못된normal·미해결은 통과시키지 않는다.
- 모델은 선언 source106파일과 manifest2개, 총108개 expected SHA를 별도 검증한다. flat/envelope map과 중복 path SHA 충돌을 거부한다. 원 run 완료/report/실제 config, 전240Hz state N+1, 전 target60 sequence 및 종료step를 확인한다. 원문과 before/after SHA를 보존한다.
- 먼저 실제 metadata schema/12부위 primitive·native count/filter/초기 compiled source 배치를 확인하고 두 actual frame numeric CPU를 수행한다. 이는 전체 생산 감사 성공이 아니다. 소스 동결 및 독립검수·Root ACK 전 pilot/full main 실행은0이다.
- 출력은 새1068쌍 coverage/failures/worst/방법수와 전후 SHA다. 기존 source14 결과는 별도 참조하고, 두 범위가 같은 run에서 모두 통과한 경우에만 준비 후 유한표본의 활성 human–physicalG source 범위를 함께 표현한다. 일반 fullbody/self/cooked/시간연속 검증 및 최종채택은 언제나 False다.

체크리스트: [ ] 실제 진입 schema/model108 확인 [ ] 12부위 배치 및 두 frame CPU [ ] 양/음·누락·mask·sequence 반례 [ ] source 동결 [ ] 독립검수·Root ACK [ ] Root 생산 실행.
