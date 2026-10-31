# V5 실제 초기 실행 독립 검수

**요약 판정: 문제없음 — PASS.** 미해결 Critical / Warning / Suggestion 없음. 준비 봉인534개 SHA와 실제 fit/평가 입력 감사가 모두 일치한다.

실제 fresh·fit checkpoint를 CPU로 직접 읽어 V4와 각71개 모델 tensor의 torch.equal을 독립 확인했다. 저장 metadata는 새 V5 schema이며 fit1000/PPO0 보고는 정상 완료·정리 상태다. fit의 completed만으로 초기 동등성을 판단하지 않고 별도 동등성 파일과 실제 checkpoint를 함께 확인했다.

실제128명 고정·확률 평가가 모두 완료됐고 교사 호출0·평가 중 모델/optimizer/update/checkpoint 불변을 확인했다. 고정은 all3=98, A해제44, all3+A해제22이고 확률은 all3=14, A해제111, all3+A해제12다. 두 모드 모두 실패0이며 원래 music/release/stage gate는 통과하지 못했다. 원장과 env0 trace의 V4 대응 비교를 rl38에서 독립 재계산했고, 달라진 보상은 기존 A 압현 달성 지급 조건뿐이다. A 달성+해제 실수령은 고정22·확률20이다.

처음 runs/fit_stochastic에 실행된 작업은 CLI --stochastic 누락으로 추가 고정 평가였다. 원자료와 오류 기록을 보존했고, acceptance stochastic=true인 fit_stochastic_actual만 확률 평가로 사용했다. 이 판정은 PPO300 성과·마지막 영상·학습 개선 완료를 포함하지 않는다.
