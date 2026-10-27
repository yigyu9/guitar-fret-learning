# 독립 검수 — UP ENTRY 경로 감사

판정: **문제없음(PASS)**. Critical / Warning / Suggestion: 남은 항목 없음. `analysis.py`·summary·README와 저장 source 관측·native pose·control feedback을 읽기 전용으로 대조했다. 신규 FK/환경 import·native 초기화·물리 실행·다른 파일 변경은 없다.

- 관측 ABI 303차원의 hand/target/recovery block과 실제 인덱스를 대조했다. Actor 169개에서 pick+상대 vector로 READY/ENTRY/geometry5를 복원했고, pick/READY/선택 목표의 최대 차이 0.000212438/9.31e−7/1.04e−6 mm가 기록과 일치했다. Exact-step/time native body origin 표본 84개의 기타 좌표 pick도 일치한다. 보간·미래 pose 예측은 사용하지 않는다.
- 명령 시각은 pre-step control이며 info는 다음 native 4 steps 이후다. Wrong 네 행의 source event·0-based string과 native `G:string(index+1)` 표기를 확인했다. 3.466667/3.483333/3.5/3.616667초 명령과 다음 feedback 시각을 구분하며 마지막 terminal은 3.633333초다. 네 행 모두 target/physical hit 및 prepared/unprepared target flag가 false다.
- 후기 표의 현재 READY XY/ENTRY 3D 거리, R9 최종 제출 목표−현재 actual RMS를 재계산했다. 이 RMS는 whole-joint SO(3)나 native drive torque가 아니다. 위치 차분 속도도 순간 물리 속도 인증으로 해석하지 않는다. Source의 cached recovery geometry5가 release-lift→next-entry-lift→next-ready를 반환한다는 코드 및 관측 설명은 정합하다. Scheduled pulse와 실제 phase 전환을 구분한 문구도 적절하다.
- 성공 event 0–3의 열린 ENTRY 미도달 표본은 각 2개이며 최대 READY XY 간격은 3.320841/1.732275/0.181505/0.859350 mm다. 3 mm 후보는 event0의 1.3초에서 먼저 원래 경로와 달라진다. UP event5의 7개 표본 최소 7.703496 mm, event6의 5개 표본 최소 12.938715 mm도 일치한다. 저장 구분값은 새 실행의 성공 prefix·timely hit·wrong 감소 보장이 아니다.
- 직접 입력 9개의 parse 전 SHA·byte-cache·종료 SHA와 현재 파일이 일치하며 Python 3.8 AST 문법을 확인했다. 원자료·consumed controller·검출기·clock/phase/threshold를 수정하지 않은 감사 범위를 유지한다.

검수 SHA256: 분석 코드 `85f0df2c1a1fbd572b593b4aa3e5fd4238d0dda8cafeb00fb1849c2c5ff7ebd6`, summary `af5265a56aac48ad4ace06a10c623f364582d178c32aeb94d1a55e3f140fea29`, README `3645c2c4797f1691362292b8417a660bb3f7b1e65a356de2c9e0e6e3a0b9bda9`.

한계: 저장 경로·원래 판정·관절 목표 오차의 사실 감사다. 접촉/특정 제어 항의 인과성·연속 경로 안전성·후속 staging 효과·완성 연주 성공은 판정하지 않는다. Root 최종 보존 감사·봉인 완료도 이 기록에 포함하지 않는다.
