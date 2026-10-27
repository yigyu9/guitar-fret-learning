# 병렬 수집 CP315→CP316 검증

## 검증된 범위

`verification_v1.json`은 22개 항목 모두 통과했습니다. N2 probe는 두 worker를 각각 5초(300 control/1,200 physics step) 실행했습니다. 시작 native 상태는 정확히 같았고 서로 다른 action 뒤 상태는 달라졌습니다. 초기 action joint q는 실제 native 값이며, physical reset noise는 꺼져 있었습니다. forbidden API 호출은 0회였습니다.

N4T64 수집은 GPU 1에서 네 환경×64 step, 총 256 transition으로 CP315에서 CP316까지 실제 갱신했습니다. 수집 시간은 4.4516초(해당 배치의 57.5069 transition/s), 총 갱신 시간은 4.8448초였습니다. 업데이트의 analytic KL은 0.019905004650354385로 gate 이내였고, RMS는 고정됐으며 model/Adam/RMS/RNG 채택 수치가 정확히 일치했습니다. 이는 해당 배치의 실측치이며 이전 처리량과의 비교나 일반적인 속도 향상을 뜻하지 않습니다.

## 평가 영상과 패널

아래 CP315와 CP316 프레임은 각각 따로 수행한 단일 환경 결정론 평가입니다. 병렬 수집 네 worker가 같은 장면에서 연주한 것으로 해석하면 안 됩니다. 전신과 손 이미지는 각 평가의 0초, 2초, 마지막 프레임(16.3667 physics seconds)을 보여줍니다.

![CP315 및 CP316 단일 환경 native 전신·손 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/artifacts_v1/cp315_cp316_native_frames_v1.png)

두 평가 모두 전체 16.3667 physics seconds를 완료했습니다(3,928 physics step, 982 control step, 492 frame; MP4 16.4초). 음악 성공은 두 평가 각각 0/42였고, strap은 켜져 있었으며 13회 호출됐습니다(physics 호출 0회). baseline 가중치는 고정됐습니다. forbidden API와 safety violation은 보고되지 않았습니다. 완주는 음악 성공 또는 성능 개선 판정이 아닙니다.

![CP315 초기 평가 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/CP315_whole_body.mp4)

![CP315 초기 평가 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/CP315_hands.mp4)

![CP316 갱신 평가 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/CP316_whole_body.mp4)

![CP316 갱신 평가 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/CP316_hands.mp4)

## 탐색 분포와 한계

초기 checkpoint의 body/head latent std 평균은 약 0.006738, arm/finger는 약 0.018315입니다. 단위는 무차원 latent 표준편차이며 관절 각도 단위가 아닙니다. physical reset randomization은 false였고 비디오 평가는 결정론적이므로 이 latent noise 값을 물리적 reset 변동이나 평가 영상의 각도 오차로 해석하지 않습니다.

새 N4T256 production run은 시작 초기 평가 중이며 마감 update는 1,140입니다. 전체 완료, 누적 처리량, 음악 성공은 아직 검증되지 않았습니다. 이 문서는 미래 평가 경로 또는 결과를 예상하거나 생성하지 않습니다.

## 근거 및 provenance

- [검증 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/verification_v1.json)
- [latent 분포 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/initial_noise_analysis_v1.json)
- [N2 probe 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/probe_v1/report.json)
- [복사 영상 매니페스트](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/manifest.json)
- [산출물 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/artifacts_v1/provenance_v1.json)
