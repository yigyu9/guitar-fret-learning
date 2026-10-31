# V3 준비 검수

**요약 판정: 문제없음 — PASS.** Critical / Warning / Suggestion 항목 없음. 검수 범위는 준비 코드·입력·CPU 검증이며 GPU 결과 승인은 아니다.

실제 `rl38` Python3.8.20에서354제어×128환경×39출력 산술 검사를 독립 재실행했다. 무마스크는 원 식과 bit exact, 마스크는 action17(index1_x)에만 영향을 주며 나머지3잡음과 RNG 상태는 동일하다. 생성된 전체 AST를 독립 기대 AST와 비교해 원 noise draw/hash 이후 clone·col0 마스크, 합산 RHS 변경, applied_noise 로그 추가의 세 변경 이외에는 차이가 없음을 확인했다. 원 Normal[128,4]·sigma·시드 경계·V2 일정·9보상·물리·종료·guard·부분 오류 보존·finally는 그대로다.

513개 입력 SHA 모두 일치한다. V2 preflight 통과, settings 및 재사용 baseline/candidate JSON은 원본 byte exact이며 신규 native 실행으로 표시하지 않았다. 독립 리뷰가 없는 상태의 자체 gate는 numpy/torch/Isaac Gym import 전에 거부했다. 예외 주입 CPU fixture에서 HERE/SCHEMA/support/run alias가 모두 원상 복구됐다.

초기 검수에서 `ast.unparse`의 Python3.8 비호환 오류를 발견했다. worker가 ast.dump 템플릿 비교로 최소 수정한 뒤 위 검사를 다시 통과했으며 이전 준비 자료는 `preparation_failures/attempt01`에 보존했다. 미해결 지적은 없다. root는 리뷰 SHA를 seal에 추가한 뒤 stdlib gate를 다시 확인해야 한다. 실제 실행 뒤 전체128 잡음 stream hash와 applied_noise, 모든128시도 및 입력·cleanup 감사는 별도로 검증해야 한다.
