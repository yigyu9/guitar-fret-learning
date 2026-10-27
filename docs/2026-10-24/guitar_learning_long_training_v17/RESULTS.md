# v17 장기 학습 결과

large/1024환경/H32/seed7의 새 2,000업데이트·65,536,000전이와 로그검증·5개 체크포인트 평가·분석·영상 렌더를 완료했다.

| 모델 | 평균 달성음 | 안전 시간축 완주 |
| --- | ---: | ---: |
| 초기 | 0.2979/67 | 1022/1024 |
| 500업데이트 | 5.1104/67 | 892/1024 |
| 1000업데이트 | 5.9961/67 | 949/1024 |
| 1500업데이트 | 5.6875/67 | 1012/1024 |
| 2000업데이트 | 5.6045/67 | 887/1024 |

평가한 학습 모델 중 최고는 1000업데이트(평균 5.9961/67음), 최종은 5.6045/67음이다. 최고 대비 최종 변화는 -0.3916음이다.

고정 1024환경 첫 종료곡의 평균이며 물리 실패도 분모에 포함한다. 달성음은 연속 clean 문턱의 학습 지표이며 음 끝까지 완전한 유지나 실제 음향 성공률이 아니다. 한 곡·한 seed의 결과로 보상 항의 인과 효과나 일반화를 확정하지 않는다.

- [학습 로그 분석](analysis_final/analysis.md)
- [고정1024환경 평가](checkpoint_evaluation.json)
- [로그·저장 검증](training_verification.json)

- [latest_fullbody_60fps.mp4](/home/ajou/yigyu/3/docs/2026-10-24/guitar_learning_long_training_v17/latest_fullbody_video/latest_fullbody_60fps.mp4)
- [latest_left_hand_60fps.mp4](/home/ajou/yigyu/3/docs/2026-10-24/guitar_learning_long_training_v17/latest_hand_video/latest_left_hand_60fps.mp4)
- [best_fullbody_60fps.mp4](/home/ajou/yigyu/3/docs/2026-10-24/guitar_learning_long_training_v17/best_fullbody_video/best_fullbody_60fps.mp4)
- [best_left_hand_60fps.mp4](/home/ajou/yigyu/3/docs/2026-10-24/guitar_learning_long_training_v17/best_hand_video/best_left_hand_60fps.mp4)
