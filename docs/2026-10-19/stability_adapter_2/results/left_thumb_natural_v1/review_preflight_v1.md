# 왼손 엄지 초기 자세 사전 검수

요약 판정: 문제없음. 엄지5만 변경하는 source와 기존 V7 runner의 손가락 검사 분리가 의도와 일치한다. source 수락은 실제 자연스러움/접촉/타현 인증이 아니다.

Critical: 0

## 확인 근거

- [source:29](/home/ajou/yigyu/3/stability_adapter_2/search_left_thumb_natural_v1.py:29): LH:thumb5만 최적화하고 나머지76 초기각을 보존한다. 결과 두 후보를 별도 FK 재계산해 nonthumb body origin/quaternion이 모두 exact 동일하고 모델 범위·thumb2≤65°/thumb3≤35°를 확인했다. 엄지1 세 scalar도 모델 범위 안이며 norm160° 미만이다. source/runner AST를 확인했다.
- [source 수락:82](/home/ajou/yigyu/3/stability_adapter_2/search_left_thumb_natural_v1.py:82): back12mm는 target 오차25.377mm로 거절, back20mm는19.307mm/전체 source clear/76각·nonthumb pose exact 및 facet 위치·방향 조건으로 수락한다. 현재 source 입력827개 SHA가 모두 일치한다. 최적화/source audit/native를 재실행하지 않았다.
- [runner:45](/home/ajou/yigyu/3/stability_adapter_2/run_left_thumb_natural_v1.py:45): 기존 finger42 invariant만 명시적 LHthumb5 제외37로 분리하고 count37/5 및 source accepted를 검사한다. thumb5는 전체 q_ref/모델 범위 검사와 별도 q_ref 동일성을 유지한다. root/lower·mass·PD·G39 예측/FK/원 guard와5초 루프·원자료 기록은 원 runner와 동일하다.
- [runner entry:134](/home/ajou/yigyu/3/stability_adapter_2/run_left_thumb_natural_v1.py:134): original_runner.main만 새 main으로 patch하고 원 V7.main을 호출하므로 현재G EW6 IK·requested/rate-final gate·원 velocity/pick feedback/33EFFORT·48POSITION·LEFT OFF·cap/단일 actuator를 유지한다. 엄지 새 q_ref는 기존 POSITION 제어에 들어가며 runtime state setter/새 힘/attachment가 없다. 오른 지지 witness는 nonthumb body/G가 불변인 source 조건에서 그대로 유효하다.

## Warning

- [입력 순서:25](/home/ajou/yigyu/3/stability_adapter_2/search_left_thumb_natural_v1.py:25): contract/config/seed/BASE 및 FK(XML)를 읽은 뒤40–41에서 before 맵을 저장한다. 실제 mesh shape build는42 이후라 mesh는 선핀되지만, 앞선 읽기의 독립 새 read-before 인증으로 표현하지 않는다. humanXML/config는 기존 EW native before SHA와 현재/이번 맵이 동일함을 확인했다. 다른 early input도 이전 봉인 맵의 합성 범위로 닫고, 향후 신규 source에서는 anchor→discovery→전체 pin→contract/FK 순서를 권고한다. 소비V1은 수정하지 않는다.
- [facet 지표:89](/home/ajou/yigyu/3/stability_adapter_2/search_left_thumb_natural_v1.py:89): `back20mm`는 명목 목표 label이며 실제 선택facet back-plane gap은36.191mm다. 실제 최소 엄지–넥 거리/접촉으로 부르지 않는다. facet의 해부학적 패드 정체와 Aug19 분포의 좌표계 호환성은 미인증이고, pinned txt/CSV 통계를 코드에서 자동 추정해 hard gate로 사용하는 구조도 아니다.
- 수락 후보 thumb2≈64.334°, thumb3≈−5° 및 thumb1_y≈−90°는 모델 범위 안이지만 일부 하한에 가깝다. 접힘 완화는 확인하나 모델 범위만으로 해부학적 자연스러움을 인증하지 않는다. 실제 새 native의 엄지 모습과 접촉을 확인해야 한다.
- [runner FK 검사:71](/home/ajou/yigyu/3/stability_adapter_2/run_left_thumb_natural_v1.py:71)는 일반 초기 FK 허용오차이며 현재 EW V7 baseline에 대한 실제 palm/나머지 네 손가락 pose exact 비교 자체는 아니다. 실행 후 current baseline과 native 초기76각·nonthumb pose·37finger/PD/G/mass·엄지 충돌·원 detector 양방향6줄을 직접 대조한다. scalar37 비교의 기존 기준은 원 legacy reference임을 구별한다.
- 전체 source LP clear는 cooked/native 또는 동적 엄지 접촉 인증이 아니다. 다른 finger 목표 유지도 실제 손 전체 상태 고정을 뜻하지 않는다.

## Suggestion

없음. 현재 code/source 범위에서 native 시험을 막는 새 구현 오류를 발견하지 못했다. 실제 초기 불변/모습/접촉/타현은 후속 검수 범위다.
