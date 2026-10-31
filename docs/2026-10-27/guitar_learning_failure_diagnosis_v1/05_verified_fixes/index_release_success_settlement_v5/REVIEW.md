# V5 준비 독립 검수

**요약 판정: 문제없음 — PASS.** 미해결 Critical / Warning / Suggestion 없음.

검토 범위는 V5의 runtime·learn·experiment·CPU 검사·PPO 실행 감독기·평가 일정과 입력 봉인이다.532개 입력 SHA가 일치하며, 실제 rl38 Python3.8.20에서 최신 CPU 검사를 독립 재실행해 통과했다. pending gate는 NumPy/Torch/Isaac import 전에 실행을 거부한다.

A(source4)의 원시 달성 보상 .5를 원래 달성 순간에만 회수하고, 원래 inclusive 해제 판정 갱신 뒤 첫 now>=end+.1 시점에 원 달성·해제 latch를 만족하면 한 번 정산한다. 최종 부모 가중 .5를 적용하므로 기존 .25×finger_weight 예산을 넘지 않는다. B7/B8과 다른8항은 그대로다. 실제 부모 substep4회와 end_control을 이용한 CPU fixture에서 정확한 deadline snapshot 해제→정산과 후속 substep 실패에 따른 실제 success 보상0·paid0을 확인했다. 권리·실수령·실패 억제 원장을 구분하고, 부분 reset은 해당 행만 초기화한다.

V4 정책·학습 루프는 별도 모듈로 재사용하며 신규 reward 계약과 모델 schema를 엄격히 검사한다. CPU fresh tensor 동일성과 자체 checkpoint roundtrip·V4 거부를 확인했다. 실제 fit 이후 fresh/fit tensor 동등성은 실행 중 별도 파일로 검증하며, 감독기는 해당 파일 부재·false를 Popen 전에 거부한다. 부모 fit learning_report의 completed는 부모 fit 작업 범위이므로 동등성 파일과 정상 프로세스 종료를 함께 확인해야 한다.

terminal trace 원장은 pool.step 반환 직후 수집하며 reset은 호출자 수집기가 이후 수행한다. 감독기 중복 실행 거부·실패 시 자식 종료·원예외 보존·종료 기록 CPU 검사도 통과했다. 실제 GPU fit/PPO·고정/확률 평가·마지막 영상과 성과 비교는 아직 실행 전이며 이 PASS에 포함하지 않는다.
