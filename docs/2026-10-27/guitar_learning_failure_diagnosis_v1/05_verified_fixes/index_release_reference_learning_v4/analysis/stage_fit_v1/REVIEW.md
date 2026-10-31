# V4 fit 단계 실제 결과 검수

**요약 판정: 문제없음 — 기록·분석 무결성 PASS. 실제 음악 성능 기준은 실패했다.** 미해결 Critical / Warning / Suggestion 없음. 범위는 고정된 fit1000과 평가2개이며 진행 중 PPO 파일은 보거나 수정하지 않았다.

최종 analyze.py SHA는 `61543bfc3be8c11388bfbe066b7c6a61d1a1fc274883a95f7f79a8d139d447ab`이다. 실제 rl38 CPU의 원자료 비변경 재실행으로 analysis/verification/RESULTS/stage_freeze가 모두 byte exact임을 확인했고62개 입력 SHA와8검사가 일치한다. fit의 현재521핀과 평가522핀도 모두 검증됐다. fresh0/fit1000 checkpoint를 CPU 자료로 비교해19개 변경 tensor가 선언된 finger_encoder/index_head에만 있고 PPO업데이트0·PPO옵티마이저 상태 비어 있음을 확인했다.1000개 실제 loss 기록은0.0490781665→0.0000505234다.

네 비교조건 모두128시도·384음 기회·9보상을 유지한다. 두 NN평가의 전체 원장에서 acceptance를 독립 재계산했다. deterministic은98/128·A해제44/128,stochastic은14/128·A해제111/128로 원교사 성과를 보존하지 못했다. 물리·손목 실패0,close완료,teacher선택helper0,모델/optimizer/checkpoint freeze와 동일fit체크포인트SHA를 확인했다. 평가 자체 fit/PPO 실행계수0과 initialization_fit_steps1000/checkpoint_updates0도 구분돼 있다.

실제 env0 N유지의 큰 PIP/DIP 목표편차·접촉 잔류와 offline 정규화MSE를 구분한 해석이 자료에 부합한다. 그림의 위상·목표각·합력·candidate를 육안 확인했다. 같은장면 holdout,대표환경 한계,60Hz끝점/240Hz 판정 차이,합력과 압력의 구분,해제 latch 의미와 확률 draw 비동일성 한계가 명확하다.

이번 PASS는 분석과 실험기록에 대한 것이다. closed-loop 압현/해제 강건성이나 PPO300 성과,자유기타·다른손가락·원곡67음의 완료를 입증하지 않는다.
