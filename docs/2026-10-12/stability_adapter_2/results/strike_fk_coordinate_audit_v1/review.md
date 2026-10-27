# 저장 native81 FK 독립 검수

요약 판정: 문제없음. Critical 없음 / Warning 없음 / 미해소 Suggestion 없음. 검수는 저장 자료의 수학·코드·문서에 한정하며 새 native 초기화·물리 실행·재생을 하지 않았다.

- `analyze_strike_fk_coordinates.py:25–44`: initial state와 trace step0의 exact, 151표본의 81 DOF/66 body, step0–1200 매8 및 시각을 확인했다. XML joint-axis 열 행렬을 사용한 parent-relative `Exp(Bq)` 초기 calibration과 Cartesian identity 대조를 독립 NumPy/SciPy 계산으로 재검증했다. 그룹별 저장 오차와 재계산 차이는 최대 `7.11e−15°`다.
- Chest의 실제 현재 pose로 정렬한 full FK의 RH:pick **body origin** 위치·회전도 별도로 재계산했다. 저장 값과 차이는 최대 `3.08e−13`이며 위치 최대/RMS `0.3164519367/0.1610814437 mm`, 회전 최대/RMS `0.3002831308/0.1528827808°`다. 8그룹 XML B 최대 `0.00003862175°`, Cartesian I 최대 `62.88158864°`도 표와 일치한다.
- 6개 SHA의 현재 일치와 종료 불변 기록, Python 3.8 AST, README/CHANGED의 실존 절대 링크·실제 함수 앵커를 확인했다. 원 실행 frame/video는 재사용 참고자료이며 이번 계산 입력이나 새 촬영으로 설명하지 않는다.

해소한 문서 권고: README:31–33에 helper import가 최초 SHA 수집보다 먼저라는 경계와 계산 입력 6개/원 실행 참고자료의 구분을 반영했다. 실제 FK 함수 호출·XML/raw 읽기는 SHA 뒤이며 종료 SHA가 동일하지만, **helper import 전 봉인 인증은 아니다.** 소비된 코드는 변경하지 않았다.

검수 source SHA256: analyzer `b8331a92e75251507997c8bcc2d5866b694520a06b675f24fd445664b3a8b962`, FK helper `224fc2f9782dbaec938843c2278ab4bebe9b90588b81693e45b3c07d25519111`. 나머지 4개 입력은 `analysis/inputs_before.json`의 현재 SHA와 대조했다.

최종 범위: 관측한 native81 궤적의 좌표 일관성은 수치적으로 뒷받침된다. 미방문 방향의 Jacobian/미분 정확성, cooked 접촉·지속 지지, 음악 성공은 인증하지 않는다. 남은 actionable finding 없이 이 검수 기록을 동결한다.
