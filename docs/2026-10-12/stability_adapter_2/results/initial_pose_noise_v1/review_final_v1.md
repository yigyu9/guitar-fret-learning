# 초기 배치 노이즈 최종 독립 검수

요약 판정: **문제없음 — 완료된 초기 배치 기능·단일 갱신·두 고정 평가 범위에 한정합니다.** 미결 Critical은 없습니다. 기타 안정화나 음악 수행 성공을 인증하지 않습니다.

## 확인한 범위

- [사전 소스 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/source_before_native_v1.json:1)의 7파일 및 [추가 reset probe 소스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/source_addition_probe_v1.json:1)를 현재 SHA와 대조했습니다. 기존 제어·물리·보상 계약을 유지하며, 초기화 이후 기타/손 자세를 강제로 덮어쓰는 경로는 없습니다. IK는 bank 생성 때 수행하고 reset은 검증된 초기각을 불러옵니다. PREP에서도 기존 PD·정책 제어는 계속됩니다.
- [bank·reset 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/analysis_v1.json:1)의 12검사를 원자료와 대조했습니다. 32제안 중 27개가 절대 회전 허용집합에서 제외되고 기준 1개+노이즈 4개가 남았습니다. 팔24만 변경되고 body/head/finger 초기각은 유지됩니다. 최대 실제 native palm 위치 오차는 0.0001717366mm입니다. 실제 2환경×3회 fresh reset에서 선택 reference 전체 native 상태와 일정한 ABI를 확인했습니다.
- CP320의 model/RMS 전체 복사, 새 Adam·카운터0 및 실제 N4 CUDA 1갱신/256전이/승인 optimizer4회/KL 0.01961852/RMS 고정을 확인했습니다. 이는 새 초기분포의 warm-start이며 기존 optimizer·RNG·물리 에피소드의 exact resume가 아닙니다.
- [전체 native 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/verification_v1.json:1)의 18검사와 입력 SHA를 대조했습니다. 평가1/4는 같은 신규 smoke checkpoint1을 사용한 고정 index1/4 평가입니다. 각각 982제어/3928물리 step/16.366667물리초를 완료했고, 스트랩 51,064회·금지 API0·안전 중단없음·baseline 동결을 확인했습니다. 4영상의 원본/보관본 SHA와 492프레임·MP4 16.4초를 구분했습니다.
- 실제 PNG 2장의 표·전신/손 프레임을 원자료와 육안 대조했습니다. [정정 설명 V2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/artifacts_v1/README_V2.md:1), [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/CHANGED_FILES_V1.md:1), [영상 색인 V10](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V10.md:1)의 절대 경로·실제 줄을 확인했습니다. 산출물 provenance의 입력/출력 63개 SHA, 네 영상 SHA 및 main4 완료 append의 원문 prefix를 대조했습니다. 기존 설명과 산출물은 보존되어 있습니다.

## Warning

- [initial_pose_noise_v1.py:54](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_noise_v1.py:54): 명시적 index 선택에도 일반 bank의 `sampling` 문자열을 기록합니다. 현재 고정 평가 여부는 `attempt.evaluation_index`와 실제 selection index로 확인했고 [결과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/README.md:19)에 한계가 공개되어 있습니다. 향후 새 버전에서 실제 `selection_method`를 분리하는 것을 권장합니다. 소비된 원본의 변경이나 이번 평가 재실행은 필요하지 않습니다.

## 결과의 한계

평가1/4의 음악 성공은 각각 0/42입니다. 공통 고정 world actor-root box 밖 시간은 55.8045%/51.3238%, 최대 이탈은 45.7416/40.4862cm이며 후기 기타 이탈이 남습니다. SO(3) 진단은 각 평가의 자체 초기 orientation 대비입니다. 초기 손 배치 검증을 후기 지지·연주 성공으로 확대할 수 없습니다.

검증된 5개 bank의 균일 이산 선택은 제안 범위 전체의 연속 균일분포가 아닙니다. 회전 제한은 world rotation-vector 각 성분이며 Euler 각이나 전체 SO(3) 각 제한과 다릅니다. source hull clear는 PhysX cooked 접촉·힘 인증이 아니며, 단일 갱신 smoke와 두 고정 평가로 노이즈의 일반적 효과를 단정할 수 없습니다.

검증 JSON SHA256: `6ef5414933a7bf782ab716a5c7c6ef57bb7a71aea099d8ad9341855f5693fc4e`. 검수자는 이 새 리뷰 파일만 작성했으며 추가 물리 실행·추론·학습은 하지 않았습니다. 이후 전체 봉인·inventory는 root의 별도 작업입니다.
