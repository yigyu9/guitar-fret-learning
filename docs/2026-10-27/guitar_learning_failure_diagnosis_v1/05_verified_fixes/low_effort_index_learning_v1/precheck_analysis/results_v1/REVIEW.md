# 독립 actual384 검수

판정: **문제없음 / PASS**. Critical·Warning·Suggestion 없음.

3개 실제 닫힌 scene의 원래128분모·384첫시도와9보상 항목을 대조했다. reference128/128(clean0.9984708358), zero0/128, random31/128(clean0.2435744519, wrong0.1920874927)이며 물리·손목실패는 모두0이다. 원래 사전 수용기준 재계산은 통과한다. 최대 보상 합산 잔차는6.66075e-7이다.

1112개 직접 입력과1079개 검증 입력 SHA가 현재 일치했다. 출력 쓰기를 메모리에 가로채 비교·검증JSON,3CSV,RESULTS를 재생성해 동일함을 확인했다. 현재 helper의 env0 663끝점 재생과 별도 NumPy 원장/합력/actual각/손목위치/팔bounds 검산을 수행했고 두 그래프를 직접 확인했다. native128×105 readback·90쌍·입력/alias/loader 복원·닫기 근거도 분석의 원자료 assertion과 대조했다.

준비1075 검수와 이번 actual384 검수는 별개다. 같은 seed7의128환경이며 상세 하중은 env0만 저장되었다. CPU gate와60Hz 합력을240Hz 최대하중·쌍압력으로 확대하지 않는다. 비NN random 성과를 미래 NN 초기 정책의 exact 성과로 보지 않는다. 원reference1_z 추종차이와 request/target 하한 체류의 한계가 보고서에 보존되어 있다.

검토한10파일의 최종 SHA는 review.json.reviewed_sha256에 기록했다. 기존 source/raw/준비/결과 변경 및 GPU/native 실행은 없었다.
