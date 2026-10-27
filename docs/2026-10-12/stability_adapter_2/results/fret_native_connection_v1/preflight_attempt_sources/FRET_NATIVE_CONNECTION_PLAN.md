# 자유 기타 왼손 Fret 연결 — 첫 독립 시험

사용자 요청: 현재 왼손에 학습된 Fret을 연결한다. 기존 Strike 구현과 실험은 보존한다.

1. 원본 계약 확인 → 420 관측 / 30 행동 / 6 value, Jazz1 `fret_035000.pt`, goal·hand target·joint profile SHA와 순서 검사.
2. readonly native Fret view 구현 → 공용 shared step/apply/reset 금지는 그대로 유지한다. SHA를 고정한 원본 action 처리와 step의 **물리 이후 평가 부분만** AST로 분리한다. 물리 전진은 native owner가 4 substep씩 한 번만 수행한다. 원본 synergy/EMA/운지·실패 판정을 유지한다. RSI 105DOF cache·pose library는 불러오지 않는다.
3. 물리 준비 2초 → 기존 초기 상태에서 왼손 30축 목표만 원본 profile 범위로 점진 이동한다(0.8rad/s). 몸통 목표 유지, root/하체 fixed-link, 기타 자유·스트랩 OFF. 최초 상태나 실제 관절 상태는 덮어쓰지 않는다. 원본 profile은 관측 정규화·정책 목표 범위에 적용하며 이번 진단의 native 물리 hard limit은 기존 XML이다. 실제 profile 초과를 별도 기록한다. 원본 고정 기타 hard-limit 환경과 물리적으로 동일하다고 주장하지 않는다.
4. t=2초 실제 제출 목표에서 EMA history 구성 후 Fret30이 단독 제어한다. 기존 L9 hold/grip을 같은 관절에 더하지 않는다. LThorax3·오른팔12는 기존 bounded hold, 오른손21·몸통9는 초기 목표 유지. 첫 시험에서 Strike actor는 사용하지 않아 왼손의 영향을 분리한다. source 준비60frame은 외부2초 준비로 대체하고, song frame0부터 시작한다. 실제 관절이 profile 밖이면 그대로 관측하고 초과량을 기록한다.
5. source 첫 done(정상·실패)까지 실제 Isaac Gym 전체/손 영상과 관측·행동·목표·접촉·기타 pose·원본 info 저장. 5초 제한이나 terminal 후 정지 프레임을 추가하지 않는다. native 비정상 상태는 즉시 중단한다.
6. 독립 검수·보존 감사 → 연결 실행 검증과 운지 성공을 구분해 보고. 실제 기타 기준 관측 변화도 copied tensor counterfactual로 확인한다.

- [x] 원본 입력·30축·초기 profile 충돌 확인
- [ ] 구현 및 원본 tail/action 분리 검사
- [ ] 독립 사전 검수
- [ ] native 실행·종료까지 녹화
- [ ] 결과 이미지 설명·영상 모음·최종 검수/보존 감사

결과: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/`
다음: 첫 시험 실패 원인에 따라 기타 상대 접근·자세 보정을 먼저 설계한 뒤 양손 동시 연결한다. 학습 업데이트는 이번 단계에서 0이다.
