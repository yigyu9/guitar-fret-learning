# 오른손 guide 거리 스케일 변경 사전 검수

**요약 판정: 문제없음.** 제한된 새 v2 native 비교를 진행할 수 있다. 음악 학습 개선을 이미 확인했다는 판정은 아니다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

보관본과 현행 dense_environment.py를 diff로 확인했다. 실행 코드 변경은 `DenseRewardConfig.right_scale_m`의 **0.02→0.05m 한 줄**이다. tests/test_dense_environment.py는 보관본과 동일하며, 보관 manifest의 모듈·검사·문서 3파일 SHA도 일치한다. 기존 사전 검수 기록은 수정하지 않았다.

이 값은 오른손 guide 거리 credit 및 그 credit이 곱해지는 방향 추가 보상에 적용된다. 최대 보상률·guide 위치/방향/시각·관절 제어·기타 상태·실제 성공 판정은 바꾸지 않는다. reward 계약에 실제 스케일 값이 저장되므로 기존20mm dense checkpoint와 새50mm 계약의 strict resume도 동일 계약으로 취급되지 않는다.

거리49.74mm를 고정했을 때 Gaussian credit은 약180.47배, 거리 미분의 절댓값은 약28.87배 커진다. 이는 수학적 거리 보상/거리 미분 비교이며 PPO parameter gradient나 음악 성공률이 같은 배수로 개선된다는 뜻이 아니다. PARALLEL_TRAINING.md가 초기 탐색 신호 강화와 근접 위치·시간 분별력 감소의 tradeoff를 명시하고, 실제 성공을 별도 지표로 둔 점은 타당하다.

담당자는 관련 dense/sampling CPU7개 통과를 보고했다. 기존 방향/늦은 도착 비교 검사와 reward 합산/strict 계약 검사를 읽었으며 검수자가 물리·학습·전체 검사를 재실행하지 않았다. 검수 시점의 cpu_tests_scale_v2.log는 전체 검사가 진행 중이므로 완료로 간주하지 않는다. 루트 담당자가 전체 CPU 통과를 확인한 뒤 새 출력 폴더에서 v2 native 및 pool cycle을 검증해야 한다. 이전20mm 실행의 입력·원자료와 새50mm 결과를 분리해 비교해야 한다.

검수 시점 SHA256:

- dense_environment.py: `f9136c995ef1e2db163b0a86afa6db588f628b4183adacbbba405f8bd6bf33dc`
- tests/test_dense_environment.py: `334547c6ff0622dd26629641f47618946dc933729e6a3431fff385ce6185b464`

이 검수자는 review_scale_v2.md 외 파일을 수정하지 않았다. 실제 v2 결과와 최종 봉인은 후속 검수 범위다.
