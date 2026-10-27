# 학습 전후 결정적 평가 영상

[결과와 해석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/README.md) · [에피소드별 원자료 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/policy_comparison.json).

아래는 실제 Isaac Gym 카메라의 전체 몸/손 확대 영상이다. 각 반복은 준비0초부터 물리3.466667초의 시간표 종료까지 녹화했다. 준비는 앞2초이며 정책 구간은 뒤1.466667초다. Root 고정·하체 유한·자유 기타 조건이다. 학습 전후 모두 지정 압현 유지/타현 매칭0이며 연주 완성 영상이 아니다.

학습 전 첫 반복 전체 몸:

![초기정책 평가: 준비부터종료까지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/eval_before_v1/episode_0000/media/whole_body.mp4)

4업데이트 후 첫 반복 전체 몸:

![4업데이트후 평가: 준비부터종료까지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/eval_after_v1/episode_0000/media/whole_body.mp4)

| 체크포인트/반복 | 전체몸 | 손확대 |
| --- | --- | --- |
| 학습전0 | [영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/eval_before_v1/episode_0000/media/whole_body.mp4) | [영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/eval_before_v1/episode_0000/media/hands.mp4) |
| 학습전1 | [영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/eval_before_v1/episode_0001/media/whole_body.mp4) | [영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/eval_before_v1/episode_0001/media/hands.mp4) |
| 학습후0 | [영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/eval_after_v1/episode_0000/media/whole_body.mp4) | [영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/eval_after_v1/episode_0000/media/hands.mp4) |
| 학습후1 | [영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/eval_after_v1/episode_0001/media/whole_body.mp4) | [영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/eval_after_v1/episode_0001/media/hands.mp4) |

각 영상은1280×720/30fps/105프레임/3.5초다. 물리 시각0..3.466667초의 양 끝 프레임을 포함하므로 MP4 길이와 실제 종료 시각은 한 프레임만큼 다르다. 총420개 capture 기록/840PNG/8MP4를 보존했고 모든 capture의 render_preserves_states가 true다. 별도 ffprobe와 SHA 대조를 통과했다.

정현파 진단은 원자료 측정용으로 영상 없이 수행했다. 실패 움직임을 이 정책 평가 영상으로 대신 설명하지 않으며 각 실패는 README의 native240Hz 수치와 도표를 참조한다. 두 반복의 재현은 native 상태/행동/음악 측정의 exact 비교이며 PNG/MP4 파일의 서로 간 bit-identical을 뜻하지 않는다.
