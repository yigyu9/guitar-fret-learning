# 해제 목적 정렬과 탐색 단위: CPU 준비

2026-10-28. 목표각 모델은 음악126/128·A해제73/128이다. 같은1000회 각도손실은109/31로 후퇴했고, 저장24상태에서 A우선순위를 유지하는 대조도 해제 목표오차가 증가했다. 이 변경들은 채택하지 않는다. 원5항 감사에서는 A종료 후 clean/wrong이 같은 두 시간표의 해제 여부가 보상을 바꾸지 않았다. 다음 음 수행의 간접 유인은 있지만 원100ms 해제 조건에 대한 직접 지급은 없다.

이번 범위는 다음 두 CPU 준비뿐이다. 실제 native·GPU·fit·PPO·원모델·활성source 변경은0이며 음악/해제90% 기준을 유지한다. 보상만의 원인이나 아래 제안의 학습 효과를 확정하지 않는다.

## 1. 기존 A달성 보너스 지급의 조건부 유보 산술

기존 prefix_release_objective_v1/audit.py의 원 production ledger/지정시간표를 재사용한다. A4의 기존 song_left_success .25b만 achieved 후 유보하고, 원 native released가 유효창에서 latch되고 실패가 없을 때 한 번 지급한다. 미해제·늦은 해제 또는 pending 중 failure/reset/end는 미지급 소멸이다. 유효release가 관측된 해당control에 실패가 없으면 즉시 지급하고, 이미 지급한 뒤의 미래실패는 소급 취소하지 않는다. 안전한 episode 종료까지 지급을 더 미루거나 미래안전을 예측하지 않는다. achieved/music/release 판정과 contact/clean/감점 및 B7/B8 지급은 그대로다. B7/B8은 공유press이므로 사이 해제를 요구하지 않는다.

새10번째항·총예산·해제감점·자세/움직임비용을 추가하지 않는다. 기존 base ledger의 달성 지급 기록과 제안된 실제 지급 기록을 구분하고 원ledger를 덮어쓰지 않는다. 새CPU 조건부 지급표에 pending/paid/expired/failed를 기록해 회계가 맞는지 확인한다.

검사: 원두동일clean/wrong 시간표가 기존5항 tick-exact인 사실 보존, 새조건에서는 적시해제만 .25b를 받음, 미달성/음끝전/마감뒤/실패/반복지급/부분reset·H32경계/동일tick 지급 및 예산상한·B두음 원지급불변. 원falling-edge의 짧은이탈 한계를 유지하며 안정된 무접촉이나 피부분리로 확대하지 않는다. 지정시간표 산술로 한정하고 합성 clean을 실제 물리결과로 부르지 않는다.

## 2. 목표각 출력의 확률 탐색 크기 확인

원70e 모델과 저장관측은 읽기전용이다. 원std .171171에서 z Gaussian→tanh→기존decode로 생기는 목표각 분포를 N/Ref와 사전지정 env0 phase별 중간1행에서 CPU로 계산한다. 공통 seed7 고정표본을 사용해 관절별 각도 RMS/평균편향/분위수와 ±4/60rad보다 큰 목표변화 비율을 기록한다. 이는 rateclip 전 목표 분포이며 실제관절 움직임/토크/PPO 성과가 아니다.

비교용 유한 std 후보는 탐색으로 고르지 않는다. 원incremental neutral의 1차 nominal RMS=(4/60)·.171171rad를 기준으로, 각관절 기존decode의 최대절대기울기 L_i(rad/raw)에 대해 sigma_i=nominal/L_i만 계산한다. tanh의 Lipschitz1로 모든고정평균에서 목표각 RMS≤nominal이라는 상한과 실제표본값을 구분한다. 기준 nominal은 기존incremental의 정확한 유한잡음 RMS라고 주장하지 않는다. N의 부호별 기울기가 비대칭이므로 평균편향도 별도 표시한다.

후보를 원checkpoint나 활성설정에 쓰지 않는다. 새정책 이전/새reward계약/동일조건 PPO대조/native 사전검사는 이번CPU결과와 독립검수 후 별도계획으로 구체화한다. 기존100PPO 유지검사의 미충족 조건을 통과로 바꾸지 않는다.

- [ ] 조건부 A지급 최소산술·경계/불변 검사·짧은해석
- [ ] 원std/유한후보 목표각분포·상한 검증·짧은해석
- [ ] 두 CPU결과 독립검수 후 다음실험 판단
