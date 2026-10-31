# 초기 동작 대조 독립 검수

요약 판정: **문제없음 / PASS**. 지적 없음.

최종 compare.py와 입력 SHA를 검토하고 실제 rl38 Python 3.8.20 CPU에서 check 함수를 다시 실행했다. 검증 파일을 덮어쓰지 않고 동일 결과를 확인했다. V5/V6 고정·확률 평가 각각 전체 128시도와 384음 시도, episode 원장·9보상·A 정산은 정확히 같다. env0의 q/target/body/candidate/wrong/released/NN raw·decoded goal/reward 배열도 같다.

고정 all3/joint/A해제는 98/22/44, 확률은 14/12/111이다. body force 최대 차이는 각각 1.1444091796875e-5N, 3.814697265625e-6N이며 별도 기록했다. 정확 동일 주장에 force를 포함하지 않는다.

동결 checkpoint SHA·모델/optimizer 불변·입력 감사·256개 완료 episode를 확인했다. 초기 동작 동일성 검증이며 후속 학습이나 비용 예측의 인과효과는 평가하지 않았다.
