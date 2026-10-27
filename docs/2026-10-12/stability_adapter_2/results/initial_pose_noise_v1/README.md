# 기타·양손 연동 초기 노이즈 결과

초기 기타 위치·회전을 바꾸고 양팔 초기각을 함께 조정하는 환경을 구현했습니다. 기타를 움직이는 동안 손을 붙이는 방식이 아니라, 검증된 기타·양손 배치로 시작한 뒤 기존 상체81관절 PD와 정책으로 제어합니다.

## 적용 범위

- 제안 범위: world actor-root x/y ±5mm, z 0–5mm. world rotation-vector 각 성분 ±1°이며 Euler 축별 각도나 SO(3) 전체 각도 ±1°와 다릅니다. 회전 중심은 기타 actor-root입니다.
- 초기 양팔24관절만 IK 조정, 기준±0.15rad/모델 한계. 실제 통과 후보의 최대 관절 변화는1.24364°였습니다. body9/head6/finger42 초기각·root/하체·초기 속도0·원본 스트랩 길이는 유지합니다. 이후 정책은 기존 상체81을 제어합니다.
- 32개 제안 중27개가 절대 회전 허용집합을 벗어나 제외됐습니다. 기준1개+노이즈4개가 source geometry와 실제 native 초기 검사를 통과했습니다. 각 에피소드에서 이5개를 균일 이산 선택하며 전체 ±5mm/±1°의 연속 균일분포는 아닙니다. 실제 제안·거절 기록을 보존했습니다.
- 양손 palm의 기타 기준 위치·방향을 초기 IK 목표로 유지하고 손가락 모양을 그대로 옮깁니다. 최대 native palm 위치 오차0.000171737mm, 회전 오차약0.000030123°입니다. 정적 source hull 검사를 PhysX cooked 접촉/힘 인증으로 해석하지 않습니다.

## 실제 검증

CPU4검사, 실제2환경×3초기화(선택[[2,3],[1,4],[0,1]])에서 ABI 일정/선택 reference 전체 native exact를 확인했습니다. 실제4환경의 초기 선택은[2,3,1,2]였으며 CUDA1갱신/256transition/승인 optimizer4회/KL0.01961852≤.02/RMS고정을 통과했습니다. CP320의 model/RMS 전체를 exact 복사하고 새 초기분포 ABI·fresh Adam/counters0로 시작했습니다. 기존 물리 에피소드/RNG/optimizer의 exact resume는 아닙니다. 기존 fixed-reference preload 보정량을 새 q_ref에 한 번만 더합니다.

노이즈1/4 두 대표 평가에서 같은 신규 smoke checkpoint1을 사용했습니다. 각각2초 PREP를 포함한 전체16.366667물리초/982제어/3928physics를 마쳤고, 스트랩51,064=13×3,928호출·금지 API0·안전 중단없음·두 baseline 동결을 확인했습니다. 각 전신/손 MP4는492frame/16.4초입니다. 음악 성공은각0/42이고 최대 actor-root box 이탈은45.74/40.49cm로 큰 후기 이동이 남습니다. 초기 배치 기능 검증과 기타 안정화·연주 성공을 구분합니다.

## 평가 선택 메타데이터 주의

학습과 반복reset은 무작위 선택입니다. 영상 두 개는 --eval-index1/4로 고정 선택했습니다. 원본 selection.sampling 문자열은 일반 bank sampling을 설명하며 고정 평가에서도 동일하게 저장된 v1 메타데이터 한계가 있습니다. 실제 선택 방식은 attempt.evaluation_index와 native selection.index를 우선합니다. 원본은 보존하며 미래 버전에서 selection_method를 분리할 예정입니다.

## 근거

- [계획](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_NOISE_PLAN_V1.md:1)
- [실제bank·병렬·반복reset 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/analysis_v1.json:1)
- [전체native·warmstart 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/verification_v1.json:1)
- [사전 독립검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/review_preflight_v1.md:1)


## 이미지·영상과 변경 경로

[한글 이미지·전체 영상 설명 정정본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/artifacts_v1/README_V2.md:1) · [영상 색인 V10](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V10.md:1) · [구현·문서 실제 줄 번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/CHANGED_FILES_V1.md:1). 기존 README/provenance/producer/영상은 보존합니다.
