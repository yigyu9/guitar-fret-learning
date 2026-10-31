# V7 실제 fit·초기 평가 독립 검수: PASS

V7 구현 비참여 peer가 완료된 배우 지도1000회·가치망 보정1000회 및 초기 두 mode 평가를 검수했다. 원672개 core 입력과 검수 대상 SHA는 전후 모두 일치한다. 실제 Python3.8 CPU에서 checkpoint tensor/RNG/optimizer와 저장 배열을 읽었으며 추가 NN forward·GPU·native·fit·PPO는0회다. root는 실제 fit와 두 평가 exit0을 보고했고, 이 검수는 저장된 완료·장면 닫힘·실패/cleanup/입력변경 없음과 freeze 증거를 독립 확인했다.

배우 지도 단계의 fresh/fit71개 텐서는 V6와 정확히 같다. 가치망 보정 뒤에는 value_encoder/reward_critic17개 텐서만 달라졌고 나머지54개는 정확히 보존됐다. costhead0, 같은 V7 architecture/contract, torch CPU/CUDA·NumPy·Python RNG4종 동일성, 빈 PPO actor/value optimizer, updates0/cost_weight1을 확인했다. 구형 checkpoint를 새 모델로 옮기지 않는 실행 코드도 준비 검수대로 유지됐다.

초기 V6 fit12개 buffer만으로 독립 NumPy gamma=.99 reverse-cumsum MC를 재계산했으며 저장 target과 최대1.55e−15 차이였다. 저장 예측으로 train/holdout 전체와10개 phase의 모든 count/MSE/bias를 재계산해 보고서와 일치했다. holdout 전체 MSE는0.317607589712→0.026549807530으로 사전 게이트를 통과했다. 그러나 tail RMSE는 train0.006892→0.152073, holdout0.006865→0.162866으로 악화했다. 전체 개선이 모든 구간 개선을 뜻하지 않는다.

초기 평균행동 평가와 확률 평가는 각각128시도·384음 기회를 유지하며, V6 동일 mode의128개 전체 원장·9보상과 env0의 모든 nonforce trace가 정확히 같다. 평균행동은 세 음 달성98/128·달성+첫음해제22/128, 확률은14/128·12/128이다. 힘 최대 차이는 두 mode 모두7.62939453125e−6N으로 별도 기록하며 exact라고 하지 않는다. 각 평가의 model/optimizer 및 checkpoint 불변과 평가 입력672핀+승인 fit checkpoint SHA도 확인했다.

initial_comparison source/verification과 fit_analysis plot source/report/image SHA를 검사했다. value_rmse.png를 직접 열어 축·10phase·분할·tail 악화가 읽히는지 확인했다. RESULTS는 전체 게이트·구간별 악화·같은 장면 holdout의 한계를 구분하며 가치 오차 감소를 압현 개선으로 확대하지 않는다.

미해결 초기 검수 지적은 없다. 상세 SHA와 독립 계산 값은 actual_initial_review.json에 기록했다. 이 PASS는 계획된 다음 PPO 비교로 진행할 초기 조건에 한정되며 PPO300·후속 평가·영상이나 전체 목표 성공을 입증하지 않는다. 다른 seed·손가락·자유 기타/J33·원67음은 미완료다.
