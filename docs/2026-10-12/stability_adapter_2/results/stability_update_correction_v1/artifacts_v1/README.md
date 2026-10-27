# 이전 ON/OFF 결과와 갱신 보정 상한

![이전 ON/OFF episode·평가·t0 KL과 새 보정 그룹 상한 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_v1/previous_analysis_summary_v1.png)

이 그림은 봉인된 [previous_analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/previous_analysis_v1.json)과 보정 계획의 **이전 저장 결과만 오프라인 분석**한 것입니다. 아래 영상도 기존 `stability_priority_training_v1`의 update 1 native 평가 영상입니다. 새 보정 설정의 native 결과가 아니며, 새 설정의 효과나 성공을 판정하지 않습니다.

## 이전 실행에서 관측한 결과

ON은 54 update 동안 35개 episode를 완료했으며 35개 모두 유한 관절 속도 안전 종료였습니다. 초기 정책 평가는 7.567초에, update 1 평가는 5.533초에 종료했고, 둘 다 R_Elbow_y 속도가 50 rad/s 안전 한계를 넘었습니다. OFF는 40 update 동안 11개 episode를 완료했습니다. 그중 8개는 16.367초 horizon을 완료했고 3개는 속도 안전 종료였습니다. 두 조건 모두 공동 음악 성공은 0회였습니다. 매 update는 optimizer 1 step 뒤 KL stop으로 종료됐습니다.

아래 초기·update 1 위치 허용범위 밖 비율은 ON 53.5%·91.0%, OFF 95.1%·97.1%입니다. 각 평가는 서로 다른 시점의 결과이므로 이 비율만으로 안정성 전체나 성공을 단정하지 않습니다.

## t0 KL과 보정 그룹 상한

초기 관측에서 초기→update 1로 계산한 해석적 Gaussian KL은 ON 328.056, OFF 493.168입니다. 같은 초기 상태에서 계산했지만 **actor와 RMS 변화가 합쳐진 값**입니다. rollout 평균도 아니며 actor와 RMS 각각의 기여를 분리한 수치도 아닙니다.

이전 ON 초기 요청 보정의 그룹별 최대치는 body 0.0377, head 0.4465, arm 1.0775, finger 0.7654 rad였습니다. 새 후보 상한은 body ±0.03, head ±0.10, arm ±0.30, finger ±0.20 rad입니다. 이 값은 요청 보정 출력에 대한 제한이고, 최종 목표는 모델 관절 한계와 기존 rate owner의 제한도 받습니다.

후속 보정 후보는 학습률 3e-5, 초기 관측 RMS 고정, 평균 0 actor·새 critic·새 Adam으로 시작합니다. optimizer step 뒤 rollout 전체의 해석적 old→new Gaussian KL 평균이 0.02 초과 또는 비유한이면 모델과 Adam을 함께 복원하고 같은 gradient를 학습률 절반으로 다시 시도하며 최대 8회까지 검사합니다. 이 변경의 개선 여부는 새 native 실행 결과를 확인한 뒤 판단해야 합니다.

이번 분석은 원래 길이 스트랩 ON, 자유 기타, 두 baseline을 유지하는 후보 설정을 설명합니다. 아래 영상은 이전 ON/OFF 정책의 저장 결과를 구별해 보여줄 뿐입니다.

### 이전 ON 평가 영상

![이전 stability_priority_training_v1 ON update 1 whole body native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/long_on_v1/evaluations/update_000001/native/episode_0001/media/whole_body.mp4)

### 이전 OFF 평가 영상

![이전 stability_priority_training_v1 OFF update 1 whole body native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/long_off_v1/evaluations/update_000001/native/episode_0001/media/whole_body.mp4)

## 입력·생성물 출처

[분석 그림·producer 입력 SHA-256 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_v1/analysis_provenance_v1.json)에는 producer, 이전 분석 JSON, 보정 계획, 두 기존 native 영상 및 그림의 해시가 기록돼 있습니다. producer는 새 물리 실행이나 학습을 수행하지 않습니다.
