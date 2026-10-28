# B250 영상의 별도 참고 기록

이 문서는 기존3조건 비교 독립검수 이후 root가 추가한 영상·QA 기록의 안내다. 기존 비교 수치나 검수 범위를 소급 변경하지 않는다.

[영상 설명과 QA](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/corrected_source_v3/native_video_B_best250/README.md) · [손 영상](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/corrected_source_v3/native_video_B_best250/hand.mp4) · [전신 영상](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/corrected_source_v3/native_video_B_best250/fullbody.mp4)

150·200·250회가128/128 달성으로 동률이어서 촬영 전 가장 최근인250회를 선택했다. 영상은 원래128환경 배치의 **env0 첫 시도**다. 이 시도도 달성·유지100%, 오압현0이지만 전체128평가를 대신하지 않는다. 마지막300회는65/128로 저하됐다.

영상 QA는 종료코드0·인코더0·scene 종료·모델 불변·685입력 검증과 구도 확인을 기록했다. 고정 기타·유한 팔 손목 안내·중지1음 조건이며 엄지035 기준과 다른 손가락 B 제어가 함께 있다.

[env0 하중 기록](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/corrected_source_v3/native_video_B_best250/qa/env0_load.json)에 따르면, 음 구간의 저장60Hz 끝점8개에서 중지 distal body resultant 중앙값53.17N·최대56.28N, 엄지 중앙값41.44N·최대45.59N이다. 높은 하중은 남아 있다. **전체128환경·240Hz 분포·실제 현 압력·접촉 상대의 증거로 확대하지 않는다.** 자유 기타·전곡·자연스러움·학습 안정성도 이 영상만으로 입증되지 않는다.
