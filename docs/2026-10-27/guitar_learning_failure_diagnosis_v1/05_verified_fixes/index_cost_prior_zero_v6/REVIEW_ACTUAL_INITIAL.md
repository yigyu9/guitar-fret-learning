# V6 실제 초기 모델·평가 독립 검수

요약 판정: **문제없음 / PASS**. Critical·Warning·Suggestion 없음. 예정된 PPO300 진행 가능.

기존 GPU fit1000 완료 자료를 CPU에서 독립 검산했다. fresh.pt·fit.pt 모두 V5의 71개 중 69개 tensor와 정확히 같고, 다른 2개는 cost_critic.weight/bias뿐이며 모두 0이다. 파일 SHA·초기화 계약·fit 횟수·완료 보고서를 확인했다. 새 GPU 실행은 하지 않았다.

봉인 core549개와 fit/고정/확률 평가의 before·after 입력 감사를 모두 확인했다. 설정 차이는 초기화 설명, 평가 contract 차이는 cost_prior뿐이다. 모델·optimizer·checkpoint 동결, native 종료, 선택 reference 호출0과 PPO0을 확인했다.

실제 rl38 Python3.8.20 CPU로 paired helper를 다시 실행했다. 고정·확률 각각 128시도의 전체 원장·9보상·정산과 env0 동작 배열은 V5와 같다. body force 차이는 별도이며 각각 최대 1.1444091796875e-5N / 3.814697265625e-6N이다. 초기 행동 동일성은 확인했지만 PPO 개선이나 기존 퇴행 원인을 입증하지 않는다.

이 검수는 완료된 초기 단계만 다룬다. PPO300·주기 평가·마지막 확률 평가·최종 영상은 후속 검수 대상이다. 최종 initial_comparison/compare.py만 완료된 대조 분석으로 pin했으며 미래 분석 helper를 미리 봉인하지 않았다.
